import configparser
import os

import pyAesCrypt


PASSWORD = "wagstaff"


def create_config():
    config = configparser.ConfigParser()

    # Default max box size is 10
    config["General"] = {"max_box_size": 10}

    with open("temp.txt", "w") as configfile:
        config.write(configfile)

    pyAesCrypt.encryptFile("temp.txt", "config.ini", PASSWORD)

    os.remove("temp.txt")


def read_config():
    pyAesCrypt.decryptFile("config.ini", "temp.txt", PASSWORD)

    config = configparser.ConfigParser()
    config.read("temp.txt")

    max_box_size = config.get("General", "max_box_size")
    config_values = {"max_box_size": max_box_size}

    pyAesCrypt.encryptFile("temp.txt", "config.ini", PASSWORD)

    os.remove("temp.txt")

    return config_values


def edit_config(max_box_size: str | None = None):
    pyAesCrypt.decryptFile("config.ini", "temp.txt", PASSWORD)

    config = configparser.ConfigParser()
    config["General"] = read_config()

    if max_box_size != None:
        config["General"]["max_box_size"] = max_box_size

    with open("temp.txt", "w") as configfile:
        config.write(configfile)

    pyAesCrypt.encryptFile("temp.txt", "config.ini", PASSWORD)

    os.remove("temp.txt")
