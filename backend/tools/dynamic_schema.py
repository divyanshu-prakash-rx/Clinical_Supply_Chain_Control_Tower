from typing import Dict, List
from tools.sql_executor import run_sql_query

_schema_cache = None

def get_all_tables() -> List[str]:
    query = """
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    ORDER BY table_name
    """
    try:
        result = run_sql_query(query)
        return [row['table_name'] for row in result]
    except Exception as e:
        print(f"Error fetching tables: {str(e)}")
        return []

def get_table_columns(table_name: str) -> List[str]:
    query = f"""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = '{table_name}' 
    ORDER BY ordinal_position
    """
    try:
        result = run_sql_query(query)
        return [row['column_name'] for row in result]
    except Exception as e:
        print(f"Error fetching columns for {table_name}: {str(e)}")
        return []

def build_schema_registry() -> Dict[str, List[str]]:
    global _schema_cache
    
    if _schema_cache is not None:
        return _schema_cache
    
    print("Building dynamic schema registry from database...")
    schema = {}
    tables = get_all_tables()
    
    for table in tables:
        columns = get_table_columns(table)
        if columns:
            schema[table] = columns
    
    _schema_cache = schema
    print(f"Schema registry built with {len(schema)} tables")
    return schema

def get_dynamic_schema(table_name: str) -> Dict:
    schema_registry = build_schema_registry()
    
    table_name_normalized = table_name.lower().replace('_', '').replace('-', '')
    
    for db_table, columns in schema_registry.items():
        db_table_normalized = db_table.lower().replace('_', '').replace('-', '')
        if db_table_normalized == table_name_normalized:
            return {
                'table_name': db_table,
                'columns': columns,
                'exists': True
            }
    
    if table_name.lower() in [t.lower() for t in schema_registry.keys()]:
        return {
            'table_name': table_name.lower(),
            'columns': schema_registry.get(table_name.lower(), []),
            'exists': True
        }
    
    return {
        'table_name': table_name,
        'columns': [],
        'exists': False,
        'error': f'Table {table_name} not found in database'
    }

def find_column(table_name: str, search_terms: List[str]) -> str:
    schema = get_dynamic_schema(table_name)
    
    if not schema['exists']:
        return None
    
    columns = schema['columns']
    
    for term in search_terms:
        term_lower = term.lower()
        for col in columns:
            if term_lower in col.lower():
                return col
    
    return None
