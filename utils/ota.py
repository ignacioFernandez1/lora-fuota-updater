#!/usr/bin/env python
#
# Copyright (c) 2020, Pycom Limited.
#
# This software is licensed under the GNU GPL version 3 or any
# later version, with permitted additional terms. For more information
# see the Pycom Licence v1.0 document supplied with this file, or
# available at https://www.pycom.io/opensource/licensing
#
# This code has been modified by Franco Lopez and Ignacio Fernandez on 03/2023.
# The following code has been altered in order to fullfill our requirements.
# The original code can be found at https://github.com/pycom/pycom-libraries/tree/master/examples/OTA-lorawan

# DISCLAIMER: This code is provided "as is" and without warranty of any kind, express or
# implied, including, but not limited to, the implied warranties of merchantability and
# fitness for a particular purpose. In no event shall the copyright holder or contributors
# be liable for any direct, indirect, incidental, special, exemplary, or consequential
# damages (including, but not limited to, procurement of substitute goods or services;
# loss of use, data, or profits; or business interruption) however caused and on any theory
# of liability, whether in contract, strict liability, or tort (including negligence or
# otherwise) arising in any way out of the use of this software, even if advised of the
# possibility of such damage.

from distutils.version import LooseVersion
from .LoraServer import LoraServerClient
from .groupUpdater import updateHandler
import threading
import json
import base64
import os
import time
from datetime import datetime
from .config import UpdaterConfig
import logging

config = UpdaterConfig()

