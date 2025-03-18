import threading
import time

from pycomm3 import CIPDriver, Services
import tkinter as tk

from constants import *


sem = threading.Semaphore()


def get_interface_counts(
    client_ip: str,
    total_packets_dict: dict,
    exception_occured: dict,
):
    try:
        with CIPDriver(client_ip) as drive:
            drive.generic_message(
                service=CIP_RESET_IFACE_COUNTER_SERVICE,
                class_code=CIP_ETH_LINK_CLASS,
                instance=CIP_ETH_LINK_2_INSTANCE,
                attribute=CIP_IFACE_COUNTER_ATTRIBUTE,
                connected=False,
            )  # Reset all counters
            drive.close()
    except Exception as e:
        print(e)
        exception_occured[client_ip] = True
        return

    time.sleep(5)

    try:
        with CIPDriver(client_ip) as drive:
            interface_counts = drive.generic_message(
                service=Services.get_attribute_single,
                class_code=CIP_ETH_LINK_CLASS,
                instance=CIP_ETH_LINK_2_INSTANCE,
                attribute=CIP_IFACE_COUNTER_ATTRIBUTE,
                connected=False,
            )[1]
            drive.close()

        sem.acquire()
        total_packets_dict[client_ip] = sum(
            int.from_bytes(interface_counts[i : i + 4], byteorder="little")
            for i in range(0, 44, 4)
        )
        sem.release()

        exception_occured[client_ip] = False
    except Exception as e:
        print(e)
        exception_occured[client_ip] = True


def start_counts(total_packets_dict: dict, status_label: tk.Label):
    temp_dict0 = dict()
    temp_dict1 = dict()
    i = 0
    while i < 3:

        if i == 0:
            status_label.config(text="Getting positions of devices...")
        elif i == 1:
            status_label.config(text="Verifying positions...")
        else:
            status_label.config(text="Revising positions...")

        threads: list[threading.Thread] = []
        exception_occured = {
            i: True for i in total_packets_dict.keys()
        }  # Used to track exceptions within threads

        while True in exception_occured.values():
            for ip in total_packets_dict:
                thread = threading.Thread(
                    target=get_interface_counts,
                    args=(ip, total_packets_dict, exception_occured),
                )
                thread.daemon = True
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()

            if True in exception_occured.values():
                print("Exception occured. Retrying...")

        sorted_dict = dict(sorted(total_packets_dict.items(), key=lambda item: item[1]))

        if i == 0:
            temp_dict0 = sorted_dict
        elif i == 1:
            temp_dict1 = sorted_dict
            if list(temp_dict0.keys()) == list(temp_dict1.keys()):
                break

        i += 1

    return sorted_dict
