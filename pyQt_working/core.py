import time
from ipaddress import ip_address


def timing(func):
    def wrapper_repeat(*args, **kwargs):
        start = time.time()
        ret = func(*args, **kwargs)
        end = time.time()
        print(f'[{func.__name__}] - {end - start}')
        return ret
    return wrapper_repeat


def check_answer(code):
    return {
        code == 0: "Узел доступен",
        code == 1: "Узел не доступен"
    }[True]


def check_ip(ip: str):
    _ip = None
    if ''.join(ip.split('.')).isdigit():
        try:
            _ip = ip_address(ip)
        except ValueError:
            print(f'Некорректный ip адрес [{ip}]')
            exit(1)
    else:
        _ip = ip
    return _ip
