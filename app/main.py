from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.db import engine, get_db
from app.models import User
from app.security import hash_password
from app.schemas import UserCreate, UserResponse
from app.config import settings
from app.schemas import LoginRequest, Token
from app.security import create_access_token, verify_password
from app.dependencies import get_current_user

app = FastAPI(title="Project management")

'''hello there its me rasem this msg was written in the first
commit of this project,i hope somebody see it cuz that means
that i have completed my project'''


@app.get("/")
def root():
    return {"message": "Welcome to the Project Management API"}


@app.get("/health")
def health_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {"status": "healthy", "database": "connected"}

    except Exception as e:
        return {"status": "unhealthy", "database": str(e)}


@app.post("/users", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    new_user = User(
        email=user.email,
        username=user.username,
        password_hash=hash_password(user.password_hash)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def authenticate_user(email: str, password: str, db: Session) -> User:
    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def create_login_response(user: User) -> dict:
    access_token = create_access_token(user.id, settings.secret_key)

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@app.post("/login", response_model=Token)
def login(user_data: LoginRequest, db: Session = Depends(get_db)):
    """JSON login endpoint retained for API clients."""
    user = authenticate_user(user_data.email, user_data.password_hash, db)
    return create_login_response(user)


@app.post("/token", response_model=Token)
def token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """OAuth2 password-flow endpoint used by the OpenAPI Authorize dialog.

    Enter the user's email in the dialog's ``username`` field.
    """
    user = authenticate_user(form_data.username, form_data.password, db)
    return create_login_response(user)


