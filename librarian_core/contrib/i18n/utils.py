from bottle import request

from ..system.utils import get_plugin


def set_default_locale(code):
    i18n = get_plugin('i18n')
    i18n.default_locale = code


def set_current_locale(code):
    i18n = get_plugin('i18n')
    i18n.set_locale(code)


def get_enabled_locales():
    return request.app.supervisor.config.get('i18n.locales', ['en'])
