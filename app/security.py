from pwdlib import PasswordHash
from datetime import datetime, timedelta, timezone
from jose import jwt

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


ALGORITHM = "HS256"


def create_access_token(user_id: int, secret_key: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=30)

    payload = {
        "sub": str(user_id),
        "exp": expire,
    }

    return jwt.encode(payload, secret_key, algorithm=ALGORITHM)
