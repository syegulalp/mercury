from core.error import LoggedException
from functools import wraps
from core.libs.bottle import request
from core.libs.peewee import OperationalError
from core.models import db
from settings import DB, DATABASE_RETRIES, RETRY_INTERVAL
from sys import exc_info
from time import sleep

DBError, error_text = DB.db_warnings()

def transaction(func):
    @wraps(func)
    def wrapper(*a, **ka):
        db.connect()
        n = 0
        while n < DATABASE_RETRIES:
            try:
                with db.atomic():
                    fn = func(*a, **ka)
            except OperationalError as e:
                print (DB.db_is_locked())
                if str(e).startswith(DB.db_is_locked()):
                    n += 1
                    if n >= DATABASE_RETRIES:
                        raise e
                    else:
                        sleep(RETRY_INTERVAL)
                        continue
                else:
                    raise e
            except LoggedException as e:
                raise exc_info()[0](e.msg)
            except DBError as e:
                raise LoggedException(error_text.format(e, request.url))
            except BaseException as e:
                raise e
            else:
                db.close()
                break

        return fn

    return wrapper
