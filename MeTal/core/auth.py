from core.libs.bottle import redirect, request
from core.models import User, Permission, Struct, MediaAssociation, Queue
from settings import BASE_URL, SECRET_KEY, MAINTENANCE_MODE
from core.error import PermissionsException, UserNotFound, QueueInProgressException
from core.utils import Status

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

def displayable():
    displayable_permissions = {
        role.CONTRIBUTOR:('Contributor', bitmask.contribute_to_blog),
        role.AUTHOR:('Author', bitmask.author_page),
        role.EDITOR:('Editor', bitmask.edit_page),
        role.DESIGNER:('Designer', bitmask.design),
        role.BLOG_ADMIN:('Blog administrator', bitmask.administrate_blog),
        role.SITE_ADMIN:('Site administrator', bitmask.administrate_site),
        role.SYS_ADMIN:('System administrator', bitmask.administrate_system)
        }
    return displayable_permissions

def displayable_list():
    displayable_list = [
        role.CONTRIBUTOR,
        role.AUTHOR,
        role.EDITOR,
        role.DESIGNER,
        role.BLOG_ADMIN,
        role.SITE_ADMIN,
        role.SYS_ADMIN,
        ]
    return displayable_list


def settable():
    settable_permissions = {
        role.CONTRIBUTOR:None,
        role.AUTHOR:None,
        role.EDITOR:(role.CONTRIBUTOR,
            role.AUTHOR,
            role.EDITOR
            ),
        role.DESIGNER:None,
        role.BLOG_ADMIN:(role.CONTRIBUTOR,
            role.AUTHOR,
            role.EDITOR,
            role.DESIGNER,
            role.BLOG_ADMIN
            ),
        role.SITE_ADMIN:(role.CONTRIBUTOR,
            role.AUTHOR,
            role.EDITOR,
            role.DESIGNER,
            role.BLOG_ADMIN,
            role.SITE_ADMIN
            ),
        role.SYS_ADMIN:(role.CONTRIBUTOR,
            role.AUTHOR,
            role.EDITOR,
            role.DESIGNER,
            role.BLOG_ADMIN,
            role.SITE_ADMIN,
            role.SYS_ADMIN
            )
        }

    return settable_permissions

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

def get_users_with_permission(level):

    permissions = Permission.select().where(
        Permission.permission == level)

    users_with_permissions = User.select().where(
        User.id << permissions[0].user)

    return users_with_permissions

def get_permissions(user, level=None, blog=None, site=None):

    permissions = Permission.select().where(
        Permission.user == user).order_by(Permission.permission.desc())

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

    if MAINTENANCE_MODE is True:
        permissions2 = permissions.select().where(
            (Permission.permission.bin_and(role.SYS_ADMIN)))
        if permissions2.count() == 0:
            from core.error import MaintenanceModeException
            raise MaintenanceModeException("The site is currently in maintenance mode and cannot be accessed by anyone except the site admins.")

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
        return get_permissions(user, None, blog)
    except PermissionsException:
        pass

    try:
        return is_site_member(user, blog.site)
    except PermissionsException:
        pass

    raise PermissionsException('User {} does not have permission to work with blog {}'.format(
        user.for_log, blog.for_log))

def is_blog_author(user, blog):
    '''Determines if the given user has author privileges on a given blog.'''
    try:
        return get_permissions(user, bitmask.author_page, blog)
    except PermissionsException:
        pass
    try:
        return get_permissions(user, bitmask.author_page, None, blog.site)
    except PermissionsException:
        pass

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
        return is_page_editor
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

def _user(func):
    '''
    Attempt at a user context decorator
    '''
    @wraps(func)
    def wrapper(*a, **ka):
        try:
            user = is_logged_in_core(request)
        except UserNotFound:
            redirect(BASE_URL + "/login?action=" + parse.quote_plus(request.path))
        ka['_user'] = user
        return func (*a, **ka)
    return wrapper


def publishing_lock(blog, return_queue=False):
    '''
    Checks to see if a publishing job for a given blog is currently running.
    If it is, it raises an exception.
    If the return_queue flag is set, it returns the queue_control object instead.
    If no job is locked, then it returns None.
    '''
    try:
        queue_control = Queue.select().where(Queue.blog == blog,
            Queue.is_control == True).order_by(Queue.id.asc())
        qc = queue_control.get()
    except Queue.DoesNotExist:
        return None

    if return_queue is True:
        return queue_control
    else:
        raise QueueInProgressException("Publishing job currently running for blog {}".format(
            blog.for_log))

def check_publishing_lock(blog, action_description, warn_only=False):
    '''
    Checks for a publishing lock and returns a status message if busy.
    '''
    try:
        publishing_lock(blog)
    except QueueInProgressException as e:
        msg = "{} is not available right now. Proceed with caution. Reason: {}".format(
            action_description, e)
        if warn_only is True:
            return Status(
                type='warning',
                message=msg
                )
        else:
            raise QueueInProgressException(msg)

def check_template_lock(blog, warn_only=False):
    '''
    Checks for a publishing lock for template editing.
    '''
    return check_publishing_lock(blog, "Template editing", warn_only)

def check_settings_lock(blog, warn_only=False):
    '''
    Checks for a publishing lock for blog settings editing.
    '''
    return check_publishing_lock(blog, "Blog settings editing", warn_only)

def check_tag_editing_lock(blog, warn_only=False):
    '''
    Checks for a publishing lock for tag editing.
    '''
    return check_publishing_lock(blog, "Tag editing", warn_only)

def check_category_editing_lock(blog, warn_only=False):
    '''
    Checks for a publishing lock for category editing.
    '''
    return check_publishing_lock(blog, "Category editing", warn_only)

def check_page_editing_lock(page):
    pass
