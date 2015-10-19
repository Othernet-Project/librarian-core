import logging.config
import sys


def configure(supervisor):
    logging.config.dictConfig({
        'version': 1,
        'root': {
            'handlers': ['file', 'console'],
            'level': logging.DEBUG,
        },
        'handlers': {
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'default',
                'filename': supervisor.config['logging.output'],
                'maxBytes': supervisor.config['logging.size'],
                'backupCount': supervisor.config['logging.backups'],
            },
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'INFO',
                'stream': sys.stdout
            }
        },
        'formatters': {
            'default': {
                'format': supervisor.config['logging.format'],
                'datefmt': supervisor.config['logging.date_format'],
            },
        },
    })
