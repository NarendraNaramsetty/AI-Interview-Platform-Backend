from rest_framework.views import exception_handler
from rest_framework import status

def custom_exception_handler(exc, context):
    """
    Custom exception handler to return consistent JSON error envelopes:
    {
        "success": false,
        "message": "Error details...",
        "errors": { ... }
    }
    """
    response = exception_handler(exc, context)

    if response is not None:
        errors = response.data
        message = "An error occurred during transaction execution."
        
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            message = "Validation Error"
        elif isinstance(errors, dict) and "detail" in errors:
            message = errors.pop("detail")
        elif isinstance(errors, list) and len(errors) > 0:
            message = errors[0]
            
        # Ensure errors is always a dictionary
        if not isinstance(errors, dict):
            errors = {"detail": errors}
            
        response.data = {
            "success": False,
            "message": message,
            "errors": errors
        }

    return response
