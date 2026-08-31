from pydantic import BaseModel, EmailStr


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