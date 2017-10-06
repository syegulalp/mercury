import datetime, sys

from core.utils import tpl, date_format, html_escape, csrf_tag, csrf_hash, trunc, create_basename_core

from settings import (DB_TYPE, DESKTOP_MODE, BASE_URL_ROOT, BASE_URL, DB_TYPE_NAME,
        SECRET_KEY, ENFORCED_CHARFIELD_CONSTRAINT, DEFAULT_THEME)

from core.libs.bottle import request, url, _stderr
from core.libs.peewee import DeleteQuery, fn, SelectQuery  # , BaseModel as _BaseModel

from core.libs.playhouse.sqlite_ext import (Model, PrimaryKeyField, CharField,
   TextField, IntegerField, BooleanField, ForeignKeyField, DateTimeField, Check)

from functools import wraps

import settings as _settings

class Struct(object):
    pass

db = DB_TYPE

parent_obj = {
    'Page':'Blog',
    'Blog':'Theme',
    'Theme':'Site',
    'Site':'System',
    'Log':'System',
    'PageRevision':'Page',
    'PageCategory':'Page',
    }

archive_type = Struct()
archive_type.page = 'Page'
archive_type.category = 'Category'
archive_type.index = 'Index'
archive_type.author = 'Author'
archive_type.archive = 'Archive'

template_type = Struct()
template_type.index = "Index"
template_type.page = "Page"
template_type.archive = "Archive"
template_type.media = "Media"
template_type.include = "Include"
template_type.system = "System"

publishing_mode = Struct()
publishing_mode.immediate = "Immediate"
publishing_mode.batch_only = "Batch only"
publishing_mode.manual = "Manual"
publishing_mode.do_not_publish = "Do not publish"
publishing_mode.include = "Include"
publishing_mode.ssi = "Server-side include"

archive_defaults = {
    template_type.index:(archive_type.index,),
    template_type.page:(archive_type.page,),
    template_type.archive:(archive_type.category,
                           archive_type.archive,
                           archive_type.author)
}


publishing_mode.description = {
        publishing_mode.immediate:{
            'label':'primary',
            'description':'Template is pushed to the queue and processed immediately.'
            },
        publishing_mode.batch_only:{
            'label':'success',
            'description':'Template is only published whenever the queue is run on a scheduled job.'},
        publishing_mode.manual:{
            'label':'warning',
            'description':'Template is pushed to the queue and published only when specifically selected,\nor during a full blog republishing.'},
        publishing_mode.do_not_publish:{
            'label':'danger',
            'description':'Template is never published.'},
        publishing_mode.include:{
            'label':'default',
            'description':'Template is published as includes present in another template.'
            },
        publishing_mode.ssi:{
            'label':'info',
            'description':'Template is published to an element to be used as a server-side include.'
            }
    }

publishing_mode.modes = (
    publishing_mode.immediate,
    publishing_mode.batch_only,
    publishing_mode.manual,
    publishing_mode.include,
    publishing_mode.ssi,
    publishing_mode.do_not_publish
    )

page_status_list = (
    ('unpublished', 'Unpublished', 1),
    ('published', 'Published', 2),
    ('scheduled', 'Scheduled', 3)
    )

page_status = Struct()
page_status.ids = Struct()
page_status.statuses = []
page_status.modes = {}
page_status.id = {}

for n in page_status_list:
    page_status.__setattr__(n[0], n[1])
    page_status.ids.__setattr__(n[0], n[2])
    page_status.statuses.append([n[2], n[1]])
    page_status.modes[n[2]] = n[1]
    page_status.id[n[1]] = n[2]

class EnforcedCharField(CharField):
    def __init__(self, max_length=255, *args, **kwargs):
        self.max_length = max_length
        super(CharField, self).__init__(*args, **kwargs)

    def db_value(self, value):
        if value is None:
            length = 0
        else:
            try:
                length = len(str.encode(value))
            except TypeError:
                length = len(value)

        if length > ENFORCED_CHARFIELD_CONSTRAINT:
            from core.error import DatabaseError
            raise DatabaseError("The field '{}' cannot be longer than {} bytes. ({})".format(
                self.name,
                ENFORCED_CHARFIELD_CONSTRAINT,
                request.url))
        return super(CharField, self).db_value(value)


class Pages(SelectQuery):
    @property
    def published(self):
        return self.where(Page.status == page_status.published)
    def scheduled(self, due=False):
        scheduled_pages = self.where(Page.status == page_status.scheduled)
        if due is True:
            scheduled_pages = scheduled_pages.select().where(
                Page.publication_date >= datetime.datetime.utcnow())
        return scheduled_pages

#         def with_title(n, titles):
#             return n.where(Page.title.contains(titles))
#         def with_id(n, page_list):
#             return n.where(Page.id << page_list)
#         def has(n, prop, value):
#             return n.where(getattr(Page, prop).contains(value))

class BaseModel(Model):

    class Meta:
        database = db

    def delete_instance(self, *a, **ka):
        no_kv_del = ka.pop('no_kv_del', False)
        if not no_kv_del:
            self.kv_del()
        super().delete_instance(*a, **ka)

    # We will eventually also provide tags
    # Add to : Fileinfo, maybe also User? anywhere that seems logical

    @property
    def pages(self):
        try:
            n = self._pages
            n.__class__ = Pages
        except Exception:
            return None
        return n

    @classmethod
    def clean(cls):

        pages = Page.select(Page.id)

        if cls == Page:
            fileinfos_to_clear = FileInfo.delete().where(
               ~(FileInfo.page << pages))
            fileinfos_to_clear.execute()

            tags_to_clear = TagAssociation.delete().where(
                ~(TagAssociation.page << pages)
                )
            tags_to_clear.execute()

            categories_to_clear = PageCategory.delete().where(
                ~(PageCategory.page << pages)
                )
            categories_to_clear.execute()

            revisions_to_clear = PageRevision.delete().where(
                ~(PageRevision.page << pages)
                )
            revisions_to_clear.execute()

        if cls == Media:
            media_to_clear = MediaAssociation.delete().where(
                ~(MediaAssociation.page << pages))
            media_to_clear.execute()

        if cls == Tag:

            tags_to_clear = TagAssociation.delete().where(
                ~(TagAssociation.page << Page.select())
            ).execute()

            tags_to_clear_2 = TagAssociation.delete().where(
                ~(TagAssociation.media << Media.select())
            ).execute()

            tags_to_clear_3 = Tag.delete().where(
                ~(Tag.id << TagAssociation.select(TagAssociation.tag))
            ).execute()


        kvs_to_clear = KeyValue.delete().where(
            KeyValue.object == cls.__name__,
            KeyValue.objectid.not_in(cls.select())
            )
        kvs_to_clear.execute()

    def parent(self):
        try:
            return parent_obj[self.__class__.__name__]
        except KeyError:
            return 'System'

    '''
    def kv_add(self, **kw):

        # TODO: deprecate

        kv = KeyValue(
            object=kw['object'],
            objectid=kw['objectid'],
            key=kw['key'],
            value=kw['value'],
            parent=kw['parent'] if 'parent' in kw else None,
            is_schema=kw['is_schema'] if 'is_schema' in kw else False,
            is_unique=kw['is_unique'] if 'is_unique' in kw else False,
            value_type=kw['value_type'] if 'value_type' in kw else ''
            )

        kv.save()

        return kv
    '''

    @property
    def n_t(self):
        # TODO: replace this with proxies for name in all fields that need it
        name = None
        for n in ('name', 'title', 'tag'):
            k = getattr(self, n, None)
            if k is not None:
                name = k
                break

        if name is None or name == '':
            return "[Untitled]"
        else:
            return trunc(name)

        '''
        try:
            name = self.name
        except:
            name = self.title

        if name is None or name == "":
            return "[Untitled]"
        return trunc(name)
        '''

    @property
    def as_text(self):
        '''
        Returns a text-only, auto-escaped version of the object title.
        '''
        return html_escape(self.n_t)

    @property
    def as_basename(self):
        '''
        Returns a basename variation of the object title.
        '''
        return create_basename_core(self.n_t)

    @property
    def permalink_as_path(self):
        '''
        For page paths that end in '/'+the base index and extension, remove that
        '''
        base_to_remove = '/' + self.blog.base_index + '\.' + self.blog.base_extension + '$'
        import re
        return re.sub(base_to_remove, '', self.permalink)
        # return self.n_t.replace()

    @property
    def for_log(self):
        '''
        Returns a version of the object title formatted for a log entry, which will be auto-escaped.
        '''
        return "'{}' (#{})".format(
            self.n_t, self.id)

    @property
    def for_listing(self):
        '''
        Returns a version of the object title as an HTML link, with an escaped title.
        '''
        try:
            listing_id = "id='list_item_" + str(self.id) + "'"
        except AttributeError:
            listing_id = self.listing_id
        return "<a {id} href='{link}'>{text}</a>".format(
            id=listing_id,
            link=self.link_format,
            text=html_escape(self.n_t))

    @property
    def for_display(self):
        '''
        Returns a version of the object title formatted for display in a header or other object,
        which will be auto-escaped.
        '''
        return "{} (#{})".format(
            self.for_listing,
            self.id)


    def kv_list(self):
        object_name = self.__class__.__name__
        # TODO: make this a classmethod and
        # have it detect whether or not it's being
        # invoked by a specific class

        kv_list = KeyValue.select().where(
            KeyValue.object == object_name,
            KeyValue.objectid == self.id)

        return kv_list

    def kv_set(self, key=None, value=None, **kw):
        # TODO: Default action should be to check for existing key
        try:
            kv = self.kv_get(key=key, value=None).get()
        except Exception:
            kv = KeyValue(
                object=self.__class__.__name__,
                objectid=self.id,
                key=key,
                value=value
            )

        kv.parent = kw['parent'] if 'parent' in kw else None
        kv.is_schema = kw['is_schema'] if 'is_schema' in kw else False
        kv.is_unique = kw['is_unique'] if 'is_unique' in kw else False
        kv.value_type = kw['value_type'] if 'value_type' in kw else ''

        return kv.save()

    def __init__(self, *a, **ka):
        self.kv_get = self._kv_get
        super().__init__(*a, **ka)

    @classmethod
    def kv_get(cls, key=None, value=None, object_type=None, object_id=None):
        if key is None:
            raise KeyError('You must provide a key name')
        try:
            return cls().kv_get(key, value, object_type, object_id, special=True)
        except Exception as e:
            raise e

    def _kv_get(self, key=None, value=None, object_type=None,
                object_id=None, special=None):
        '''
        Retrieves one or more KVs for a specific key, value, and object ID.
        This is a "master" function -- other KV functions will use it in some form.

        If invoked from a class -- e.g., Page.kv_get() -- it returns matches
        for all objects in that class.

        If invoked from a class instance -- e.g., Page.load(260).kv_get() -- it
        returns matches only from that one instance.
        '''

        if object_type is None:
            object_type = self.__class__.__name__
        if object_id is None and self.id is not None:
            object_id = self.id

        kv = KeyValue.select().where(
            KeyValue.object == object_type
            )

        if object_id is not None:
            kv = kv.select().where(
                KeyValue.objectid == object_id
                )

        if key is not None:
            kv = kv.select().where(
                KeyValue.key == key
                )

        if value is not None:
            kv = kv.select().where(
                KeyValue.value == value
                )

        return kv

    def kv_del(self, key=None):
        '''
        Deletes a specific key on a selected object.
        If no specific key is provided, all keys on
        the current object are purged.
        '''
        if key is not None:
            kv = KeyValue.delete().where(
                KeyValue.key == key)
        else:
            kv = KeyValue.delete().where(
                KeyValue.object == self.__class__.__name__,
                KeyValue.objectid == self.id,
                )

        return kv.execute()

    def kv_val(self, key=None):
        if key is None:
            raise KeyError('You must provide a key name')
        try:
            kv_to_check = self.kv(key=key)
        except Exception as e:
            raise e
        return getattr(kv_to_check, 'value', None)
        # FIXME: How do we know this is a key with a NoneType setting?
        # If the key doesn't exist at all, we should raise a KeyError?

    def kv(self, key=None, value=None, _all=False):
        # TODO: base this off _kv_get or get rid of it
        '''
        Retrieves a KV for a given object in context.
        E.g., if you call this from an instance of Page,
        it will fetch any KVs attached to that page.
        Set 'all' to True if you are expecting to retrieve
        multiple keys with the same name.
        It's never a good idea to have multiple keys
        with the same name stored on an object, but we
        do want to make sure we have a way to handle that
        case.
        '''
        # TODO: Use kv_get

        kv = KeyValue.select().where(
                KeyValue.object == self.__class__.__name__,
                KeyValue.objectid == self.id,
                KeyValue.key == key,
                )

        if value is not None:
            kv = kv.select().where(
                KeyValue.value == value)

        if kv.count() == 0:
            return None
        if kv is not None:
            if _all:
                return kv
            else:
                return kv[0]
        else:
            return None


