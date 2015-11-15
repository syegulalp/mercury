from core.models.transaction import transaction
from core.libs.bottle import (request, template, redirect)
from core import auth, utils
from core.models import (template_tags, get_user, get_site, get_blog)
from core.menu import generate_menu, colsets
from .ui import search_context

def system_context(user_to_edit=None, path='basic'):
    from core.models import User
    users = User.select()
    try:
        root_path = '/system/user/{}'.format(user_to_edit.id)
    except AttributeError:
        root_path = ''
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
        ),
        }

def site_context():
    pass
def blog_context():
    pass
def self_context():
    pass

def system_new_user():

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

        errors = []

        try:

            new_user = User(
                name=new_name,
                email=new_email,
                password=new_password)

            if new_name == '':
                errors.append('Username cannot be blank.')

                '''
                status = utils.Status(
                    type='danger',
                    message='Error: Username cannot be blank.'
                    )
                raise UserCreationError
                '''

            if new_email == '':
                errors.append('Email cannot be blank.')
                '''
                status = utils.Status(
                    type='danger',
                    message='Error: Email cannot be blank.'
                    )
                raise UserCreationError
                '''

            if new_password == '' or new_password_confirm == '':
                errors.append('Password or confirmation field is blank.')
                '''
                status = utils.Status(
                    type='danger',
                    message='Error: Password or confirmation field is blank.'
                    )
                raise UserCreationError
                '''

            if len(new_password) < 8:
                errors.append('Password or confirmation field is blank.')
                '''
                status = utils.Status(
                    type='danger',
                    message='Error: Password or confirmation field is blank.'
                    )
                raise UserCreationError
                '''

            if new_password != new_password_confirm:
                errors.append('Passwords do not match.')
                '''
                status = utils.Status(
                    type='danger',
                    message='Error: Passwords do not match.'
                    )
                raise UserCreationError
                '''
            if len(errors) > 0:
                raise UserCreationError
        except UserCreationError:
            status = utils.Status(
                type='danger',
                message='There were problems creating the new user:',
                message_list=errors
                )
        except Exception:
            raise
        else:
            from core.libs import peewee
            try:
                new_user.save()
            except peewee.IntegrityError as e:
                status = utils.Status(
                    type='danger',
                    message='The new user\'s email or username is the same as another user\'s. Emails and usernames must be unique.'
                    )

            except Exception as e:
                raise e
            else:
                from settings import BASE_URL
                redirect(BASE_URL + '/system/user/{}'.format(new_user.id))

    else:
        new_user = User(name='',
            email='')

    tags = template_tags(user=user)
    tags.status = status

    tpl = template('edit/edit_user_settings',
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
    # Obtains user edit in system context.
    user = auth.is_logged_in(request)
    permission = auth.is_sys_admin(user)
    user_to_edit = get_user(user_id=user_id)

    status = None

    from core.error import PermissionsException

    if request.method == 'POST':

        if request.forms.getunicode('submit_settings') is not None:

            from core import mgmt
            from core.libs import peewee

            new_name = request.forms.getunicode('user_name')
            new_email = request.forms.getunicode('user_email')

            try:
                user_to_edit = mgmt.update_user(user_to_edit, user,
                    name=new_name,
                    email=new_email
                    )
            except peewee.IntegrityError:
                status = utils.Status(
                    type='danger',
                    message='Error: user <b>{}</b> (#{}) cannot be changed to the same name or email as another user.',
                    vals=(user_to_edit.name, user_to_edit.id)
                    # TODO: use standard form exception?
                    )
            else:
                status = utils.Status(
                    type='success',
                    message='Data for user <b>{}</b> (#{}) successfully updated.',
                    vals=(user_to_edit.name, user_to_edit.id)
                    )

        if request.forms.getunicode('delete_permissions') is not None:
            deletes = request.forms.getall('del')
            from core import mgmt
            try:
                mgmt.remove_user_permissions(user, deletes)
            except PermissionsException as e:
                raise e
            status = utils.Status(
                type='success',
                message='Data for user <b>{}</b> (#{}) successfully updated.',
                vals=(user_to_edit.name, user_to_edit.id)
                )

        if request.forms.getunicode('submit_permissions') is not None:

            permission_to_add = int(request.forms.getunicode('permission_list'))
            permission_target = request.forms.getunicode('permission_target_list')
            target_site = None
            target_blog = None
            if permission_to_add != auth.role.SYS_ADMIN:
                permission_target_item = permission_target[:5]
                if permission_target_item == 'site-':
                    target_site = get_site(permission_target[5:])
                else:
                    target_blog = get_blog(permission_target[5:])


            from core import mgmt
            mgmt.add_user_permission(user_to_edit,
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
                message='User <b>{}</b> successfully created.'.format(user_to_edit.for_display),
                )
            import datetime
            user_to_edit.last_login = datetime.datetime.now()
            user_to_edit.save()

    tags = template_tags(user=get_user(user_id=user.id))
    tags.status = status
    try:
        tags.permissions = auth.get_permissions(user_to_edit)
    except PermissionsException:
        tags.permissions = []
    tags.editor_permissions = auth.get_permissions(user)
    return edit_user(user_to_edit, editing_user=user,
        context=system_context(user_to_edit, path),
        tags=tags)

@transaction
def system_users():
    user = auth.is_logged_in(request)
    permission = auth.is_sys_admin(user)
    context = system_context()
    tags = template_tags(user=user)

    paginator, rowset = utils.generate_paginator(context['users'], request)
    path = context['path']
    tpl = template('listing/listing_ui',
        section_title=context['title'],
        search_context=context['search_context'],
        menu=context['menu'],
        colset=colsets['system_users'],
        paginator=paginator,
        rowset=rowset,
        **tags.__dict__)

    return tpl


@transaction
def site_user(user_id, site_id):
    # Obtains user edit in site context.
    user = auth.is_logged_in(request)
    site = get_site(site_id)
    permission = auth.is_site_admin(user, site)
    user_to_edit = get_user(user_id)

    return edit_user(user_to_edit, editing_user=user, context=site_context, site=site)

@transaction
def blog_user(user_id, blog_id):
    # Obtains user edit in blog context.
    user = auth.is_logged_in(request)
    blog = get_blog(blog_id)
    permission = auth.is_blog_admin(user, blog)
    user_to_edit = get_user(user_id)

    return edit_user(user_to_edit, editing_user=user, context=blog_context, blog=blog)

@transaction
def self_edit():
    # Obtains user edit when a user is editing his or her own properties.
    user = auth.is_logged_in(request)
    return edit_user(user, context=self_context)

# blog_user_edit et al will eventually be moved into this context

def edit_user(edit_user, **ka):
    context = ka.get('context')

    editing_user = ka.get('editing_user', edit_user)
    site = ka.get('site')
    blog = ka.get('blog')

    tags = ka.get('tags')
    tags.nav_default = context['nav_default']
    tags.nav_tabs = context['nav_tabs']

    tpl = template('edit/edit_user_settings',

        edit_user=edit_user,
        menu=generate_menu('system_edit_user', edit_user),
        search_context=(search_context['sites'], None),
        context=None,
        **tags.__dict__
        )

    return tpl


