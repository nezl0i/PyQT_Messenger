import sys
import logging
import traceback
import socket
sys.path.append('../')
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


def login_required(func):
    def checker(*args, **kwargs):
        from server_app.core import MessageProcessor
        from common.variables import ACTION, PRESENCE
        if isinstance(args[0], MessageProcessor):
            found = False
            for arg in args:
                if isinstance(arg, socket.socket):
                    for client in args[0].names:
                        if args[0].names[client] == arg:
                            found = True
            for arg in args:
                if isinstance(arg, dict):
                    if ACTION in arg and arg[ACTION] == PRESENCE:
                        found = True
            if not found:
                raise TypeError
        return func(*args, **kwargs)

    return checker
