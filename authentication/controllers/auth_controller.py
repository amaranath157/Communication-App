from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from common.utils import success_response, error_response
from authentication.services.auth_service import AuthService
from authentication.serializers.auth_serializer import (
    RegisterSerializer, LoginSerializer,
    ForgotPasswordSerializer, VerifyOtpSerializer, ResetPasswordSerializer
)
from authentication.dto.auth_dto import RegisterDTO, LoginDTO, ForgotPasswordDTO, VerifyOtpDTO, ResetPasswordDTO
from rest_framework_simplejwt.tokens import RefreshToken

class RegisterController(APIView):
    permission_classes = [AllowAny]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auth_service = AuthService()

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            dto = RegisterDTO(**serializer.validated_data)
            success, message, data = self.auth_service.register_user(dto)
            if success:
                return success_response(data=data, message=message, status_code=201)
            return error_response(message=message)
        return error_response(message="Validation failed", errors=serializer.errors)

class LoginController(APIView):
    permission_classes = [AllowAny]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auth_service = AuthService()

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            dto = LoginDTO(**serializer.validated_data)
            success, message, data = self.auth_service.login_user(dto)
            if success:
                return success_response(data=data, message=message)
            return error_response(message=message, status_code=401)
        return error_response(message="Validation failed", errors=serializer.errors)

class LogoutController(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return error_response(message="Refresh token is required")
                
            token = RefreshToken(refresh_token)
            token.blacklist()
            return success_response(message="Logged out successfully")
        except Exception as e:
            return error_response(message="Invalid token", status_code=400)

class ForgotPasswordController(APIView):
    permission_classes = [AllowAny]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auth_service = AuthService()

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            dto = ForgotPasswordDTO(**serializer.validated_data)
            success, message, data = self.auth_service.forgot_password(dto)
            if success:
                return success_response(data=data, message=message)
            return error_response(message=message)
        return error_response(message="Validation failed", errors=serializer.errors)

class VerifyOtpController(APIView):
    permission_classes = [AllowAny]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auth_service = AuthService()

    def post(self, request):
        serializer = VerifyOtpSerializer(data=request.data)
        if serializer.is_valid():
            dto = VerifyOtpDTO(**serializer.validated_data)
            success, message, data = self.auth_service.verify_otp(dto)
            if success:
                return success_response(data=data, message=message)
            return error_response(message=message, status_code=400)
        return error_response(message="Validation failed", errors=serializer.errors)

class ResetPasswordController(APIView):
    permission_classes = [AllowAny]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auth_service = AuthService()

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            dto = ResetPasswordDTO(**serializer.validated_data)
            success, message, data = self.auth_service.reset_password(dto)
            if success:
                return success_response(data=data, message=message)
            return error_response(message=message, status_code=400)
        return error_response(message="Validation failed", errors=serializer.errors)
