from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
# from app.core.config import {
#     DB_PASSWORD,
#     DB_HOST,
#     DB_NAME,
#     DB_PORT,
#     DB_USER,
    

# }

SQLALCHEMY_DATABASE_URL=f"postgresql://postgres:pass@localhost:5432/docs"
engine=create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal=sessionmaker(autocommit=False , autoflush=False , bind=engine)
Base=declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

