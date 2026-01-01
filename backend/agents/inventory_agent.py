from openai import OpenAI
from config import LLM_MODEL_NAME, LLM_CLIENT, EXPIRY_WARNING_DAYS, CRITICAL_EXPIRY, HIGH_EXPIRY
from tools.sql_executor import run_sql_query
from tools.dynamic_schema import get_dynamic_schema, find_column
import json
from datetime import datetime, timedelta

class InventoryAgent:
    def __init__(self):
        self.client = LLM_CLIENT
        self.model_name = LLM_MODEL_NAME
        self.allowed_tables = [
            'affiliate_warehouse_inventory',
            'available_inventory_report'
        ]
    
    def work(self, query: str, entities: dict) -> dict:
        trial_id = entities.get('trial_id')
        country = entities.get('country')
        
        schema = get_dynamic_schema('available_inventory_report')
        
        if not schema['exists']:
            return self._error_response('Table available_inventory_report not found')
        
        table_name = schema['table_name']
        
        lot_col = find_column(table_name, ['lot', 'batch'])
        expiry_col = find_column(table_name, ['expiry', 'expiration'])
        trial_col = find_column(table_name, ['trial', 'study'])
        location_col = find_column(table_name, ['location', 'country', 'site'])
        qty_col = find_column(table_name, ['qty', 'quantity', 'initial'])
        
        if not all([lot_col, expiry_col]):
            return self._error_response('Required columns not found in table')
        
        sql_query = f"""
        SELECT 
            "{lot_col}" as batch_id,
            "{expiry_col}" as expiry_date"""
        
        if trial_col:
            sql_query += f',\n            "{trial_col}" as trial_id'
        if location_col:
            sql_query += f',\n            "{location_col}" as country'
        if qty_col:
            sql_query += f',\n            "{qty_col}" as available_quantity'
        
        sql_query += f"""
        FROM {table_name}
        WHERE 1=1
        """
        
        if trial_id and trial_col:
            sql_query += f" AND \"{trial_col}\" ILIKE '%{trial_id}%'"
        if country and location_col:
            sql_query += f" AND \"{location_col}\" ILIKE '%{country}%'"
        
        sql_query += f" AND \"{expiry_col}\"::date <= CURRENT_DATE + INTERVAL '{EXPIRY_WARNING_DAYS} days'"
        
        try:
            data = run_sql_query(sql_query)
        except Exception as e:
            return self._error_response(f'SQL execution failed: {str(e)}')
        
        prompt = f"""
You are an inventory analysis agent.

Task: Analyze the following inventory data and classify expiry risk.

Rules:
- CRITICAL if expiry <= {CRITICAL_EXPIRY} days
- HIGH if expiry <= {HIGH_EXPIRY} days
- MEDIUM if expiry <= {EXPIRY_WARNING_DAYS} days

Data:
{json.dumps(data, indent=2)}

Return ONLY a JSON object with this exact structure:
{{
    "decision": "YES or NO",
    "severity": "CRITICAL or HIGH or MEDIUM",
    "risk_type": "EXPIRY",
    "weeks_of_cover": null,
    "reasoning": {{
        "technical": "detailed analysis",
        "regulatory": "N/A or relevant info",
        "logistical": "N/A or relevant info"
    }},
    "source_tables": {json.dumps(self.allowed_tables)},
    "recommended_action": "specific action to take"
}}

Return only JSON, no markdown or explanation.
"""
        
        try:
            print(f"[INVENTORY] Sending {len(data)} records to LLM for analysis...")
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000
            )
            print(f"[INVENTORY] LLM response received")
            
            response_text = response.choices[0].message.content.strip().replace('```json', '').replace('```', '')
            print(f"[INVENTORY] Raw response: {response_text[:200]}...")
            
            result = json.loads(response_text)
            print(f"[INVENTORY] Parsed JSON successfully")
            print(f"[INVENTORY] Decision: {result.get('decision')} | Severity: {result.get('severity')}")
            return result
        except Exception as e:
            print(f"[INVENTORY] ERROR: {str(e)}")
            return self._error_response(f'LLM processing failed: {str(e)}')
    
    def _error_response(self, error_msg: str) -> dict:
        return {
            'decision': 'NO',
            'severity': 'MEDIUM',
            'risk_type': 'EXPIRY',
            'reasoning': {
                'technical': error_msg,
                'regulatory': 'N/A',
                'logistical': 'N/A'
            },
            'source_tables': self.allowed_tables,
            'recommended_action': 'Check database connectivity and table schema',
            'uncertainty': 'Unable to fetch inventory data'
        }