class Log(BaseModel):
    date = DateTimeField(default=datetime.datetime.utcnow, index=True)
    level = IntegerField()
    message = TextField()

class User(BaseModel):

    name = EnforcedCharField(index=True, null=False, unique=True)
    email = EnforcedCharField(index=True, null=False, unique=True)
    password = CharField(null=False)
    password_confirm = None
    encrypted_password = None
    avatar = IntegerField(null=True)  # refers to an asset ID
    last_login = DateTimeField(null=True)
    path_prefix = "/system"
    site = None
    blog = None
    logout_nonce = CharField(max_length=64, null=True, default=None)

    @property
    def short_name(self):
        return '@' + (self.email.split('@', 1)[0])

    def add_permission(self, **permission):
        new_permission = Permission(
            user=self,
            permission=permission['permission'],
            site=permission['site'],
            )

        try:
            new_permission.blog = permission['blog']
        except KeyError:
            pass

        new_permission.save()

        return new_permission

    def remove_permissions(self, permission_ids):
        # TODO: Rewrite this!
        # Test FIRST, and THEN do the delete.
        # Don't depend on this being inside a transaction!!
        from core import auth
        remove_permission = Permission.delete().where(
            Permission.user == self,
            Permission.id << permission_ids)
        done = remove_permission.execute()

        try:
            no_sysop = auth.get_users_with_permission(auth.role.SYS_ADMIN)
        except IndexError:
            from core.error import PermissionsException
            raise PermissionsException('You have attempted to delete the last known SYS_ADMIN privilege in the system. There must be at least one user with the SYS_ADMIN privilege.')
        return done

    @classmethod
    def login_verify(cls, email, password):
        from core.utils import encrypt_password
        try:
            user = cls.get(cls.email == email,
                cls.password == encrypt_password(password))
        except cls.DoesNotExist:
            raise cls.DoesNotExist
        else:
            user.last_login = datetime.datetime.utcnow()
            user.save()
            return user

    @classmethod
    def find(self, user_id=None):
        try:
            user = self.get(User.id == user_id)
        except User.DoesNotExist:
            raise User.DoesNotExist('User #{} was not found.'.format(user_id))
        else:
            return user

    def save_mod(self, **ka):
        # Save modification to user data other than last_login
        # TODO: make this into a confirmation function a la what we did with blog settings
        errors = []
        if self.name == '' or self.name is None:
            errors.append('Username cannot be blank.')

        if len(self.name) < 3:
            errors.append('Username cannot be less than three characters.')

        if self.email == '' or self.email is None:
            errors.append('Email cannot be blank.')

        if len(self.password) < 8:
            errors.append('Password cannot be less than 8 characters.')

        if len(errors) > 0:
            from core.error import UserCreationError
            raise UserCreationError(errors)

        return BaseModel.save(self, **ka)

    def save_pwd(self, **ka):
        # Save modification to password and verify user data
        errors = []

        if self.encrypted_password is None:

            if self.password is None or self.password == '' or self.password_confirm == '':
                errors.append('Password or confirmation field is blank.')

            if self.password != self.password_confirm:
                errors.append('Passwords do not match.')

            if len(errors) > 0:
                from core.error import UserCreationError
                raise UserCreationError(errors)

            from core.utils import encrypt_password
            self.password = encrypt_password(self.password)

        else:
            self.password = self.encrypted_password

        return self.save_mod(**ka)

    def from_site(self, site):
        self.site = site
        self.path_prefix = "/site/{}".format(str(site.id))
        return self

    def from_blog(self, blog):
        self.blog = blog
        self.path_prefix = "/blog/{}".format(str(blog.id))
        return self

    # for creating new post from main menu, among other things
    def blogs(self):

        from core.auth import role, bitmask, get_permissions

        permissions = get_permissions(self, level=bitmask.contribute_to_blog)

        if permissions[0].permission & role.SYS_ADMIN:
            all_blogs = Blog.select()
            return all_blogs

        sites = self.sites(bitmask.contribute_to_blog).select(Permission.site).tuples()

        blogs = Blog.select().where(
            Blog.id << permissions.select(Permission.blog).tuples() |
            Blog.site << sites)

        return blogs

    def sites(self, bitmask=1):
        sites = Permission.select().where(
            Permission.user == self,
            Permission.site > 0,
            Permission.permission.bin_and(bitmask))

        return sites

    @property
    def link_format(self):
        return "{}{}/user/{}".format(BASE_URL, self.path_prefix, self.id)


class SiteBase(BaseModel):

    name = TextField(null=False)
    url = CharField(null=False, index=True, unique=True)
    path = EnforcedCharField(index=True, unique=True, null=False)
    local_path = EnforcedCharField(index=True, unique=True, null=False)
    base_index = CharField(null=False, default='index')
    base_extension = CharField(null=False, default='html')
    description = TextField()
    media_path = TextField(default="'media/%Y'")
    ssi_path = TextField(default='_include')
    editor_css = TextField(null=True)

    @property
    def max_revisions(self):
        return _settings.MAX_PAGE_REVISIONS

class ConnectionBase(BaseModel):

    remote_connection = CharField(null=True, default='ftp')
    remote_address = CharField(null=True)
    remote_login = CharField(null=True)
    remote_password = CharField(null=True)

class Theme(BaseModel):
    title = TextField()
    description = TextField()
    json = TextField(null=True)
    is_default = BooleanField(null=True)
    # path = TextField()

    @classmethod
    def install_to_system(cls, theme_path):
        from settings import THEME_FILE_PATH, _join
        import json

        theme_dir = _join(THEME_FILE_PATH, theme_path)
        with open(_join(theme_dir, '__manifest__.json'), 'r') as f:
            json_data = f.read()

        json_obj = json.loads(json_data)

        new_theme = cls(
            title=json_obj["title"],
            description=json_obj["description"],
            json=theme_path
            )

        new_theme.save()
        return new_theme

    @classmethod
    def default_theme(cls):
        try:
            default_theme = cls.get(cls.title == DEFAULT_THEME)
        except:
            default_theme = Theme.get(Theme.is_default == True)
        return default_theme

    @classmethod
    def load(cls, theme_id=None):
        try:
            theme = Theme.get(Theme.id == theme_id)
        except Theme.DoesNotExist as e:
            raise Theme.DoesNotExist('Theme #{} does not exist.'.format(theme_id), e)
        return theme

    @property
    def link_format(self):
        return "{}/system/theme/{}".format(
            BASE_URL, self.id)

    @property
    def parent(self, context):
        if context.__class__.__name__ == 'Blog':
            return context.site

    @property
    def path(self):
        import os, settings
        from core.utils import create_basename_core
        return os.path.join(settings.THEME_FILE_PATH,
            create_basename_core(self.title))

    # TODO: This should be stored as a field.
    # If we rename the theme, then this will break.

    def actions(self, blog=None):
        pass


    '''
    returns the theme's module for things like action hooks
    .menus()

    '''

class Site(SiteBase, ConnectionBase):

    @classmethod
    def create(cls, **new_site_data):
        new_site = cls()
        new_site.name = new_site_data['name']
        new_site.description = new_site_data['description']
        new_site.url = new_site_data['url']
        new_site.path = new_site_data['path']
        new_site.local_path = new_site.path
        new_site.save()
        return new_site

    @classmethod
    def load(cls, site_id=None):
        try:
            site = Site.get(Site.id == site_id)
        except Site.DoesNotExist as e:
            raise Site.DoesNotExist('Site #{} does not exist'.format(site_id), e)
        return site

    @property
    def parent(self, context=None):
        return System()

    @property
    def link_format(self):
        return "{}/site/{}".format(
            BASE_URL, self.id)

    @property
    def blogs(self):
        return Blog.select().where(Blog.site == self)

    def pages(self, page_list=None):
        raise Exception('Use _pages!')

        blogs = Blog.select(Blog.id).where(
            Blog.site == self).tuples()

        pages = Page.select(Page, PageCategory).where(
            Page.blog << blogs).join(
            PageCategory).where(
            PageCategory.primary == True).order_by(
            Page.publication_date.desc(), Page.id.desc())

        if page_list is not None:
            pages = pages.where(Page.id << page_list)

        return pages

    def module(self, module_name):
        pass


    @property
    def users(self):

        site_user_list = Permission.select(fn.Distinct(Permission.user)).where(
            Permission.site << [self.id, 0]).tuples()

        site_users = User.select().where(User.id << site_user_list)

        return site_users

    @property
    def templates(self):
        '''
        Returns all templates associated with a given blog.
        '''
        templates_in_site = Template.select().where(Template.site == self)

        return templates_in_site

    def template(self, template_id):

        templates_in_site = Template.select().where(Template.site == self, Template.id == template_id)

        return templates_in_site

    @property
    def permalink(self):
        '''
        Returns the permalink for a site.
        '''
        return self.url

    @property
    def index_file(self):
        '''
        Returns the index filename used in a given site.
        '''
        return self.base_index + "." + self.base_extension

    @property
    def media(self):
        '''
        Stub for: Returns iterable of all Media types associated with a site.
        '''
        pass


