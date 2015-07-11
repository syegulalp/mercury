import logging

from settings import PRODUCT_NAME, DAYS_TO_KEEP_LOGS
import datetime

logger = logging.getLogger(PRODUCT_NAME)
logger.setLevel(logging.DEBUG)

from core.models import Log, db

log_record = Log()

try:
    date_diff = int(DAYS_TO_KEEP_LOGS)
except BaseException:
    date_diff = 0
    
class DBLogHandler(logging.Handler):
    
    def emit(self, record):
        
        with db.atomic() as nested_txn:
        
            msg = self.format(record)
            level = self.level
            log_record = Log(
                message=msg,
                level=level)
            log_record.save()            
            
            if date_diff > 0:

                delete_date = datetime.datetime.now() - datetime.timedelta(days=date_diff)
                delete_older_logs = Log.delete().where(
                    Log.date < delete_date)
                delete_older_logs.execute()
            
        
db_log = DBLogHandler()
db_log.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(message)s')
db_log.setFormatter(formatter)

logger.addHandler(db_log)
