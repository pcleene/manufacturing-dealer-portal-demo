"""
Utility functions for the OEMPartner Dealer Portal.
"""
from typing import Any, Dict, List, Union
from datetime import datetime
from bson import ObjectId


def serialize_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Serialize a MongoDB document for JSON response.
    Converts ObjectId to string and datetime to ISO format.
    
    Args:
        doc: MongoDB document dictionary
        
    Returns:
        Serialized dictionary safe for JSON
    """
    if doc is None:
        return None
    
    result = {}
    for key, value in doc.items():
        result[key] = serialize_value(value)
    return result


def serialize_value(value: Any) -> Any:
    """
    Serialize a single value for JSON response.
    
    Args:
        value: Any value from a MongoDB document
        
    Returns:
        JSON-serializable value
    """
    if isinstance(value, ObjectId):
        return str(value)
    elif isinstance(value, datetime):
        return value.isoformat()
    elif isinstance(value, dict):
        return serialize_doc(value)
    elif isinstance(value, list):
        return [serialize_value(item) for item in value]
    else:
        return value


def serialize_docs(docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Serialize a list of MongoDB documents.
    
    Args:
        docs: List of MongoDB document dictionaries
        
    Returns:
        List of serialized dictionaries
    """
    return [serialize_doc(doc) for doc in docs]

