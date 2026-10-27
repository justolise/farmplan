from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.models import Base

# Using SQLite for portability and ease of setup
DATABASE_URL = "sqlite:///./farmplan.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    # Base.metadata.create_all(bind=engine) handles "IF NOT EXISTS" automatically 
    # in standard SQLAlchemy, but some environments/versions can trigger issues 
    # if there's a mismatch between the model and the existing table.
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:  # noqa: BLE001
        print(f"Database initialization notice: {e}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
