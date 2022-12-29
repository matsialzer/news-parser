import os
from pprint import pprint


LOGGER_NAMES = [
    'django',
    'parsers',
]

LOG_LEVELS = [
    "debug",
    "info",
    "warning",
    "error",
    "critical"
]

def check_directories(base_dir):
    LOGS_ROOT = f'{base_dir}/logs'
    if not os.path.exists(LOGS_ROOT):
        os.makedirs(LOGS_ROOT)
    for app_name in LOGGER_NAMES:
        app_dir = f'{LOGS_ROOT}/{app_name}'
        if not os.path.exists(app_dir):
            os.makedirs(app_dir)


def _get_logging(base_dir):
    check_directories(base_dir)

    handlers = {}
    for level in LOG_LEVELS:
        for name in LOGGER_NAMES:
            handler_name = f'{name}_{level}_handler'
            handlers.update({
                handler_name: {
                    'class': 'logging.FileHandler',
                    'level': f'{level.upper()}',
                    'filename': f'{base_dir}/logs/{name}/{level}.log',
                    'formatter': 'default',
                }
            })

    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                'format': '%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
            },
        },
        'loggers': {
            name: {
                'handlers': [
                    f'{name}_{level}_handler' for level in LOG_LEVELS
                ],
                'propagate': False,
            }
            for name in LOGGER_NAMES
        },
        'handlers': handlers
    }

    return LOGGING