class Blog(SiteBase):
    site = ForeignKeyField(Site, null=False, index=True)
    theme = ForeignKeyField(Theme, null=True, index=True)
    theme_modified = BooleanField(null=True, default=False)
    timezone = TextField(null=True, default='UTC')
    set_timezone = None

    # def theme_apply_to_blog(theme, blog, user):
    def apply_theme(self, theme, user):

        from core.cms import fileinfo, cms

        fileinfo.purge_fileinfos(self.fileinfos)
        self.erase_theme()

        from settings import THEME_FILE_PATH, _join
        import os, json

        theme_dir = _join(THEME_FILE_PATH, theme.json)

        for subdir, dirs, files in os.walk(theme_dir):
            for n in files:
                if n == '__manifest__.json':
                    continue
                if n[-4:] == '.tpl':
                    continue
                with open(_join(theme_dir, n), 'r', encoding='utf8') as f:
                    template = json.loads(f.read())
                    tpl_data = template['template']
                    with open(_join(theme_dir, n[:-5] + '.tpl'), 'r', encoding='utf8') as b:
                        tpl_data['body'] = b.read()

                    mapping_data = template['mappings']

                    table_obj = Template()

                    for name in table_obj._meta.fields:
                        if name not in ('id', 'blog', 'template_ref'):
                            setattr(table_obj, name, tpl_data[name])

                    table_obj.template_ref = n
                    table_obj.blog = self
                    table_obj.theme = theme
                    table_obj.save(user)

                    for mapping in mapping_data:
                        mapping_obj = TemplateMapping()
                        for name in mapping_obj._meta.fields:
                            if name not in ('id', 'template'):
                                setattr(mapping_obj, name, mapping_data[mapping][name])

                        mapping_obj.template = table_obj.id
                        mapping_obj.save()


        set_theme = Template.update(theme=theme).where(Template.theme == self.theme)
        set_theme.execute()

        self.theme = theme
        self.theme_modified = False
        self.save()

        cms.purge_blog(self)


    def archive(self, name):
        '''
        Gets the named archive template.
        '''
        archive = self.templates().select().where(
            Template.title == name,
            Template.template_type == template_type.archive)

        return archive

    def archive_default(self, default_type):
        archive_default = self.templates().select().where(
            Template.default_type == default_type).get()
        return archive_default

    @property
    def archive_templates(self):
        archive_templates_in_blog = self.templates(template_type.archive)
        return archive_templates_in_blog

    def archives(self, name):
        archives = self.archive(name).get().fileinfos_published.order_by(FileInfo.mapping_sort.desc())
        return archives

    @property
    def author_archive(self):
        return self.archive_default(archive_type.author)

    def category(self, category_id=None, title=None):
        category = self.categories

        if category_id is not None:
            category = category.where(Category.id == category_id)

        if title is not None:
            category = category.where(Category.title == title)

        return category.get()

    @property
    def categories(self):
        '''
        Lists all categories for this blog.
        Right now this just returns a flat dump; the hierarchical list will come later,
        perhaps by way of an option.
        '''
        categories = Category.select().where(
            Category.blog == self)

        return categories

    @property
    def category_archive(self):
        return self.archive_default(archive_type.category)

    @property
    def date_archive(self):
        return self.archive_default(archive_type.archive)

    @property
    def default_category(self):
        '''
        Return default category for this blog.
        '''
        try:
            default_category = Category.get(
            blog=self,
            default=True)
        except Category.DoesNotExist:
            raise Category.DoesNotExist(
                "No default category set for blog {}. This blog's category listing may have been damaged or improperly imported.".format(
                self.for_log))
        else:
            return default_category

    def erase_theme(self):
        '''
        Erases a blog's theme in preparation for installing a new one.
        '''

        mappings_to_delete = TemplateMapping.delete().where(TemplateMapping.id << self.template_mappings())
        m = mappings_to_delete.execute()

        revisions_to_delete = TemplateRevision.delete().where(TemplateRevision.template_id << self.templates())
        t = revisions_to_delete.execute()

        templates_to_delete = Template.delete().where(Template.id << self.templates())
        n = templates_to_delete.execute()

        return m, n  # , p

    def export_theme(self, title, description, user):
        '''
        Returns a dictionary object containing a dump of the blog's theme.
        Used mainly for saving a blog theme.
        '''

        theme_to_export = self.templates()

        from core.utils import json_dump, create_basename_core, default
        import json
        from core.error import PageNotChanged

        theme = {}

        theme_manifest = {}
        theme_manifest["title"] = title
        theme_manifest["description"] = description

        theme['__manifest__.json'] = json.dumps(theme_manifest,
            indent=1,
            sort_keys=True,
            allow_nan=True)

        for index, n in enumerate(theme_to_export):

            template = {}
            j_d = json_dump(n)

            filename = "{}-{}".format(
                create_basename_core(n.title),
                str(index))

            filename_tpl = filename + ".tpl"
            filename_json = filename + ".json"

            body = j_d['body']
            body = body.replace('\r\n', '\n')

            theme[filename_tpl] = body

            n.template_ref = filename_tpl

            # FIXME: I'm not sure why a save is required here.
            try:
                n.save(user)
            except PageNotChanged:
                pass

            template['template'] = j_d
            del template['template']['body']

            mappings_to_export = n.mappings

            template['mappings'] = {}

            for m in mappings_to_export:
                template['mappings'][m.id] = json_dump(m)

            theme[filename_json] = json.dumps(template,
                indent=1,
                sort_keys=True,
                allow_nan=True)


        return theme

    @property
    def fileinfos(self):
        '''
        Returns all fileinfos associated with a given blog.
        '''

        fileinfos_for_blog = FileInfo.select().where(FileInfo.template_mapping <<
            self.template_mappings())

        return fileinfos_for_blog

    @property
    def index_archive(self):
        return self.archive_default(archive_type.index)

    @property
    def index_file(self):
        return self.base_index + "." + self.base_extension

    @property
    def index_templates(self):
        index_templates_in_blog = self.templates(template_type.index)
        return index_templates_in_blog

    def last_n_edited_pages(self, count=5):
        last_n_edited_pages = self.pages.order_by(Page.modified_date.desc()).limit(count)
        return last_n_edited_pages

    def last_n_pages(self, count=0):
        '''
        Returns the most recent pages posted in a blog, ordered by publication date.
        Set count to zero to retrieve all published pages.
        '''

        last_n_pages = self.pages.published.order_by(
            Page.publication_date.desc())

        if count > 0:
            last_n_pages = last_n_pages.limit(count)

        return last_n_pages

    @property
    def link_format(self):
        return "{}/blog/{}".format(
            BASE_URL, self.id)

    @classmethod
    def load(cls, blog_id=None):
        try:
            blog = Blog.get(Blog.id == blog_id)
        except Blog.DoesNotExist as e:
            raise Blog.DoesNotExist('Blog #{} does not exist'.format(blog_id), e)
        return blog

    @property
    def media(self):
        '''
        Returns all Media types associated with a given blog.
        '''
        media = Media.select().where(Media.blog == self)

        return media

    @property
    def media_path_(self, media_object=None):

        tags = template_tags(
            media=media_object,
            blog=self)

        try:
            template = tpl(self.media_path,
                           **tags)
        except Exception:
            template = None

        # TODO: strip all newlines for a multi-line template?

        return template

    @property
    def media_path_generated(self):

        tags = template_tags(blog=self)
        from core.utils import generate_date_mapping

        try:
            template = generate_date_mapping(
                datetime.datetime.now(),
                tags,
                self.media_path)
        except Exception:
            return None

        return template

    def module(self, module_name):
        '''
        Returns a module from the current blog that matches this name.
        If no module of the name is found, it will attempt to also import a template.
        '''
        pass


    def page(self, page_id=None, title=None):
        '''
        Select a single page in this blog by either its ID or title.
        '''
        try:
            if title is not None:
                page = self.pages.where(Page.titles == title).get()
            else:
                page = self.pages.where(Page.id == page_id).get()
        except Exception:
            return None
        else:
            return page

    @property
    def page_archive(self):
        return self.archive_default(archive_type.page)

    @property
    def _pages(self):
        return Page.select().where(
            Page.blog == self.id).order_by(
            Page.publication_date.desc(), Page.id.desc())

#         return Page.select(Page, PageCategory).where(
#             Page.blog == self.id).join(
#             PageCategory).where(
#             PageCategory.primary == True).order_by(
#             Page.publication_date.desc(), Page.id.desc())


    # TODO: I don't think we need this anymore
    @property
    def parent(self):
        return self.theme

    @property
    def permalink(self):
        return self.url

    """
    def pages_where(self, page_list=None, titles=None):
        '''
        Select a list of pages in this blog by their IDs or titles
        '''
        pages = self.pages

        if page_list is not None:
            pages = pages.where(Page.id << page_list)
        if titles is not None:
            pages = pages.where(Page.title.contains(titles))

        return pages

    @property
    def published_pages(self):
        published_pages = self.pages.where(Page.status == page_status.published)
        return published_pages

    @property
    def scheduled_pages(self, due=False):
        scheduled_pages = self.pages.where(Page.status == page_status.scheduled)
        if due is True:
            scheduled_pages = scheduled_pages.select().where(
                Page.publication_date >= datetime.datetime.utcnow())
        return scheduled_pages
    """

    def set_default_archive_template(self, tpl, a_type):
        pass
        # clear all other templates associated with blog
        # set a_type

    def setup(self, user, theme=None):
        '''
        Prepares a newly-created blog with a default category.
        '''

        # We need this to flush any pending changes
        self.save()

        new_blog_default_category = Category(
            blog=self,
            title="Uncategorized",
            default=True)

        new_blog_default_category.save()

        if theme is not None:
            # from core.mgmt import theme_apply_to_blog
            # theme_apply_to_blog(theme, self, user)
            self.apply_theme(theme, user)
            self.save()

        from core.log import logger
        logger.info("Blog {} created on site {} by user {}.".format(
            self.for_log,
            self.site.for_log,
            user.for_log))

        return self

    def ssi(self, ssi_name):
        ssi = self.templates(template_type.include).select().where(
            Template.title == ssi_name).get()
        return '<!--#include virtual="/{}{}" -->'.format(
            self.subdir,
            ssi.default_mapping.fileinfos.get().file_path)

    @property
    def ssi_templates(self):
        ssi_templates = self.templates(template_type.include).select().where(
            Template.publishing_mode == publishing_mode.ssi)
        return ssi_templates

    @property
    def subdir(self):
        import urllib
        return urllib.parse.urlparse(self.url)[2] + '/'

    @property
    def tags(self):
        '''
        Select all tags that belong to this blog.
        '''
        return Tag.select().where(Tag.blog == self).order_by(Tag.tag.asc())

    def tags_where(self, tags_in=None):
        tags = self.tags
        if tags_in is not None:
            tags = tags.select().where(Tag.id << tags_in)
        return tags

    @property
    def tags_all(self):
        return self.tags

    @property
    def tags_private(self):
        return self.tags.select().where(Tag.is_hidden == True)

    @property
    def tags_public(self):
        return self.tags.select().where(Tag.is_hidden == False)

    def template(self, template_id):
        template_in_blog = self.templates_in_blog.select().where(Template.id == template_id)
        return template_in_blog

    def template_mappings(self, template_type=None):
        '''
        Returns all template mappings associated with a given blog.
        '''

        template_mappings_in_blog = TemplateMapping.select().where(TemplateMapping.template <<
            self.templates())

        if template_type is not None:
            template_mappings_in_blog = template_mappings_in_blog.select().where(
                TemplateMapping.template << self.templates(template_type))

        return template_mappings_in_blog

    def templates(self, template_type=None):
        '''
        Returns all templates associated with a given blog.
        '''
        templates_in_blog = Template.select().where(Template.blog == self)

        if template_type is not None:
            templates_in_blog = templates_in_blog.select().where(Template.template_type == template_type)

        return templates_in_blog

    @property
    def theme_actions(self):
        return self.theme.actions(self)



    @property
    def users(self):

        blog_user_list = Permission.select(fn.Distinct(Permission.user)).where(
            (Permission.site << [self.site.id, 0]) |
            (Permission.blog << [self.id, 0])
            ).tuples()

        blog_users = User.select().where(User.id << blog_user_list)

        return blog_users

    def validate(self):
        '''
        Validates a blog's settings before saving.
        '''
        errors = []
        from core.utils import is_blank

        if is_blank(self.name):
            errors.append('Blog name cannot be blank.')

        if is_blank(self.description):
            errors.append('Blog description cannot be blank.')

        if not is_blank(self.url):
            self.url = self.url.rstrip('/')
        else:
            errors.append('Blog URL cannot be blank.')

        if not is_blank(self.path):
            self.path = self.path.rstrip('/')
            self.local_path = self.path
        else:
            errors.append('Blog path cannot be blank.')

        # TODO: Ensure blog path does not collide with other blog paths

        if not is_blank(self.base_extension):
            self.base_extension = self.base_extension.lstrip('.')
        else:
            errors.append('Blog base extension cannot be blank.')

        if is_blank(self.media_path):
            errors.append('Blog media path cannot be blank.')

        # TODO: Ensure media path does not collide with any mappings?

        if not is_blank(self.set_timezone):
            from core.libs import pytz
            try:
                self.timezone = pytz.all_timezones[int(self.set_timezone)]
            except Exception:
                errors.append('You must choose a valid timezone.')

        if self.media_path_generated is None:
            errors.append('Invalid media path. Path must be a mapping expression.')

        if len(errors) > 0:
            raise Exception(errors)
        else:
            return self

