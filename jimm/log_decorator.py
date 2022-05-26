import sys
import logging
import traceback

import logs.server_log_config
import logs.client_log_config


def log(func):
    def wrapper(*args, **kwargs):
        logger_name = 'server' if 'server.py' in sys.argv[0] else 'client'
        LOGGER = logging.getLogger(logger_name)

        res = func(*args, **kwargs)
        LOGGER.debug(f'Вызов функции {func.__name__} c параметрами {args}, {kwargs}.'
                     f'Вызов из модуля {func.__module__}.'
                     f'Вызов из функции {traceback.format_stack()[0].strip().split()[-1]}.')
        return res
    return wrapper
