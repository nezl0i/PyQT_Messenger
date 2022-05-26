from tabulate import tabulate
from host_range_ping import host_range_ping

_CREATE = True


def host_range_ping_tab():
    _core = host_range_ping(_CREATE)
    print()
    print(tabulate([_core], headers='keys', tablefmt='pipe', stralign='center'))


if __name__ == "__main__":
    host_range_ping_tab()
