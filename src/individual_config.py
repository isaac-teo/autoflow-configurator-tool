# Based on code from https://github.com/ptef/dhcp-scapy-server/blob/master/send-dhcp.py
import time

from pycomm3 import INT, CIPDriver, Services
from scapy.all import BOOTP, DHCP, UDP, Ether, IP, UDP, sendp, sniff
from eeip import *
import tkinter as tk

from constants import *
from ping import ping_ip


def individual_config(
    iface,
    host_eth_mac: str,
    host_eth_ip: str,
    status_label: tk.Label,
    ip: str,
):
    discovered_mac_addrs: list[str] = []

    def set_ip(p):
        if not (p.haslayer(BOOTP) and p.haslayer(DHCP) and p.haslayer(UDP)):
            status_label.config(text="[-] not yet..")
            return

        readable_mac = ":".join(f"{byte:02x}" for byte in p[BOOTP].chaddr)[:17]

        # Store discovered MAC addresses
        if readable_mac not in discovered_mac_addrs:
            discovered_mac_addrs.append(readable_mac)

        # Ether / IP / UDP / BOOTP / DHCP
        e = Ether(src=host_eth_mac, dst="ff:ff:ff:ff:ff:ff")
        i = IP(src=host_eth_ip, dst=ip)
        u = UDP(sport=67, dport=68)
        b = BOOTP(
            op=2,
            xid=p[BOOTP].xid,
            yiaddr=ip,
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

                status_label.config(text=f"{ip} assigned to {readable_mac}.")

    status_label.config(text="Searching for DHCP devices...")

    for _ in range(2):
        sniff(filter="udp port 68 and port 67", prn=set_ip, count=1, timeout=30)

    if len(discovered_mac_addrs) == 0:
        status_label.config(text="No devices found. Check connections and try again.")
        return
    elif len(discovered_mac_addrs) != 1:
        status_label.config(
            text="Found multiple devices. Disconnect extra devices and try again."
        )
        return

    # Do not continue until device is active again
    status_label.config(text="Waiting for connections to be reestablished...")
    start_time = time.time()
    ip_set = False
    while not ip_set:
        if time.time() - start_time > 10:
            status_label.config(
                text="Could not reestablish connections. Check connections and try again."
            )
            return
        ip_set = ping_ip(ip)
        if not ip_set:
            break

    status_label.config(text="Disabling BOOTP/DHCP...")

    exception = Exception()
    while exception != None:
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
            status_label.config(text="Configuration complete.")
            exception = None
        except Exception as e:
            exception = e
