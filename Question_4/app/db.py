from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.models import Base
import os

# Use writeable path in serverless (e.g., /tmp) if project directory is read-only
default_db_path = "./zus_outlets.db"

# If read-only FS, fall back to /tmp
test_path = default_db_path
try:
    # Attempt to open for append to test write permission
    with open(test_path, "a"):
        pass
except (IOError, OSError):
    default_db_path = "/tmp/zus_outlets.db"

# Allow overriding via environment variable
SQLITE_PATH = os.getenv("SQLITE_PATH", default_db_path)

SQLALCHEMY_DATABASE_URL = f"sqlite:///{SQLITE_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    Base.metadata.create_all(bind=engine) 