class Category(BaseModel):
    blog = ForeignKeyField(Blog, null=False, index=True)

    title = TextField()
    # description = TextField(default=None, null=True, index=True)
    basename = TextField()
    parent_category = IntegerField(default=None, null=True, index=True)
    default = BooleanField(default=False, index=True)
    sort = IntegerField(default=None, null=True, index=True)

    security = 'is_blog_admin'

    def save(self, *a, **ka):
        if self.basename is None:
            self.basename = create_basename_core(self.title)
        super().save(*a, **ka)

    @property
    def basename_path(self):
        if self.parent_category is None:
            return self.basename
        else:
            path = [self.basename, ]
            s = self.parent_category
            while s is not None:
                path.insert(0, s.basename)
                if s.parent_category is not None:
                    s = s.parent_category
                else:
                    s = None
            return '/'.join(path)


    @property
    def site(self):
        return self.blog.site

    @property
    def _pages(self):
        categories = PageCategory.select(PageCategory.page).where(
            PageCategory.category == self)
        pages = Page.select().where(Page.id << categories).order_by(Page.publication_date.desc(),
                                                                    Page.id.desc())
        return pages

    @classmethod
    def load(cls, category_id=None, **kwargs):
        if category_id is None:
            raise Category.DoesNotExist('Category \'None\' does not exist')
        blog_id = kwargs.get('blog_id', None)
        try:
            category_to_get = Category.select().where(
                Category.id == category_id)
            if blog_id is not None:
                category_to_get = category_to_get.select().where(
                    Category.blog == blog_id)
            category_to_get = category_to_get.get()
        except Category.DoesNotExist:
            raise Category.DoesNotExist('Category #{} does not exist'.format(category_id))
        return category_to_get

    # TODO: convert manual links to link_format,
    # both here and for other models where it's appropriate
    @property
    def link_format(self):
        if self.id is None:
            return "{}/blog/{}/categories".format(
                BASE_URL, self.blog.id)
        return "{}/blog/{}/category/{}".format(
            BASE_URL, self.blog.id, self.id)

    # TODO: Add archive_default based on what Blog uses
    @property
    def archive_default(self):
        return None

    @property
    def next_category(self):
        pass

    @property
    def previous_category(self):
        pass

    @property
    def parent_c(self):
        if self.parent_category is None:
            return Category(blog=self.blog, title='[Top-level]')
        return Category.get(Category.id == self.parent_category)

class DateMod():

    def _date_from_utc(self, timezone, field):
        if field is None:
            return None
        from core.libs import pytz
        utc = pytz.timezone('UTC')
        tz = 'UTC' if timezone is None else timezone
        new_tz = pytz.timezone(tz)
        localized = utc.localize(field)
        return localized.astimezone(new_tz)

    def _date_to_utc(self, timezone, field):
        if field is None:
            return None
        from core.libs import pytz
        utc = pytz.timezone('UTC')
        tz = 'UTC' if timezone is None else timezone
        new_tz = pytz.timezone(tz)
        localized = new_tz.localize(field)
        return localized.astimezone(utc)

class Page(BaseModel, DateMod):

    title = TextField()
    type = IntegerField(default=0, index=True)  # 0 = regular blog post; 1 = standalone page
    path = EnforcedCharField(unique=True, null=True)  # only used if this is a standalone page
    external_path = EnforcedCharField(null=True, index=True)  # used for linking in an external file
    basename = TextField()
    user = ForeignKeyField(User, null=False, index=True)
    text = TextField()
    excerpt = TextField(null=True)
    blog = ForeignKeyField(Blog, null=False, index=True)
    created_date = DateTimeField(default=datetime.datetime.utcnow)
    modified_date = DateTimeField(null=True)
    publication_date = DateTimeField(null=True, index=True)
    status = CharField(max_length=32, index=True, default=page_status.unpublished)
    tag_text = TextField(null=True)
    currently_edited_by = IntegerField(null=True)
    author = user

    security = 'is_page_editor'

    def clear_categories(self):
        return PageCategory.delete().where(PageCategory.page == self).execute()

    def clear_tags(self):
        return TagAssociation.delete().where(
                TagAssociation.page == self).execute()

    def clear_media(self):
        return MediaAssociation.delete().where(
            MediaAssociation.page == self).execute()

    def clear_kvs(self):
        return self.kv_del()

    def delete_preview(self):
        for n in self.fileinfos:
            n.clear_preview()

