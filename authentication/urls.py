from django.urls import path
from authentication.controllers.auth_controller import (
    RegisterController, LoginController, LogoutController,
    ForgotPasswordController, VerifyOtpController, ResetPasswordController
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('register/',        RegisterController.as_view(),       name='register'),
    path('login/',           LoginController.as_view(),          name='login'),
    path('logout/',          LogoutController.as_view(),         name='logout'),
    path('refresh-token/',   TokenRefreshView.as_view(),         name='token_refresh'),
    path('forgot-password/', ForgotPasswordController.as_view(), name='forgot_password'),
    path('verify-otp/',      VerifyOtpController.as_view(),      name='verify_otp'),
    path('reset-password/',  ResetPasswordController.as_view(),  name='reset_password'),
]
