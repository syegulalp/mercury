from core.error import LoggedException
from functools import wraps
from core.libs.bottle import request
from core.libs.peewee import OperationalError
from core.models import db
from settings import DB, DATABASE_TIMEOUT, RETRY_INTERVAL
from sys import exc_info
from time import sleep, clock

DBError, error_text = DB.db_warnings()

def transaction(func):
    @wraps(func)
    def wrapper(*a, **ka):
        db.connect()
        db.execute_sql('PRAGMA journal_mode=WAL;')
        db.execute_sql('PRAGMA busy_timeout=30000;')
        start = clock()
        while 1:
            try:
                with db.transaction():
                    fn = func(*a, **ka)
            except OperationalError as e:
                db.rollback()
                if clock() - start > DATABASE_TIMEOUT:
                    raise e
                else:
                    sleep(RETRY_INTERVAL)
                    continue
            except LoggedException as e:
                db.rollback()
                raise exc_info()[0](e.msg)
            except DBError as e:
                db.rollback()
                raise LoggedException(error_text.format(e, request.url))
            except Exception as e:
                db.rollback()
                raise e
            else:
                break
            # db.close()
        return fn
    return wrapper
