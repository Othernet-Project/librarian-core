import functools

from .routes import error_403, error_404, error_500, error_503


def set_default_route_id(supervisor, route_id):
    supervisor.config['default_route_id'] = route_id


def initialize(supervisor):
    supervisor.app.error(403)(error_403)
    supervisor.app.error(404)(error_404)
    supervisor.app.error(500)(error_500)
    supervisor.app.error(503)(error_503)
    set_route_id = functools.partial(set_default_route_id, supervisor)
    supervisor.events.subscribe('set_default_route_id', set_route_id)
