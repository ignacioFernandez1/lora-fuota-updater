# lora-fuota-updater
Update IoT devices with LoRa

## Usage
### Inputs
* `LORASERVER_IP` - IP of the LoRa server.
* `LORASERVER_URL` - URL  of the LoRa server.
* `LORASERVER_MQTT_PORT` - Port for the MQTT broker of the LoRa server. Default: `1883`
* `LORASERVER_API_PORT` - Port for the LoRa server API. Default: `1883`
* `LORASERVER_API_KEY` - API key for the API.
* `LORASERVER_TENANT_ID` - Tenant ID of the LoRa Server.
* `LORASERVER_DOWNLINK_DR` - Downlink data rate of the LoRa Server. Default: `5`
* `LORASERVER_DOWNLINK_FREQ` -"Downlink frequency of the LoRa Server. Default: `869525000`
* `LORASERVER_APP_ID` - Application ID of the LoRa Server.
* `DEVICE_EUIS` - Application ID of the LoRa Server.

### Example usage
```yaml
name: Update device
on:
  push:
    branches:
      - main
jobs:
  update:
    runs-on: ubuntu-latest
    name: Update device
    steps:
      - name: Check out repository code
        uses: actions/checkout@v3
      - name: LoRa FUOTA Updater
        uses: ignacioFernandez1/lora-fuota-updater@v1.0.0
        with:
          LORASERVER_IP: 127.0.0.1
          LORASERVER_URL: http://127.0.0.1:8080
          LORASERVER_MQTT_PORT: 1883
          LORASERVER_API_PORT: 8090
          LORASERVER_API_KEY: {{ secrets.LORASERVER_API_KEY }}
          LORASERVER_TENANT_ID: a0642b7c1784286f
          LORASERVER_DOWNLINK_DR: 5
          LORASERVER_DOWNLINK_FREQ: 869525000
          LORASERVER_APP_ID: a0642b7c1784286f
          DEVICE_EUIS: '["a0642b7c1784286f","c1712f9a3612430f"]'
```
