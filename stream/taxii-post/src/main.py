import json
import os
import sys
import time
import uuid

import requests
import yaml
from pycti import OpenCTIConnectorHelper, get_config_variable


class TaxiiPostConnector:
    def __init__(self):
        # Instantiate the connector helper from config
        config_file_path = os.path.dirname(os.path.abspath(__file__)) + "/config.yml"
        config = (
            yaml.load(open(config_file_path), Loader=yaml.FullLoader)
            if os.path.isfile(config_file_path)
            else {}
        )
        self.helper = OpenCTIConnectorHelper(config)
        self.taxii_url = get_config_variable(
            "TAXII_URL",
            ["taxii", "url"],
            config,
        )
        self.taxii_ssl_verify = get_config_variable(
            "TAXII_SSL_VERIFY", ["taxii", "ssl_verify"], config, False, True
        )
        self.taxii_collection_id = get_config_variable(
            "TAXII_COLLECTION_ID",
            ["taxii", "collection_id"],
            config,
        )
        self.taxii_token = get_config_variable(
            "TAXII_TOKEN", ["taxii", "token"], config
        )
        self.taxii_login = get_config_variable(
            "TAXII_LOGIN", ["taxii", "login"], config
        )
        self.taxii_password = get_config_variable(
            "TAXII_PASSWORD",
            ["taxii", "password"],
            config,
        )
        self.taxii_version = get_config_variable(
            "TAXII_VERSION", ["taxii", "version"], config
        )
        self.taxii_stix_version = get_config_variable(
            "TAXII_STIX_VERSION", ["taxii", "stix_version"], config
        )

    def _process_message(self, msg):
        try:
            data = json.loads(msg.data)["data"]
        except:
            raise ValueError("Cannot process the message")
        url = (
            self.taxii_url
            + "/root/collections/"
            + self.taxii_collection_id
            + "/objects"
        )
        headers = {
            "Content-Type": "application/vnd.oasis.stix+json; version="
            + self.taxii_stix_version,
            "Accept": "application/vnd.oasis.taxii+json; version=" + self.taxii_version,
        }
        try:
            data_object = data
            data_object["spec_version"] = self.taxii_stix_version
            if self.taxii_stix_version != "2.1":
                del data_object["extensions"]
                if "pattern_version" in data_object:
                    del data_object["pattern_version"]
            bundle = {
                "type": "bundle",
                "spec_version": self.taxii_stix_version,
                "id": "bundle--" + str(uuid.uuid4()),
                "objects": [data_object],
            }
            if self.taxii_token is not None:
                headers["Authorization"] = "Bearer " + self.taxii_token
                response = requests.post(url, headers=headers, json=bundle)
                response.raise_for_status()
            else:
                response = requests.post(
                    url,
                    headers=headers,
                    auth=(self.taxii_login, self.taxii_password),
                    json=bundle,
                )
                response.raise_for_status()
        except Exception as e:
            self.helper.log_error(str(e))

    def start(self):
        self.helper.listen_stream(self._process_message)


if __name__ == "__main__":
    try:
        connector = TaxiiPostConnector()
        connector.start()
    except Exception as e:
        print(e)
        time.sleep(10)
        sys.exit(0)
