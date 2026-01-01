import psycopg2
from psycopg2.extras import RealDictCursor
from config import DB_NAME, DB_USER, DB_PASS, DB_HOST, DB_PORT

_connection = None

def get_connection():
    global _connection
    
    if _connection is None or _connection.closed:
        try:
            _connection = psycopg2.connect(
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASS,
                host=DB_HOST,
                port=DB_PORT,
                cursor_factory=RealDictCursor
            )
            _connection.autocommit = True
        except psycopg2.Error as e:
            raise ConnectionError(f"Database connection failed: {str(e)}")
    
    try:
        cursor = _connection.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
    except psycopg2.Error:
        _connection = None
        return get_connection()
    
    return _connection

def close_connection():
    global _connection
    if _connection and not _connection.closed:
        _connection.close()
        _connection = None
