from openai import OpenAI
from config import LLM_MODEL_NAME, LLM_CLIENT, DEMAND_FORECAST_WEEKS
from tools.sql_executor import run_sql_query
from tools.dynamic_schema import get_dynamic_schema, find_column
import json

class DemandAgent:
    def __init__(self):
        self.client = LLM_CLIENT
        self.model_name = LLM_MODEL_NAME
        self.allowed_tables = [
            'enrollment_rate_report',
            'country_level_enrollment_report',
            'available_inventory_report'
        ]
    
    def work(self, query: str, entities: dict) -> dict:
        trial_id = entities.get('trial_id')
        country = entities.get('country')
        
        # Get dynamic schema for enrollment_rate_report
        enroll_schema = get_dynamic_schema('enrollment_rate_report')
        if not enroll_schema['exists']:
            return {
                'decision': 'NO',
                'severity': 'MEDIUM',
                'risk_type': 'SHORTFALL',
                'weeks_of_cover': None,
                'reasoning': {
                    'technical': 'enrollment_rate_report table not found',
                    'regulatory': 'N/A',
                    'logistical': 'N/A'
                },
                'source_tables': self.allowed_tables,
                'recommended_action': 'Check database schema',
                'uncertainty': 'Unable to fetch demand data'
            }
        
        enroll_table = enroll_schema['table_name']
        
        # Find columns dynamically
        print(f"[DEMAND] Available columns in {enroll_table}: {enroll_schema['columns']}")
        
        country_col = find_column(enroll_table, ['country', 'location', 'region', 'site'])
        trial_col = find_column(enroll_table, ['trial', 'study', 'trial_id', 'study_id'])
        rate_col = find_column(enroll_table, ['enrollment_rate', 'rate', 'enrollment', 'enrolled', 'patients'])
        date_col = find_column(enroll_table, ['report_date', 'date', 'timestamp', 'time', 'week', 'month'])
        
        print(f"[DEMAND] Found columns - Country: {country_col}, Trial: {trial_col}, Rate: {rate_col}, Date: {date_col}")
        
        # If rate column not found, we can't do proper demand forecasting
        if not rate_col:
            print(f"[DEMAND] WARNING: No enrollment rate column found. Cannot calculate demand forecast.")
            return {
                'decision': 'NO',
                'severity': 'MEDIUM',
                'risk_type': 'SHORTFALL',
                'weeks_of_cover': None,
                'reasoning': {
                    'technical': f'Enrollment rate data not available in {enroll_table}. Available columns: {", ".join(enroll_schema["columns"][:5])}. This table structure does not support demand forecasting.',
                    'regulatory': 'N/A',
                    'logistical': 'N/A'
                },
                'source_tables': self.allowed_tables,
                'recommended_action': 'Use country_level_enrollment_report or study_level_enrollment_report for demand analysis, or provide enrollment rate data',
                'uncertainty': 'Enrollment rate data structure not compatible with forecasting model'
            }
        
        # Get schema for inventory table
        inv_schema = get_dynamic_schema('available_inventory_report')
        inv_table = inv_schema['table_name'] if inv_schema['exists'] else 'available_inventory_report'
        
        inv_country_col = find_column(inv_table, ['country', 'location', 'region'])
        inv_trial_col = find_column(inv_table, ['trial', 'study', 'trial_id'])
        qty_col = find_column(inv_table, ['available_quantity', 'quantity', 'qty', 'available'])
        
        if not all([country_col, trial_col, date_col]):
            return {
                'decision': 'NO',
                'severity': 'MEDIUM',
                'risk_type': 'SHORTFALL',
                'weeks_of_cover': None,
                'reasoning': {
                    'technical': 'Required columns (country, trial, date) not found in enrollment_rate_report',
                    'regulatory': 'N/A',
                    'logistical': 'N/A'
                },
                'source_tables': self.allowed_tables,
                'recommended_action': 'Check database schema',
                'uncertainty': 'Unable to fetch demand data'
            }
        
        sql_query = f"""
        WITH weekly_demand AS (
            SELECT
                "{country_col}" as country,
                "{trial_col}" as trial_id,
                AVG("{rate_col}") * 7 AS weekly_consumption
            FROM {enroll_table}
            WHERE "{date_col}"::date >= CURRENT_DATE - INTERVAL '28 days'
        """
        
        if trial_id:
            sql_query += f" AND \"{trial_col}\" ILIKE '%{trial_id}%'"
        if country:
            sql_query += f" AND \"{country_col}\" ILIKE '%{country}%'"
        
        sql_query += """
            GROUP BY country, trial_id
        ),
        available_stock AS (
            SELECT
        """
        
        if inv_country_col:
            sql_query += f'        "{inv_country_col}" as country,\n'
        if inv_trial_col:
            sql_query += f'        "{inv_trial_col}" as trial_id,\n'
        if qty_col:
            sql_query += f'        SUM("{qty_col}") AS total_inventory\n'
        else:
            sql_query += '        0 AS total_inventory\n'
        
        sql_query += f"""
            FROM {inv_table}
            WHERE 1=1
        """
        
        if trial_id and inv_trial_col:
            sql_query += f" AND \"{inv_trial_col}\" ILIKE '%{trial_id}%'"
        if country and inv_country_col:
            sql_query += f" AND \"{inv_country_col}\" ILIKE '%{country}%'"
        
        if inv_country_col and inv_trial_col:
            sql_query += f"""
            GROUP BY "{inv_country_col}", "{inv_trial_col}"
        """
        
        sql_query += f"""
        )
        SELECT
            d.country,
            d.trial_id,
            COALESCE(a.total_inventory, 0) AS total_inventory,
            d.weekly_consumption,
            CASE 
                WHEN d.weekly_consumption > 0 THEN 
                    COALESCE(a.total_inventory, 0) / d.weekly_consumption
                ELSE NULL
            END AS weeks_of_cover
        FROM weekly_demand d
        LEFT JOIN available_stock a
        ON d.country = a.country AND d.trial_id = a.trial_id
        WHERE COALESCE(a.total_inventory, 0) / NULLIF(d.weekly_consumption, 0) <= {DEMAND_FORECAST_WEEKS}
        """
        
        try:
            data = run_sql_query(sql_query)
        except Exception as e:
            return {
                'decision': 'NO',
                'severity': 'MEDIUM',
                'risk_type': 'SHORTFALL',
                'weeks_of_cover': None,
                'reasoning': {
                    'technical': f'SQL execution failed: {str(e)}',
                    'regulatory': 'N/A',
                    'logistical': 'N/A'
                },
                'source_tables': self.allowed_tables,
                'recommended_action': 'Check database connectivity',
                'uncertainty': 'Unable to fetch demand data'
            }
        
        prompt = f"""
You are a demand forecasting agent.

Task: Analyze enrollment velocity and project supply shortfall risk.

Rules:
- CRITICAL if weeks_of_cover < 2
- HIGH if weeks_of_cover < 4
- MEDIUM if weeks_of_cover < {DEMAND_FORECAST_WEEKS}

Data:
{json.dumps(data, indent=2)}

Return ONLY a JSON object with this exact structure:
{{
    "decision": "YES or NO",
    "severity": "CRITICAL or HIGH or MEDIUM",
    "risk_type": "SHORTFALL",
    "weeks_of_cover": number or null,
    "reasoning": {{
        "technical": "detailed analysis of demand vs supply",
        "regulatory": "N/A or relevant info",
        "logistical": "impact on distribution"
    }},
    "source_tables": {json.dumps(self.allowed_tables)},
    "recommended_action": "specific action to take"
}}

Return only JSON, no markdown or explanation.
"""
        
        try:
            print(f"[DEMAND] Sending query to LLM for analysis...")
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000
            )
            print(f"[DEMAND] LLM response received")
            
            response_text = response.choices[0].message.content.strip().replace('```json', '').replace('```', '')
            print(f"[DEMAND] Raw response: {response_text[:200]}...")
            
            result = json.loads(response_text)
            print(f"[DEMAND] Parsed JSON successfully")
            print(f"[DEMAND] Decision: {result.get('decision')} | Severity: {result.get('severity')} | Weeks of Cover: {result.get('weeks_of_cover')}")
            return result
        except Exception as e:
            return {
                'decision': 'NO',
                'severity': 'MEDIUM',
                'risk_type': 'SHORTFALL',
                'weeks_of_cover': None,
                'reasoning': {
                    'technical': f'LLM processing failed: {str(e)}',
                    'regulatory': 'N/A',
                    'logistical': 'N/A'
                },
                'source_tables': self.allowed_tables,
                'recommended_action': 'Manual review required',
                'uncertainty': 'Unable to process demand data'
            }
