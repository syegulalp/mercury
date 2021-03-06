from core.models.transaction import transaction
from settings import BASE_URL, SECRET_KEY
from core.libs.bottle import template, request, response, redirect
from core.models import template_tags, User, Page
from core.log import logger
from core import utils, auth
from . import search_contexts
from core.menu import generate_menu

@transaction
def login():
    '''
    User login interface
    '''
    tpl = template('ui/ui_login',
        **template_tags().__dict__)

    logger.info("Login page requested from IP {}.".format(request.remote_addr))

    response.delete_cookie("login", path="/")

    return tpl

def login_verify():
    '''
    Verifies user login, provides session cookie if successful
    '''
    _forms = request.forms

    email = _forms.get('email')
    password = _forms.get('password')

    if login_verify_core(email, password) is True:

        if request.query.action:
            utils.safe_redirect(request.query.action)
        else:
            redirect(BASE_URL)

    else:
        tags = template_tags()

        tags.status = utils.Status(
            type='danger',
            no_sure=True,
            message="Email or password not found.")

        return template('ui/ui_login',
            **tags.__dict__)

@transaction
def login_verify_core(email, password):

    try:
        user = User.login_verify(email, password)
    except User.DoesNotExist:

        logger.info("User at {} attempted to log in as '{}'. User not found or password not valid.".format(
            request.remote_addr,
            email))

        return False

    else:

        response.set_cookie("login", user.email, secret=SECRET_KEY, path="/")

        logger.info("User {} logged in from IP {}.".format(
            user.for_log,
            request.remote_addr))

        user.logout_nonce = utils.url_escape(utils.logout_nonce(user))
        user.save()

        return True


def logout():
    from core.error import UserNotFound

    try:
        user = auth.is_logged_in_core(request)
    except UserNotFound:
        user = None

    try:
        nonce = request.query['_']
    except KeyError:
        nonce = None

    if nonce == utils.url_unescape(user.logout_nonce):

        logger.info("User {} logged out from IP {}.".format(
            user.for_log,
            request.remote_addr))

        response.delete_cookie("login", path="/")

        return "You have logged out. <a href='{}/login'>Click here to log in again.</a>".format(BASE_URL)

    return "No logout nonce. <a href='{}/logout?_={}'>Click here to log out.</a>".format(
        BASE_URL, user.logout_nonce)


@transaction
def main_ui():
    '''
    Top level UI
    This will eventually become a full-blown user dashboard.
    Right now it just returns a list of sites in the system.
    All users for the system can see this dashboard.
    '''
    user = auth.is_logged_in(request)

    # TODO: replace with actual user-centric setting
    try:
        from settings import MAX_RECENT_PAGES
    except ImportError:
        MAX_RECENT_PAGES = 10

    recent_pages = Page.select().where(
        Page.user == user).order_by(
        Page.modified_date.desc()).limit(MAX_RECENT_PAGES)

    your_blogs = user.blogs()

    tpl = template('ui/ui_dashboard',
        search_context=(search_contexts['sites'], None),
        menu=generate_menu('system_menu', None),
        recent_pages=recent_pages,
        your_blogs=your_blogs,
        **template_tags(user=user).__dict__
        )

    return tpl
