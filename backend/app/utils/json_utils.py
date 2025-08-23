import json
from datetime import datetime, date, time
from decimal import Decimal
from uuid import UUID
from typing import Any

class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles non-serializable types"""
    
    def default(self, obj: Any) -> Any:
        # Handle datetime types
        if hasattr(obj, 'isoformat'):  # datetime, date, time
            return obj.isoformat()
        
        # Handle Decimal type
        if isinstance(obj, Decimal):
            return float(obj)
        
        # Handle UUID type
        if isinstance(obj, UUID):
            return str(obj)
        
        # Handle Timestamp (pandas/numpy)
        if obj.__class__.__name__ in ['Timestamp', 'Timedelta']:
            return str(obj)
        
        # Handle bytes
        if isinstance(obj, bytes):
            return obj.decode('utf-8', errors='ignore')
        
        # Let the base class default method raise the TypeError
        return super().default(obj)

def safe_json_dumps(obj: Any, **kwargs) -> str:
    """Safely serialize object to JSON string"""
    return json.dumps(obj, cls=CustomJSONEncoder, **kwargs)

def safe_json_loads(s: str, **kwargs) -> Any:
    """Safely deserialize JSON string"""
    return json.loads(s, **kwargs)