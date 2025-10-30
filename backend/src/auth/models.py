from pydantic import BaseModel, EmailStr
from typing import Optional, Literal
from datetime import datetime

class AuthUser(BaseModel):
    id: str
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    role: Literal["user"] = "user"
    email_confirmed: bool = False
    created_at: Optional[datetime] = None
    last_sign_in: Optional[datetime] = None

class GoogleTokenRequest(BaseModel):
    access_token: str

class AuthResponse(BaseModel):
    success: bool
    message: str
    user: Optional[AuthUser] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None

class RoleUpdateRequest(BaseModel):
    user_id: str
    new_role: Literal["user", "admin"]

class AccountStatusRequest(BaseModel):
    user_id: str
    status: Literal["active", "blocked"]

class EmailVerificationRequest(BaseModel):
    email: EmailStr

class CodeVerificationRequest(BaseModel):
    email: EmailStr
    code: str

class EmailVerificationResponse(BaseModel):
    success: bool
    message: str
    email: Optional[str] = None