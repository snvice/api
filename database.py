from sqlmodel import create_engine
import os 
# DATABASE_URL = f"postgresql+psycopg2://vicee:vicee@heroes_db:5432/heroes_db"
# ... existing code ...
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
# ... existing code ...


