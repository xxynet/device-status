from flask import Flask, render_template, request, jsonify, send_file
import sqlite3
import configparser
import random
import os

config = configparser.ConfigParser()
config.read('config.ini')

SERVER_HOST = config.get("server", "host")
SERVER_PORT = config.get("server", "port")

TITLE = config.get("frontend", "title")
THEME = config.get("frontend", "theme")
BACKGROUND_URL = config.get("frontend", "background_url")
REFRESH_INTERVAL = int(config.get("frontend", "refresh_interval"))*1000
OFFLINE_INTERVAL = int(config.get("frontend", "offline_interval"))
TOKEN = config.get("server", "token")
DB_PATH = 'devices.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS device (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT UNIQUE,
            name TEXT,
            type TEXT,
            hardware TEXT,
            os TEXT,
            created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS device_status (
            device_id TEXT PRIMARY KEY,
            cpu_percent REAL,
            memory_percent REAL,
            disk_percent REAL,
            network_recv_speed REAL,
            network_send_speed REAL,
            timestamp REAL,
            battery_percent REAL,
            battery_plugged BOOLEAN,
            FOREIGN KEY(device_id) REFERENCES device(device_id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

app = Flask(__name__, template_folder=f'theme/{THEME}', static_folder=f'theme/{THEME}/static')


@app.route('/')
def home():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Get all devices
    c.execute('SELECT device_id, name, type, hardware, os FROM device')
    devices = []
    for row in c.fetchall():
        device_id, name, device_type, hardware, os = row
        # Get the latest status of the device
        c.execute('''
            SELECT cpu_percent, memory_percent, disk_percent, network_recv_speed, network_send_speed, timestamp, battery_percent, battery_plugged
            FROM device_status WHERE device_id=? ORDER BY timestamp DESC LIMIT 1
        ''', (device_id,))
        status_row = c.fetchone()
        if status_row:
            cpu_percent, memory_percent, disk_percent, network_recv_speed, network_send_speed, timestamp, battery_percent, battery_plugged = status_row
        else:
            cpu_percent = memory_percent = disk_percent = network_recv_speed = network_send_speed = timestamp = battery_percent = battery_plugged = None
        devices.append({
            'device_id': device_id,
            'name': name,
            'device_type': device_type,
            'hardware': hardware,
            'os': os,
            'cpu_percent': cpu_percent,
            'memory_percent': memory_percent,
            'disk_percent': disk_percent,
            'network_recv_speed': network_recv_speed,
            'network_send_speed': network_send_speed,
            "timestamp": timestamp,
            "battery_percent": battery_percent,
            "battery_plugged": battery_plugged
        })
    conn.close()
    return render_template('index.html', title=TITLE, background_url=BACKGROUND_URL, refresh_interval=REFRESH_INTERVAL, offline_interval=OFFLINE_INTERVAL, devices=devices)


@app.route('/api/report', methods=['POST'])
def recv_status():
    report_data = request.get_json()
    if TOKEN == report_data.get("token"):
        device = report_data.get("device", {})
        status = report_data.get("status", {})
        device_id = device.get("id")
        force_update = device.get("force_update", False)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        # Only update device information when force_update is True, otherwise only insert (if it does not exist)
        if force_update:
            c.execute('''
                INSERT INTO device (device_id, name, type, hardware, os)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(device_id) DO UPDATE SET
                    name=excluded.name,
                    type=excluded.type,
                    hardware=excluded.hardware,
                    os=excluded.os
            ''', (
                device_id,
                device.get("name"),
                device.get("type"),
                device.get("hardware"),
                device.get("os")
            ))
        else:
            c.execute('''
                INSERT OR IGNORE INTO device (device_id, name, type, hardware, os)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                device_id,
                device.get("name"),
                device.get("type"),
                device.get("hardware"),
                device.get("os")
            ))
        # Only keep the latest status
        c.execute('''
            INSERT INTO device_status (
                device_id, cpu_percent, memory_percent, disk_percent, network_recv_speed, network_send_speed, timestamp, battery_percent, battery_plugged
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(device_id) DO UPDATE SET
                cpu_percent=excluded.cpu_percent,
                memory_percent=excluded.memory_percent,
                disk_percent=excluded.disk_percent,
                network_recv_speed=excluded.network_recv_speed,
                network_send_speed=excluded.network_send_speed,
                timestamp=excluded.timestamp,
                battery_percent=excluded.battery_percent,
                battery_plugged=excluded.battery_plugged
        ''', (
            device_id,
            status.get("cpu_percent"),
            status.get("memory_percent"),
            status.get("disk_percent"),
            status.get("network_recv_speed"),
            status.get("network_send_speed"),
            report_data.get("timestamp"),
            status.get("battery").get("percent"),
            status.get("battery").get("plugged")
        ))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Invalid token"}), 403


@app.route('/api/devices', methods=['GET'])
def api_devices():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT device_id, name, type, hardware, os FROM device')
    devices = []
    for row in c.fetchall():
        device_id, name, device_type, hardware, os = row
        c.execute('''
            SELECT cpu_percent, memory_percent, disk_percent, network_recv_speed, network_send_speed, timestamp, battery_percent, battery_plugged
            FROM device_status WHERE device_id=? LIMIT 1
        ''', (device_id,))
        status_row = c.fetchone()
        if status_row:
            cpu_percent, memory_percent, disk_percent, network_recv_speed, network_send_speed, timestamp, battery_percent, battery_plugged = status_row
        else:
            cpu_percent = memory_percent = disk_percent = network_recv_speed = network_send_speed = timestamp = battery_percent = battery_plugged = None
        devices.append({
            'device_id': device_id,
            'name': name,
            'device_type': device_type,
            'hardware': hardware,
            'os': os,
            'cpu_percent': cpu_percent,
            'memory_percent': memory_percent,
            'disk_percent': disk_percent,
            'network_recv_speed': network_recv_speed,
            'network_send_speed': network_send_speed,
            "timestamp": timestamp,
            "battery_percent": battery_percent,
            "battery_plugged": battery_plugged
        })
    conn.close()
    return jsonify({'devices': devices})


@app.route('/pic')
def background_pic():
    folder = f'theme/{THEME}/static/bg'
    files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
    if not files:
        return "No images found", 404

    selected_file = random.choice(files)
    full_path = os.path.join(folder, selected_file)

    return send_file(full_path, mimetype='image/jpeg')


if __name__ == '__main__':
    app.run(host=SERVER_HOST, port=SERVER_PORT)