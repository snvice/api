from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from starlette import status
from database import engine
from pydantic import BaseModel, Field
from typing import Annotated
from models import Users, Team, Hero
from passlib.context import CryptContext
from router.auth_user import get_current_user

admin_router = APIRouter(
    prefix='/admin',
    tags=['admin']
)


def create_db_session():
    with Session(engine) as session:
        yield session


DatabaseSession = Annotated[Session, Depends(create_db_session)]
CurrentAdminUser = Annotated[dict, Depends(get_current_user)]


class CreateUserRequest(BaseModel):
    name: str = Field()
    password: str

    class Config:
        json_schema_extra = {
            "example": {
                "name": "admin",
                "password": "admin"
            }
        }


password_context = CryptContext(schemes=['bcrypt'], deprecated='auto', bcrypt__rounds=12)


@admin_router.post("/user", status_code=status.HTTP_201_CREATED)
async def create_user(user_data: CreateUserRequest, db: DatabaseSession):
    new_user = Users(
        name=user_data.name,
        password=password_context.hash(user_data.password),
        role="user"
    )
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return {"message": "User created successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.post("/team", status_code=status.HTTP_201_CREATED)
async def create_team(team_data: Team, current_user: CurrentAdminUser, db: DatabaseSession):
    if current_user is None or current_user.get('user_role') != 'admin':
        raise HTTPException(status_code=401, detail='Authentication Failed')
    new_team = Team(
        name=team_data.name,
    )
    try:
        db.add(new_team)
        db.commit()
        db.refresh(new_team)
        return {"message": "Team created successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


class CreateHeroRequest(BaseModel):
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


@admin_router.post("/hero", status_code=status.HTTP_201_CREATED)
async def create_hero(current_user: CurrentAdminUser, hero_data: CreateHeroRequest, db: DatabaseSession):
    if current_user is None or current_user.get('user_role') != 'admin':
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Authentication Failed'
        )

    try:
        # Check if hero already exists
        existing_hero = db.exec(select(Hero).where(Hero.name == hero_data.name)).first()
        if existing_hero:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Hero with this name already exists"
            )

        new_hero = Hero(
            name=hero_data.name,
            age=hero_data.age,
            power=hero_data.power,
            password=password_context.hash(hero_data.password)
        )

        db.add(new_hero)
        db.commit()
        db.refresh(new_hero)

        return {
            "message": "Hero created successfully",
            "hero_id": new_hero.id
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create hero: {str(e)}"
        )


@admin_router.get("/heroes", status_code=status.HTTP_200_OK)
async def get_all_heroes(current_user: CurrentAdminUser, db: DatabaseSession):
    if current_user is None or current_user.get('user_role') != 'admin':
        raise HTTPException(status_code=401, detail='Authentication Failed')
    heroes = db.exec(select(Hero)).all()
    if not heroes:
        raise HTTPException(status_code=404, detail="No heroes found")
    return heroes


@admin_router.get("/teams", status_code=status.HTTP_200_OK)
async def get_all_teams(current_user: CurrentAdminUser, db: DatabaseSession):
    if current_user is None or current_user.get('user_role') != 'admin':
        raise HTTPException(status_code=401, detail='Authentication Failed')
    teams = db.exec(select(Team)).all()
    if not teams:
        raise HTTPException(status_code=404, detail="No teams found")
    return teams

@admin_router.put("/hero/{hero_id}", status_code=status.HTTP_200_OK)
async def update_hero(
    hero_id: int,
    team_id: int,
    current_user: CurrentAdminUser,
    db: DatabaseSession
):
    if current_user is None or current_user.get('user_role') != 'admin':
        raise HTTPException(status_code=401, detail='Authentication Failed')

    try:
        hero = db.exec(select(Hero).where(Hero.id == hero_id)).first()
        if not hero:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Hero not found"
            )

        # Update team_id only
        hero.team_id = team_id
        
        db.add(hero)
        db.commit()
        db.refresh(hero)

        return {
            "message": "Hero team updated successfully",
            "hero_id": hero.id
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update hero team: {str(e)}"
        )


@admin_router.get("/heroes/no-team", status_code=status.HTTP_200_OK)
async def get_heroes_without_team(current_user: CurrentAdminUser, db: DatabaseSession):
    if current_user is None or current_user.get('user_role') != 'admin':
        raise HTTPException(status_code=401, detail='Authentication Failed')
    
    try:
        heroes = db.exec(select(Hero).where(Hero.team_id == None)).all()
        if not heroes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No heroes without team found"
            )
        return heroes

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch heroes without team: {str(e)}"
        )
