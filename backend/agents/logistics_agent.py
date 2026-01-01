from openai import OpenAI
from config import LLM_MODEL_NAME, LLM_CLIENT
from tools.sql_executor import run_sql_query
from tools.dynamic_schema import get_dynamic_schema, find_column
import json

class LogisticsAgent:
    def __init__(self):
        self.client = LLM_CLIENT
        self.model_name = LLM_MODEL_NAME
        self.allowed_tables = [
            'distribution_order_report',
            'ip_shipping_timelines_report'
        ]
    
    def work(self, query: str, entities: dict) -> dict:
        country = entities.get('country')
        
        schema = get_dynamic_schema('ip_shipping_timelines_report')
        
        if not schema['exists']:
            return self._error_response('Table ip_shipping_timelines_report not found')
        
        table_name = schema['table_name']
        
        sql_query = f'SELECT * FROM {table_name} WHERE 1=1'
        
        dest_col = find_column(table_name, ['destination', 'location', 'country'])
        if country and dest_col:
            sql_query += f' AND "{dest_col}" ILIKE \'%{country}%\''
        
        sql_query += ' LIMIT 50'
        
        try:
            data = run_sql_query(sql_query)
        except Exception as e:
            return {
                'decision': 'NO',
                'severity': 'MEDIUM',
                'risk_type': 'LOGISTICS',
                'weeks_of_cover': None,
                'reasoning': {
                    'technical': f'SQL execution failed: {str(e)}',
                    'regulatory': 'N/A',
                    'logistical': 'Unable to assess shipping timelines'
                },
                'source_tables': self.allowed_tables,
                'recommended_action': 'Check database connectivity',
                'uncertainty': 'Unable to fetch logistics data'
            }
        
        prompt = f"""
You are a logistics analysis agent.

Task: Analyze shipping timelines and lead time feasibility.

Rules:
- CRITICAL if lead_time > 30 days
- HIGH if lead_time > 21 days
- MEDIUM if lead_time > 14 days

Data:
{json.dumps(data, indent=2)}

Return ONLY a JSON object with this exact structure:
{{
    "decision": "YES or NO",
    "severity": "CRITICAL or HIGH or MEDIUM",
    "risk_type": "LOGISTICS",
    "weeks_of_cover": null,
    "reasoning": {{
        "technical": "N/A or relevant info",
        "regulatory": "N/A or relevant info",
        "logistical": "detailed analysis of shipping timelines"
    }},
    "source_tables": {json.dumps(self.allowed_tables)},
    "recommended_action": "specific action to take"
}}

Return only JSON, no markdown or explanation.
"""
        
        try:
            print(f"[LOGISTICS] Sending {len(data)} records to LLM for analysis...")
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000
            )
            print(f"[LOGISTICS] LLM response received")
            
            response_text = response.choices[0].message.content.strip().replace('```json', '').replace('```', '')
            print(f"[LOGISTICS] Raw response: {response_text[:200]}...")
            
            result = json.loads(response_text)
            print(f"[LOGISTICS] Parsed JSON successfully")
            print(f"[LOGISTICS] Decision: {result.get('decision')} | Severity: {result.get('severity')}")
            return result
        except Exception as e:
            return {
                'decision': 'NO',
                'severity': 'MEDIUM',
                'risk_type': 'LOGISTICS',
                'weeks_of_cover': None,
                'reasoning': {
                    'technical': 'N/A',
                    'regulatory': 'N/A',
                    'logistical': f'LLM processing failed: {str(e)}'
                },
                'source_tables': self.allowed_tables,
                'recommended_action': 'Manual review required',
                'uncertainty': 'Unable to process logistics data'
            }
    
    def _error_response(self, error_msg: str) -> dict:
        return {
            'decision': 'NO',
            'severity': 'MEDIUM',
            'risk_type': 'LOGISTICS',
            'weeks_of_cover': None,
            'reasoning': {
                'technical': 'N/A',
                'regulatory': 'N/A',
                'logistical': error_msg
            },
            'source_tables': self.allowed_tables,
            'recommended_action': 'Check database connectivity and table schema',
            'uncertainty': 'Unable to fetch logistics data'
        }
