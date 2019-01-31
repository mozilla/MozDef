import netaddr


def is_ip(ip):
    try:
        netaddr.IPNetwork(ip)
        return True
    except Exception:
        return False
