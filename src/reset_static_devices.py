import tkinter as tk
from eeip import *
from pycomm3 import INT, CIPDriver, Services

from constants import *
from ping import start_pings


def reset_static_devices(
    status_label: tk.Label, is_box: bool, final_ip_octet: str | None = None
):
    status_label.config(text="Searching for active IPs...")
    ip_addresses = [f"{NETWORK}{i}" for i in range(1, 251)]
    active_ips: list[str] = []

    # Ping IP addresses in the network to find static IP addresses
    start_pings(ip_addresses, active_ips)
    status_label.config(text=f"Active IP(s): {", ".join(ip for ip in active_ips)}")
    print(f"Active IP(s): {", ".join(ip for ip in active_ips)}")

    if len(active_ips) == 0:
        status_label.config(text="No active IP(s) found.")
        if is_box:
            return 0

    #  Individual config
    if not is_box:
        if len(active_ips) > 1:
            status_label.config(
                text="Found too many IPs. Disconnect extra devices and try again."
            )
            return 0
        else:
            data = (
                bytes([int(f"{NETWORK}{final_ip_octet}".split(".")[3])]) + CIP_IP_VALUE
            )

            with CIPDriver(active_ips[0]) as drive:
                drive.generic_message(
                    service=Services.set_attribute_single,
                    class_code=CIP_TCIP_CLASS,
                    instance=CIP_TCIP_INSTANCE,
                    attribute=CIP_IP_ATTRIBUTE,
                    request_data=data,
                    connected=False,
                )  # Set final IP address

                drive.close()

            status_label.config(text="Configuration complete.")
            print(f"Device {active_ips[0]} set to {NETWORK}{final_ip_octet}.")
            return 1
    else:
        status_label.config(text="Resettings active IP(s) to DHCP...")
        for active_ip in active_ips:
            try:
                with CIPDriver(active_ip) as drive:
                    config_ctrl = drive.generic_message(
                        service=Services.get_attribute_single,
                        class_code=CIP_TCIP_CLASS,
                        instance=CIP_TCIP_INSTANCE,
                        attribute=CIP_ADDR_SOURCE_ATTRIBUTE,
                        data_type=INT,
                        connected=False,
                    )[1]
                    drive.close()

                # If a device has an IP but is still in DHCP mode, set to static mode
                if config_ctrl == CIP_DHCP_VALUE:
                    with CIPDriver(active_ip) as drive:
                        drive.generic_message(
                            service=Services.set_attribute_single,
                            class_code=CIP_TCIP_CLASS,
                            instance=CIP_TCIP_INSTANCE,
                            attribute=CIP_ADDR_SOURCE_ATTRIBUTE,
                            request_data=INT.encode(CIP_STORED_VALUE),
                            connected=False,
                        )

                        drive.close()
            except Exception as e:
                print(e)

            try:
                with CIPDriver(active_ip) as drive:
                    drive.generic_message(
                        service=Services.set_attribute_single,
                        class_code=CIP_TCIP_CLASS,
                        instance=CIP_TCIP_INSTANCE,
                        attribute=CIP_ADDR_SOURCE_ATTRIBUTE,
                        request_data=INT.encode(CIP_DHCP_VALUE),
                        connected=False,
                    )  # Set active IPs to DHCP

                    drive.close()
            except Exception as e:
                print(f"Error: {e}")

            status_label.config(text=f"Reset device with IP: {active_ip} to DHCP.")

        if is_box:
            status_label.config(text="All devices reset.")
