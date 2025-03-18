import threading
import subprocess


def ping_ip(ip: str, active_ips: list[str] | None = None):
    try:
        output = subprocess.check_output(f"ping -n 1 -w 1 {ip}", shell=True)
        if "TTL=" in output.decode("utf-8"):
            if active_ips is not None and ip not in active_ips:
                active_ips.append(ip)
            return True
    except:
        return False


def start_pings(ip_addresses: list[str], active_ips: list[str]):
    threads: list[threading.Thread] = []
    for _ in range(2):
        for ip in ip_addresses:
            thread = threading.Thread(target=ping_ip, args=(ip, active_ips))
            thread.daemon = True
            threads.append(thread)
            thread.start()

    for thread in threads:
        thread.join()
