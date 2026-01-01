from openai import OpenAI
from config import LLM_MODEL_NAME, LLM_CLIENT
from tools.sql_executor import run_sql_query
from tools.dynamic_schema import get_dynamic_schema, find_column
import json

class QaAgent:
    def __init__(self):
        self.client = LLM_CLIENT
        self.model_name = LLM_MODEL_NAME
        self.allowed_tables = [
            're-evaluation',
            'qdocs'
        ]
    
    def work(self, query: str, entities: dict) -> dict:
        batch_id = entities.get('batch_id')
        
        table_name = 're-evaluation'
        
        # Get actual columns from database
        schema = get_dynamic_schema(table_name)
        
        if not schema['exists']:
            return self._error_response(f'Table {table_name} not found')
        
        # Try to find batch/lot column dynamically
        batch_col = find_column(table_name, ['batch', 'lot', 'batch_id', 'lot_id'])
        
        sql_query = f'SELECT * FROM "{table_name}" WHERE 1=1'
        
        if batch_id and batch_col:
            sql_query += f' AND "{batch_col}" ILIKE \'%{batch_id}%\''
        
        sql_query += ' LIMIT 50'
        
        try:
            print(f"[QA] Executing SQL: {sql_query}")
            data = run_sql_query(sql_query)
            print(f"[QA] Retrieved {len(data)} records")
        except Exception as e:
            return self._error_response(f'SQL execution failed: {str(e)}')
        
        prompt = f"""
You are a quality assurance and stability agent.

Task: Analyze re-evaluation history and stability data.

Rules:
- Decision = "YES" if past re-evaluation successful
- HIGH if re-evaluation required but not done
- MEDIUM if stability data inconclusive

Data:
{json.dumps(data, indent=2)}

Return ONLY a JSON object with this exact structure:
{{
    "decision": "YES or NO",
    "severity": "CRITICAL or HIGH or MEDIUM",
    "risk_type": "QA",
    "weeks_of_cover": null,
    "reasoning": {{
        "technical": "detailed analysis of stability and re-evaluation",
        "regulatory": "compliance status",
        "logistical": "N/A or relevant info"
    }},
    "source_tables": {json.dumps(self.allowed_tables)},
    "recommended_action": "specific action to take"
}}

Return only JSON, no markdown or explanation.
"""
        
        try:
            print(f"[QA] Sending {len(data)} records to LLM for analysis...")
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000
            )
            print(f"[QA] LLM response received")
            
            response_text = response.choices[0].message.content.strip().replace('```json', '').replace('```', '')
            print(f"[QA] Raw response: {response_text[:200]}...")
            
            result = json.loads(response_text)
            print(f"[QA] Parsed JSON successfully")
            print(f"[QA] Decision: {result.get('decision')} | Severity: {result.get('severity')}")
            return result
        except Exception as e:
            print(f"[QA] ERROR: {str(e)}")
            return self._error_response(f'LLM processing failed: {str(e)}')
    
    def _error_response(self, error_msg: str) -> dict:
        return {
            'decision': 'NO',
            'severity': 'MEDIUM',
            'risk_type': 'QA',
            'weeks_of_cover': None,
            'reasoning': {
                'technical': error_msg,
                'regulatory': 'N/A',
                'logistical': 'N/A'
            },
            'source_tables': self.allowed_tables,
            'recommended_action': 'Check database connectivity and table schema',
            'uncertainty': 'Unable to fetch QA data'
        }
