from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Base

# Using SQLite for portability and ease of setup
DATABASE_URL = "sqlite:///./farmplan.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
