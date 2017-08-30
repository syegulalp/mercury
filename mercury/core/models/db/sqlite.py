# from core.models import Page, TextField, Site

from core.error import LoggedException
from core.libs.peewee import OperationalError
from core.libs import bottle
_stderr = bottle._stderr

import os

from . import InitDBClass

from core.libs.playhouse.sqlite_ext import FTSModel, SqliteExtDatabase, TextField

class SqliteDB(SqliteExtDatabase, InitDBClass):

    def initialize_connection(self, *a, **ka):
        self.execute_sql('PRAGMA read_uncommitted = True;PRAGMA busy_timeout = 30000;PRAGMA schema.journal_mode=WAL;')

    def db_is_locked(self):
        return "database is locked"

    def recreate_database(self):
        import settings
        self.close()

        try:
            os.remove(settings.FULL_SQLITE_DATABASE_PATH)
        except OSError as e:
            from core.error import not_found
            if not_found(e) is False:
                raise e
        except Exception as e:
            raise e

        try:
            os.mkdir(os.path.join(settings.APPLICATION_PATH, settings.DATA_FILE_PATH))
        except OSError as e:
            from core.error import file_exists
            if file_exists(e) is False:
                raise e
        except Exception as e:
            raise e

        self._recreate_database()


    def clean_database(self):
        self._recreate_database()
        self.remove_indexes()

    def test_db_connection(self):

        # I'm thinking about ditching this entirely
        # and replacing it with troubleshooting/test routes

        import settings
        _stderr ("Looking for database in " + settings.DATABASE_PATH + "\n")

        if settings.RESET or not os.path.exists(settings.FULL_SQLITE_DATABASE_PATH):
            # FIXME: will this throw a spurious error on MySQL?

            _stderr ("No database found or settings.RESET was set.\n")

            try:
                self.close()
            except Exception:
                pass

            from core.error import FileExistsError

            try:
                os.remove(settings.FULL_SQLITE_DATABASE_PATH)
            except (OSError, FileExistsError):
                _stderr ("Database already removed.\n")
            else:
                _stderr ("Database removed.\n")
            finally:
                _stderr ("Re-initializing database.\n")
            print ("Recreating")

            self._recreate_database()

    def create_index_table(self):
        _stderr ("Creating SQLite index tables.\n")
        try:
            Page_Search.create_table()
        except OperationalError:
            _stderr ("Could not add full-text indexes to this version of SQLite.\n")

    def recreate_indexes(self):
        _stderr ("Recreating SQLite indexes.\n")
        from core.models import Page
        Page_Search.create_table(content=Page)
        Page_Search.rebuild()
        Page_Search.optimize()

    def site_search(self, search_terms_enc, site):
        from core.models import Page, Site

        ct = 0

        if site is not None:
            site_to_search = Site.load(site).pages.select(Page.id).tuples()

        try:
            search_results = (Page_Search.select(Page_Search.id)
                .where(Page_Search.id << site_to_search,
                    Page_Search.title.contains(search_terms_enc) | Page_Search.text.contains(search_terms_enc))
                .order_by(Page_Search.id.desc()).tuples())
            ct = search_results.count()  # This statement is used to trap FTS4 errors
        except OperationalError:
            pass
        if ct == 0:
            search_results = (Page.select(Page.id)
                .where(Page.blog.site == site,
                    Page.title.contains(search_terms_enc) | Page.text.contains(search_terms_enc))
                .order_by(Page.id.desc()).tuples())

        return search_results

    def blog_search(self, search_terms_enc, blog):
        from core.models import Page

        ct = 0

        if blog is not None:
            blog_to_search = blog.pages.select(Page.id).tuples()

        try:
            search_results = (Page_Search.select(Page_Search.id)
                .where(Page_Search.id << blog_to_search,
                    Page_Search.title.contains(search_terms_enc) | Page_Search.text.contains(search_terms_enc))
                .order_by(Page_Search.id.desc()).tuples())
            ct = search_results.count()  # This statement is used to trap FTS4 errors
        except OperationalError:
            pass
        if ct == 0:
            search_results = (Page.select(Page.id)
                .where(Page.blog == blog,
                    Page.title.contains(search_terms_enc) | Page.text.contains(search_terms_enc))
                .order_by(Page.id.desc()).tuples())

        return search_results

    def media_search(self):
        pass

    def dataset_connection(self):
        import settings
        return 'sqlite:///' + settings.DATABASE_PATH

    def clear_table(self, *args):  # @UnusedVariable
        return ""

    def set_table(self, *args):  # @UnusedVariable
        return ""

    def pre_import(self):
        return ""

    def post_import(self):
        return ""

    def post_recreate(self):
        return ""

    def db_warnings(self):
        # from core.error import LoggedException
        return LoggedException, "{} ({})"
        # return Exception, "{} ({})"


class Page_Search(FTSModel):
    title = TextField()
    text = TextField()
    class Meta:
        database = SqliteDB

