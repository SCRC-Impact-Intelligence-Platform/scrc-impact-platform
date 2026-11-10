# app/database.py

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# SQL Server connection URL, e.g.
# mssql+pyodbc://user:password@host:1433/scrc_impact?driver=ODBC+Driver+18+for+SQL+Server
DATABASE_URL = os.environ["DATABASE_URL"]

# pool_pre_ping replaces connections the server has dropped.
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    with SessionLocal() as db:
        yield db