#         preview_file = self.preview_file
#         preview_fileinfo = self.default_fileinfo
#         split_path = preview_fileinfo.file_path.rsplit('/', 1)
#
#         preview_fileinfo.file_path = preview_fileinfo.file_path = (
#              split_path[0] + "/" +
#              preview_file
#              )
#
#         import os
#         from os.path import join as _join
#
#         try:
#             return os.remove(_join(self.blog.path, preview_fileinfo.file_path))
#         except OSError as e:
#             from core.error import not_found
#             if not_found(e) is False:
#                 raise e
#         except Exception as e:
#             raise e

    def proxy(self, object_map):
        page_proxy = Page.load(self.id)
        iterables = {Tag:'tag', PageCategory:'category'}
        page_proxy.context = lambda:None
        for n in object_map:
            if type(n) in iterables:
                setattr(page_proxy.context, iterables[type(n)], n)
        return page_proxy

    @classmethod
    def load(cls, page_id=None):
        try:
            page = Page.get(Page.id == page_id)
        except Page.DoesNotExist as e:
            raise Page.DoesNotExist('Page #{} does not exist'.format(page_id), e)
        return page

    @property
    def created_date_tz(self):
        return self._date_from_utc(self.blog.timezone, self.created_date)

    @property
    def modified_date_tz(self):
        return self._date_from_utc(self.blog.timezone, self.modified_date)

    @property
    def publication_date_tz(self):
        return self._date_from_utc(self.blog.timezone, self.publication_date)

    @property
    def parent(self, context=None):
        return self.blog

    @property
    def preview_file(self):
        from core import utils
        return utils.preview_file(self.basename, self.blog.base_extension)

    @property
    def filename(self):
        return self.basename + "." + self.blog.base_extension

    @property
    def status_id(self):
        return page_status.id[self.status]

    @property
    def link_format(self):
        return '{}/page/{}/edit'.format(BASE_URL, self.id)

    @property
    def listing_id(self):
        return 'page_title_{}'.format(self.id)

    @property
    def paginated_text(self):
        paginated_text = self.text.split('<!-- pagebreak -->')
        return paginated_text

    @property
    def tags_public(self):
        return self.tags.where(Tag.is_hidden == False)

    @property
    def tags_private(self):
        return self.tags.where(Tag.is_hidden == True)

    @property
    def tags(self):
        return Tag.select().where(
            Tag.id << TagAssociation.select(TagAssociation.tag).where(
                TagAssociation.page == self)).order_by(Tag.tag)

    @property
    def tags_all(self):
        return self.tags

    @property
    def tags_list(self):
        tags = self.tags
        return [x.tag for x in tags]

    @property
    def author(self):
        return self.user

    @property
    def revisions(self):
        revisions = PageRevision.select().where(
            PageRevision.page == self.id).order_by(PageRevision.modified_date.desc())

        return revisions

    @property
    def templates(self):
        '''
        Returns all page templates for this page.
        '''
        page_templates = Template.select().where(
            Template.blog == self.blog.id,
            Template.template_type == template_type.page)

        return page_templates

    @property
    def default_template(self):
        '''
        Returns the default page template used by this blog.
        '''
        default_template = self.templates.select().where(
            Template.default_type == archive_type.page).get()

        return default_template

    @property
    def archives(self):
        '''
        Returns all archive templates for this page.
        '''
        page_templates = Template.select().where(
            Template.blog == self.blog.id,
            Template.template_type == template_type.archive)

        return page_templates

    @property
    def archive_mappings(self):
        '''
        Returns mappings for all date-based archive templates for this page.
        '''
        archive_mappings = TemplateMapping.select().where(
            TemplateMapping.template << self.archives.select(Template.id).tuples())

        return archive_mappings

    @property
    def template_mappings(self):
        '''
        Returns mappings for all page templates for this page.
        '''

        template_mappings = TemplateMapping.select().where(
            TemplateMapping.template << self.templates.select(Template.id).tuples())

        return template_mappings


    @property
    def default_template_mapping(self):
        '''
        Returns the default template mapping associated with this page.
        '''

        t = TemplateMapping.get(TemplateMapping.is_default == True,
            TemplateMapping.template << self.templates.select(Template.id).where(
                Template.default_type == "P").tuples())
        # FIXME: I think the "P" here is the old, old default_type signifier.
        # Look into this.

        default_template_mapping = self.publication_date.date().strftime(t.path_string)

        return default_template_mapping

    @property
    def fileinfos(self):
        '''
        Returns any fileinfo objects associated with this page.
        The loop is for the sake of generating fileinfos on-demand.
        '''

        while 1:
            fileinfos = FileInfo.select().where(
                FileInfo.page == self)
            try:
                fileinfos[0]
            except IndexError:
                from core.cms import fileinfo
                # TODO: inconsistent return values!
                m = fileinfo.build_archives_fileinfos((self,))
                n = len(fileinfo.build_pages_fileinfos((self,)))
                if n + m == 0:
                    raise Exception('No fileinfos could be built for page {}'.self.for_log)
            else:
                break

        return fileinfos

    @property
    def default_fileinfo(self):
        '''
        Returns the default fileinfo associated with the page.
        Useful if you have pages that have multiple mappings.
        '''

        default_fileinfo = self.fileinfos.where(
            FileInfo.template_mapping == self.default_template.default_mapping).get()

        # default_fileinfo = FileInfo.get(
            # FileInfo.page == self,
            # FileInfo.template_mapping == self.default_template.default_mapping)

        return default_fileinfo

    @property
    def permalink(self):
        '''
        Returns the permalink or canonical URL associated with the page.
        Derived from the default fileinfo.
        '''
        if self.id is not None:
            f_info = self.default_fileinfo
            permalink = self.blog.url + "/" + f_info.file_path
        else:
            permalink = ""

        return permalink

    @property
    def permalink_dir(self):
        '''
        Returns a version of the page's permalink that leaves off the filename.
        This is useful if you have pages that build as /index.html
        in a directory, and want to just permalink to the directory.
        '''
        return self.permalink.split(self.blog.index_file, 1)[0]

    @property
    def preview_permalink(self):

        if self.status_id == page_status.published:

            if DESKTOP_MODE is True:

                tags = template_tags(page_id=self.id)

                preview_permalink = tpl(BASE_URL_ROOT + '/' +
                     self.default_template_mapping + "." +
                     self.blog.base_extension + "?_=" + str(self.blog.id), **tags.__dict__)
            else:
                preview_permalink = self.permalink

        else:
            preview_permalink = BASE_URL + "/page/" + str(self.id) + "/preview"

        return preview_permalink

    @property
    def categories(self):

        categories = PageCategory.select().where(PageCategory.page == self)

        return categories

    @property
    def primary_category(self):

        primary = self.categories.select().where(PageCategory.primary == True).get()

        return primary.category

    @property
    def media(self):
        '''
        Returns iterable of all Media types associated with an entry.
        '''

        media_association = MediaAssociation.select(MediaAssociation.media).where(
            MediaAssociation.page == self.id)

        media = Media.select().where(Media.id << media_association)

        return media

    @property
    def next_all(self):
        '''
        Returns all pages in this blog later than the current one
        so that it can be filtered by some other method.
        This allows any number of next/previous methods to be built.
        '''
        next_all = self.blog.pages.published.where(
                Page.blog == self.blog, Page.id != self.id,
                ((Page.publication_date > self.publication_date) |
                ((Page.publication_date == self.publication_date) & (Page.id > self.id)))).order_by(
                Page.publication_date.asc(), Page.id.asc())

        return next_all

    @property
    def prev_all(self):
        '''
        Returns all pages in this blog earlier than the current one
        so that it can be filtered by some other method.
        '''
        prev_all = self.blog.pages.published.where(
Page.blog == self.blog, Page.id != self.id,
                ((Page.publication_date < self.publication_date) |
                ((Page.publication_date == self.publication_date) & (Page.id < self.id)))).order_by(
                Page.publication_date.desc(), Page.id.desc())

        return prev_all

    @property
    def next_pages(self):
        '''
        Returns an iterable of all next pages across categories for this page.
        '''

    @property
    def previous_pages(self):
        '''
        Returns an iterable of all previous pages across categories for this page.
        '''

    @property
    def next_page(self):
        '''
        Returns the next published page in the blog, in ascending chronological order.
        This ignores all categories.
        '''

        try:
            next_page = self.next_all.get()
        except Page.DoesNotExist:
            next_page = None
        return next_page

    @property
    def previous_page(self):
        '''
        Returns the previous published page in the blog, in descending chronological order.
        This ignores all categories.
        '''

        try:
            previous_page = self.prev_all.get()
        except Page.DoesNotExist:
            previous_page = None
        return previous_page

    @property
    def next_in_categories(self, categories=None, _all=False):
        '''
        Returns the next entry in the blog under the category in question.
        The default category choice is the blog's default category.
        If all is true, then iterate through all categories for the page
        and return the next in each category.
        '''
        # determine if page is in category
        # if not, just return first next
        # if so:
        # get all next pages
        # join by category (look up the exclusive join function)
        pass

    @property
    def previous_in_categories(self, categories=None, _all=False):
        '''
        This returns the previous entry in the blog under the category in question.
        The default category choice is the blog's default category.
        '''
        pass

    def save(self, user, no_revision=False, backup_only=False, change_note=None, force_update=False):

        '''
        Wrapper for the model's .save() action, which also updates the
        PageRevision table to include a copy of the current revision of
        the page BEFORE the save is committed.
        '''
        from core.log import logger

        revision_save_result = None

        if no_revision == False and self.id is not None:
            page_revision = PageRevision.copy(self)
            revision_save_result = page_revision.save(user, self, backup_only, change_note)

        page_save_result = Model.save(self) if backup_only is False else None

        if revision_save_result is not None:
            logger.info("Page {} edited by user {}.".format(
                self.for_log,
                user.for_log))

        else:
            logger.info("Page {} edited by user {} but without changes.".format(
                self.for_log,
                user.for_log))


        return (page_save_result, revision_save_result)

    revision_fields = {'id':'page'}

class RevisionMixin(object):
    @classmethod
    def copy(_class, source, **ka):

        instance = _class(**ka)
        subst = _class.revision_fields

        for name in source._meta.fields:

            value = getattr(source, name)
            target_name = subst[name] if name in subst else name
            setattr(instance, target_name, value)

        return instance

class PageRevision(Page, RevisionMixin):
    # page_id = IntegerField(null=False)
    page = ForeignKeyField(Page, null=False, index=True)
    is_backup = BooleanField(default=False)
    change_note = TextField(null=True)
    saved_by = IntegerField(null=True)

    @property
    def saved_by_user(self):

        saved_by_user = User.find(user_id=self.saved_by)
        if saved_by_user is None:
            dead_user = User(name='Deleted user (ID #' + str(self.saved_by) + ')', id=saved_by_user)
            return dead_user
        else:
            return saved_by_user


    def save(self, user, current_revision, is_backup=False, change_note=None):

        from core.log import logger
        from core.error import PageNotChanged

        max_revisions = self.blog.max_revisions
        previous_revisions = self.page.revisions

        if previous_revisions.count() > 0:

            last_revision = previous_revisions[0]

            page_changed = False

            for name in last_revision._meta.fields:
                if name not in ("modified_date", "id", "page", "is_backup", "change_note", "saved_by"):
                    value = getattr(current_revision, name)
                    new_value = getattr(last_revision, name)

                    if value != new_value:
                        page_changed = True
                        break

            if page_changed is False:
                raise PageNotChanged('Page {} was saved but without changes.'.format(
                    current_revision.for_log))


        if previous_revisions.count() >= max_revisions:

            older_revisions = DeleteQuery(PageRevision).where(
                PageRevision.page == self.page,
                PageRevision.modified_date <= previous_revisions[max_revisions - 1].modified_date)

            older_revisions.execute()

        self.is_backup = is_backup
        self.change_note = change_note
        self.saved_by = user.id

        results = Model.save(self)

        logger.info("Revision {} for page {} created.".format(
            date_format(self.modified_date),
            self.for_log))

        return results


class PageCategory(BaseModel):

    page = ForeignKeyField(Page, null=False, index=True)
    category = ForeignKeyField(Category, null=False, index=True)
    primary = BooleanField(default=True)

    @property
    def next_in_category(self):

        pass

    @property
    def previous_in_category(self):

        pass


class System(BaseModel):
    # we can consolidate this
    def scheduled_pages(self, due=False):
        scheduled_pages = (
            Page.select().where(Page.status == page_status.scheduled).order_by(
            Page.publication_date.desc())
            )
        if due is True:
            scheduled_pages = (
                scheduled_pages.select().where(
                    Page.publication_date <= datetime.datetime.utcnow())
                )
        return scheduled_pages

class KeyValue(BaseModel):

    object = CharField(max_length=64, null=False, index=True)  # table name
    objectid = IntegerField(null=True, index=True)
    key = EnforcedCharField(null=False, default="Key", index=True)
    value = TextField(null=True)
    parent = ForeignKeyField('self', null=True, index=True)
    is_schema = BooleanField(default=False)
    is_unique = BooleanField(default=False)
    value_type = CharField(max_length=64)

    @property
    def object_ref(self):
        obj = globals()[self.object]
        return obj.select().where(obj.id == self.objectid).get()

    @property
    def key_parent(self):
        try:
            schema = self.select().where(KeyValue.key == self.key,
            KeyValue.object == self.object,
            KeyValue.objectid == 0,
            KeyValue.is_schema == True).get()
        except KeyValue.DoesNotExist:
            return None
        return schema

    def children(self, field=None, value=None):
        if self.is_schema is False:
            return None
        else:
            children = self.select().where(KeyValue.parent == self)

        if field is not None:
            children = children.select().where(getattr(KeyValue, field) == value)

        return children

    def siblings(self, field=None, value=None):
        if self.parent is None:
            return None
        else:
            siblings = self.select().where(KeyValue.parent == self.parent)

        if field is not None:
            siblings = siblings.select().where(getattr(KeyValue, field) == value)

        return siblings

