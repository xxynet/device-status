import os
import time
import requests
import json
import subprocess
import logging
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

SERVER_URL = os.getenv("SERVER_URL", config.get("report", "server"))
TOKEN = os.getenv("TOKEN", config.get("report", "token"))
REPORT_INTERVAL = int(os.getenv("REPORT_INTERVAL", config.get("report", "interval")))

DEVICE_NAME = os.getenv("DEVICE_NAME", config.get("device", "display_name"))
DEVICE_ID = os.getenv("DEVICE_ID", config.get("device", "id_name"))
DEVICE_TYPE = os.getenv("DEVICE_TYPE", config.get("device", "type"))
DEVICE_HARDWARE = os.getenv("DEVICE_HARDWARE", config.get("device", "hardware"))
DEVICE_OS = os.getenv("DEVICE_OS", config.get("device", "os"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def get_battery():
    try:
        result = subprocess.check_output(['termux-battery-status'])
        data = json.loads(result)
        return {
            "percent": data["percentage"],
            "plugged": data["plugged"] == "PLUGGED_AC" or data["plugged"] == "PLUGGED_USB"
        }
    except:
        return {"percent": None, "plugged": None}

def get_memory_percent():
    return None

def get_cpu_usage():
    return None

def get_status():
    return {
        "cpu_percent": get_cpu_usage(),
        "memory_percent": get_memory_percent(),
        "disk_percent": get_memory_percent(),
        "network_recv_speed": None,
        "network_send_speed": None,
        "battery": get_battery()
    }

while True:
    system_status = get_status()

    report_data = {
        "token": TOKEN,
        "device": {
            "name": DEVICE_NAME,
            "id": DEVICE_ID,
            "type": DEVICE_TYPE,
            "hardware": DEVICE_HARDWARE,
            "os": DEVICE_OS,
            "force_update": False
        },
        "status": system_status,
        "timestamp": time.time()
    }

    try:
        resp = requests.post(f"{SERVER_URL}/api/report", json=report_data)
        if resp.ok:
            resp_json = resp.json()
            if resp_json.get("success"):
                logging.info("Reported current device status")
            else:
                logging.error("Failed reporting to the server")
        else:
            print("Status Code:", resp.status_code)
            print("Response Text:", resp.text)
    except Exception as e:
        logging.error(f"Error reporting: {e}")

    time.sleep(REPORT_INTERVAL)