# app/database.py
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

DATABASE_URL = 'sqlite:///database.db'
engine = create_engine(DATABASE_URL)
Session = scoped_session(sessionmaker(bind=engine))

Base = declarative_base()  # Base única para todos os modelos

def init_db():
    Base.metadata.create_all(bind=engine)
    return Session()

def get_db():
    return Session()