class Tag(BaseModel):
    tag = TextField()
    blog = ForeignKeyField(Blog, null=False, index=True)
    is_hidden = BooleanField(default=False, index=True)

    tag_template = '''
    <span class='tag-block'><button {new} data-tag="{id}" id="tag_{id}" title="See details for tag '{tag_esc}'"
    type="button" class="btn btn-{btn_type} btn-xs tag-title">{tag}</button><button id="tag_del_{id}"
    data-tag="{id}" title="Remove tag '{tag_esc}'" type="button" class="btn btn-{btn_type} btn-xs tag-remove"><span class="glyphicon glyphicon-remove"></span></button></span>
    '''
    tag_link_template = '''
    <a class="tag_link" target="_blank" href="{url}">{tag}</a>'''

    new_tag_template = '''
    <span class="tag_link">{tag}</span>'''

    @classmethod
    def load(cls, tag_id=None):
        try:
            tag = Tag.get(Tag.id == tag_id)
        except Tag.DoesNotExist as e:
            raise Tag.DoesNotExist('Tag #{} does not exist'.format(tag_id), e)
        return tag


    def save(self, *a, **ka):
        if str(self.tag)[:1] == '@':
            self.is_hidden = True
        else:
            self.is_hidden = False
        super().save(*a, **ka)

    @classmethod
    def add_or_create(self, tags, page=None, media=None, blog=None):

        if blog is None:
            if page is not None:
                blog = page.blog
                assoc = {'page':page,
                    'blog':page.blog}
            elif media is not None:
                blog = media.blog
                assoc = {'media':media}
        else:
            assoc = {'blog':blog}

        tags_added = []
        tags_existing = []
        all_tags = []

        for tag in tags:
            try:
                tag_to_match = Tag.get(
                    Tag.tag == tag,
                    Tag.blog == blog)
            except Tag.DoesNotExist:
                tag_to_match = Tag(
                    blog=blog,
                    tag=tag)
                tag_to_match.save()
                tags_added.append(tag_to_match)
            else:
                tags_existing.append(tag_to_match)
            all_tags.append(tag)

            association = TagAssociation(
                tag=tag_to_match,
                **assoc)

            association.save()

        return (tags_added, tags_existing, all_tags)


    # @property
    # TODO: allow filtering?

    @property
    def _pages(self):
        tagged_pages = TagAssociation.select(TagAssociation.page).where(
            TagAssociation.tag == self)

        in_pages = Page.select().where(
            Page.id << tagged_pages)

        return in_pages


    """
    @property
    def published_pages(self):
        return self.pages.where(Page.status == page_status.published)
    """


    @property
    def for_listing(self):

        template = self.tag_link_template.format(
            id=self.id,
            url=BASE_URL + "/blog/" + str(self.blog.id) + "/tag/" + str(self.id),
            tag=html_escape(self.tag))

        return template

    @property
    def for_display(self):

        btn_type = 'warning' if self.tag[0] == "@" else 'info'

        template = self.tag_template.format(
            tag_esc=self.tag.replace('"', "''"),
            id=self.id,
            btn_type=btn_type,
            new='',
            tag=self.tag_link_template.format(
                id=self.id,
                url=BASE_URL + "/blog/" + str(self.blog.id) + "/tag/" + str(self.id),
                tag=html_escape(self.tag))
            )

        return template

    @property
    def new_tag_for_display(self):

        btn_type = 'warning' if self.tag[0] == "@" else 'info'

        template = self.tag_template.format(
            id=0,
            tag=self.new_tag_template.format(
                tag=html_escape(self.tag)),
            btn_type=btn_type,
            tag_esc=self.tag.replace('"', "''"),
            new='data-new-tag="{}" '.format(html_escape(self.tag))
            )

        return template


class Template(BaseModel, DateMod):
    title = TextField(default="Untitled Template", null=False)
    theme = ForeignKeyField(Theme, null=True, index=True)
    template_type = CharField(max_length=32, index=True, null=False)
    blog = ForeignKeyField(Blog, null=False, index=True)
    body = TextField(null=True)
    publishing_mode = CharField(max_length=32, index=True, null=False)
    external_path = TextField(null=True)  # used for linking in an external file
    modified_date = DateTimeField(default=datetime.datetime.utcnow)
    is_include = BooleanField(default=False, null=True)
    default_type = CharField(max_length=32, default=None, null=True)
    template_ref = TextField(null=True)

    def delete_preview(self):
        for n in self.fileinfos:
            n.clear_preview()

    def delete_instance(self, *a, **ka):
        # eventually we shouldn't need these once we have all the proper
        # ID refs set up

        t0 = FileInfo.delete().where(FileInfo.template_mapping << self.mappings)
        t0.execute()

        t1 = TemplateMapping.delete().where(TemplateMapping.id << self.mappings)
        t1.execute()

        delete_revisions = TemplateRevision.delete().where(
                TemplateRevision.template_id == self.id)
        delete_revisions.execute()

        t2 = Template.delete().where(Template.id == self.id)
        t2.execute()

        return BaseModel.delete_instance(self, *a, **ka)

    @classmethod
    def load(cls, template_id=None):
        try:
            template = Template.get(Template.id == template_id)
        except Template.DoesNotExist as e:
            raise Template.DoesNotExist('Template #{} does not exist'.format(template_id), e)

        return template

    def as_module(self, tags):
        from types import ModuleType
        my_code = self.body
        m = ModuleType('new_module')
        m.__dict__.update(tags)
        exec(my_code, m.__dict__)
        return m

    @property
    def modified_date_tz(self):
        return self._date_from_utc(self.blog.timezone, self.modified_date)

    @property
    def default_url(self):
        if self.default_type is None:
            return None
        return self.default_mapping.fileinfos[0].url

    @property
    def link_format(self):
        return "{}/template/{}/edit".format(BASE_URL, self.id)

    @property
    def preview_file(self):
        from core import utils
        return utils.preview_file(str(self.id), self.blog.base_extension)

    def preview_path(self, fileinfo=None):
        # from core.template import preview_path
        # return preview_path(self)

        if self.default_mapping.fileinfos.count() == 0:
            return {'subpath':'',
            'path':self.blog.path,
            'file':self.preview_file}

        from os.path import join as _join
        file_path = self.default_mapping.fileinfos[0].file_path if fileinfo is None else fileinfo.file_path

        preview_subpath = file_path.rsplit('/', 1)
        if len(preview_subpath) > 1:
            preview_subpath = preview_subpath[0]
        else:
            preview_subpath = ''

        preview_path = _join(self.blog.path, preview_subpath)

        preview_file = self.preview_file

        return {'subpath':preview_subpath,
            'path':preview_path,
            'file':preview_file}

    def include(self, include_name):
        include = Template.get(Template.title == include_name,
            Template.theme == self.theme.id)
        return include.body

    def save(self, user, no_revision=False, backup_only=False, change_note=None):
        '''
        Wrapper for the model's .save() action, which also updates the
        PageRevision table to include a copy of the current revision of
        the page BEFORE the save is committed.
        '''
        from core.log import logger

        revision_save_result = None

        if no_revision == False and self.id is not None:
            page_revision = TemplateRevision.copy(self)
            revision_save_result = page_revision.save(user, self, False, change_note)

        page_save_result = Model.save(self) if backup_only is False else None


        if revision_save_result is not None:
            logger.info("Template {} edited by user {}.".format(
                self.for_log,
                user.for_log))

        else:
            logger.info("Template {} edited by user {} but without changes.".format(
                self.for_log,
                user.for_log))


        return (page_save_result, revision_save_result)

    @property
    def includes(self):
        # get most recent fileinfo for page
        # use that to compute includes
        # we may want to make that something we can control the context for
        pass

    @property
    def mappings(self):
        '''
        Returns all file mappings for the template.
        '''
        template_mappings = TemplateMapping.select().where(TemplateMapping.template == self)
        return template_mappings

    @property
    def fileinfos(self):
        '''
        Returns a list of all fileinfos associated with the selected template.
        '''
        fileinfos = FileInfo.select().where(
            FileInfo.template_mapping << self.mappings)
        return fileinfos

    @property
    def fileinfos_published(self):
        if self.template_type == "Page":
            return self.fileinfos.select().join(Page).where(
                Page.status == page_status.published)

        else:
            if self.publishing_mode != publishing_mode.do_not_publish:
                return self.fileinfos


    @property
    def default_mapping(self):
        '''
        Returns the default file mapping for the template.
        '''
        default_mapping = TemplateMapping.select().where(TemplateMapping.template == self,
            TemplateMapping.is_default == True).get()
        return default_mapping


class TemplateRevision(Template, RevisionMixin):
    template_id = IntegerField(null=False)
    is_backup = BooleanField(default=False)
    change_note = TextField(null=True)
    saved_by = IntegerField(null=True)

    revision_fields = {'id':'template_id'}

    @property
    def saved_by_user(self):
        saved_by_user = User.find(user_id=self.saved_by)
        if saved_by_user is None:
            dead_user = User(name='Deleted user (ID #' + str(self.saved_by) + ')',
                id=saved_by_user)
            return dead_user
        else:
            return saved_by_user


    def save(self, user, current_revision, is_backup=False, change_note=None):

        from core.log import logger
        from core.error import PageNotChanged

        max_revisions = self.blog.max_revisions

        previous_revisions = (self.select().where(TemplateRevision.template_id == self.template_id)
            .order_by(TemplateRevision.modified_date.desc()).limit(max_revisions))

        if previous_revisions.count() > 0:

            last_revision = previous_revisions[0]

            template_changed = False

            for name in last_revision._meta.fields:
                if name not in ("modified_date", "id", "template_id", "theme", "is_backup", "change_note", "saved_by"):
                    value = getattr(current_revision, name)
                    new_value = getattr(last_revision, name)

                    if value != new_value:
                        template_changed = True
                        break

            if template_changed is False:
                raise PageNotChanged('Template {} was saved but without changes.'.format(
                    current_revision.for_log))


        if previous_revisions.count() >= max_revisions:

            older_revisions = DeleteQuery(TemplateRevision).where(
                TemplateRevision.template_id == self.template_id,
                TemplateRevision.modified_date < previous_revisions[max_revisions - 1].modified_date)

            older_revisions.execute()


        self.is_backup = is_backup
        self.change_note = change_note
        self.saved_by = user.id

        results = Model.save(self)

        logger.info("Revision {} for template {} created.".format(
            date_format(self.modified_date),
            self.for_log))

        return results

class TemplateMapping(BaseModel):

    template = ForeignKeyField(Template, null=False, index=True)
    is_default = BooleanField(default=False, null=True)
    path_string = TextField()
    archive_xref = CharField(max_length=16, null=True)
    modified_date = DateTimeField(default=datetime.datetime.utcnow)

    @property
    def fileinfos(self):
        '''
        Returns a list of all fileinfos associated with the selected template mapping.
        '''
        fileinfos = FileInfo.select().where(
            FileInfo.template_mapping == self)

        return fileinfos

    @property
    def fileinfos_published(self):

        if self.template_type == "Page":
            return self.fileinfos.select().join(Page).where(
                Page.status == page_status.published)
        else:
            if self.publishing_mode != publishing_mode.do_not_publish:
                return self.fileinfos

    @property
    def next_in_mapping(self):
        '''
        Stub for the next archive entry for a given template.
        Determines from xref map.
        We should have the template mapping as part of a context as well.
        I don't think we do this yet.

        '''
        pass

    @property
    def previous_in_mapping(self):
        pass

    @property
    def first_in_mapping(self):
        pass

    @property
    def last_in_mapping(self):
        pass

##########################

