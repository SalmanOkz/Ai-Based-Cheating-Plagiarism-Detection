"""
Response utility functions
"""
from flask import jsonify
from typing import Dict, Any, Optional

def success_response(data: Optional[Dict] = None, message: str = "Success") -> Dict:
    """Create success response"""
    response = {
        'status': 'success',
        'message': message,
        'timestamp': __import__('datetime').datetime.now().isoformat()
    }
    if data:
        response['data'] = data
    return response

def error_response(message: str, error_code: str = "ERROR", 
                  details: Optional[Dict] = None) -> Dict:
    """Create error response"""
    response = {
        'status': 'error',
        'error_code': error_code,
        'message': message,
        'timestamp': __import__('datetime').datetime.now().isoformat()
    }
    if details:
        response['details'] = details
    return response

def validation_response(errors: Dict) -> Dict:
    """Create validation error response"""
    return error_response(
        message="Validation failed",
        error_code="VALIDATION_ERROR",
        details={'errors': errors}
    )