from dataclasses import dataclass

@dataclass
class RegisterDTO:
    name: str
    email: str
    password: str

@dataclass
class LoginDTO:
    email: str
    password: str

@dataclass
class ForgotPasswordDTO:
    email: str

@dataclass
class VerifyOtpDTO:
    email: str
    otp: str

@dataclass
class ResetPasswordDTO:
    email: str
    new_password: str
