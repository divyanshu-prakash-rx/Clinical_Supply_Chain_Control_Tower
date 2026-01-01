from openai import OpenAI
from config import LLM_MODEL_NAME, LLM_CLIENT

class RouterAgent:
    def __init__(self):
        self.client = LLM_CLIENT
        self.model_name = LLM_MODEL_NAME
        self.conversation_memory = {}
    
    def classify_intent(self, query: str) -> dict:
        prompt = f"""
You are an intent classification agent for a clinical supply chain system.

Analyze this user query and return ONLY a JSON object with this structure:
{{
    "intent": "STOCK" | "DEMAND" | "LOGISTICS" | "REGULATORY" | "QA" | "GENERAL",
    "entities": {{
        "trial_id": "extracted trial name or null",
        "country": "extracted country or null",
        "batch_id": "extracted batch ID or null"
    }},
    "confidence": 0.0 to 1.0
}}

User Query: {query}

Return only the JSON object, no explanation.
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500
            )
            import json
            
            response_text = response.choices[0].message.content.strip()
            
            if response_text.startswith('```json'):
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            elif response_text.startswith('```'):
                response_text = response_text.replace('```', '').strip()
            
            result = json.loads(response_text)
            return result
        except json.JSONDecodeError as e:
            return {
                'intent': 'GENERAL',
                'entities': {},
                'confidence': 0.0,
                'error': f'JSON parsing failed: {str(e)}. Response was: {response.text[:200] if "response" in locals() else "No response"}'
            }
        except Exception as e:
            return {
                'intent': 'GENERAL',
                'entities': {},
                'confidence': 0.0,
                'error': str(e)
            }
    
    def route_to_agent(self, intent: str, query: str, entities: dict) -> dict:
        from agents.inventory_agent import InventoryAgent
        from agents.demand_agent import DemandAgent
        from agents.logistics_agent import LogisticsAgent
        from agents.regulatory_agent import RegulatoryAgent
        from agents.qa_agent import QaAgent
        
        agent_map = {
            'STOCK': ('Inventory Agent', InventoryAgent()),
            'DEMAND': ('Demand Agent', DemandAgent()),
            'LOGISTICS': ('Logistics Agent', LogisticsAgent()),
            'REGULATORY': ('Regulatory Agent', RegulatoryAgent()),
            'QA': ('QA Agent', QaAgent())
        }
        
        if intent in agent_map:
            agent_name, agent = agent_map[intent]
            print(f"[ROUTER] Selected: {agent_name}")
            print(f"[ROUTER] Calling {agent_name}.work()...")
            result = agent.work(query, entities)
            print(f"[{agent_name.upper()}] Processing complete")
            return result
        else:
            print(f"[ROUTER] No agent found for intent: {intent}")
            return {
                'decision': 'NO',
                'severity': 'MEDIUM',
                'risk_type': 'GENERAL',
                'reasoning': {
                    'technical': 'Unable to classify query intent',
                    'regulatory': 'N/A',
                    'logistical': 'N/A'
                },
                'source_tables': [],
                'recommended_action': 'Please rephrase your query',
                'uncertainty': 'Query intent unclear'
            }
