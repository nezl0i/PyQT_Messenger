import platform
import subprocess
import threading
from core import timing, check_ip, check_answer

_CREATE = False
cmd = ['ping', '-c', '1', '-w', '1']
if platform.system().lower() == 'windows':
    cmd[1] = '-n'

threads = []
summary = {check_answer(0): "", check_answer(1): ""}


def ping_ip(ip, create):
    cmd.insert(1, str(ip))
    response = subprocess.Popen([*cmd], stdout=subprocess.PIPE)
    answer = check_answer(response.wait())
    print("{0:<20s}{1}".format(str(ip), answer))
    if create:
        summary[answer] += f"{ip}\n"


@timing
def host_ping_no_thread(ip_list: list, create=False):
    """Функция проверки доступности IP адресов из списка без применения потоков
    """
    for ip in ip_list:
        _ip = check_ip(ip)
        ping_ip(_ip, create)
        cmd.pop(1)
    return summary


@timing
def host_ping(ip_list: list, create=False):
    """Функция проверки доступности IP адресов из списка с помощью потоков
    """
    for ip in ip_list:
        _ip = check_ip(ip)
        thread = threading.Thread(target=ping_ip, args=(_ip, create), daemon=True)
        thread.start()
        threads.append(thread)
        cmd.pop(1)

    for thread in threads:
        thread.join()
    return summary


if __name__ == "__main__":
    hosts_list = ['yandex.ru', 'google.com', '10.0.0.0', '10.10.0.0', '10.10.0.1', '10.10.0.2', '10.10.0.0']
    print(host_ping(hosts_list, _CREATE))
    host_ping_no_thread(hosts_list, _CREATE)
