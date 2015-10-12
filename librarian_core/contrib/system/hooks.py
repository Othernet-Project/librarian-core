from .logs import configure
from .routes import error_403, error_404, error_500, error_503


def initialize(supervisor):
    configure(supervisor)
    supervisor.app.error(403)(error_403)
    supervisor.app.error(404)(error_404)
    supervisor.app.error(500)(error_500)
    supervisor.app.error(503)(error_503)
