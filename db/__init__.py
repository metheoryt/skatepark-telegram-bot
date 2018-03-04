from functools import wraps
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from config import DB_DSN


Base = declarative_base()

Session = scoped_session(sessionmaker())

engine = create_engine(DB_DSN)


class DB:

    def __init__(self, Session):
        self._sess = Session

    @property
    def s(self):
        return self._sess()


Session.configure(bind=engine)


dbc = DB(Session)


def db_context(f):
    @wraps(f)
    def wrapper(*args, **kwargs):

        r = f(*args, **kwargs)

        dbc.s.close()

        return r

    return wrapper
