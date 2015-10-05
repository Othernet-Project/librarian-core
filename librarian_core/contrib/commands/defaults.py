import os


def debug_on(arg, supervisor):
    supervisor.config['app.debug'] = arg


def install_default_commands(supervisor):
    default_path = os.path.join(supervisor.config['root'],
                                supervisor.DEFAULT_CONFIG_FILENAME)
    supervisor.exts.commands.register('config',
                                      None,
                                      '--conf',
                                      metavar='PATH',
                                      default=default_path,
                                      help='path to configuration file')
    supervisor.exts.commands.register('debug',
                                      debug_on,
                                      '--debug',
                                      action='store_true',
                                      help='enable debugging')
