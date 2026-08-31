from pydantic import BaseModel, EmailStr
from app.models import WorkspaceRole


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password_hash: str


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    username: str

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: EmailStr
    password_hash: str


class Token(BaseModel):
    access_token: str
    token_type: str


class WorkspaceCreate(BaseModel):
    name: str
    role: WorkspaceRole = WorkspaceRole.OWNER


class WorkspaceResponse(BaseModel):
    id: int
    name: str
    owner_id: int

    class Config:
        from_attributes = True


class WorkspaceUpdate(BaseModel):
    name: str


class MemberCreate(BaseModel):
    user_id: int
    role: WorkspaceRole = WorkspaceRole.MEMBER


class MemberResponse(BaseModel):
    user_id: int
    username: str
    email: EmailStr
    role: WorkspaceRole