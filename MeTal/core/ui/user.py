from core.models.transaction import transaction
from core.libs.bottle import (request, template)
from core import auth
from core.models import (template_tags, get_user, get_site, get_blog)
from core.menu import generate_menu
from .ui import search_context

def system_context():
    pass
def site_context():
    pass
def blog_context():
    pass
def self_context():
    pass

@transaction
def system_user(user_id):
    # Obtains user edit in system context.
    user = auth.is_logged_in(request)
    permission = auth.is_sys_admin(user)
    user_to_edit = get_user(user_id)

    return edit_user(user_to_edit, editing_user=user, context=system_context)

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

def edit_user(user_to_edit, **ka):
    context = ka.get('context')
    editing_user = ka.get('editing_user', user_to_edit)
    site = ka.get('site')
    blog = ka.get('blog')

    '''
    context contains:
    - list of all permissions that can be set by the current user for the current context
    - any permissions not allowed will be shown but greyed out, with an explanation
    '''

    c_settings = context()


'''
@transaction
def _me():
    user = auth.is_logged_in(request)
    tags = template_tags(user=user)

    from core.ui import blog
    return blog.blog_user_edit(blog_id, user.id)


    if request.method == 'POST':
        new_name = request.forms.getunicode('user_name')
        if new_name != user.name:
            user.name = new_name
            user.save()

    tpl = template('edit/edit_user_settings',
        edit_user=user,
        menu=generate_menu('all_sites', None),
        search_context=(search_context['sites'], None),
        **tags.__dict__
        )

    return tpl
    '''

