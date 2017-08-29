from core.error import LoggedException
from functools import wraps
from core.libs.bottle import request
from core.libs.peewee import OperationalError
from core.models import db
from settings import DB, DATABASE_TIMEOUT, RETRY_INTERVAL
from sys import exc_info
from time import clock, sleep

DBError, error_text = DB.db_warnings()

# what we might want to do is instead subclass transaction
# so we can use it without the decorator context

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
            except LoggedException as e:
                db.rollback()
                raise exc_info()[0](e.msg)
            except DBError as e:
                db.rollback()
                raise LoggedException(error_text.format(e, request.url))
            except OperationalError as e:
                if clock() - start > DATABASE_TIMEOUT:
                    raise Exception('Database timeout', e)
                else:
                    # sleep(RETRY_INTERVAL)
                    continue
            else:
                # sleep(RETRY_INTERVAL * 3)
                break
        return fn
    return wrapper
