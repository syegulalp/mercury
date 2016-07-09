from core.log import logger

class LoggedException(Exception):
    def __init__(self, msg):
        super().__init__(msg)
        self.msg = msg
        logger.error(msg)

class PermissionsException(LoggedException):
    pass

class ArchiveMappingFormatException(LoggedException):
    pass

class PluginImportError(LoggedException):
    pass

class UserNotFound(LoggedException):
    pass

class CSRFTokenNotFound(LoggedException):
    pass

class PageNotChanged(LoggedException):
    pass

class EmptyQueueError(Exception):
    pass

class PublicException(Exception):
    pass

class QueueAddError(LoggedException):
    pass

class QueueInProgressException(PublicException):
    pass

class PageTemplateError(LoggedException):
    pass

class DatabaseError(LoggedException):
    pass

class TemplateSaveException(LoggedException):
    pass

class MaintenanceModeException(Exception):
    pass

class UserCreationError(Exception):
    pass

class DeletionError(Exception):
    pass

class FileInfoCollision(Exception):
    # Used for when we attempt to write a fileinfo that has the same
    # pathname or URL as some other fileinfo
    # We should return as many details as we can about the offending fileinfo
    # and the one it collided with
    pass

# for earlier Python 3.x backwards compatibility

try:
    FileExistsError
except NameError:
    class FileExistsError(LoggedException):
        pass
else:
    class FileExistsError(FileExistsError):
        pass

def not_found(e):
    import errno
    if e.errno == errno.ENOENT or e.errno == 20:
        return True
    else:
        return False

def file_exists(e):
    import errno
    if e.errno == errno.EEXIST:
        return True
    else:
        return False
