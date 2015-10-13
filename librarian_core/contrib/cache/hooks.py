from .cache import setup


def initialize(supervisor):
    optional = dict((key, supervisor.config[key])
                    for key in ('config.limit', 'config.servers')
                    if key in supervisor.config)
    supervisor.exts.cache = setup(backend=supervisor.config['cache.backend'],
                                  timeout=supervisor.config['cache.timeout'],
                                  **optional)
