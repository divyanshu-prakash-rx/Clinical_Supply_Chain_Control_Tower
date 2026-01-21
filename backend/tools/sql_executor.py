from typing import List, Dict
import psycopg2
from db.connection import get_connection
from datetime import date, datetime
from decimal import Decimal

def serialize_value(value):
    """Convert non-JSON-serializable types to JSON-serializable formats"""
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    elif isinstance(value, Decimal):
        return float(value)
    elif value is None:
        return None
    else:
        return value

def run_sql_query(query: str) -> List[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(query)
        results = cursor.fetchall()
        # Convert each row to dict and serialize values
        return [{key: serialize_value(value) for key, value in dict(row).items()} for row in results]
    except psycopg2.Error as e:
        raise RuntimeError(f"SQL execution failed: {str(e)}")
    finally:
        cursor.close()
