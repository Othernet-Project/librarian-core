"""
routes.py: System routes such as static files and error handlers

Copyright 2014-2015, Outernet Inc.
Some rights reserved.

This software is free software licensed under the terms of GPLv3. See COPYING
file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
"""

import logging

from bottle import request, redirect, abort
from bottle_utils.i18n import i18n_url

from librarian_core.contrib.templates.renderer import view


def root_handler():
    route = request.app.config['app.default_route']
    if hasattr(request, 'default_route'):
        route = request.default_route

    redirect(i18n_url(route))


@view('errors/403')
def error_403(exc):
    return dict()


@view('errors/404')
def error_404(exc):
    return dict(redirect_url='/')


@view('errors/500')
def error_500(exc):
    logging.error("Unhandled error '%s' at %s %s:\n\n%s",
                  exc.exception,
                  request.method.upper(),
                  request.path,
                  exc.traceback)
    return dict(trace=exc.traceback)


@view('errors/503')
def error_503(exc):
    return dict()


def all_404(path):
    abort(404)


def routes(config):
    return (
        ('sys:root', root_handler, 'GET', '/', dict()),
        # This route handler is added because unhandled missing pages cause
        # bottle to _not_ install any plugins, and some are essential to
        # rendering of the 404 page (e.g., i18n, sessions, auth).
        ('sys:all404', all_404, ['GET', 'POST'], '<path:path>', dict()),
    )
