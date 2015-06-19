from libs.bottle import redirect, request
from models import User, Permission, Struct, MediaAssociation
from settings import BASE_URL, SECRET_KEY
from core.error import PermissionsException, UserNotFound

from urllib import parse
from functools import wraps

role = Struct()

role.CONTRIBUTOR = 1
role.AUTHOR = 2
role.EDITOR = 4 
role.DESIGNER = 8
role.BLOG_ADMIN = 16
role.SITE_ADMIN = 32
role.SYS_ADMIN = 64

bitmask = Struct()

bitmask.administrate_system = role.SYS_ADMIN
bitmask.administrate_site = bitmask.administrate_system + role.SITE_ADMIN
bitmask.administrate_blog = bitmask.administrate_site + role.BLOG_ADMIN
bitmask.design = bitmask.administrate_blog + role.DESIGNER
bitmask.edit_page = bitmask.administrate_blog + role.EDITOR
bitmask.author_page = bitmask.edit_page + role.AUTHOR
bitmask.contribute_to_blog = bitmask.author_page + role.CONTRIBUTOR
bitmask.publish_blog = bitmask.edit_page + bitmask.administrate_blog

def is_logged_in(request):
    '''
    Determines if a logged-in user exists, with a redirection wrapper.
    '''
    
    try:
        user = is_logged_in_core(request)
    except UserNotFound:
        redirect(BASE_URL + "/login?action=" + parse.quote_plus(request.url))
    return user

def is_logged_in_core(request):
    '''
    Determines if a logged-in user exists.
    '''
    user_name = request.get_cookie("login", secret=SECRET_KEY) or None

    if user_name is None:
        raise UserNotFound("User at {} attempted to access '{}'. Not logged in.".format(
            request.remote_addr,
            request.path))
    try:
        user_found = User.get(User.email == user_name)
    except User.DoesNotExist:
        raise UserNotFound("User at {} attempted to log in as '{}'. User not found.".format(
            request.remote_addr,
            user_name))
    
    return user_found

def get_permissions(user, level=None, blog=None, site=None):
    
    permissions = Permission.select().where(
        Permission.user == user)

    if blog:
        permissions = permissions.select().where(
            (Permission.blog == blog) | 
            (Permission.permission.bin_and(role.SYS_ADMIN)) | 
                (
                (Permission.site == blog.site) & 
                (Permission.permission.bin_and(role.SITE_ADMIN))
                )
            )

    if site:
        permissions = permissions.select().where(
            (Permission.site == site) | 
            (Permission.permission.bin_and(role.SYS_ADMIN))
            )
        
    if level:
        permissions = permissions.select().where(
            Permission.permission.bin_and(level))
        
    if permissions.count() == 0:
        raise PermissionsException('Permission {} not found'.format(level))
    
    return permissions

def is_sys_admin(user):
    '''Determines if the given user has sysadmin privileges.'''
    try:
        is_admin = get_permissions(user, bitmask.administrate_system)
        return is_admin
    except PermissionsException:
        raise PermissionsException('User {} does not have access to system admin resources.'.format(user.for_log))

    
def is_site_admin(user, site):
    '''Determines if the given user has site admin privileges on a given site.'''
    try:
        is_site_admin = get_permissions(user, bitmask.administrate_site, None, site)
        return is_site_admin 
    except PermissionsException:
        raise PermissionsException('User {} does not have permission to change settings on site {}'.format(
            user.for_log, site.for_log))
    

def is_site_member(user, site):
    '''Determines if the given user has site member privileges on a given site.'''
    try:
        is_site_member = get_permissions(user, None, None, site)
        return is_site_member 
    except PermissionsException:
        raise PermissionsException("User {} does not have permission to work with site {}".format(
            user.for_log,
            site.for_log))

        
def is_blog_member(user, blog):
    '''Determines if the given user has member privileges on a given blog.'''
    try:
        is_blog_member = get_permissions(user, None, blog)
        return is_blog_member

    except PermissionsException:
        raise PermissionsException('User {} does not have permission to work with blog {}'.format(
            user.for_log, blog.for_log))

def is_blog_author(user, blog):
    '''Determines if the given user has author privileges on a given blog.'''
    try:
        is_blog_author = get_permissions(user, bitmask.author_page, blog)
        return is_blog_author

    except PermissionsException: 
        raise PermissionsException('User {} does not have permission to author pages on blog {}'.format(
            user.for_log, blog.for_log))
        
def is_blog_editor(user, blog):
    '''Determines if the given user has editor privileges on a given blog.'''
    try:
        is_blog_editor = get_permissions(user, bitmask.edit_page, blog)
        return is_blog_editor

    except PermissionsException:        
        raise PermissionsException('User {} does not have permission to edit pages on blog {}'.format(
            user.for_log, blog.for_log))
        

def is_page_editor(user, page):
    '''Determines if the given user has page editor privileges on a given page.
    A blog, site, or sysadmin will automatically have page editor privileges.'''
    if page.author == user:
        return True 
    try:
        is_page_editor = is_blog_editor(user, page.blog)
    except PermissionsException:
        raise PermissionsException('User {} does not have permission to work with page {}'.format(user.for_log, page.for_log))
        

def is_blog_designer(user, blog):
    '''Determines if the given user has blog designer privileges on a given blog.
    A blog, site, or sysadmin will automatically have blog designer privileges.'''
    try:
        is_blog_designer = get_permissions(user, bitmask.design, blog)
        return is_blog_designer

    except PermissionsException:
        raise PermissionsException('User {} does not have permission to edit templates on blog {}'.format(user.for_log, blog.for_log))

def is_blog_publisher(user, blog):
    '''Determines if the given user has blog publisher privileges on a given blog.
    A blog, site, or sysadmin will automatically have blog publisher privileges.'''
    try:
        is_blog_publisher = get_permissions(user, bitmask.publish_blog, blog)
        return is_blog_publisher

    except PermissionsException:
        raise PermissionsException('User {} does not have permission to manually activate the publishing queue on blog {}'.format(
            user.for_log, blog.for_log))
    
   
def is_blog_admin(user, blog):
    '''Determines if the given user has blog admin privileges on a given blog.
    #A site or sysadmin will automatically have blog admin privileges.'''
    try:
        is_blog_admin = get_permissions(user, bitmask.administrate_blog, blog)
        return is_blog_admin

    except PermissionsException:
        raise PermissionsException('User {} does not have permission to change settings on blog {}'.format(
            user.for_log, blog.for_log))

    
def is_media_owner(user, media):
    '''
    Determines if the given user has owner privileges on a given media item.
    A blog, site, or sysadmin will automatically have privileges for media.
    ''' 
    
    if media.user == user:
        return media
    
    # figure out if this media belongs to a blog where the user has designer permissions
    
    media_association = MediaAssociation.select().where(
        MediaAssociation.media == media)
    
    for m in media_association:
        if m.blog is not None:
            try:
                designer = is_blog_designer(user, m.blog)
                return media
            except PermissionsException:
                pass
                
    raise PermissionsException('User {} does not have permission to edit media ID {}'.format(
        user.for_log, media.id))
   
# Attempt at a user context decorator
def _user(func):
    @wraps(func)
    def wrapper(*a, **ka):
        try:
            user = is_logged_in_core(request)
        except UserNotFound:
            redirect(BASE_URL + "/login?action=" + parse.quote_plus(request.path))
        ka['_user'] = user 
        return func (*a, **ka)
    return wrapper
