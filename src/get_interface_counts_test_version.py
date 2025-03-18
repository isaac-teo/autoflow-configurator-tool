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
        print(f"{e} | {time.time()}")
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
        print(f"{e} | {time.time()}")
        exception_occured[client_ip] = True


def start_threads(
    total_packets_dict: dict,
    status_label: tk.Label,
    error_count: list[int],
    caught_errors: list[int],
):
    temp_dict0 = dict()
    temp_dict1 = dict()
    i = 0
    while i < 3:
        threads = []
        exception_occured = {
            i: True for i in total_packets_dict.keys()
        }  # Used to track exceptions within threads
        print(i)
        while True in exception_occured.values():
            for ip in total_packets_dict:
                thread = threading.Thread(
                    target=get_interface_counts,
                    args=(ip, total_packets_dict, exception_occured, status_label),
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
            else:
                caught_errors[0] += 1

        i += 1

        print(f"{sorted_dict} | {time.time()}")

    print(f"*****{sorted_dict} | {time.time()}*****")
    if list(sorted_dict.keys()) != [
        "10.99.5.5",
        "10.99.5.4",
        "10.99.5.3",
        "10.99.5.2",
        "10.99.5.1",
    ]:
        error_count[0] += 1

    return sorted_dict


status_label = tk.Label()
total_packets_dict = {f"10.99.5.{i}": 0 for i in range(1, 6)}
error_count = [0]
caught_errors = [0]
t = time.time()
iterations = 500
for _ in range(iterations):
    start_threads(total_packets_dict, status_label, error_count, caught_errors)

print(f"\nMissed Errors: {error_count[0]}")
print(f"Total Errors: {caught_errors[0]}")
print(f"Time: {time.time() - t} | Iterations: {iterations}\n")
