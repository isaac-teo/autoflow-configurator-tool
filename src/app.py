from threading import Thread

import tkinter as tk
from tkinter import ttk
from tkinter import simpledialog
from scapy.all import conf

from config_file import create_config, edit_config, read_config
from constants import NETWORK, SPACER, SPACER_SM
from identify_ip import identify_ip
from host_info import get_host_info
from individual_config import individual_config
from set_final_ips import set_final_ips
from set_to_spare_config import set_to_spare_config
from reset_static_devices import reset_static_devices


class App:
    def __init__(self, root: tk.Tk, config_values: dict):
        self.max_box_size = int(config_values["max_box_size"])
        self.box_size = 0
        self.slot = None
        self.box_size = None

        # Build UI
        self.root = root
        self.root.title("AutoFlow Configurator Tool")
        self.root.geometry(
            f"385x245+{root.winfo_screenwidth() // 2 - 385 // 2}+{root.winfo_screenheight() // 2 - 245 // 2}"
        )  # Open window in center of screen

        self.notebook = ttk.Notebook(root)

        # Create frames for each tab
        self.box_config_tab = ttk.Frame(self.notebook)
        self.ind_config_tab = ttk.Frame(self.notebook)
        self.admin_tab = ttk.Frame(self.notebook)
        self.admin_tab.grid_columnconfigure(1, weight=1)
        self.admin_tab.grid_columnconfigure(3, weight=1)

        # Add tabs to the Notebook
        self.notebook.add(self.box_config_tab, text="Box Configuration")
        self.notebook.add(self.ind_config_tab, text="Individual Configuration")
        self.notebook.add(self.admin_tab, text="Admin")
        self.notebook.pack(expand=True, fill="both")

        self.notebook.hide(self.admin_tab)

        # Box selected (1-20)
        self.selected_box1 = tk.IntVar()
        self.selected_box2 = tk.IntVar()

        # Box config tab
        self.boxes_label1 = tk.Label(self.box_config_tab, text="Select Box:")
        self.boxes_label1.grid(row=0, column=1, columnspan=10)

        self.status_label1 = tk.Label(
            self.box_config_tab, text="Click 'Configure' to start."
        )
        self.status_label1.grid(row=6, sticky="nsew", column=1, columnspan=10)

        self.start_button1 = tk.Button(
            self.box_config_tab,
            text="Configure (Size 0)",
            state="disabled",
            command=self.box_configure,
            width=15,
        )
        self.start_button1.grid(pady=10, row=10, column=4, columnspan=4)

        # Individual config tab
        self.boxes_label2 = tk.Label(self.ind_config_tab, text="Select Box:")
        self.boxes_label2.grid(row=0, column=1, columnspan=10)

        self.status_label2 = tk.Label(
            self.ind_config_tab,
            text="Click 'Configure' to start or 'Identify IP' to find IP address.",
        )
        self.status_label2.grid(row=6, sticky="nsew", column=1, columnspan=10)

        self.start_button2 = tk.Button(
            self.ind_config_tab,
            text="Configure (Slot 0)",
            state="disabled",
            command=self.ind_configure,
            width=15,
        )
        self.start_button2.grid(pady=10, row=10, sticky="w", column=3, columnspan=3)

        self.discover_ip_button = tk.Button(
            self.ind_config_tab,
            text="Identify IP",
            command=self.start_discover_ip,
            width=15,
        )
        self.discover_ip_button.grid(
            pady=10, row=10, sticky="e", column=6, columnspan=3
        )

        # Make grid of box options for both tabs
        for j in range(2):
            i = 0
            if j == 0:
                tab = self.box_config_tab
                variable = self.selected_box1
                command = self.select_box_size
            else:
                tab = self.ind_config_tab
                variable = self.selected_box2
                command = self.select_slot

            for r in range(1, 3):
                for c in range(1, 11):
                    rb = tk.Radiobutton(
                        tab,
                        text=chr(ord("A") + i),
                        value=i + 1,
                        variable=variable,
                        indicatoron=0,
                        background="light grey",
                        command=command,
                    )
                    rb.grid(
                        padx=10,
                        pady=10,
                        sticky="nsew",
                        row=r,
                        column=c,
                    )
                    i = i + 1

            rb = tk.Radiobutton(
                tab,
                text="SPARE",
                value=25,
                variable=variable,
                indicatoron=0,
                background="light grey",
                command=command,
            )
            rb.grid(padx=10, pady=10, sticky="nsew", row=3, column=5, columnspan=2)

        # Add hidden button to tabs
        for tab in self.notebook.winfo_children():
            if tab != self.admin_tab:
                self.activate_admin = tk.Button(
                    tab,
                    text="",
                    command=self.allow_admin,
                )

                self.activate_admin.grid(column=10, row=10, columnspan=10, sticky="se")
                self.activate_admin.config(width=1, height=1, borderwidth=0)

        # Admin tab
        vcmd = root.register(self.validate_input)

        self.max_box_size_label = tk.Label(self.admin_tab, text="Max Box Size: ")
        self.max_box_size_label.grid(pady=10, padx=5, column=0, row=1)

        self.max_box_size_textfield = tk.Entry(
            self.admin_tab,
            textvariable=tk.StringVar(value=config_values["max_box_size"]),
            validate="key",
            validatecommand=(vcmd, "%P"),
        )
        self.max_box_size_textfield.grid(pady=10, sticky="w", column=1, row=1)

        self.save_config_button = tk.Button(
            self.admin_tab, text="Save Configuration", command=self.save_config
        )
        self.save_config_button.grid(pady=145, sticky="s", column=1, row=10)

    def select_box_size(self):
        self.box_size = simpledialog.askinteger(
            "Select Box Size",
            f"{SPACER_SM}Please enter box size:{SPACER_SM}",
            maxvalue=self.max_box_size,
            minvalue=1,
        )
        if self.box_size:
            self.start_button1.config(
                state="normal", text=f"Configure (Size {self.box_size})"
            )
        else:
            self.selected_box1.set(0)
            self.start_button1.config(state="disabled", text="Configure (Size 0)")

    def select_slot(self):
        self.slot = simpledialog.askinteger(
            "Select Slot",
            f"{SPACER_SM}Please enter slot:{SPACER_SM}",
            maxvalue=self.max_box_size,
            minvalue=1,
        )
        if self.slot:
            self.start_button2.config(
                state="normal", text=f"Configure (Slot {self.slot})"
            )
        else:
            self.selected_box2.set(0)
            self.start_button2.config(state="disabled", text="Configure (Slot 0)")

    def validate_input(self, P):
        if P.isdigit() or P == "":
            return True
        return False

    def save_config(self):
        max_box_size = self.max_box_size_textfield.get()

        if max_box_size:
            edit_config(max_box_size)
            self.max_box_size = int(max_box_size)

            # Reset state
            self.slot = None
            self.box_size = None

            self.selected_box1.set(0)
            self.start_button1.config(state="disabled", text="Configure (Size 0)")

            self.selected_box2.set(0)
            self.start_button2.config(state="disabled", text="Configure (Slot 0)")

            print(f"Max box size set to {max_box_size}")

    # Helper functions to determine config type
    def box_configure(self):
        self.start_process(is_box=True)

    def ind_configure(self):
        self.start_process(is_box=False)

    # Starts the thread to run the configuration operations
    def start_process(self, is_box: bool):
        conf.iface, host_eth_mac, host_eth_ip = get_host_info()
        if host_eth_mac == None or host_eth_ip == None:
            if is_box:
                self.status_label1.config(
                    text=f"Could not find active Ethernet port. Please try again."
                )
            else:
                self.status_label2.config(
                    text=f"Could not find active Ethernet port. Please try again."
                )
            return

        if is_box:
            self.status_label1.config(text="Starting configuration...")
        else:
            self.status_label2.config(text="Starting configuration...")

        self.thread = Thread(
            target=self.call_functions,
            args=(is_box, conf.iface, host_eth_mac, host_eth_ip),
        )
        self.thread.daemon = True
        self.thread.start()

    # Calls each operation function within the thread
    def call_functions(self, is_box: bool, iface, host_eth_mac: str, host_eth_ip: str):
        num_devices = 0

        # Box config process
        if is_box:
            if self.selected_box1.get() == 25:
                last_device_final_ip_octet = (
                    24 * 10 + self.box_size
                )  # Spare config is always 241-250
            else:
                last_device_final_ip_octet = (
                    # self.selected_box1.get() * self.box_size  # If box IP range depends on size (i.e. size 4,  A: 1-4, B: 5-8, etc.)
                    (self.selected_box1.get() - 1) * 10
                    + self.box_size
                )  # Final IP (last octet only) of last device in chain

            if last_device_final_ip_octet > 250:
                self.status_label1.config(text="Selected configuration exceeds allowed IP range. Lower box size or letter.")
                return

            reset_static_devices(self.status_label1, is_box)

            num_devices = set_to_spare_config(
                iface, host_eth_mac, host_eth_ip, self.status_label1, self.box_size
            )

            if num_devices != self.box_size:
                return

            set_final_ips(last_device_final_ip_octet, self.status_label1, self.box_size)

        # Individual config process
        else:
            final_ip_octet = str((self.selected_box2.get() * 10) - 10 + self.slot)

            status = reset_static_devices(self.status_label2, is_box, final_ip_octet)
            if status is not None:
                return

            individual_config(
                iface,
                host_eth_mac,
                host_eth_ip,
                self.status_label2,
                NETWORK + final_ip_octet,
            )

    def start_discover_ip(self):
        self.status_label2.config(text="Identifying device...")

        conf.iface, host_eth_mac, host_eth_ip = get_host_info()
        if host_eth_mac == None or host_eth_ip == None:
            self.status_label2.config(
                text=f"Could not find active Ethernet port. Please try again."
            )
            return

        self.thread = Thread(
            target=identify_ip,
            args=(conf.iface, self.status_label2),
        )
        self.thread.daemon = True
        self.thread.start()

    def allow_admin(self):
        if self.notebook.tab(self.admin_tab)["state"] == "hidden":
            password = simpledialog.askstring(
                "Enable Admin Access",
                f"{SPACER}Enter password:{SPACER}",
                show="*",
            )
            if password == "wagstaff":
                self.notebook.add(self.admin_tab)
