
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base

from app.config.settings import settings

DATABASE_URL = settings.DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    echo=False,
    future=True
)

Base = declarative_base()