class Media(BaseModel, DateMod):
    filename = CharField(null=False)
    path = EnforcedCharField(unique=True)
    local_path = EnforcedCharField(unique=True, null=True)  # deprecated?
    # should eventually be used to calculate where on the local filesystem
    # the file is when we are running in desktop mode, but I think we may
    # be able to deduce that from other things

    url = EnforcedCharField(unique=True, null=True)
    type = CharField(max_length=32, index=True)
    created_date = DateTimeField(default=datetime.datetime.utcnow)
    modified_date = DateTimeField(default=datetime.datetime.utcnow)
    friendly_name = TextField(null=True)
    tag_text = TextField(null=True)
    user = ForeignKeyField(User, null=False)
    blog = ForeignKeyField(Blog, null=True)
    site = ForeignKeyField(Site, null=True)

    security = 'is_media_owner'

    @classmethod
    def load(cls, media_id=None, blog=None):
        try:
            media = Media.get(Media.id == media_id)
        except Media.DoesNotExist as e:
            raise Media.DoesNotExist ('Media element #{} does not exist'.format(media_id), e)
        if blog:
            if media.blog != blog:
                raise MediaAssociation.DoesNotExist('Media #{} is not associated with blog {}'.format(media.id, blog.for_log))
        return media

    @classmethod
    def register_media(cls, filename, path, user, **ka):
        from core.cms import media_filetypes
        import os

        media = cls(
            filename=filename,
            path=path,
            type=media_filetypes.types[os.path.splitext(filename)[1][1:]],
            user=user,
            friendly_name=ka.get('friendly_name', filename)
            )

        media.save()

        if 'page' in ka:
            page = ka['page']
            media.associate(page)
            media.blog = page.blog
            media.site = page.blog.site
            media.url = '/'.join((page.blog.url, page.blog.media_path_generated, media.filename))
            media.save()

        return media

    @property
    def created_date_tz(self):
        return self._date_from_utc(self.blog.timezone, self.created_date)

    @property
    def modified_date_tz(self):
        return self._date_from_utc(self.blog.timezone, self.modified_date)

    @property
    def name(self):
        return self.friendly_name

    @property
    def link_format(self):
        return "{}/blog/{}/media/{}/edit".format(
            BASE_URL, str(self.blog.id), self.id)

    @property
    def preview_url(self):
        '''
        In desktop mode, returns a preview_url
        otherwise, returns the mapped URL to the media
        as if it were being accessed through the site in question
        (assuming it can be found there)
        '''
        if DESKTOP_MODE:
            return BASE_URL + "/media/" + str(self.id)
        else:
            return self.url

    @property
    def _pages(self):
        '''
        Returns a listing of all pages this media is associated with.
        '''
        pages = MediaAssociation.select(MediaAssociation.page).where(
            MediaAssociation.media == self)

        return pages

    @property
    def pages(self):
        return Page.select().where(Page.id << self._pages)

    """
    @property
    def associated_with(self):
        '''
        Returns a listing of all pages this media is associated with.
        '''
        associated_with = MediaAssociation.select().where(
            MediaAssociation.media == self)

        return associated_with
    """

    @property
    def tags(self):
        return Tag.select().where(
            Tag.id << TagAssociation.select(TagAssociation.tag).where(
                TagAssociation.media == self)).order_by(Tag.tag)

    @property
    def preview_for_listing(self):
        return '''<a href="{}"><img class="img-responsive img-listing-preview" src="{}"></a>'''.format(
            self.link_format,
            self.preview_url)

    def associate(self, page):
        association = MediaAssociation(
            media=self,
            page=page,
            blog=page.blog,
            site=page.blog.site)

        association.save()

class MediaAssociation(BaseModel):

    media = ForeignKeyField(Media)
    page = ForeignKeyField(Page, null=True)
    blog = ForeignKeyField(Blog, null=True)
    site = ForeignKeyField(Site, null=True)

class TagAssociation(BaseModel):
    tag = ForeignKeyField(Tag, null=False, index=True)
    page = ForeignKeyField(Page, null=True, index=True)
    media = ForeignKeyField(Media, null=True, index=True)


class FileInfo(BaseModel):
    page = ForeignKeyField(Page, null=True, index=True)
    template_mapping = ForeignKeyField(TemplateMapping, null=False, index=True)
    file_path = EnforcedCharField(null=False)
    sitewide_file_path = EnforcedCharField(index=True, null=False, unique=True)
    url = EnforcedCharField(null=False, index=True, unique=True)
    modified_date = DateTimeField(default=datetime.datetime.utcnow)
    mapping_sort = EnforcedCharField(null=True, default=None, index=True)
    preview_path = TextField(null=True, index=True, default=None)

    def make_preview(self):
        from core import utils
        from os import path

        full_file_path = self.file_path.rsplit(path.sep, 1)
        if len(full_file_path) == 1:
            full_file_path.insert(0, '')

        blog = self.template_mapping.template.blog

        preview_file = utils.preview_file(
                full_file_path[1],
                blog.base_extension
            )

        preview_file_path = path.join(full_file_path[0],
            preview_file)

        preview_url = '/'.join(
            (blog.permalink,
            full_file_path[0],
            preview_file)
            )

        self.preview_path = preview_file_path

        self.save()

        return (preview_file_path, preview_url)

    def clear_preview(self):
        import os
        if self.preview_path is not None:
            try:
                os.remove(
                    os.path.join(
                    self.template_mapping.template.blog.path,
                    self.preview_path
                    )
                )
            except OSError as e:
                import errno
                if e.errno == errno.ENOENT:
                    pass
                else:
                    raise e
            self.preview_path = None
            self.save()


    @property
    def xref(self):
        xref = TemplateMapping.select().where(
            TemplateMapping.id == self.template_mapping).get()
        return xref

    @property
    def author(self):
        try:
            author = self.context.select().where(FileInfoContext.object == "A").get()
            author = author.ref
        except FileInfoContext.DoesNotExist:
            author = None
        return author

    @property
    def context(self):
        context = FileInfoContext.select().where(
            FileInfoContext.fileinfo == self).order_by(FileInfoContext.id.asc())
        return context

    @property
    def date(self):
        return datetime.date(self.year, self.month, 1)

    @property
    def year(self):
        try:
            year = self.context.select().where(FileInfoContext.object == "Y").get()
            year = year.ref
        except FileInfoContext.DoesNotExist:
            year = None
        return year

    @property
    def month(self):
        try:
            month = self.context.select().where(FileInfoContext.object == "M").get()
            month = month.ref
        except FileInfoContext.DoesNotExist:
            month = None
        return month

    @property
    def category(self):
        try:
            category = self.context.select().where(FileInfoContext.object == "c").get()
            category = category.ref
        except FileInfoContext.DoesNotExist:
            category = None
        return category

    @property
    def tag(self):
        return self.tags

    @property
    def tags(self):
        try:
            category = self.context.select().where(FileInfoContext.object == "T").get()
            category = category.ref
        except FileInfoContext.DoesNotExist:
            category = None
        return category

class FileInfoContext(BaseModel):
    fileinfo = ForeignKeyField(FileInfo, null=False, index=True)
    object = CharField(max_length=1)
    ref = IntegerField(null=True)

class Queue(BaseModel):
    job_type = CharField(null=False, max_length=16, index=True)
    is_control = BooleanField(null=False, default=False, index=True)
    is_running = BooleanField(null=False, default=False, index=True)
    priority = IntegerField(default=9, index=True)
    data_string = TextField(null=True)
    data_integer = IntegerField(null=True, index=True)
    date_touched = DateTimeField(default=datetime.datetime.utcnow)
    blog = ForeignKeyField(Blog, index=True, null=False)
    site = ForeignKeyField(Site, index=True, null=False)
    # status = CharField(max_length=1, null=True, default=None)
    # processing = P
    # failed = F
    # .set_processing
    # .set_failed
    # .clear_completed

    @classmethod
    def is_insert_active(cls, b):
        most_recent = cls.select(cls.date_touched).where(cls.blog == b,
            cls.is_control == False).order_by(cls.date_touched.desc()).limit(1)
        if most_recent.count() == 0:
            return False
        most_recent_time = datetime.datetime.utcnow() - most_recent[0].date_touched
        if most_recent_time.seconds < 10:
            return True
        return False

    @classmethod
    def push(cls, **ka):
        '''
        Inserts a single job item into the work queue.

        :param job_type:
            A string representing the type of job to be inserted.
            One of a list of strings from the job_type object in core.cms.

        :param data_integer:
            Any integer data passed along with the job. For a job control item, this
            is the number of items remaining for that particular job.
            For a regular publishing job, this is the id of the fileinfo.

        :param blog:
            The blog object associated with the job.

        :param site:
            The site object associated with the job.

        :param priority:
            An integer, from 0-9, representing the processing priority associated with the job.
            Higher-priority jobs are processed first. Most individual pages are given a high
            priority; indexes are lower.
        '''

        try:
            queue_job = cls.get(
                cls.job_type == ka['job_type'],
                cls.data_integer == ka['data_integer'],
                cls.blog == ka['blog'],
                cls.site == ka['site']
                )
        except cls.DoesNotExist:
            queue_job = cls()
        else:
            return False

        queue_job.job_type = ka['job_type']
        queue_job.data_integer = int(ka.get('data_integer', None))
        queue_job.blog = ka.get('blog', None)
        queue_job.site = ka.get('site', None)
        queue_job.priority = ka.get('priority', 9)
        queue_job.is_control = ka.get('is_control', False)

        if queue_job.is_control:
            queue_job.data_string = ka.get('data_string', ("{}: Blog {}".format(
                queue_job.job_type,
                queue_job.blog.for_log)))
        else:
            queue_job.data_string = ("{}: {}".format(
                queue_job.job_type,
                FileInfo.get(FileInfo.id == queue_job.data_integer).file_path))

        queue_job.date_touched = datetime.datetime.utcnow()
        queue_job.save()
        return True

    # TODO: MOVE THIS TO THE QUEUE MODEL
    @classmethod
    def remove(cls, queue_deletes):
        '''
        Removes jobs from the queue.
        :param queue_deletes:
            A list of queue items, represented by their IDs, to be deleted.
        '''
        deletes = cls.delete().where(cls.id << queue_deletes)
        return deletes.execute()

    @classmethod
    def stop(cls, blog=None):
        delete_queue = cls.delete().where(cls.is_control == True)
        if blog is not None:
            delete_queue = delete_queue.where(cls.blog == blog)
        return delete_queue.execute()

    @classmethod
    def start(cls, blog=None, queue_length=None, jobtype=None):
        from core.cms.queue import job_type

        if blog is None:
            raise Exception("You must specify a blog when starting a queue process.")

        if jobtype == None:
            jobtype = job_type.control

        if queue_length is None:
            queue_length = Queue.job_counts(blog=blog)

        cls.push(blog=blog,
            site=blog.site,
            job_type=jobtype,
            is_control=True,
            data_integer=queue_length
            )

        return queue_length

        # TODO: eventually this will include insert jobs as well?
        # Make sure the queue is locked properly when we do that
        # and when we do the insert, perhaps we should get the total number
        # of prospective jobs from a model object.
        # for instance, if we want to push all the insert jobs
        # for a given template, we can get that directly from the template
        # likewise, for a whole blog (all template objects)
        # likewise, for other classes of objects (e.g., all the templates from a page)
        # easiest to start with just individual templates or whole blogs,
        # since those are easy to calculate and coalesce

    @classmethod
    def clear(cls, blog=None):
        delete_queue = cls.delete()
        if blog is not None:
            delete_queue = delete_queue.where(cls.blog == blog)
        return delete_queue.execute()

    def lock(self):
        if self.is_running:
            from core.error import QueueInProgressException
            raise QueueInProgressException("Publishing job currently running for blog {}".format(
                self.blog.for_log))
        self.is_running = True
        self.save()

    def unlock(self):
        if not self.is_running:
            from core.error import QueueInProgressException
            raise QueueInProgressException("Publishing job not currently running for blog {}".format(
                self.blog.for_log))
        self.is_running = False
        self.save()

    # we may want to make a context manager at some point
    # we may also want to auto-acquire the lock as a default
    @classmethod
    def acquire(cls, blog, return_queue=False):
        '''
        Checks to see if a publishing job for a given blog is currently running.
        If it is, it raises an exception.
        If the return_queue flag is set, it returns the queue_control object instead.
        If no job is locked, then it returns None.
        '''
        try:
            queue_control = cls.select().where(cls.blog == blog,
                cls.is_control == True).order_by(cls.id.asc()).get()
        except cls.DoesNotExist:
            return None

        if return_queue is True:
            return queue_control
        else:
            from core.error import QueueInProgressException
            raise QueueInProgressException("Publishing job currently running for blog {}".format(
                blog.for_log))

    @classmethod
    def for_blog(self, blog=None):
        if blog is None:
            raise Blog.DoesNotExist("You need to supply a blog object to retrive queue information.")
        return Queue.select().where(Queue.blog == blog)

    @classmethod
    def control_jobs(cls, blog=None):
        return cls.for_blog(blog).where(Queue.is_control == True)

    @classmethod
    def control_job(cls, blog=None):
        return cls.control_jobs(blog).get()

    @classmethod
    def jobs(cls, blog=None):
        return cls.for_blog(blog).where(Queue.is_control == False)

    @classmethod
    def job_counts(cls, blog=None, site=None):
        from core.cms.queue import job_type as jt

        # all_jobs = all_queue_jobs(blog, site)

        all_jobs = Queue.select()

        if blog is not None:
            all_jobs = all_jobs.select().where(Queue.blog == blog)
        if site is not None:
            all_jobs = all_jobs.select().where(Queue.site == site)

        publish_jobs = all_jobs.select().where(Queue.is_control == False).count()
        insert_jobs = all_jobs.select(Queue, fn.SUM(Queue.data_integer).alias('total')).where(
            Queue.is_control == True and Queue.job_type == jt.insert).get()

        return int(0 if publish_jobs is None else publish_jobs) + int(
            0 if insert_jobs.total is None else insert_jobs.total)

