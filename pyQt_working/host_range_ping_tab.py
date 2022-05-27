from tabulate import tabulate
from host_range_ping import host_range_ping


def host_range_ping_tab():
    _core = host_range_ping()
    print()
    print(tabulate([_core], headers='keys', tablefmt='pipe', stralign='center'))


if __name__ == "__main__":
    host_range_ping_tab()
