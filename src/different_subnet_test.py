import os

# from scapy.all import sniff, Raw


# def reset_device(iface):
#     ip_octets: list[str] = []

#     def lldp_packet_handler(p):
#         if p.haslayer(Raw):
#             raw_data = p[Raw].load
#             if raw_data.startswith(b"\x02\x07\x04"):  # LLDP Chassis ID TLV
#                 print("LLDP Packet Captured:")
#                 ip_octets.extend([str(raw_data[32 + i]) for i in range(0, 4)])

#     sniff(
#         iface=iface,
#         prn=lldp_packet_handler,
#         filter="ether proto 0x88cc",
#         count=1,
#         timeout=30,
#         store=0,
#     )
#     return ip_octets


# ip_octets = reset_device("Ethernet 2")
# print(ip_octets)


def change_ip_address(interface_name, new_ip, subnet_mask, gateway):
    command = f'netsh interface ip set address name="{interface_name}" source=static address={new_ip} mask={subnet_mask} gateway={gateway}'
    os.system(command)
    print(f"IP address changed to {new_ip}")


# Example usage
interface_name = "Ethernet 2"  # Replace with your network interface name
new_ip = "10.99.5.251"  # New IP address on the same subnet as the host
subnet_mask = "255.255.255.0"
gateway = "0.0.0.0"

change_ip_address(interface_name, new_ip, subnet_mask, gateway)

# print(f"{os.environ.get("userdomain")}\\{os.getlogin()}")