'''
def all_queue_jobs(blog=None, site=None):

    all_jobs = Queue.select()

    if blog is not None:
        all_jobs = all_jobs.select().where(Queue.blog == blog)
    if site is not None:
        all_jobs = all_jobs.select().where(Queue.site == site)

    return all_jobs
'''
# def queue_jobs_waiting(blog=None, site=None):
    # return Queue.job_counts(blog, site)


class Permission(BaseModel):
    user = ForeignKeyField(User, index=True)
    permission = IntegerField(null=False)
    blog = ForeignKeyField(Blog, index=True, null=True)
    site = ForeignKeyField(Site, index=True, null=True)
    # for sitewide, use site = 0, blog = None

class Plugin(BaseModel):

    name = TextField(null=False)
    friendly_name = TextField(null=False)
    path = TextField(null=False)
    priority = IntegerField(null=True, default=0)
    enabled = BooleanField(null=False, default=False)

    @property
    def n_t(self):
        return self.friendly_name

    # move to model definition
    @classmethod
    def load(cls, plugin_id, action_text='initialize'):
        try:
            existing_plugin = cls.select().where(
                cls.id == plugin_id).get()
        except cls.DoesNotExist:
            from core.error import PluginImportError
            raise PluginImportError("Plugin {} not found to {}.".format(plugin_id, action_text))
        return existing_plugin

    @property
    def link_format(self):
        return '{}/system/plugin/{}'.format(BASE_URL, self.id)

    @property
    def _plugin_list(self):
        from core.plugins import plugin_list
        return plugin_list

    def ui(self):
        return self.plugin.ui(self)

    def data(self, blog=None, site=None, user=None):
        return PluginData.select().where(PluginData.plugin == self.id)

    def clear_data(self):
        data_del = PluginData.delete().where(PluginData.plugin == self)
        data_del.execute()

    def reset(self):
        self.clear_data()

        try:
            plugin_settings = self.plugin.install()['settings']
        except (AttributeError, TypeError) as e:
            raise e
        except Exception as e:
            raise e
        else:
            for n in plugin_settings:
                settings_data = PluginData(
                    plugin=self,
                    key=n.get('key', None),
                    # text_value=n.get('text_value', None),
                    int_value=n.get('int_value', None),
                    )

                    # blog=n.get('blog', None),
                    # site=n.get('site', None),
                    # parent=n.get('parent', None)
                    # )
                settings_data.save()


    @property
    def plugin(self):
        return self._plugin_list[self.id]

    def _get_plugin_property(self, plugin_property, deactivated_message):
        if self.enabled is True:
            return self.plugin.__dict__[plugin_property]
        else:
            return deactivated_message

    @property
    def loaded_plugins(self):
        return self.plugin_list

    @property
    def description(self):
        return self._get_plugin_property('__plugin_description__', '[Not activated]')

    @property
    def version(self):
        return self._get_plugin_property('__version__', '')
    @property
    def _friendly_name(self):
        return self._get_plugin_property('__plugin_name__', '')

class AuxData(BaseModel):

    key = TextField(null=False)
    text_value = TextField(null=True)
    int_value = IntegerField(null=True)
#     parent = IntegerField(null=True)
#
#     @property
#     def children(self):
#         return self.select().where(
#             self.parent == self.id)
#
#     @property
#     def parent(self):
#         return self.select().where(
#             self.id == self.parent)

class PluginData(AuxData):

    plugin = ForeignKeyField(Plugin, index=True, null=False)
    blog = ForeignKeyField(Blog, null=True)
    site = ForeignKeyField(Site, null=True)
    user = ForeignKeyField(User, null=True)

    @property
    def remove_settings(self, plugin):
        settings_to_remove = self.delete().where(
            self.plugin == plugin)
        return settings_to_remove.execute()

#     @property
#     def plugin(self, plugin_name):
#         return self.select().where(
#             PluginData.plugin == Plugin.get().where(
#                 Plugin.name == plugin_name))

class ThemeData(AuxData):

    blog = ForeignKeyField(Blog, null=True)
    theme = ForeignKeyField(Theme, index=True, null=False)

    # both theme and blog must match a given blog for the settings to be applied
    # this way you can switch themes on a blog and keep the data from the old theme

    @property
    def remove_settings(self, blog):
        settings_to_remove = self.delete().where(
            self.blog == blog)
        return settings_to_remove.execute()


    @property
    def theme(self, theme_title):
        return self.select().where(
            ThemeData.theme == Theme.get().where(
                Theme.title == theme_title))


# We should eventually convert this to a class where the attributes
# are generated as needed on demand, not all at once. If possible

from core import utils as _utils

class TemplateTags(object):
    # Class for the template tags that are used in page templates.
    # Also used for building many other things.

    tags_init = ("blog", "page", "authors", "site", "user", "media",
        "template", "archive")

    def __init__(self, **ka):

        for key in self.tags_init:
            setattr(self, key, None)

        self.request = request
        self.settings = _settings
        self.utils = _utils
        self.sites = Site.select()
        self.status_modes = page_status

        self.tags = template_tags

        self.search_query, self.search_terms = '', ''
        if 'search' in ka:
            if ka['search'] is not None:
                self.search_terms = ka['search']
                self.search_query = "&search=" + self.search_terms

        self.pages = ka.get('pages', None)
        self.status = ka.get('status', None)

        if 'user' in ka:
            self.user = ka['user']
            token = self.user.last_login
        else:
            token = SECRET_KEY

        self.csrf_token = csrf_tag(token)
        self.csrf = csrf_hash(token)

        if 'media_id' in ka:
            self.media = Media.load(ka['media_id'])
            ka['blog_id'] = self.media.blog.id
        elif 'media' in ka:
            self.media = ka.get('media', None)

        if 'page_id' in ka:
            self.page = Page.load(ka['page_id'])
            ka['page'] = self.page

        if 'page' in ka:
            self.page = ka['page']
            ka['blog_id'] = self.page.blog.id
            self.pages = (self.page,)

        if 'category_id' in ka:
            self.category = Category.load(ka['category_id'])
            ka['blog_id'] = self.category.blog.id

        if 'template_id' in ka:
            self.template = Template.load(ka['template_id'])
            ka['blog_id'] = self.template.blog.id
        elif 'template' in ka:
            self.template = ka['template']
            ka['blog_id'] = self.template.blog.id

        if 'blog_id' in ka:
            self.blog = Blog.load(ka['blog_id'])
            ka['site_id'] = self.blog.site.id
        else:
            self.blog = ka.get('blog', self.blog)

        if 'site_id' in ka:
            self.site = Site.load(ka['site_id'])
        else:
            self.site = ka.get('site', self.site)

        # Set queue for context
        if self.blog:
            self.queue = Queue.select().where(Queue.blog == self.blog)
            self.queue_count = Queue.job_counts(blog=self.blog)

        elif self.site:
            self.queue = Queue.select().where(Queue.site == self.site)
            self.queue_count = Queue.job_counts(site=self.site)
        else:
            self.queue = Queue.select()
            self.queue_count = Queue.job_counts()

        if 'archive' in ka:
            # this whole thing is no good we need to rethink it
            # what's the point?

            # TODO: make archive into its own class
            # This is already being done in cms
            # we just need to fully populate all the objects there
            # and have proper next/prev support, etc.

            # ?? Shouldn't archive just be the page proxy??

            archive = Struct()
            setattr(archive, "pages", ka['archive'])

            if archive.pages.count() == 0:
                setattr(archive, "context", self.blog.pages.get().publication_date)
                setattr(archive, "context_tz", self.blog.pages.get().publication_date_tz)
            else:
                setattr(archive, "context", ka['archive'].get().publication_date)
                setattr(archive, "context_tz", ka['archive'].get().publication_date_tz)

            # do we even use this anywhere?
            # would this even be the right metaphor? archive.tag?

            for n in (
                (Tag, 'tag'),
                ):
                item_id = getattr(ka['archive_context'], n[1], None)
                if item_id is not None:
                    try:
                        tags_in_archive = n[0].get(n[0].id == item_id)
                    except:
                        tags_in_archive = Tag()
                    setattr(archive,
                        n[1],
                        # n[0].get(n[0].id == item_id),
                        tags_in_archive
                        )

            # archive.pages = a list of pages constrained by the current archive definition
            # archive.context = the DATE context for those pages
            # archive.archive_context.year/month = date values
            # archive.archive_context.category = category object
            # archive.archive_context.author = user object
            # archive.archive_context.tags = collection of tag objects

            # TODO: how do we compute next/previous in archive?
            # we need to have archive from blog.archive
            # blog.archive should take a context in much the same way we compute
            # for previews of an archive template
            # by way of next_in_mapping, etc.

            # TODO: replace this with a proper fixed list of archive types!!

            # These are taken from the fileinfo for the underlying object
            for n in ('year', 'month', 'category', 'author'):
                setattr(archive, n, getattr(ka['archive_context'], n, None))
            # eventually we'll handle these more elegantly
            # convert each one to their respective objects
            if archive.category is not None:
                setattr(archive, 'category', Category.load(archive.category))
            if archive.author is not None:
                setattr(archive, 'author', User.get(User.id == archive.author))

            self.archive = archive


        if 'fileinfo' in ka:
            self.fileinfo = ka['fileinfo']


def template_tags(**ka):
    return TemplateTags(**ka)
