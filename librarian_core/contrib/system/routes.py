"""
routes.py: System routes such as static files and error handlers

Copyright 2014-2015, Outernet Inc.
Some rights reserved.

This software is free software licensed under the terms of GPLv3. See COPYING
file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
"""

import logging
import os

from bottle import request, redirect, static_file, abort
from bottle_utils.i18n import i18n_url
from bottle_utils.lazy import caching_lazy

from librarian_core.contrib.templates.renderer import view


def root_handler():
    route = request.app.config['app.default_route']
    if hasattr(request, 'default_route'):
        route = request.default_route

    redirect(i18n_url(route))


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


@view('403')
def error_403(exc):
    return dict()


@view('404')
def error_404(exc):
    return dict(redirect_url='/')


@view('500')
def error_500(exc):
    logging.error("Unhandled error '%s' at %s %s:\n\n%s",
                  exc.exception,
                  request.method.upper(),
                  request.path,
                  exc.traceback)
    return dict(trace=exc.traceback)


@view('503')
def error_503(exc):
    return dict()


def all_404(path):
    abort(404)


def routes(config):
    skip_plugins = config['app.skip_plugins']
    return (
        ('sys:root', root_handler, 'GET', '/', dict()),
        ('sys:static', send_static,
         'GET', '/static/<path:path>',
         dict(no_i18n=True, unlocked=True, skip=skip_plugins)),
        ('sys:favicon', send_favicon,
         'GET', '/favicon.ico',
         dict(no_i18n=True, unlocked=True, skip=skip_plugins)),
        # This route handler is added because unhandled missing pages cause
        # bottle to _not_ install any plugins, and some are essential to
        # rendering of the 404 page (e.g., i18n, sessions, auth).
        ('sys:all404', all_404,
         ['GET', 'POST'], '<path:path>', dict()),
    )
