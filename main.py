from fastapi import FastAPI
from sqlmodel import SQLModel
from database import engine
from router import admin, auth_user, auth_hero, hero

app = FastAPI(
    title="VaiCe",
    description=">>>",
    version="1.0.0"
)

SQLModel.metadata.create_all(engine)

# Auth routers first (both user and hero authentication)
app.include_router(auth_user.user_auth_router)
app.include_router(auth_hero.hero_auth_router)

# Then feature routers (admin and hero)
app.include_router(admin.admin_router)
app.include_router(hero.hero_router)
