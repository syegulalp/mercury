from core import (auth, utils)
from core.menu import generate_menu, colsets, icons
from core.search import site_search_results

from core.models import (Struct, get_site, template_tags)

from core.models.transaction import transaction

from core.libs.bottle import (template, request)

from .ui import search_context

@transaction
def site(site_id, errormsg=None):
    '''
    UI for listing contents of a given site
    '''
    user = auth.is_logged_in(request)
    site = get_site(site_id)
    permission = auth.is_site_member(user, site)

    try:
        blogs_searched, search = site_search_results(request, site)
    except (KeyError, ValueError):
        blogs_searched, search = None, None

    # page = utils.page_list_id(request)

    tags = template_tags(site_id=site.id,
        search=search,
        user=user)

    if errormsg is not None:
        tags.status = errormsg

    taglist = tags.site.blogs

    paginator, rowset = utils.generate_paginator(taglist, request)

    tpl = template('listing/listing_ui',
        paginator=paginator,
        search_context=(search_context['site'], site),
        menu=generate_menu('site', site),
        rowset=rowset,
        colset=colsets['site'],
        icons=icons,
        **tags.__dict__)

    return tpl

'''
@transaction
def site_create_user(site_id):

    #Creates a user and gives it certain permissions within the context of a given blog

    user = auth.is_logged_in(request)
    site = get_site(site_id)
    permission = auth.is_site_admin(user, site)
    tags = template_tags(site_id=site.id,
        user=user)

    edit_user = Struct()
    edit_user.name = ""
    edit_user.email = ""

    tpl = template('edit/edit_user_settings',
        menu=generate_menu('site_create_users', site),
        search_context=(search_context['sites'], None),
        edit_user=edit_user,
        **tags.__dict__
        )

    return tpl


# TODO: add proper transaction support
def site_create_user_save(site_id):

    user = auth.is_logged_in(request)
    site = get_site(site_id)
    permission = auth.is_site_admin(user, site)

    tags = template_tags(site_id=site.id,
        user=user)

    new_user = mgmt.create_user_site(
        name=request.forms.getunicode('user_name'),
        email=request.forms.getunicode('user_email')
        )

    redirect(BASE_URL + "/site/" + str(site.id) + "/user/" + str(new_user.id))

@transaction
def site_edit_user(site_id, user_id, status=None):

    user = auth.is_logged_in(request)

    site = get_site(site_id)
    permission = auth.is_site_admin(user, site)

    edit_user = get_user(user_id=user_id)

    referer = request.headers.get('Referer')

    if (referer is None
        or edit_user.last_login is None
        or re.match(re.escape("/site/" + str(site.id) + "/users"), referer) is None):

        referer = BASE_URL + "/site/" + str(site.id) + "/users"

    if edit_user.last_login is None:

        status = utils.Status(
            type='success',
            message='User <b>{}</b> (#{}) successfully created.',
            vals=(edit_user.name, edit_user.id)
            )

        edit_user.last_login = datetime.datetime.now()
        edit_user.save()

    tags = template_tags(site_id=site.id,
        user=user,
        status=status)

    return site_edit_user_output(tags, edit_user)

@transaction
def site_edit_user_save(site_id, user_id):

    user = auth.is_logged_in(request)
    site = get_site(site_id)
    permission = auth.is_site_admin(user, site)

    edit_user = get_user(user_id=user_id)

    # TODO: move to its own function?

    try:
        mgmt.update_user(edit_user, user,
            name=request.forms.getunicode('user_name'),
            email=request.forms.getunicode('user_email')
            )
    except peewee.IntegrityError:
        status = utils.Status(
            type='danger',
            message='Error: user <b>{}</b> (#{}) cannot be changed to the same name or email as another user.',
            vals=(edit_user.name, edit_user.id)
            )
    else:
        status = utils.Status(
            type='success',
            message='Data for user <b>{}</b> (#{}) successfully updated.',
            vals=(edit_user.name, edit_user.id)
            )

    tags = template_tags(site_id=site.id,
        user=user,
        status=status)

    return site_edit_user_output(tags, edit_user)

def site_edit_user_output(tags, edit_user):

    tpl = template('edit/edit_user_settings',
        search_context=(search_context['sites'], None),
        edit_user=edit_user,
        menu=generate_menu('site_manage_user', edit_user.from_site(tags.site)),
        **tags.__dict__
        )
    return tpl

@transaction
def site_list_users(site_id):

    user = auth.is_logged_in(request)
    site = get_site(site_id)
    permission = auth.is_site_admin(user, site)
    user_list = site.users

    tags = template_tags(site_id=site.id,
        user=user)

    paginator, page_list = utils.generate_paginator(user_list, request)

    tpl = template('user_listing/listing_ui',
        menu=generate_menu('site_manage_users', site),
        search_context=(search_context['sites'], None),
        paginator=paginator,
        page_list=page_list,
        user_list=user_list,
        **tags.__dict__
        )

    return tpl
'''
