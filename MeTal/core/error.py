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

class QueueInProgressException(PublicException):
    pass

class PageTemplateError(LoggedException):
    pass

class DatabaseError(LoggedException):
    pass

class TemplateSaveException(LoggedException):
    pass

# for earlier Python 3.x backwards compatibility

try:
    FileNotFoundError
except NameError:
    class FileNotFoundError(LoggedException):
        pass
else:
    class FileNotFoundError(FileExistsError):
        pass

try:
    FileExistsError
except NameError:
    class FileExistsError(LoggedException):
        pass
else:
    class FileExistsError(FileExistsError):
        pass