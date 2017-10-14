from core.libs.bottle import SimpleTemplate, cached_property
from functools import partial

def tpl_include(tpl):
    return '<!--#include virtual="{}" -->'.format(
        tpl)

class MetalTemplate(SimpleTemplate):
    class TemplateError(Exception):
        pass

    @cached_property
    def co(self):
        return compile(self.code, self.filename or self.template_name or '<string>', 'exec')

    def __init__(self, *args, **kwargs):
        self.template_name = kwargs.pop('template_name', None)
        super(MetalTemplate, self).__init__(*args, **kwargs)
        self._tags = kwargs.get('tags', None)
        self.blog = self._tags['blog']
        self.blog_id = '{}_'.format(self.blog.id)
        from core.models import Template
        self.T = Template
        from core.cms import Cache
        self.M = Cache.module_cache
        self.I = Cache.include_cache

    def _load_ssi(self, env, ssi_name=None, **kwargs):
        try:
            tpl = self.I[self.blog_id + ssi_name]
        except KeyError:
            ssi = self.blog.ssi(ssi_name)
            tpl = MetalTemplate(ssi, tags=self._tags, **kwargs)
            self.I[self.blog_id + ssi_name] = tpl
        try:
            n = tpl.execute(env['_stdout'], env)
        except Exception as e:
            raise Exception(e, ssi_name)
        return n

    def _load_module(self, module_name):
        try:
            return self.M[self.blog_id + module_name]
        except KeyError:
            module = self.blog.templates().where(
                self.T.title == module_name).get().as_module(self._tags)
            self.M[self.blog_id + module_name] = module
            return module


    def test(self, env):
        env['_stdout'] += 'is a test'
        return env

    # Copied from the underlying class.
    def execute(self, _stdout, kwargs):
        env = self.defaults.copy()
        env.update(kwargs)
        env.update({
            'module':self._load_module,
            'test':partial(self.test, env),
            'ssi': partial(self._load_ssi, env),
            'include': partial(self._include, env),
            '_stdout': _stdout, '_printlist': _stdout.extend,
            'rebase': partial(self._rebase, env), '_rebase': None,
            '_str': self._str, '_escape': self._escape, 'get': env.get,
            'setdefault': env.setdefault, 'defined': env.__contains__ })
        eval(self.co, env)
        if env.get('_rebase'):
            subtpl, rargs = env.pop('_rebase')
            rargs['base'] = ''.join(_stdout)  # copy stdout
            del _stdout[:]  # clear stdout
            return self._include(env, subtpl, **rargs)
        return env

    def _include(self, env, _name=None, **kwargs):
        try:
            tpl = self.I[self.blog_id + _name]
        except KeyError:
            template_to_import = self.blog.templates().where(
                self.T.title == _name).get().body
            tpl = MetalTemplate(template_to_import, tags=self._tags, **kwargs)
            self.I[self.blog_id + _name] = tpl
        try:
            n = tpl.execute(env['_stdout'], env)
        except Exception as e:
            raise Exception(e, _name)
        return n

    def render(self, *args, **kwargs):
        return super(MetalTemplate, self).render(*args, **kwargs)

def tpl(*args, **ka):
    '''
    Shim/shortcutfor the MetalTemplate function.
    '''
    # TODO: debug handler for errors in submitted user templates here?
    # TODO: allow analysis only to return object with list of includes

    try:
        return MetalTemplate(source=args[0], tags=ka).render(ka)
    except Exception as e:
        raise Exception("Template error: {} / {}".format(e, ka))

def tplt(template, tags):
    '''
    Shim/shortcut for the MetalTemplate function.
    Provides detailed error information at the exact line of a template.
    '''

    context = tags.__dict__
    try:
        return MetalTemplate(source=template.body, tags=context).render(context)
    except Exception as e:
        import traceback
        template_error_line = traceback.extract_tb(e.__traceback__.tb_next)[-1][1]
        raise MetalTemplate.TemplateError(
            "{} in '{}' at line {}: {}".format(
                e.__class__.__name__,
                template.title,
                template_error_line,
                e,
                )
            )