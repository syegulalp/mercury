from core.models.transaction import transaction
from core.libs.bottle import (request, template)
from core import auth, utils
from core.models import (template_tags, get_user, get_site, get_blog, db)
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

@transaction
def system_user(user_id, path):
    # Obtains user edit in system context.
    user = auth.is_logged_in(request)
    permission = auth.is_sys_admin(user)
    user_to_edit = get_user(user_id=user_id)

    status = None

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

    tags = template_tags(user=get_user(user_id=user.id))
    tags.status = status
    tags.permissions = auth.get_permissions(user_to_edit)
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


