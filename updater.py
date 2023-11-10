#!/usr/bin/env python3
"""Github action entry point script."""

import os
import paho.mqtt.client as paho
import atexit
import threading
from utils.ota import OTAHandler
from utils.config import UpdaterConfig
from utils.files import move_files
import logging

exit = False
client = None
config = UpdaterConfig()


def sigint_handler(signum, frame):
    logging.info("Terminating Lora OTA updater")
    os._exit(0)
    
def exit_handler():
    logging.info("Terminating Lora OTA updater")

atexit.register(exit_handler)

def on_message(mosq, ota, msg):
    ota.process_rx_msg(msg.payload.decode())

def on_connect(client, userdata, flags, rc):
    if rc==0:
        client.subscribe("application/+/device/+/event/up", 0)
    else:
        logging.info("Bad connection Returned code=",rc) 

def start_lora_ota_updater():
    ota = OTAHandler()

    client = paho.Client(userdata=ota)

    client.on_message = on_message
    client.on_connect = on_connect
    
    client.connect(config.LORASERVER_IP, config.LORASERVER_MQTT_PORT, 60)
    ota.set_mqtt_client(client)

    ota_thread = threading.Thread(target=ota.start)
    ota_thread.start()
    
    logging.info("Lora OTA updater started")
    while client.loop() == 0:
        if ota.exit == True:
            break
        elif ota.failed_exit == True:
            logging.info("Device update did not finish successfully")
            os._exit(1)
        pass
    
    client.disconnect()
    os._exit(0)

if __name__ == '__main__':
    move_files()
    try:
        start_lora_ota_updater()
    except KeyboardInterrupt:
        sigint_handler(None, None)


