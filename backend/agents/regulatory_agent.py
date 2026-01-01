from openai import OpenAI
from config import LLM_MODEL_NAME, LLM_CLIENT
from tools.sql_executor import run_sql_query
from tools.dynamic_schema import get_dynamic_schema, find_column
import json

class RegulatoryAgent:
    def __init__(self):
        self.client = LLM_CLIENT
        self.model_name = LLM_MODEL_NAME
        self.allowed_tables = [
            'rim',
            'material_country_requirements'
        ]
    
    def work(self, query: str, entities: dict) -> dict:
        country = entities.get('country')
        
        schema = get_dynamic_schema('rim')
        
        if not schema['exists']:
            return self._error_response('Table rim not found')
        
        table_name = schema['table_name']
        
        sql_query = f'SELECT * FROM {table_name} WHERE 1=1'
        
        country_col = find_column(table_name, ['country', 'location', 'region'])
        if country and country_col:
            sql_query += f' AND "{country_col}" ILIKE \'%{country}%\''
        
        sql_query += ' LIMIT 50'
        
        try:
            data = run_sql_query(sql_query)
        except Exception as e:
            return {
                'decision': 'NO',
                'severity': 'MEDIUM',
                'risk_type': 'REGULATORY',
                'weeks_of_cover': None,
                'reasoning': {
                    'technical': 'N/A',
                    'regulatory': f'SQL execution failed: {str(e)}',
                    'logistical': 'N/A'
                },
                'source_tables': self.allowed_tables,
                'recommended_action': 'Check database connectivity',
                'uncertainty': 'Unable to fetch regulatory data'
            }
        
        prompt = f"""
You are a regulatory compliance agent.

Task: Analyze ALL the regulatory data and provide ONE SINGLE consolidated decision.

Rules:
- CRITICAL if ANY status = "REJECTED"
- HIGH if ANY status = "PENDING" and urgent
- MEDIUM if ANY status = "PENDING"
- Decision = "NO" if there are ANY issues, "YES" if all clear

Data (multiple records):
{json.dumps(data, indent=2)}

IMPORTANT: Analyze ALL rows together and return ONLY ONE JSON object (not an array) with this exact structure:
{{
    "decision": "YES or NO",
    "severity": "CRITICAL or HIGH or MEDIUM",
    "risk_type": "REGULATORY",
    "weeks_of_cover": null,
    "reasoning": {{
        "technical": "N/A or relevant info",
        "regulatory": "consolidated analysis of ALL approval statuses - mention key findings",
        "logistical": "N/A or relevant info"
    }},
    "source_tables": {json.dumps(self.allowed_tables)},
    "recommended_action": "specific action to take based on most critical finding"
}}

Return ONLY ONE JSON object, NOT an array. No markdown or explanation.
"""
        
        try:
            print(f"[REGULATORY] Sending {len(data)} records to LLM for analysis...")
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000
            )
            response_text = response.choices[0].message.content.strip().replace('```json', '').replace('```', '')
            
            print(f"[REGULATORY] LLM response received")
            
            # Parse the response
            parsed = json.loads(response_text)
            
            # If LLM returns an array instead of single object, take the most critical one
            if isinstance(parsed, list):
                print(f"[REGULATORY] WARNING: LLM returned array of {len(parsed)} decisions, consolidating...")
                
                # Find the most critical decision
                severity_order = {'CRITICAL': 3, 'HIGH': 2, 'MEDIUM': 1}
                result = max(parsed, key=lambda x: severity_order.get(x.get('severity', 'MEDIUM'), 0))
                
                # Add note about consolidation
                result['reasoning']['regulatory'] = f"Consolidated from {len(parsed)} findings. Most critical: " + result['reasoning'].get('regulatory', '')
                print(f"[REGULATORY] Selected most critical: {result.get('severity')} - {result.get('decision')}")
            else:
                result = parsed
            
            print(f"[REGULATORY] Final decision: {result.get('decision')} | Severity: {result.get('severity')}")
            return result
        except Exception as e:
            print(f"[REGULATORY] ERROR: {str(e)}")
            return {
                'decision': 'NO',
                'severity': 'MEDIUM',
                'risk_type': 'REGULATORY',
                'weeks_of_cover': None,
                'reasoning': {
                    'technical': 'N/A',
                    'regulatory': f'LLM processing failed: {str(e)}',
                    'logistical': 'N/A'
                },
                'source_tables': self.allowed_tables,
                'recommended_action': 'Manual review required',
                'uncertainty': 'Unable to process regulatory data'
            }
    
    def _error_response(self, error_msg: str) -> dict:
        return {
            'decision': 'NO',
            'severity': 'MEDIUM',
            'risk_type': 'REGULATORY',
            'weeks_of_cover': None,
            'reasoning': {
                'technical': 'N/A',
                'regulatory': error_msg,
                'logistical': 'N/A'
            },
            'source_tables': self.allowed_tables,
            'recommended_action': 'Check database connectivity and table schema',
            'uncertainty': 'Unable to fetch regulatory data'
        }
