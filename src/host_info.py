import psutil
import socket


def get_ethernet_info():
    net_if_addrs = psutil.net_if_addrs()
    net_if_stats = psutil.net_if_stats()
    mac = None
    name = None
    ip = None

    for interface, addrs in net_if_addrs.items():
        # return active ethernet port name, MAC and IP
        if (
            interface.lower().startswith("eth") or interface.lower().startswith("en")
        ) and net_if_stats[interface].isup == 1:
            for addr in addrs:
                if addr.family == psutil.AF_LINK:
                    mac = ":".join(a for a in addr.address.split("-"))
                if addr.family == socket.AF_INET:
                    # Ensure the correct ethernet port is selected
                    if addr.address.split(".")[:3] == ["10", "99", "5"]:
                        ip = addr.address
            name = interface

        # Once correct port is found, exit loop and return info
        if name != None and mac != None and ip != None:
            break
    return name, mac, ip


def get_host_info():
    try:
        iface, host_eth_mac, host_eth_ip = (
            get_ethernet_info()
        )  # This machine's ethernet port name, MAC, and IP
        return iface, host_eth_mac, host_eth_ip
    except:
        return [None] * 3
