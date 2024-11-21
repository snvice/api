from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from starlette import status
from database import engine
from pydantic import BaseModel, Field
from typing import Annotated
from models import Hero
from passlib.context import CryptContext
from router.auth_hero import get_current_hero

hero_router = APIRouter(
    prefix='/hero',
    tags=['hero']
)


def create_db_session():
    with Session(engine) as session:
        yield session


DatabaseSession = Annotated[Session, Depends(create_db_session)]
CurrentHero = Annotated[dict, Depends(get_current_hero)]


class HeroUpdateRequest(BaseModel):
    name: str = Field()
    age: int = Field()
    power: str = Field()
    password: str

    class Config:
        json_schema_extra = {
            "example": {
                "name": "vice",
                "age": "555",
                "power": "mind reading",
                "password": "vice"
            }
        }


hero_password_context = CryptContext(schemes=['bcrypt'], deprecated='auto', bcrypt__rounds=14)  # Increased rounds for security


@hero_router.get("/", status_code=status.HTTP_200_OK)
async def get_hero_info(current_hero: CurrentHero, db: DatabaseSession):
    if current_hero is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Authentication Failed'
        )
    
    hero = db.exec(select(Hero).where(Hero.id == current_hero.get('id'))).first()
    if not hero:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hero not found"
        )
    
    return hero
