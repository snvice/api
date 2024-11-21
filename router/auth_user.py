from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from starlette import status
from database import engine
from pydantic import BaseModel
from typing import Annotated
from models import Users
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from datetime import timedelta, datetime, timezone
from jose import jwt, JWTError

user_auth_router = APIRouter(
    prefix='/auth_user',
    tags=['auth_user']
)


def create_user_db_session():
    with Session(engine) as session:
        yield session


UserDatabaseSession = Annotated[Session, Depends(create_user_db_session)]

# This password context is used in admin.py for hashing passwords
user_password_context = CryptContext(schemes=['bcrypt'], deprecated='auto', bcrypt__rounds=14)


class UserToken(BaseModel):
    access_token: str
    token_type: str


def authenticate_user(username: str, password: str, db) -> Users | None:
    """Authenticate a user with username and password"""
    try:
        user = db.query(Users).filter(Users.name == username).first()
        if not user or not user_password_context.verify(password, user.password):
            return None
        return user
    except Exception:
        return None


# Move to environment variables in production
USER_SECRET_KEY = '2dc74cee32c1e140282d6844aa5734ee35526c5ea98baa7388b1062a295ca889f'
USER_ALGORITHM = 'HS256'


def create_user_access_token(name: str, user_id: int, role: str, expires_delta: timedelta) -> str:
    """Create a JWT access token"""
    payload = {
        'sub': name,
        'id': user_id,
        'role': role,
        'exp': datetime.now(timezone.utc) + expires_delta
    }
    return jwt.encode(payload, USER_SECRET_KEY, algorithm=USER_ALGORITHM)


@user_auth_router.post("/token", response_model=UserToken)
async def login_for_access_token_user(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        db: UserDatabaseSession
) -> UserToken:
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    token = create_user_access_token(user.name, user.id, user.role, timedelta(minutes=20))
    return UserToken(access_token=token, token_type="bearer")


oauth2_scheme_admin = OAuth2PasswordBearer(tokenUrl="auth_user/token", scheme_name="admin_auth")

# This function is used in admin.py for authentication and authorization
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme_admin)]) -> dict:
    """Get current user from JWT token. Used in admin.py for protected routes"""
    try:
        payload = jwt.decode(token, USER_SECRET_KEY, algorithms=[USER_ALGORITHM])
        user_name: str = payload.get("sub")
        user_id: str = payload.get("id")
        user_role: str = payload.get("role")

        if user_name is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate user."
            )
        return {'username': user_name, 'id': user_id, "user_role": user_role}

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate user."
        )
