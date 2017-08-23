from core.models.transaction import transaction
from core.libs.bottle import (request, template, redirect)
from core import auth, utils
from core.models import (template_tags, User, Site, Blog)
from core.menu import generate_menu, colsets
from . import search_context

def site_context():
    pass
def blog_context():
    pass

def self_context(user_to_edit=None, path='basic'):
    return master_context(user_to_edit, path, '/me')

def system_context(user_to_edit=None, path='basic'):
    try:
        root_path = '/system/user/{}'.format(user_to_edit.id)
    except AttributeError:
        root_path = ''
    return master_context(User.select(), path, root_path)

def master_context(users, path, root_path):
    return {
        'users':users,
        'search_context':(search_context['sites'], None),
        'menu':generate_menu('system_manage_users', None),
        'title':'List all users',
        'path':root_path,
        'nav_default': path,
        'nav_tabs': (
            ('basic', root_path + '/basic', 'Basic',),
            ('permissions', root_path + '/permissions', 'Permissions')
        )
        }

'''
# todo: move all this to user stuff in core.mgmt
def verify_user_changes(user, new_password_confirm):

    from core.error import UserCreationError
    errors = []

    if user.name == '':
        errors.append('Username cannot be blank.')

    if len(user.name) < 3:
        errors.append('Username cannot be less than three characters.')

    if user.email == '':
        errors.append('Email cannot be blank.')

    if user.password == '' or new_password_confirm == '':
        errors.append('Password or confirmation field is blank.')

    if len(user.password) < 8:
        errors.append('Password cannot be less than 8 characters.')

    if user.password != new_password_confirm:
        errors.append('Passwords do not match.')

    if len(errors) > 0:
        raise UserCreationError(errors)
'''

@transaction
def system_new_user():

    from core.models import db

    user = auth.is_logged_in(request)
    permission = auth.is_sys_admin(user)

    nav_tabs = None
    status = None

    from core.models import User

    if request.method == 'POST':

        new_name = request.forms.getunicode('user_name')
        new_email = request.forms.getunicode('user_email')
        new_password = request.forms.getunicode('user_password')
        new_password_confirm = request.forms.getunicode('user_password_confirm')

        from core.error import UserCreationError

        from core.libs import peewee

        # TODO: make this into a confirmation function a la what we did with blog settings

        new_user = User(
            name=new_name,
            email=new_email,
            password=new_password,
            password_confirm=new_password_confirm)

        try:
            new_user.save_pwd()

        except UserCreationError as e:
            status = utils.Status(
                type='danger',
                no_sure=True,
                message='There were problems creating the new user:',
                message_list=e.args[0]
                )
        # TODO: replace with integrity error utility
        except peewee.IntegrityError as e:
            status = utils.Status(
                type='danger',
                no_sure=True,
                message='There were problems creating the new user:',
                message_list=['The new user\'s email or username is the same as another user\'s. Emails and usernames must be unique.']
                )


        except Exception as e:
            raise e
        else:
            db.commit()
            from settings import BASE_URL
            return redirect(BASE_URL + '/system/user/{}'.format(new_user.id))

    else:
        new_user = User(name='',
            email='',
            password='')

    tags = template_tags(user=user)
    tags.status = status

    tpl = template('edit/user_settings',
        edit_user=new_user,
        menu=generate_menu('system_create_user', new_user),
        search_context=(search_context['sites'], None),
        nav_tabs=nav_tabs,
        nav_default='basic',
        **tags.__dict__
        )

    return tpl

@transaction
def system_user(user_id, path):
    return user_edit(user_id, path, context=system_context, permission=auth.is_sys_admin)

@transaction
def self_edit(path):
    return user_edit(None, path, context=self_context, permission=auth.is_sys_admin)
    # Not sure how to handle permission set here

