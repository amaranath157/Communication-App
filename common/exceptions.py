from rest_framework.views import exception_handler
from .utils import error_response

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    
    if response is not None:
        return error_response(
            message="An error occurred",
            errors=response.data,
            status_code=response.status_code
        )
        
    return error_response(
        message=str(exc),
        status_code=500
    )