class OTAHandler:

    MSG_HEADER = b'$OTA'
    MSG_TAIL = b'*'
    MSG_END = b'<!EOF>'

    DEVICE_VERSION_MSG = 0

    UPDATE_INFO_MSG = 1
    UPDATE_INFO_REPLY = 2

    MULTICAST_KEY_MSG = 3
    LISTENING_MSG = 4

    UPDATE_TYPE_FNAME = 5
    UPDATE_TYPE_PATCH = 6
    UPDATE_TYPE_CHECKSUM = 7
    DELETE_FILE_MSG = 8
    MANIFEST_MSG = 9

    def __init__(self):
        self.exit = False
        self.failed_exit = False
        self.update_finished = False
        self.p_client = None
        self._latest_version = '0.0.0'
        self.firmware_dir = '../firmware'

        # mcId, mcAddr, mcNwkSKey, mcAppSKey
        self._multicast_keys = list()

        self._clientApp = LoraServerClient()
        self._loraserver_api_key = config.LORASERVER_API_KEY
        self._loraserver_tenant_id = config.LORASERVER_TENANT_ID
        self._loraserver_app_id = config.LORASERVER_APP_ID

        self._downlink_datarate = config.LORASERVER_DOWNLINK_DR
        self._downlink_freq = config.LORASERVER_DOWNLINK_FREQ

        self._devices_eui_list = config.DEVICE_EUI
        if len(self._devices_eui_list) == 0:
            logging.info("No devices EUI found")
            exit(1)
        self._devices_dict = dict()
        self._devices_current_version = None
        self._devices_failed_update = list()
        
        watchdog_thread = threading.Thread(target=self._watchdog_timer, args=(300,))
        self._stop_whatchdog = threading.Event()
        self._devices_dict_lock = threading.Lock()
        self._devices_list_lock = threading.Lock()
        self.watchdog_reset = True
        watchdog_thread.start()

    def _check_version(self):
        latest = '0.0.0'
        for d in os.listdir(self.firmware_dir):
            if os.path.isfile(d):
                continue
            if LooseVersion(latest) < LooseVersion(d):
                latest = d
        return latest

    def start(self):
        self._latest_version = self._check_version()
        logging.info(f"Latest version Available: {self._latest_version}")
        logging.info("sending update info to devices...")
        for device_eui in self._devices_eui_list:
            with self._devices_dict_lock:
                self._devices_dict[device_eui] = {
                    'update_info_reply': False,
                    'version': None, 
                    'listening': False, 
                    'update_finished': False, 
                }
        self.watchdog_reset = False
        all_received = False
        while not all_received:
            all_received = True
            for device_eui in self._devices_eui_list:
                if self._devices_dict[device_eui]['update_info_reply'] == False:
                    all_received = False
                    self._send_update_info(device_eui)
                    time.sleep(8)
        return

    def stop(self):
        self.stop_thread()
        self.exit = True
        
    def failed_update(self):
        self.stop_thread()
        self.failed_exit = True

    def set_mqtt_client(self, client):
        self.p_client = client

    def _init_update_params(self):
        try:
            logging.info("Creating multicast group...")
            group_name = self._devices_current_version.strip() + '-' + self._latest_version.strip()
            # (multicast_id, mcAddr, mcNwkSKey, mcAppSKey)
            self._multicast_keys = self._clientApp.create_multicast_group(self._downlink_datarate, self._downlink_freq, group_name,
                                                                        self._loraserver_api_key, self._loraserver_app_id)
            for device_eui in self._devices_eui_list:
                logging.info(f"Adding device {device_eui} to multicast group...")
                self._clientApp.add_device_multicast_group(device_eui, self._multicast_keys[0], self._loraserver_api_key)
                logging.info(f"Device {device_eui} added to multicast group successfully!")
        except Exception as e:
            logging.info(f"Error creating update parameters: {e}")
            self.failed_update()

    def _check_version(self):
        latest = '0.0.0'
        for d in os.listdir(self.firmware_dir):
            if os.path.isfile(d):
                continue
            if latest is None or LooseVersion(latest) < LooseVersion(d):
                latest = d
        return latest

    def is_empty_multicast_queue(self, jwt, multicast_group_id):
        queue_length = self._clientApp.multicast_queue_length(jwt, multicast_group_id)
        if queue_length > 0:
            return False
        else:
            return True

    def delete_multicast_group(self):
        try:
            logging.info("deleting multicast group...")
            self._clientApp.delete_multicast_group(self._multicast_keys[0], self._loraserver_api_key)
        except Exception as e:
            logging.info(f"Error deleting multicast group: {e}")
            self.failed_update()


    def _create_update_info_msg(self):
        # $OTA,1,1.17.1,1674930013,*
        msg = bytearray()
        msg.extend(self.MSG_HEADER)
        msg.extend(b',' + str(self.UPDATE_INFO_MSG).encode())
        msg.extend(b',' + self._latest_version.encode())
        msg.extend(b',' + str(int(time.time())).encode())
        msg.extend(b',' + self.MSG_TAIL)
        return msg

    def send_payload(self, dev_eui, data):
        b64Data = base64.b64encode(data)
        payload = '{"devEui": "' + dev_eui + '","fPort":1,"data": "' + b64Data.decode() + '"}'
        topic = "application/" + self._loraserver_app_id  + "/device/" + dev_eui + "/command/down"
        self.p_client.publish(topic=topic, payload=payload)


    def _send_update_info(self, dev_eui):
        msg = self._create_update_info_msg()
        self.send_payload(dev_eui, msg)
        
    def _send_multicast_keys(self, dev_eui):
        # $OTA,3,mcAddr,mcNwkSKey,mcAppSKey,*
        msg = bytearray()
        msg.extend(self.MSG_HEADER)
        msg.extend(b',' + str(self.MULTICAST_KEY_MSG).encode())

        msg.extend(b',' + self._multicast_keys[1])
        msg.extend(b',' + self._multicast_keys[2])
        msg.extend(b',' + self._multicast_keys[3])

        msg.extend(b',' + self.MSG_TAIL)
        self.send_payload(dev_eui, msg)

    def get_msg_type(self, msg):
        msg_type = -1

        try:
            msg_type = int(msg.split(",")[1])
        except Exception as ex:
            logging.info("Exception getting message type")

        return msg_type

    def decode_device_msg(self, payload):
        dev_msg = None
        try:
            rx_pkt = json.loads(payload)
            dev_msg = base64.b64decode(rx_pkt["data"])
        except Exception as ex:
            logging.info("Exception decoding device message")
        return dev_msg
    
    def get_device_eui(self, payload):
        dev_eui = None
        try:
            dev_eui = json.loads(payload)["deviceInfo"]["devEui"]
        except Exception as ex:
            logging.info("Exception extracting device eui")

        return dev_eui

    def _process_update_info_reply(self, dev_eui, msg):
        # $OTA,2,1.17.0,*
        if dev_eui not in self._devices_eui_list or self._devices_current_version != None:
            return
        token_msg = msg.split(",")
        with self._devices_dict_lock:
            self._devices_dict[dev_eui]['version'] = token_msg[2]
            self._devices_dict[dev_eui]['update_info_reply'] = True
        logging.info(f"Device {dev_eui} version: {token_msg[2]}")

        # if device version is the same as latest version then no update and communications end
        if LooseVersion(token_msg[2]) == LooseVersion(self._latest_version):
            logging.info(f"Device {dev_eui} is up to date to latest version.")
            with self._devices_list_lock:
                self._devices_eui_list.remove(dev_eui)
            with self._devices_dict_lock:
                self._devices_dict.pop(dev_eui)
            if len(self._devices_eui_list) == 0:
                self.stop()
                return


        for device in self._devices_dict:
            if not self._devices_dict[device]['update_info_reply']:
                return

        # check if all devices to update have the same version
        devices_versions = {device: self._devices_dict.get(device, {}).get('version') for device in self._devices_dict}
        if len(set(devices_versions.values())) > 1:
            logging.info(f"Devices have different versions: {devices_versions}")
            self.failed_update()
            return
            
        self._devices_current_version = token_msg[2]
        time.sleep(5)
        multi_thread = threading.Thread(target=self._start_multicast_group)
        multi_thread.start()
        self.watchdog_reset = False
        return

    def _process_device_version(self, dev_eui, msg):
        token_msg = msg.split(",")
        if token_msg[2] != self._latest_version:
            self._devices_failed_update.append(dev_eui)

        with self._devices_dict_lock:
            self._devices_dict[dev_eui]['update_finished'] = True
        
        for device in self._devices_dict:
            if self._devices_dict[device]['update_finished'] == False:
                return
        
        if len(self._devices_failed_update) == 0:
            logging.info(f"Devices updated succesfully to latest version: {self._latest_version}")
            self.stop()
            return
        elif len(self._devices_failed_update) == len(self._devices_eui_list):
            logging.info(f"All devices failed to update to latest version: {self._latest_version}")
            self.failed_update()
            return
        else:
            logging.info(f"The following devices failed to update to latest version: {self._devices_failed_update}")
            self.failed_update()
            return               

    def update_process(self):
        logging.info("Devices are ready, starting update process...")
        update_handler = updateHandler(self._devices_current_version, self._latest_version, self._clientApp, self._loraserver_api_key, self._multicast_keys[0], self)
        update_handler.start()
        self.update_finished = True
        self.watchdog_reset = False
        
    def _start_multicast_group(self):
        self._init_update_params()
        logging.info("Sending multicast keys to devices...")
        self.watchdog_reset = False
        for dev_eui in self._devices_eui_list:
            self._send_multicast_keys(dev_eui)
            time.sleep(10)
        for dev_eui in self._devices_eui_list:
            if self._devices_dict[dev_eui]['listening'] == False:
                self._send_multicast_keys(dev_eui)
                time.sleep(10)
        
    def _watchdog_timer(self, timeout_seconds):
        start_time = time.time()
        while not self._stop_whatchdog.is_set():
            if time.time() - start_time < timeout_seconds:
                if self.watchdog_reset:
                    # Reset the watchdog timer
                    start_time = time.time()
                time.sleep(0.5)
            else:
                logging.info("Watchdog timer expired")
                # If the loop finishes without the watchdog being reset, raise an exception
                self.failed_exit = True
                exit()

    def stop_thread(self):
        self._stop_whatchdog.set()
        
    def process_rx_msg(self, payload):
        # self.watchdog_reset = True
        dev_eui = self.get_device_eui(payload)
        dev_msg = self.decode_device_msg(payload)

        if self.MSG_HEADER in dev_msg:
            msg_type = self.get_msg_type(dev_msg.decode())
            
            if msg_type == self.UPDATE_INFO_REPLY:
                self._process_update_info_reply(dev_eui, dev_msg.decode())
            elif msg_type == self.LISTENING_MSG:
                with self._devices_dict_lock:
                    self._devices_dict[dev_eui]['listening'] = True
                logging.info(f"device {dev_eui} is listening")
                for device in self._devices_dict:
                    with self._devices_dict_lock:
                        if self._devices_dict[device]['listening'] == False:
                            return
                time.sleep(5)
                self.update_process()
            elif msg_type == self.DEVICE_VERSION_MSG:
                if self.update_finished:
                    self._process_device_version(dev_eui, dev_msg.decode())