def user_edit(user_id, path, context, permission):
    # Obtains user edit in system context.
    user = auth.is_logged_in(request)
    permission = permission(user)
    user_to_edit = User.find(user_id=user_id) if user_id is not None else user

    status = None

    from core.error import PermissionsException

    if request.method == 'POST':

        if request.forms.getunicode('submit_settings') is not None:

            from core.libs import peewee

            user_to_edit.name = request.forms.getunicode('user_name')
            user_to_edit.email = request.forms.getunicode('user_email')

            try:
                user_to_edit.save()

            except peewee.IntegrityError:
                status = utils.Status(
                    type='danger',
                    no_sure=True,
                    message='Error: user <b>{}</b> cannot be changed to the same name or email as another user.'.format(
                        user_to_edit.for_display)
                    )
            else:
                status = utils.Status(
                    type='success',
                    message='Data for user <b>{}</b> successfully updated.'.format(
                        user_to_edit.for_display)
                    )

        # TODO: all actions could be consolidated w/o multiple status lines

        if request.forms.getunicode('delete_permissions') is not None:

            deletes = request.forms.getall('del')
            try:
                user.remove_permissions(deletes)
            except PermissionsException as e:
                raise e
            status = utils.Status(
                type='success',
                message='Data for user <b>{}</b> successfully updated.'.format(user_to_edit.for_display)
                )

        if request.forms.getunicode('submit_permissions') is not None:

            permission_to_add = int(request.forms.getunicode('permission_list'))
            permission_target = request.forms.getunicode('permission_target_list')
            target_site = None
            target_blog = None
            if permission_to_add != auth.role.SYS_ADMIN:
                permission_target_item = permission_target[:5]
                if permission_target_item == 'site-':
                    target_site = Site.load(permission_target[5:])
                else:
                    target_blog = Blog.load(permission_target[5:])


            user_to_edit.add_permission(
                permission=permission_to_add,
                site=target_site,
                blog=target_blog)

            '''
            what we should do:
            - get any existing permission
            - update it with the proper bitmask
            then, when listing permissions,
            go through and compare each bitmask against it
            the bitmask needs to be all in one entry per site/blog/user object
            it *might* work as we have it now but we'll need to test
            we might need to order by level to make sure it works
            '''
    else:
        if user_to_edit.last_login is None:
            status = utils.Status(
                type='success',
                message='User <b>{}</b> successfully created.'.format(
                    user_to_edit.for_display),
                )
            import datetime
            user_to_edit.last_login = datetime.datetime.utcnow()
            user_to_edit.save()

    tags = template_tags(user=User.find(user_id=user.id))
    tags.status = status
    try:
        tags.permissions = auth.get_permissions(user_to_edit)
    except PermissionsException:
        tags.permissions = []
    tags.editor_permissions = auth.get_permissions(user)
    return edit_user(user_to_edit, editing_user=user,
        context=context(user_to_edit, path),
        tags=tags)

@transaction
def system_users():
    user = auth.is_logged_in(request)
    permission = auth.is_sys_admin(user)
    context = system_context()
    tags = template_tags(user=user)

    import settings

    action = utils.action_button(
        'Create new user',
        '{}/system/user/new'.format(settings.BASE_URL)
        )

    paginator, rowset = utils.generate_paginator(context['users'], request)
    path = context['path']
    tpl = template('listing/listing_ui',
        section_title=context['title'],
        search_context=context['search_context'],
        menu=context['menu'],
        colset=colsets['system_users'],
        action=action,
        paginator=paginator,
        rowset=rowset,
        **tags.__dict__)

    return tpl


@transaction
def site_user(user_id, site_id):
    # Obtains user edit in site context.
    user = auth.is_logged_in(request)
    site = Site.load(site_id)
    permission = auth.is_site_admin(user, site)
    user_to_edit = User.find(user_id)

    return edit_user(user_to_edit, editing_user=user, context=site_context, site=site)

@transaction
def blog_user(user_id, blog_id):
    # Obtains user edit in blog context.
    user = auth.is_logged_in(request)
    blog = Blog.load(blog_id)
    permission = auth.is_blog_admin(user, blog)
    user_to_edit = User.find(user_id)

    return edit_user(user_to_edit, editing_user=user, context=blog_context, blog=blog)

@transaction
def self_setting():
    user = auth.is_logged_in(request)
    setting_key = request.forms.getunicode('key')
    setting_value = request.forms.getunicode('value')

    kv_to_set = user.kv(setting_key)
    if kv_to_set is None:
        user.kv_set(setting_key, setting_value)
    else:
        kv_to_set.value = setting_value
        kv_to_set.save()

    return

# blog_user_edit et al will eventually be moved into this context

def edit_user(edit_user, **ka):
    context = ka.get('context')

    editing_user = ka.get('editing_user', edit_user)
    site = ka.get('site')
    blog = ka.get('blog')

    tags = ka.get('tags')
    tags.nav_default = context['nav_default']
    tags.nav_tabs = context['nav_tabs']

    tpl = template('edit/user_settings',

        edit_user=edit_user,
        menu=generate_menu('system_edit_user', edit_user),
        search_context=(search_context['sites'], None),
        context=None,
        **tags.__dict__
        )

    return tpl


