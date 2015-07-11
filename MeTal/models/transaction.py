from core.error import LoggedException
from functools import wraps
from core.libs.bottle import request
from models import db
from settings import DB
from sys import exc_info

DBError, error_text = DB.db_warnings()

def transaction(func):
    @wraps(func)
    def wrapper(*a, **ka):
        db.connect()
        try:
            with db.atomic():
                fn = func(*a, **ka)
        except LoggedException as e:
            raise exc_info()[0](e.msg)
        except DBError as e:
            raise LoggedException(error_text.format(e, request.url))           
        db.close()
        return fn
    return wrapper
