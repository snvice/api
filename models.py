from sqlmodel import SQLModel, Field
from typing import Optional


class Users(SQLModel, table=True):
    id: int = Field(primary_key=True, index=True)
    name: str
    password: str
    role: str


class Team(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True, index=True)
    name: str


class Hero(SQLModel, table=True):
    id: int = Field(primary_key=True, index=True)
    name: str
    age: Optional[int]
    power: str
    password: str
    team_id: Optional[int]
