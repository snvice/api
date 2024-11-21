from sqlmodel import create_engine

DATABASE_URL = f"postgresql+psycopg2://vicee:vicee@heroes_db:5432/heroes_db"

engine = create_engine(DATABASE_URL)


