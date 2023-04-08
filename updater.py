#!/usr/bin/env python3
"""Github action entry point script."""

from pydantic import BaseSettings, validator
from typing import List
import os
import shutil

PREV_VERSION_DIR = 'prev_version'
NEW_VERSION_DIR = 'new_version'
FIRMWARE_DIR = 'firmware'
VERSION_FILE = 'version.py'

def get_version():
    with open(VERSION_FILE) as f:
        return f.read()

def list_files(startpath):
    for root, dirs, files in os.walk(startpath):
        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 4 * (level)
        print('{}{}/'.format(indent, os.path.basename(root)))
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            print('{}{}'.format(subindent, f))

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

    os.makedirs(FIRMWARE_DIR, exist_ok=True)
    os.chdir(PREV_VERSION_DIR)
    # import ipdb; ipdb.set_trace()
    os.system('git reset --hard HEAD~1')
    os.chdir('./src')
    dev_version = get_version()
    os.chdir('..')
    os.system(f'mkdir ../{FIRMWARE_DIR}/{dev_version} && mv ./src/* ../{FIRMWARE_DIR}/{dev_version} && rm -rf src')
    os.chdir('../' + NEW_VERSION_DIR)
    os.chdir('./src')
    dev_version = get_version()
    os.chdir('..')
    os.system(f'mkdir ../{FIRMWARE_DIR}/{dev_version} && mv ./src/* ../{FIRMWARE_DIR}/{dev_version} && rm -rf src')

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


