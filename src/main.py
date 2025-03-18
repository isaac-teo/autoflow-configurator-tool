import tkinter as tk

from config_file import create_config, read_config
from app import App


if __name__ == "__main__":
    # Get config_values, or create config.ini with defaults if doesn't exist
    try:
        config_values = read_config()
    except ValueError:
        create_config()
        config_values = read_config()

    root = tk.Tk()
    root.resizable(0, 0)
    App(root, config_values)
    root.mainloop()
