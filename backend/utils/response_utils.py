"""
Response utilities for API endpoints
"""
from flask import jsonify
from typing import Any, Dict, Optional

def success_response(data: Any = None, message: str = "Success") -> tuple:
    """Return success response"""
    response = {
        'success': True,
        'message': message
    }
    
    if data is not None:
        response['data'] = data
    
    return jsonify(response), 200

def error_response(message: str, status_code: int = 400, error_code: Optional[str] = None) -> tuple:
    """Return error response"""
    response = {
        'success': False,
        'message': message
    }
    
    if error_code:
        response['error_code'] = error_code
    
    return jsonify(response), status_code

def validation_error(message: str, errors: Dict = None) -> tuple:
    """Return validation error response"""
    response = {
        'success': False,
        'message': message
    }
    
    if errors:
        response['errors'] = errors
    
    return jsonify(response), 422