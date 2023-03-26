#!/usr/bin/env python3
"""Github action entry point script."""

from pydantic import BaseSettings

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

    class Config:
        env_prefix = "INPUT_"

config = UpdaterConfig()
print(config.__dict__)