import psutil
import time
import os
import platform
import requests
import logging
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

# --- Report settings ---
SERVER_URL = os.getenv("SERVER_URL", config.get("report", "server"))
TOKEN = os.getenv("TOKEN", config.get("report", "token"))
REPORT_INTERVAL = int(os.getenv("REPORT_INTERVAL", config.get("report", "interval"))) - 1  # network needs 1 sec

# --- Device properties ---
DEVICE_NAME = os.getenv("DEVICE_NAME", config.get("device", "display_name"))
DEVICE_ID = os.getenv("DEVICE_ID", config.get("device", "id_name"))
DEVICE_TYPE = os.getenv("DEVICE_TYPE", config.get("device", "type"))
DEVICE_HARDWARE = os.getenv("DEVICE_HARDWARE", config.get("device", "hardware"))
DEVICE_OS = os.getenv("DEVICE_OS", config.get("device", "os"))


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logging.info(f"Current system: {platform.system()}")
logging.info(f"Current token: {TOKEN}")


def bytes_to_mb(bytes_val):
    return bytes_val / 1024 / 1024


def get_system_info():
    # CPU utilization (percentage)
    cpu_usage = psutil.cpu_percent(interval=1)

    # Memory usage
    mem = psutil.virtual_memory()
    mem_total = mem.total / (1024 ** 3)  # convert to GB
    mem_used = mem.used / (1024 ** 3)
    mem_percent = mem.percent

    # Disk usage (root directory)
    disk_data = get_total_disk_usage()
    disk_total = disk_data.get("disk_total", "")
    disk_used = disk_data.get("disk_used", "")
    disk_percent = disk_data.get("disk_percent", "")

    # Network receive and transmit traffic (cumulative bytes)
    # net = psutil.net_io_counters()
    # net_sent = net.bytes_sent / (1024 ** 2)
    # net_recv = net.bytes_recv / (1024 ** 2)

    # battery
    battery = psutil.sensors_battery()

    if battery is None:
        battery_data = {
            "percent": None,
            "plugged": None
        }
    else:
        battery_data = {
            "percent": battery.percent,
            "plugged": battery.power_plugged
        }

    # cpu_percent = f"CPU usage: {cpu_usage}%"
    # memory_percent = f"Memory: {mem_used:.2f}GB / {mem_total:.2f}GB ({mem_percent}%)"
    # disk_percent
    # print(f"Network send: {net_sent:.2f}MB")
    # print(f"Network recv: {net_recv:.2f}MB")
    network_io = get_io_stats()
    return {
        "cpu_percent": cpu_usage,
        "memory_percent": mem_percent,
        "disk_percent": disk_percent,
        "network_recv_speed": network_io.get("recv_speed"),
        "network_send_speed": network_io.get("send_speed"),
        "battery": battery_data
    }


def get_io_stats(interval=1):
    # Initial sampling
    disk1 = psutil.disk_io_counters()
    net1 = psutil.net_io_counters()

    time.sleep(interval)

    # Second sampling
    disk2 = psutil.disk_io_counters()
    net2 = psutil.net_io_counters()

    # Disk IO speed（MB/s）
    # read_speed = bytes_to_mb(disk2.read_bytes - disk1.read_bytes) / interval
    # write_speed = bytes_to_mb(disk2.write_bytes - disk1.write_bytes) / interval

    # Network IO speed（MB/s）
    send_speed = format(bytes_to_mb(net2.bytes_sent - net1.bytes_sent) / interval, ".1f")
    recv_speed = format(bytes_to_mb(net2.bytes_recv - net1.bytes_recv) / interval, ".1f")

    # print(f"disk read: {read_speed:.2f} MB/s")
    # print(f"disk write: {write_speed:.2f} MB/s")
    # print(f"network send: {send_speed} MB/s")
    # print(f"network recv: {recv_speed} MB/s")
    return {
        "send_speed": send_speed,
        "recv_speed": recv_speed
    }


def get_total_disk_usage():
    total = 0
    used = 0

    for p in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(p.mountpoint)
            total += usage.total
            used += usage.used
        except (PermissionError, FileNotFoundError):
            continue  # Ignore unreachable partitions

    if total == 0:
        print("Unable to fetch disk info")
        return

    percent = format(used / total * 100, ".1f")
    disk_total = format (total / (1024 ** 3), ".1f")  # GB
    disk_used = format(used / (1024 ** 3), ".1f")  # GB

    disk_data = {
        "disk_total": disk_total,
        "disk_used": disk_used,
        "disk_percent": percent
    }

    return disk_data


while True:
    system_status = get_system_info()

    report_data = {
        "token": TOKEN,
        "device": {
            "name": DEVICE_NAME,
            "id": DEVICE_ID,
            "type": DEVICE_TYPE,
            "hardware": DEVICE_HARDWARE,
            "os": DEVICE_OS,
            "force_update": False # device properties won't be updated repeatedly
        },
        "status": {
            "cpu_percent": system_status.get("cpu_percent"),
            "memory_percent": system_status.get("memory_percent"),
            "disk_percent": system_status.get("disk_percent"),
            "network_recv_speed": system_status.get("network_recv_speed"),
            "network_send_speed": system_status.get("network_send_speed"),
            "battery": system_status.get("battery")
        },
        "timestamp": time.time()
    }

    resp = requests.post(f"{SERVER_URL}/api/report", json=report_data)
    resp_json = resp.json()
    if resp.ok:
        if resp_json["success"]:
            logging.info(f"Reported current device status")
        else:
            logging.error(f"Failed reporting to the server")
    else:
        print("Status Code:", resp.status_code)
        print("Response Text:", resp.text)

    time.sleep(REPORT_INTERVAL)