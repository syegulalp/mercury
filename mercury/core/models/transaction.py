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
        retries = 0
        while retries < DATABASE_RETRIES:
            # conn = db.get_conn()
            try:
                db.connect()
                with db.atomic():
                # with db.execution_context() as dbx:
                    # x=db.get_conn()
                    fn = func(*a, **ka)
            except OperationalError as e:
                if str(e).startswith(DB.db_is_locked()):
                    retries += 1
                    if retries >= DATABASE_RETRIES:
                        raise e
                    else:
                        db.close()
                        sleep(RETRY_INTERVAL)
                        continue
                else:
                    # $dbx.close()
                    db.close()
                    raise e
            except LoggedException as e:
                # dbx.close()
                db.close()
                raise exc_info()[0](e.msg)
            except DBError as e:
                # dbx.close()
                db.close()
                raise LoggedException(error_text.format(e, request.url))
            except Exception as e:
                # dbx.close()
                db.close()
                raise e
            else:
                db.commit()
                # db.close()
                break
        return fn

    return wrapper
