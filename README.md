# Device Status

An elegant web page that displays your devices' status

## 📷 ScreenShots

![](./Screenshots/Screenshot01.png)

![](./Screenshots/Screenshot02.png)

![](./Screenshots/Screenshot03.png)

## 🚀 Features

- [x] support for displaying CPU, memory, disk, and network usage
- [x] Support for displaying device battery, whether it is charging, and online status
- [x] Customizable background image, refresh_interval, offline_interval

## 🔨 Usage

First install requirements
```
pip install -r requirements.txt
```

Modify the configuration files for the server and client. ( `server/config.ini` `client/config.ini`)

Run `server/server.py` on your server

Configure `client/config.ini` & run `client/client.py` on your clients respectively