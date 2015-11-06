import settings

def setup_args():
    '''
    Parses command-line arguments for setup operations.
    We will eventually move this into its own module (cmd or somthing like that)
    '''
    import argparse

    parser = argparse.ArgumentParser(description='MeTal command line options.')

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

        _stderr('\nNo configuration file [{}] found in \'{}\'.\n'.format(
            settings.INI_FILE_NAME,
            settings.config_file))
        _stderr('Navigate to http://{}:{} to begin setup.\n\n'.format(
                settings.DEFAULT_LOCAL_ADDRESS,
                settings.DEFAULT_LOCAL_PORT[1:]))

        from core.routes import server_static  # ,setup

        def setup(step_id=None):
            if step_id is None:
                step_id = 0
            from install import install
            return install.step(step_id)

        app = bottle.Bottle()
        app.route(path=settings.BASE_PATH + "/", callback=setup)
        app.route(path=settings.BASE_PATH + '/install', callback=setup)
        app.route(path=settings.BASE_PATH + '/install/step-<step_id:int>', callback=setup, method=('GET', 'POST'))
        app.route(path=settings.BASE_PATH + settings.STATIC_PATH + '/<filepath:path>', callback=server_static)

        @app.error(404)
        def fnf_error(error):  # @UnusedVariable
            return setup()

    else:

        from core.routes import app
        settings.DB.make_db_connection()


        from core import plugins
        try:
            plugins.activate_plugins()
        except (plugins.PluginImportError, BaseException) as e:
            _stderr ("\nProblem importing plugins: " + (str(e)) + '\n')

    if settings.DESKTOP_MODE and arguments.url:
        import webbrowser
        webbrowser.open('http://' + settings.DEFAULT_LOCAL_ADDRESS + settings.DEFAULT_LOCAL_PORT + '/' + arguments.url)

    if (settings.DEBUG_MODE is True and settings.NO_SETUP is False and settings.USE_WSGI is False):
        from core.log import logger
        logger.info("Starting server at {} on port {}".format(
            settings.DEFAULT_LOCAL_ADDRESS,
            settings.DEFAULT_LOCAL_PORT[1:]))

    if settings.USE_WSGI:
        bottle.run(app,
            server="cgi",
            debug=settings.DEBUG_MODE)

    else:
        bottle.run(app,
            server="auto",
            port=settings.DEFAULT_LOCAL_PORT[1:],
            debug=settings.DEBUG_MODE)

def reboot():
    '''
    Resets the Web server. Used after committing system changes (e.g., activating plugins).
    '''
    import os, sys
    sys.stderr.close()
    python = sys.executable
    os.execl(python, python, * sys.argv)
