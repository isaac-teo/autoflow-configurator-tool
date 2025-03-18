from scapy.all import sniff, Raw, Packet
import tkinter as tk

from constants import NETWORK
from ping import start_pings


def identify_ip(iface, status_label: tk.Label):
    ip_octets: list[str] = []
    ip_addresses = [f"{NETWORK}{i}" for i in range(1, 251)]
    active_ips: list[str] = []

    def lldp_packet_handler(p: Packet):
        if p.haslayer(Raw):
            raw_data = p[Raw].load
            if raw_data.startswith(b"\x02\x07\x04"):  # LLDP Chassis ID TLV
                ip_octets.extend([str(raw_data[32 + i]) for i in range(0, 4)])

    # Ping IP addresses in the network
    start_pings(ip_addresses, active_ips)

    if len(active_ips) > 1:
        status_label.config(
            text="Found multiple devices. Disconnect extra devices and try again."
        )
        return

    elif len(active_ips) > 0:
        status_label.config(text=f"Identified IP: {active_ips[0]}")
        return active_ips[0].split(".")

    sniff(
        iface=iface,
        prn=lldp_packet_handler,
        filter="ether proto 0x88cc",
        count=1,
        timeout=30,
        store=0,
    )

    if ip_octets == []:
        status_label.config(text=f"No IP found.")
    else:
        status_label.config(text=f"Identified IP: {".".join(ip_octets)}")
    return ip_octets
