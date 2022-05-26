from core import check_ip
from host_ping import host_ping

ip_list = []
_CREATE = False


def host_range_ping(create=False):
    default_ip = input("Enter your default IP: ")
    _ip = check_ip(default_ip)
    end_ip = default_ip.split('.')[-1]
    if not end_ip.isdigit():
        print('last octet is not a number')
        return
    count = int(input("Enter total count IP: "))
    if int(end_ip) + count > 256:
        print('last octet is greater than 256')
        return
    for _ in range(count+1):
        ip_list.append(str(_ip + _))
    return host_ping(ip_list, create)


if __name__ == "__main__":
    host_range_ping()
