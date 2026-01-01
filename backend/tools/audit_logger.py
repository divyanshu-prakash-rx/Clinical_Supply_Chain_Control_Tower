from typing import Dict
from datetime import datetime
import json
from db.connection import get_connection

def log_decision(payload: Dict) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        insert_query = """
        INSERT INTO ai_decisions (
            decision_json,
            decision_type,
            source_tables,
            timestamp
        ) VALUES (%s, %s, %s, %s)
        """
        
        cursor.execute(
            insert_query,
            (
                json.dumps(payload),
                payload.get('risk_type', 'UNKNOWN'),
                json.dumps(payload.get('source_tables', [])),
                datetime.utcnow()
            )
        )
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"Failed to log decision: {str(e)}")
    finally:
        cursor.close()
