"""
API response utilities for consistent JSON responses
"""

from flask import jsonify
from datetime import datetime

def success_response(data=None, message=None, status_code=200):
    """
    Create a successful API response
    
    Args:
        data: Response data
        message: Optional success message
        status_code: HTTP status code (default: 200)
        
    Returns:
        Flask Response object
    """
    
    response = {
        'success': True,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if data is not None:
        response['data'] = data
    
    if message:
        response['message'] = message
    
    return jsonify(response), status_code

def error_response(error_message, status_code=400, error_code=None, details=None):
    """
    Create an error API response
    
    Args:
        error_message: Error message
        status_code: HTTP status code (default: 400)
        error_code: Optional error code
        details: Optional error details
        
    Returns:
        Flask Response object
    """
    
    response = {
        'success': False,
        'error': error_message,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if error_code:
        response['error_code'] = error_code
    
    if details:
        response['details'] = details
    
    return jsonify(response), status_code

def validation_error_response(validation_errors, message="Validation failed"):
    """
    Create a validation error response
    
    Args:
        validation_errors: List of validation errors
        message: Error message
        
    Returns:
        Flask Response object
    """
    
    return error_response(
        error_message=message,
        status_code=422,
        error_code='VALIDATION_ERROR',
        details={'validation_errors': validation_errors}
    )

def not_found_response(resource_type="Resource", resource_id=None):
    """
    Create a not found error response
    
    Args:
        resource_type: Type of resource (e.g., "Video", "Chapter")
        resource_id: ID of the resource
        
    Returns:
        Flask Response object
    """
    
    message = f"{resource_type} not found"
    if resource_id:
        message = f"{resource_type} with ID '{resource_id}' not found"
    
    return error_response(
        error_message=message,
        status_code=404,
        error_code='NOT_FOUND',
        details={
            'resource_type': resource_type,
            'resource_id': resource_id
        }
    )

def rate_limit_response(limit_info):
    """
    Create a rate limit error response
    
    Args:
        limit_info: Rate limit information
        
    Returns:
        Flask Response object
    """
    
    return error_response(
        error_message="Rate limit exceeded",
        status_code=429,
        error_code='RATE_LIMIT',
        details=limit_info
    )

def processing_error_response(stage, original_error):
    """
    Create a processing error response
    
    Args:
        stage: Processing stage where error occurred
        original_error: Original error message
        
    Returns:
        Flask Response object
    """
    
    return error_response(
        error_message="Video processing failed",
        status_code=500,
        error_code='PROCESSING_ERROR',
        details={
            'stage': stage,
            'original_error': str(original_error)
        }
    )

def paginated_response(items, pagination_info, message=None):
    """
    Create a paginated response
    
    Args:
        items: List of items
        pagination_info: Pagination metadata
        message: Optional message
        
    Returns:
        Flask Response object
    """
    
    data = {
        'items': items,
        'pagination': pagination_info
    }
    
    return success_response(data=data, message=message) 