from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.db import engine, get_db
from app.models import User
from app.security import hash_password
from app.schemas import (
    UserCreate,
    UserResponse,
)
from app.config import settings
from app.schemas import Token
from app.security import create_access_token, verify_password
from app.dependencies import get_current_user
from fastapi.security import OAuth2PasswordRequestForm
from app.routers import tasks, projects, workspaces


app = FastAPI(title="Project management")
app.include_router(tasks.router)
app.include_router(projects.router)
app.include_router(workspaces.router)

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
    existing_user = db.query(User).filter(
        User.email == user.email
        ).first()

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="email already registered"
        )
    existing_username = db.query(User).filter(
            User.username == user.username
            ).first()

    if existing_username:
        raise HTTPException(
                status_code=409,
                detail="username already registered"
            )

    new_user = User(
        email=user.email,
        username=user.username,
        password_hash=hash_password(user.password_hash)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/login", response_model=Token)
def Login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: Session = Depends(get_db)
        ):
    user = db.query(User).filter(User.email == form_data.username).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    access_token = create_access_token(
        user.id,
        settings.secret_key
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@app.get("/me", response_model=UserResponse)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user
