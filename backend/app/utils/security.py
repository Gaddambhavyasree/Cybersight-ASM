import bcrypt
import secrets
import hashlib


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def generate_token() -> str:
    return secrets.token_urlsafe(32)


def generate_numeric_token(length: int = 6) -> str:
    return ''.join(secrets.choice('0123456789') for _ in range(length))


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
