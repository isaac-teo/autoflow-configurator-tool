import tkinter as tk
from eeip import *
from pycomm3 import CIPDriver, Services

from constants import *
from get_interface_counts import start_counts


def set_final_ips(
    last_device_final_ip_octet: int, status_label: tk.Label, box_size: int
):
    client_ips_dict = {
        i: 0 for i in SPARE_IPS[:box_size]
    }  # Current IPs of all the devices

    status_label.config(text="Assigning final IPs...")
    total_packets_dict = start_counts(client_ips_dict, status_label)

    i = 0
    for client_ip in total_packets_dict:
        final_ip = NETWORK + str(last_device_final_ip_octet - i)
        i += 1

        data = bytes([int(final_ip.split(".")[3])]) + CIP_IP_VALUE
        try:
            with CIPDriver(client_ip) as drive:
                drive.generic_message(
                    service=Services.set_attribute_single,
                    class_code=CIP_TCIP_CLASS,
                    instance=CIP_TCIP_INSTANCE,
                    attribute=CIP_IP_ATTRIBUTE,
                    request_data=data,
                    connected=False,
                )  # Set final IP address

                drive.close()
        except Exception as e:
            print(f"Error: {e}")

        status_label.config(text=f"Device {client_ip} set to {final_ip}.")
        print(f"Device {client_ip} set to {final_ip}.")

    status_label.config(text="Configuration complete.")
