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

import urllib.request
import binascii
import base64
import os
import json
from .config import UpdaterConfig
import logging

config = UpdaterConfig()


mcGroup_payload = {
    "multicastGroup": {
        "dr": 0,
        "fCnt": 0,
        "frequency": 0,
        "groupType": "CLASS_C",
        "id": "string",
        "mcAddr": "string",
        "mcAppSKey": "string",
        "mcNwkSKey": "string",
        "name": "string",
        "pingSlotPeriod": 0,
        "serviceProfileID": "string"
    }
}

mcQueue_payload = {
    "queueItem": {
        "data": "string",
        "fCnt": 0,
        "fPort": 1,
    }
}

mcAddDevice_payload = {
    "devEUI": "string",
    "multicastGroupID": "string"
}


class LoraServerClient:

    def __init__(self):
        self.server = config.LORASERVER_URL
        self.port = config.LORASERVER_API_PORT
        self.api_key = config.LORASERVER_API_KEY

    def create_multicast_group(self, dr, freq, group_name, api_key, app_id):

        group_id = self.generate_random_id()
        mcAddr = self.generate_randon_addr()
        mcAppSKey = self.generate_random_key()
        mcNwkSKey = self.generate_random_key()

        url = self.server + ':' + str(self.port) + '/api/multicast-groups'

        mcGroup_payload["multicastGroup"]["applicationId"] = app_id
        mcGroup_payload["multicastGroup"]["dr"] = dr
        mcGroup_payload["multicastGroup"]["frequency"] = freq
        mcGroup_payload["multicastGroup"]["id"] = group_id.decode("utf-8")
        mcGroup_payload["multicastGroup"]["mcAddr"] = mcAddr.decode("utf-8")
        mcGroup_payload["multicastGroup"]["mcAppSKey"] = mcAppSKey.decode("utf-8")
        mcGroup_payload["multicastGroup"]["mcNwkSKey"] = mcNwkSKey.decode("utf-8")
        mcGroup_payload["multicastGroup"]["name"] = group_name
        # default region is EU868

        payload = bytes(json.dumps(mcGroup_payload), 'utf-8')

        try:
            r = urllib.request.Request(url, data=payload, method='POST')
            r.add_header("Content-Type", "application/json")
            r.add_header("Accept", "application/json")
            r.add_header("Grpc-Metadata-Authorization", "Bearer " + api_key)

            with urllib.request.urlopen(r) as f:
                resp = f.read().decode('utf-8')
                if '"id":' in resp:
                    multicast_id = json.loads(resp)["id"]
                    return (multicast_id, mcAddr, mcNwkSKey, mcAppSKey)
                else:
                    return None
        except Exception as ex:
            logging.info("Error creating multicast data: {}".format(ex))

        return None

    def delete_multicast_group(self, group_id, api_key):

        url = self.server + ':' + str(self.port) + '/api/multicast-groups/' + group_id

        try:
            r = urllib.request.Request(url, method='DELETE')
            r.add_header("Grpc-Metadata-Authorization", "Bearer " + api_key)

            with urllib.request.urlopen(r) as f:
                return f.getcode() == 200

        except Exception as ex:
            logging.info("Error deleting multicast group: {}".format(ex))

        return False

    def add_device_multicast_group(self, devEUI, group_id, api_key):

        url = self.server + ':' + str(self.port) + '/api/multicast-groups/' + group_id + '/devices'

        mcAddDevice_payload["devEui"] = devEUI

        payload = json.dumps(mcAddDevice_payload).encode('utf-8')

        try:
            r = urllib.request.Request(url, data=payload, method='POST')
            r.add_header("Content-Type", "application/json")
            r.add_header("Accept", "application/json")
            r.add_header("Grpc-Metadata-Authorization", "Bearer " + api_key)

            with urllib.request.urlopen(r) as f:
                return f.getcode() == 200

        except Exception as ex:
            logging.info("Error adding device to multicast group: {}".format(ex))

        return False

    def request_multicast_keys(self, group_id, api_key):

        url = self.server + ':' + str(self.port) + '/api/multicast-groups/' + group_id

        try:
            r = urllib.request.Request(url, method='GET')
            r.add_header("Accept", "application/json")
            r.add_header("Grpc-Metadata-Authorization", "Bearer " + api_key)

            with urllib.request.urlopen(r) as f:
                resp = f.read().decode('utf-8')
                if "mcNwkSKey" in resp:
                    json_resp = json.loads(resp)["multicastGroup"]
                    return (json_resp["mcAddr"], json_resp["mcNwkSKey"], json_resp["mcAppSKey"])
                else:
                    return None
        except Exception as ex:
            logging.info("Error getting multicast keys: {}".format(ex))

        return None

    def generate_randon_addr(self):
        return binascii.hexlify(os.urandom(4))

    def generate_random_key(self):
        return binascii.hexlify(os.urandom(16))

    def generate_random_id(self):
        return binascii.hexlify(os.urandom(4)) + b'-' + binascii.hexlify(os.urandom(2)) + b'-' + binascii.hexlify(os.urandom(2)) \
            + b'-' + binascii.hexlify(os.urandom(2)) + b'-' + binascii.hexlify(os.urandom(6))

    def multicast_queue_length(self, api_key, multicast_group):
        url = self.server + ':' + str(self.port) + '/api/multicast-groups/' + multicast_group + '/queue'

        try:
            r = urllib.request.Request(url, method='GET')
            r.add_header("Content-Type", "application/json")
            r.add_header("Grpc-Metadata-Authorization", "Bearer " + api_key)

            with urllib.request.urlopen(r) as f:
                resp = f.read().decode('utf-8')
                if "multicastQueueItems" in resp:
                    logging.info(resp)
                    json_resp = json.loads(resp)["multicastQueueItems"]
                    logging.info("Len: {}".format(len(json_resp)))
                    return len(json_resp)
                else:
                    return -1

        except Exception as ex:
            logging.info("Error getting multicast queue length: {}".format(ex))

        return -1

    def send(self, api_key, multicast_group, data):
        url = self.server + ':' + str(self.port) + '/api/multcast-groups/' + multicast_group + '/queue'

        mcQueue_payload["queueItem"]["data"] = base64.b64encode(data).decode("utf-8")

        payload = bytes(json.dumps(mcQueue_payload), 'utf-8')

        try:
            r = urllib.request.Request(url, data=payload, method='POST')
            r.add_header("Content-Type", "application/json")
            r.add_header("Accept", "application/json")
            r.add_header("Grpc-Metadata-Authorization", "Bearer " + api_key)

            with urllib.request.urlopen(r) as f:
                return f.getcode() == 200

        except Exception as ex:
            logging.info("Error sending multicast data: {}".format(ex))

        return False
