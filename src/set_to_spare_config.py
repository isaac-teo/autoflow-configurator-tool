# Based on code from https://github.com/ptef/dhcp-scapy-server/blob/master/send-dhcp.py
import time

from pycomm3 import INT, CIPDriver, Services
from scapy.all import BOOTP, DHCP, UDP, Ether, IP, UDP, sendp, sniff, Packet
from eeip import *
import tkinter as tk

from constants import *
from ping import ping_ip


# Sets DHCP devices to the spare configuration
def set_to_spare_config(
    iface,
    host_eth_mac: str,
    host_eth_ip: str,
    status_label: tk.Label,
    box_size: int,
):
    discovered_mac_addrs: list[str] = []
    spare_ip_pool = SPARE_IPS.copy()

    def set_ip(p: Packet):
        if not (p.haslayer(BOOTP) and p.haslayer(DHCP) and p.haslayer(UDP)):
            status_label.config(text="[-] not yet..")
            return

        spare_ip = spare_ip_pool[0]

        readable_mac = ":".join(f"{byte:02x}" for byte in p[BOOTP].chaddr)[:17]

        # Store discovered MAC addresses
        if readable_mac not in discovered_mac_addrs:
            discovered_mac_addrs.append(readable_mac)

        # Ether / IP / UDP / BOOTP / DHCP
        e = Ether(src=host_eth_mac, dst="ff:ff:ff:ff:ff:ff")
        i = IP(src=host_eth_ip, dst=spare_ip)
        u = UDP(sport=67, dport=68)
        b = BOOTP(
            op=2,
            xid=p[BOOTP].xid,
            yiaddr=spare_ip,
            siaddr=host_eth_ip,
            chaddr=p[BOOTP].chaddr,
        )
        d = DHCP(
            options=[
                ("message-type", "offer"),
                ("server_id", host_eth_ip),
                ("lease_time", 9999999),
                ("subnet_mask", "255.255.255.0"),
                ("router", host_eth_ip),
                ("name_server", host_eth_ip),
                "end",
            ]
        )

        # Sends packets to assign new IP from IP pool
        for op in p[DHCP].options:
            if op[0] == "message-type" and op[1] == 1:
                d.options[0] = ("message-type", 2)  # 2=offer
                sendp(e / i / u / b / d, iface=iface)

            elif op[0] == "message-type" and op[1] == 3:
                d.options[0] = ("message-type", 5)  # 5=ack
                sendp(e / i / u / b / d, iface=iface)

                status_label.config(text=f"{spare_ip} assigned to {readable_mac}.")
                spare_ip_pool.pop(0)  # remove assigned IP from pool

    status_label.config(text="Searching for DHCP devices...")

    # Keep searching for new devices until no packets found
    start_time = time.time()
    for _ in range(box_size * 2):
        sniff(filter="udp port 68 and port 67", prn=set_ip, count=1, timeout=30)

        if time.time() - start_time < 30:
            start_time = time.time()
        else:
            break

    if len(discovered_mac_addrs) == 0:
        status_label.config(text="No devices found. Check connections and try again.")
        return 0
    elif len(discovered_mac_addrs) != box_size:
        status_label.config(
            text="Did not find enough devices. Check connections and try again."
        )
        return 0

    # Do not continue until devices are active again
    status_label.config(text="Waiting for connections to be reestablished...")
    start_time = time.time()
    ip_set = False
    while not ip_set:
        for ip in SPARE_IPS[:box_size]:
            if time.time() - start_time > 10:
                status_label.config(
                    text="Could not reestablish connections. Check connections and try again."
                )
                return 0
            ip_set = ping_ip(ip)
            if not ip_set:
                break

    status_label.config(text="Disabling BOOTP/DHCP...")
    for ip in SPARE_IPS[:box_size]:
        try:
            with CIPDriver(ip) as drive:
                drive.generic_message(
                    service=Services.set_attribute_single,
                    class_code=CIP_TCIP_CLASS,
                    instance=CIP_TCIP_INSTANCE,
                    attribute=CIP_ADDR_SOURCE_ATTRIBUTE,
                    request_data=INT.encode(CIP_STORED_VALUE),
                    connected=False,
                )  # Set interface control to static

                drive.close()
        except Exception as e:
            print(f"Error: {e}")
    time.sleep(5)
    return len(discovered_mac_addrs)
