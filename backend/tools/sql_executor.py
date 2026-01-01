from typing import List, Dict
import psycopg2
from db.connection import get_connection

def run_sql_query(query: str) -> List[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(query)
        results = cursor.fetchall()
        return [dict(row) for row in results]
    except psycopg2.Error as e:
        raise RuntimeError(f"SQL execution failed: {str(e)}")
    finally:
        cursor.close()
