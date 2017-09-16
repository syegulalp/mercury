import settings
routes_ready = False

def setup_args():
    '''
    Parses command-line arguments for setup operations.
    We will eventually move this into its own module (cmd or somthing like that)
    '''
    import argparse

    parser = argparse.ArgumentParser(description='Mercury command line options.')

    parser.add_argument('--debug', action="store_true", default=settings.DEBUG_MODE, help='enable debug mode')
    parser.add_argument('--reset', action="store_true", default=settings.RESET,
        help='resets entire database and restores factory settings')
    parser.add_argument('--max_batch_ops', action="store", dest="max_batch_ops", type=int, default=settings.MAX_BATCH_OPS,
        help=('max number of queue operations to perform in one pass, default is {0}'.format(settings.MAX_BATCH_OPS)))
    parser.add_argument('--browser', dest="url", nargs="?", const='.',
        help='launch web browser after starting local server; default URL is site admin base')

    arguments = parser.parse_args()

    settings.DEBUG_MODE = arguments.debug
    settings.RESET = arguments.reset
    settings.MAX_BATCH_OPS = arguments.max_batch_ops

    return arguments

def boot(aux_settings=None):
    '''
    Reads setup options and starts the Web server for the application.
    '''
    if aux_settings is not None:
        for n in aux_settings:
            if n in settings.__dict__:
                settings.__dict__[n] = aux_settings[n]

    from core.libs import bottle
    _stderr = bottle._stderr

    import sys

    if len(sys.argv) > 0:
        arguments = setup_args()

    bottle.TEMPLATE_PATH = [settings.VIEW_PATH]

    _stderr (settings.PRODUCT_NAME + "\n")
    _stderr ("Running in " + settings.APPLICATION_PATH + "\n")

    if settings.DEBUG_MODE:
        _stderr ("\n" + ('*' * 40) + "\nDebug mode!\nThis may impact performance.\nDo not use this setting in production.\n" + ('*' * 40) + "\n\n")

    if settings.NO_SETUP:

        # We could probably move all this into its own module ala core.routes

        _stderr('\nNo configuration file [{}] found in \'{}\'.\n'.format(
            settings.INSTALL_INI_FILE_NAME,
            settings.config_file))

        import os
        os.makedirs(os.path.join(settings.APPLICATION_PATH, 'data'), exist_ok=True)

        app = bottle.Bottle()

        def make_server(_app, settings):

            # we could move these two into utils and import from there for both
            # here and core.routes

            @_app.hook('before_request')
            def strip_path():
                if len(bottle.request.environ['PATH_INFO']) > 1:
                    bottle.request.environ['PATH_INFO'] = bottle.request.environ['PATH_INFO'].rstrip('/')

            @_app.route(settings.BASE_PATH + settings.STATIC_PATH + '/<filepath:path>')
            def server_static(filepath):
                '''
                Serves static files from the application's own internal static path,
                e.g. for its CSS/JS
                '''
                bottle.response.add_header('Cache-Control', 'max-age=7200')
                return bottle.static_file(filepath, root=settings.APPLICATION_PATH + settings.STATIC_PATH)

            @_app.route(settings.BASE_PATH + '/install', ('GET', 'POST'))
            @_app.route(settings.BASE_PATH + '/install/step-<step_id:int>', ('GET', 'POST'))
            def setup_step(step_id=0):
                try:
                    from install.install import step
                    s = step(step_id)
                except Exception as e:
                    raise e
                return s


        @app.route('/')
        def setup():
            global routes_ready

            if routes_ready is False:

                try:
                    url = bottle.request.urlparts

                    # let's assume there's always going to be redirection to hide the script name

                    path = url.path.rstrip('/').rsplit('/', 1)

                    settings.BASE_URL_PROTOCOL = url.scheme + "://"
                    # The URL scheme

                    settings.BASE_URL_NETLOC = url.netloc
                    # The server name

                    settings.BASE_URL_ROOT = settings.BASE_URL_PROTOCOL + settings.BASE_URL_NETLOC
                    # Everything up to the first / after the server name

                    settings.BASE_URL_PATH = path[0]
                    # Any additional path to the script (subdirectory)

                    settings.BASE_URL = settings.BASE_URL_ROOT + settings.BASE_URL_PATH
                    # The URL we use to reach the script by default

                    make_server(app, settings)

                    routes_ready = True

                except Exception as e:
                    return "Oops: {}".format(e)

            bottle.redirect(settings.BASE_PATH + '/install')

    else:

        from core.routes import app
        try:
            settings.DB.make_db_connection()
        except Exception as e:
            _stderr("Could not make DB connection: {}".format(e))

        from core import plugins
        try:
            plugins.activate_plugins()
        except (plugins.PluginImportError, BaseException) as e:
            _stderr ("\nProblem importing plugins: " + (str(e)) + '\n')

    if settings.DESKTOP_MODE and arguments.url:
        import webbrowser
        webbrowser.open(settings.BASE_URL_PROTOCOL + settings.DEFAULT_LOCAL_ADDRESS + settings.DEFAULT_LOCAL_PORT + '/' + arguments.url)

    if (settings.DEBUG_MODE is True and settings.NO_SETUP is False and settings.USE_WSGI is False):
        from core.log import logger
        logger.info("Starting server at {} on port {}".format(
            settings.DEFAULT_LOCAL_ADDRESS,
            settings.DEFAULT_LOCAL_PORT[1:]))

    if settings.SERVER_MODE == 'wsgi':
        bottle.run(app,
            server="flipflop",
            debug=settings.DEBUG_MODE)
    elif settings.SERVER_MODE == 'cgi':
        bottle.run(app,
            server="cgi",
            debug=settings.DEBUG_MODE)
    else:
        bottle.run(app,
            server="auto",
            port=settings.DEFAULT_LOCAL_PORT[1:],
            debug=settings.DEBUG_MODE)


