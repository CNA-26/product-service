import os
from sqlmodel import create_engine, SQLModel
from dotenv import load_dotenv

load_dotenv("../.env")

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set!")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

def create_db():
    SQLModel.metadata.create_all(engine)