from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base


DB_USER = "root"
DB_PASSWORD = ""  
DB_HOST = "localhost"
DB_NAME = "plantscan"


NO_DB_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}"

SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"


temp_engine = create_engine(NO_DB_URL)
with temp_engine.connect() as conn:
    conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}"))

engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()
