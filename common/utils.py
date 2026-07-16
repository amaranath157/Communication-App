from typing import Any, Optional
from rest_framework.response import Response
from rest_framework import status

def success_response(data: Any = None, message: str = "Success", status_code: int = status.HTTP_200_OK) -> Response:
    payload = {
        "success": True,
        "message": message,
        "data": data if data is not None else {}
    }
    return Response(payload, status=status_code)

def error_response(message: str, errors: Optional[Any] = None, status_code: int = status.HTTP_400_BAD_REQUEST) -> Response:
    payload = {
        "success": False,
        "message": message,
        "errors": errors if errors is not None else {}
    }
    return Response(payload, status=status_code)
