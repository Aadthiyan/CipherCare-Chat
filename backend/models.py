from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime

# --- Auth Models ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    roles: List[str] = []

class LoginRequest(BaseModel):
    username: str
    password: str

class SignupRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    full_name: str = Field(..., min_length=2, max_length=100)
    role: str = Field(default="resident", description="Role: attending, resident, or admin")
    department: Optional[str] = Field(default=None, description="Optional department name")

class OTPVerifyRequest(BaseModel):
    user_id: str
    otp_code: str = Field(..., min_length=6, max_length=6, description="6-digit OTP code")

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int = 3600

class UserResponse(BaseModel):
    username: str
    email: str
    full_name: str
    roles: List[str]
    department: Optional[str]
    created_at: datetime
    is_active: bool

class PasswordResetRequest(BaseModel):
    email: str

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)

# --- Patient / Search Models ---
class PatientSearchRequest(BaseModel):
    patient_id: str = Field(..., description="Pseudonymized patient ID")
    question: str = Field(..., min_length=3, max_length=1000, description="Clinical question")
    # Default top-k to 20, enforce maximum of 50
    retrieve_k: int = Field(20, ge=1, le=50)
    temperature: float = Field(0.7, ge=0.0, le=1.0)
    filter_doc_type: Optional[str] = None

class SourceDocument(BaseModel):
    type: str = "unknown"
    date: Optional[str] = "unknown"
    snippet: str
    similarity: float

class QueryResponse(BaseModel):
    query_id: str
    answer: str
    sources: List[SourceDocument]
    confidence: float
    disclaimer: str

# --- Error Models ---
class ErrorResponse(BaseModel):
    detail: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
