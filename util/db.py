from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.sql.schema import ForeignKey

from util import store

import requests

engine = create_engine(f'sqlite:///{store.DATABASE_URI}')
db_session = scoped_session(sessionmaker(autocommit=False,
                                      autoflush=False,
                                      bind=engine))

Base = declarative_base()
Base.query = db_session.query_property()

class User(Base):
    __tablename__ = 'Users'

    id = Column(Integer, primary_key=True)
    github_access_token = Column(String(255))
    github_id = Column(Integer)
    github_login = Column(String(255))

    def __init__(self, github_access_token):
        self.github_access_token = github_access_token

class Organization(Base):
    __tablename__ = 'Organizations'

    id = Column(Integer, primary_key=True)
    github_login = Column(String(255))
    user_github_login = Column(String(255), ForeignKey('Users.github_login'))
    user_github_id = Column(Integer, ForeignKey('Users.github_id'))

    def __init__(self, github_login, user_github_login):
        self.github_login = github_login
        self.user_github_login = user_github_login
        self.user_github_id = requests.get(f'https://api.github.com/users/{user_github_login}').json()['id']

# Creates database tables if the don't exist
def create_database():
    Base.metadata.create_all(bind=engine)