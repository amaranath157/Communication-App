from dataclasses import dataclass
from typing import Optional

@dataclass
class UserDTO:
    id: int
    name: str
    email: str
    phone: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    bio: Optional[str] = None
    country: Optional[str] = None
    profile_photo: Optional[str] = None
    is_online: bool = False
    subscription_type: str = "FREE"

@dataclass
class UserUpdateDTO:
    name: Optional[str] = None
    phone: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    bio: Optional[str] = None
    country: Optional[str] = None
    profile_photo: Optional[str] = None
    is_online: Optional[bool] = None
