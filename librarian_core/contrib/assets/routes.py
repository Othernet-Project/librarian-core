import os

from bottle import request, static_file
from bottle_utils.lazy import caching_lazy


@caching_lazy
def static_root():
    project_root = request.app.config['root']
    static_dir = request.app.config.get('assets.directory', 'static')
    return os.path.join(project_root, static_dir)


def send_static(path):
    return static_file(path, root=static_root())


@caching_lazy
def favicon_path():
    return request.app.config.get('favicon.path', 'favicon.ico')


def send_favicon():
    return send_static(favicon_path())


def routes(config):
    skip_plugins = config['app.skip_plugins']
    return (
        ('sys:static', send_static,
         'GET', '/static/<path:path>',
         dict(no_i18n=True, unlocked=True, skip=skip_plugins)),
        ('sys:favicon', send_favicon,
         'GET', '/favicon.ico',
         dict(no_i18n=True, unlocked=True, skip=skip_plugins)),
    )
