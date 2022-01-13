# Copyright (c) 2021 OnePro Cloud Ltd.
#
#   prophet is licensed under Mulan PubL v2.
#   You can use this software according to the terms and conditions of the Mulan PubL v2.
#   You may obtain a copy of Mulan PubL v2 at:
#
#            http://license.coscl.org.cn/MulanPubL-2.0
#
#   THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
#   EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
#   MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
#   See the Mulan PubL v2 for more details.

"""Base collector class for different resources collection

Inherit this class and implement collect method in sub class.

"""

import json
import logging
import os

import yaml


class BaseHostCollector(object):
    """Base class for host collector

    This may extends more base class for different resources in future.

    Yaml Data Structure:
      {
        "ostype_ip": {
          "results": {results for collection},
          "os_type": "os_type"
          "tcp_ports": "tcp_ports"
        }
      }
    """

    def __init__(self, ip, username, password, ssh_port, key_path,
                 output_path, os_type, **kwargs):
        self.ip = ip
        self.username = username
        self.password = password
        self.ssh_port = ssh_port
        self.key_path = key_path
        self.output_path = output_path
        self.os_type = os_type

        # For more arguments, auto set self
        for k, v in kwargs.items():
            setattr(self, k, v)

    @property
    def base_path(self):
        """Base path to save collection results, by os type"""
        os_path = os.path.join(self.output_path, self.os_type)

        if not os.path.exists(os_path):
            logging.info("Create os path %s" % os_path)
            os.makedirs(os_path)

        return os_path

    @property
    def root_key(self):
        """Root key for yaml file"""
        return "%s_%s" % (self.os_type, self.ip)

    @property
    def collect_path(self):
        """yaml report save path"""
        filename = "%s.yaml" % self.root_key
        return os.path.join(self.base_path, filename)

    def collect(self):
        """Implement in each sub class, main method to collect"""
        raise NotImplementedError

    def get_summary(self):
        """Summary for each collection if you want to display

        If no summary returns, no need to inherit this method, summary
        contains two parts of log, info and debug level

            summary = {
                "info": [lines],
                "debug": [lines]
            }
        """
        return

    def save_to_yaml(self, save_path, values):
        """Save collection report to yaml file"""
        logging.info("Saving report to yaml %s..." % save_path)

        # When we use safe_dump save to yaml, we may get 'can not
        # represent an object' error, so we need to convert to json
        # and then dumps to yaml as workaround
        json_datas = json.dumps(values)
        data_values = json.loads(json_datas)

        with open(save_path, "w") as yamlfile:
            logging.debug("Save values %s: " % data_values)
            yaml.safe_dump(data_values, yamlfile,
                           default_flow_style=False)

        logging.info("Saved report to yaml %s" % save_path)
