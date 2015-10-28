from bottle import request, response


def set_default_locale(code):
    for plugin in request.app.plugins:
        if getattr(plugin, 'name', '') == 'i18n':
            plugin.default_locale = code


def set_current_locale(code):
    request.locale = code
    response.set_cookie('locale', code, path='/')


def get_enabled_locales():
    return request.app.supervisor.config.get('i18n.locales', ['en'])
