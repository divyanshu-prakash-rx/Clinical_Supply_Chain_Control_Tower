from flask import Flask, request, jsonify
from flask_cors import CORS
from agents.router_agent import RouterAgent
from tools.sql_executor import run_sql_query
from tools.audit_logger import log_decision
from db.connection import get_connection
from openai import OpenAI
from config import LLM_API_KEY, LLM_MODEL_NAME, LLM_CLIENT
import sys
import os
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_database_connection():
    print("Checking database connection...")
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        print("✓ Database connection successful")
        return True
    except Exception as e:
        print(f"✗ Database connection failed: {str(e)}")
        return False

def check_llm_connection():
    print("Checking LLM connection...")
    try:
        if not LLM_CLIENT:
            print("✗ LLM connection failed: No API key configured")
            return False
        
        response = LLM_CLIENT.chat.completions.create(
            model=LLM_MODEL_NAME,
            messages=[{"role": "user", "content": "Say 'OK'"}],
            max_tokens=10
        )
        if response.choices[0].message.content:
            print(f"✓ LLM connection successful (Model: {LLM_MODEL_NAME})")
            return True
        else:
            print("✗ LLM connection failed: No response from model")
            return False
    except Exception as e:
        print(f"✗ LLM connection failed: {str(e)}")
        return False

app = Flask(__name__)
CORS(app)

router = RouterAgent()

@app.route('/api/health', methods=['GET'])
def health_check():
    print("\n[API] Health check requested")
    return jsonify({'status': 'ok'}), 200

@app.route('/api/query', methods=['POST'])
def process_query():
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        print("\n" + "="*60)
        print(f"[API] New query received: {query}")
        print("="*60)
        
        if not query:
            print("[API] ERROR: Empty query")
            return jsonify({'error': 'Query parameter is required'}), 400
        
        print("[ROUTER] Classifying intent...")
        intent_result = router.classify_intent(query)
        
        if 'error' in intent_result:
            print(f"[ROUTER] ERROR: {intent_result['error']}")
            return jsonify({
                'error': 'Intent classification failed',
                'details': intent_result['error']
            }), 500
        
        intent = intent_result.get('intent', 'GENERAL')
        entities = intent_result.get('entities', {})
        
        print(f"[ROUTER] Intent: {intent}")
        print(f"[ROUTER] Entities: {entities}")
        print(f"[ROUTER] Routing to agent...")
        
        decision = router.route_to_agent(intent, query, entities)
        
        # Debug check
        if not isinstance(decision, dict):
            print(f"[API] ERROR: Agent returned {type(decision)} instead of dict!")
            print(f"[API] Value: {decision}")
            return jsonify({
                'error': 'Internal error: Agent returned invalid response type',
                'details': f'Expected dict, got {type(decision).__name__}'
            }), 500
         
        print(f"[AGENT] Decision: {decision.get('decision', 'N/A')}")
        print(f"[AGENT] Severity: {decision.get('severity', 'N/A')}")
        print(f"[AGENT] Risk Type: {decision.get('risk_type', 'N/A')}")
        
        if decision.get('decision') in ['YES', 'NO'] and 'uncertainty' not in decision:
            try:
                log_decision(decision)
                print("[AUDIT] Decision logged to database")
            except Exception as log_error:
                decision['log_warning'] = f'Failed to log decision: {str(log_error)}'
                print(f"[AUDIT] WARNING: {log_error}")
        
        print("\n" + "="*60)
        print("[API] FINAL RESPONSE JSON:")
        print("="*60)
        print(json.dumps(decision, indent=2))
        print("="*60 + "\n")
        
        print("[API] Query processed successfully")
        print("="*60 + "\n")
        return jsonify(decision), 200
        
    except Exception as e:
        print(f"[API] ERROR: Query processing failed - {str(e)}")
        print("="*60 + "\n")
        return jsonify({
            'error': 'Query processing failed',
            'details': str(e)
        }), 500

@app.route('/api/sql', methods=['POST'])
def execute_sql():
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        print("\n" + "="*60)
        print(f"[SQL] Direct SQL query received")
        print(f"[SQL] Query: {query[:100]}..." if len(query) > 100 else f"[SQL] Query: {query}")
        print("="*60)
        
        if not query:
            print("[SQL] ERROR: Empty query")
            return jsonify({'error': 'SQL query parameter is required'}), 400
        
        if not query.strip().upper().startswith('SELECT'):
            print("[SQL] ERROR: Non-SELECT query attempted")
            return jsonify({'error': 'Only SELECT queries are allowed'}), 403
        
        print("[SQL] Executing query...")
        result = run_sql_query(query)
        
        print(f"[SQL] Query successful - {len(result)} rows returned")
        print("="*60 + "\n")
        
        return jsonify({
            'success': True,
            'data': result,
            'row_count': len(result)
        }), 200
        
    except Exception as e:
        print(f"[SQL] ERROR: {str(e)}")
        print("="*60 + "\n")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/watchdog/run', methods=['GET'])
def run_watchdog():
    return jsonify({
        'status': 'not_implemented',
        'message': 'Watchdog scheduler endpoint - to be implemented'
    }), 200

if __name__ == '__main__':
    print("="*60)
    print("Clinical Supply Chain Control Tower - Backend Starting...")
    print("="*60)
    
    db_ok = check_database_connection()
    llm_ok = check_llm_connection()
    
    print("="*60)
    
    if not db_ok:
        print("WARNING: Database connection failed. Some features may not work.")
    
    if not llm_ok:
        print("WARNING: LLM connection failed. Agent queries will not work.")
    
    if db_ok and llm_ok:
        print("All systems operational. Starting server...")
    else:
        print("Starting server with warnings...")
    
    print("="*60)
    print()
    
    app.run(debug=True, host='0.0.0.0', port=5000)
