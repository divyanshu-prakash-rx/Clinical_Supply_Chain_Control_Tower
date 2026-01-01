from typing import Dict

TABLE_REGISTRY = {
    'Affiliate_Warehouse_Inventory': ['warehouse_id', 'batch_id', 'quantity', 'location'],
    'Allocated_Materials': ['batch_id', 'order_id', 'quantity', 'expiry_date'],
    'Available_Inventory_Report': ['trial_id', 'country', 'available_quantity', 'batch_id'],
    'Enrollment_Rate_Report': ['trial_id', 'country', 'enrollment_rate', 'report_date'],
    'Country_Level_Enrollment': ['country', 'trial_id', 'total_enrolled', 'date'],
    'Distribution_Order_Report': ['order_id', 'destination', 'status', 'created_date'],
    'IP_Shipping_Timelines': ['order_id', 'origin', 'destination', 'lead_time_days'],
    'RIM': ['country', 'material_id', 'approval_status', 'approval_date'],
    'Material_Country_Requirements': ['material_id', 'country', 'required', 'compliance_status'],
    'Re_Evaluation': ['batch_id', 'evaluation_date', 'result', 'extended_expiry'],
    'QDocs': ['doc_id', 'batch_id', 'doc_type', 'status'],
    'Stability_Documents': ['batch_id', 'test_date', 'stability_status', 'notes']
}

COLUMN_ALIAS_MAP = {
    'Allocated_Materials': {
        'batch_id': ['batch_no', 'material_batch'],
        'expiry_date': ['exp_date', 'shelf_expiry'],
        'quantity': ['qty', 'available_qty']
    },
    'Enrollment_Rate_Report': {
        'enrollment_rate': ['rate', 'enrollment_velocity'],
        'report_date': ['date', 'reporting_date']
    }
}

def get_schema(table_name: str) -> Dict:
    if table_name not in TABLE_REGISTRY:
        return {'error': f'Table {table_name} not found in registry'}
    
    schema = {
        'table_name': table_name,
        'columns': TABLE_REGISTRY[table_name],
        'aliases': COLUMN_ALIAS_MAP.get(table_name, {})
    }
    
    return schema
