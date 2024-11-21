from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from starlette import status
from database import engine
from pydantic import BaseModel
from typing import Annotated
from models import Hero
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from datetime import timedelta, datetime, timezone
from jose import jwt, JWTError

hero_auth_router = APIRouter(
    prefix='/auth_hero',
    tags=['auth_hero']
)


def create_hero_db_session():
    with Session(engine) as session:
        yield session


HeroDatabaseSession = Annotated[Session, Depends(create_hero_db_session)]

hero_password_context = CryptContext(schemes=['bcrypt'], deprecated='auto', bcrypt__rounds=14)


class HeroToken(BaseModel):
    access_token: str
    token_type: str


def authenticate_hero(username: str, password: str, db) -> Hero | None:
    """Authenticate a hero with username and password"""
    try:
        hero = db.query(Hero).filter(Hero.name == username).first()
        if not hero or not hero_password_context.verify(password, hero.password):
            return None
        return hero
    except Exception:
        return None


# Move to environment variables in production
HERO_SECRET_KEY = '2dc74cee32c1e140282d6844aa5734ee35526c5ea98baa7388b1062a295ca6cf'
HERO_ALGORITHM = 'HS256'


def create_hero_access_token(name: str, hero_id: int, expires_delta: timedelta) -> str:
    """Create a JWT access token"""
    payload = {
        'sub': name,
        'id': hero_id,
        'exp': datetime.now(timezone.utc) + expires_delta
    }
    return jwt.encode(payload, HERO_SECRET_KEY, algorithm=HERO_ALGORITHM)


@hero_auth_router.post("/token", response_model=HeroToken)
async def login_for_access_token_hero(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: HeroDatabaseSession
) -> HeroToken:
    hero = authenticate_hero(form_data.username, form_data.password, db)
    if not hero:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    token = create_hero_access_token(hero.name, hero.id, timedelta(minutes=20))
    return HeroToken(access_token=token, token_type="bearer")


oauth2_scheme_hero = OAuth2PasswordBearer(tokenUrl="auth_hero/token", scheme_name="hero_auth")

async def get_current_hero(token: Annotated[str, Depends(oauth2_scheme_hero)]) -> dict:
    """Get current hero from JWT token"""
    try:
        payload = jwt.decode(token, HERO_SECRET_KEY, algorithms=[HERO_ALGORITHM])
        hero_name: str = payload.get("sub")
        hero_id: str = payload.get("id")

        if hero_name is None or hero_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate hero."
            )
        return {'username': hero_name, 'id': hero_id}

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate hero."
        )

