#!/usr/bin/env python3
"""Github action entry point script."""

from pydantic import BaseSettings
from git import Repo
import os

def list_files(startpath):
    for root, dirs, files in os.walk(startpath):
        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 4 * (level)
        print('{}{}/'.format(indent, os.path.basename(root)))
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            print('{}{}'.format(subindent, f))

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
    DEVICE_EUI: str
    GITHUB_REPOSITORY: str
    GITHUB_TOKEN: str

    class Config:
        env_prefix = "INPUT_"

config = UpdaterConfig()
print(config.__dict__)
list_files('.')
