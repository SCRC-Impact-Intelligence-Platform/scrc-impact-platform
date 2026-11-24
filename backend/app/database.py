# app/database.py

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# SQLite file next to the backend package unless DATABASE_URL overrides it
# (tests use DATABASE_URL=sqlite:// for an in-memory database).
DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "local.db"
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")

# FastAPI runs sync endpoints in a thread pool, so SQLite connections cross threads.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    with SessionLocal() as db:
        yield db
