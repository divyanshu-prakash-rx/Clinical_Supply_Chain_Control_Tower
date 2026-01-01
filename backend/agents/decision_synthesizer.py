import google.generativeai as genai
from config import LLM_API_KEY, LLM_MODEL_NAME
import json

genai.configure(api_key=LLM_API_KEY)

class DecisionSynthesizerAgent:
    def __init__(self):
        self.model = genai.GenerativeModel(LLM_MODEL_NAME)
    
    def synthesize(self, agent_outputs: list) -> dict:
        prompt = f"""
You are a decision synthesis agent.

Task: Merge multiple agent outputs into a single cohesive decision.

Rules:
- Take the HIGHEST severity across all agents
- Combine all source_tables into one list
- Merge reasoning from all agents
- Provide a comprehensive recommended_action
- If any agent reports uncertainty, include it

Agent Outputs:
{json.dumps(agent_outputs, indent=2)}

Return ONLY a JSON object with this exact structure:
{{
    "decision": "YES or NO",
    "severity": "CRITICAL or HIGH or MEDIUM",
    "risk_type": "combined type or primary risk",
    "weeks_of_cover": number or null,
    "reasoning": {{
        "technical": "merged technical analysis",
        "regulatory": "merged regulatory analysis",
        "logistical": "merged logistical analysis"
    }},
    "source_tables": ["all unique tables from all agents"],
    "recommended_action": "comprehensive action plan",
    "uncertainty": "if any uncertainty exists"
}}

Return only JSON, no markdown or explanation.
"""
        
        try:
            response = self.model.generate_content(prompt)
            result = json.loads(response.text.strip().replace('```json', '').replace('```', ''))
            return result
        except Exception as e:
            severity_order = {'CRITICAL': 3, 'HIGH': 2, 'MEDIUM': 1}
            highest_severity = max(
                agent_outputs,
                key=lambda x: severity_order.get(x.get('severity', 'MEDIUM'), 1)
            )
            
            all_tables = []
            for output in agent_outputs:
                all_tables.extend(output.get('source_tables', []))
            
            return {
                'decision': highest_severity.get('decision', 'NO'),
                'severity': highest_severity.get('severity', 'MEDIUM'),
                'risk_type': 'MULTIPLE',
                'weeks_of_cover': None,
                'reasoning': {
                    'technical': 'Multiple agent analysis completed',
                    'regulatory': 'Multiple agent analysis completed',
                    'logistical': 'Multiple agent analysis completed'
                },
                'source_tables': list(set(all_tables)),
                'recommended_action': 'Review individual agent outputs',
                'uncertainty': f'Synthesis failed: {str(e)}'
            }
