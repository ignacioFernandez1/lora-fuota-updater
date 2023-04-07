#!/usr/bin/env python3
"""Github action entry point script."""

from pydantic import BaseSettings, validator
from typing import List
import os
import shutil

PREV_VERSION_DIR = 'prev_version'
NEW_VERSION_DIR = 'new_version'

def move_files():
    new_dir = PREV_VERSION_DIR
    os.makedirs(new_dir, exist_ok=True)  # create the new directory if it doesn't already exist

    for item in os.listdir('.'):
        print(item)
        if os.path.isfile(item):  # check if the item is a file
            shutil.move(item, os.path.join(new_dir, item))  # move the file to the new directory
        elif os.path.isdir(item) and item != new_dir:  # check if the item is a directory
            shutil.move(item, os.path.join(new_dir, item))  # move the directory to the new directory
    shutil.copytree(new_dir, NEW_VERSION_DIR)  
    # git reset --hard HEAD~1 in PREV_VERSION_DIR
    os.chdir(PREV_VERSION_DIR)
    os.system('git reset --hard HEAD~1')
    print('PREV', os.listdir('.'))
    os.chdir('../' + NEW_VERSION_DIR)
    print('NEW', os.listdir('.'))

class UpdaterConfig(BaseSettings):
    """Updater configuration parameters"""

    LORASERVER_IP: str
    LORASERVER_URL: str
    LORASERVER_MQTT_PORT: int = 1883
    LORASERVER_API_PORT: int = 8090
    LORASERVER_API_KEY: str
    LORASERVER_TENANT_ID: str
    LORASERVER_DOWNLINK_DR: int = 5
    LORASERVER_DOWNLINK_FREQ: int = 869525000
    LORASERVER_APP_ID: str
    DEVICE_EUIS: List[str]

    class Config:
        env_prefix = "INPUT_"

config = UpdaterConfig()
print(config.__dict__)
move_files()


