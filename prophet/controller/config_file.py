# -*- coding=utf8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2019 Prophet Tech (Shanghai) Ltd.
#
# Authors: Ray <sunqi@prophetech.cn>
#
# Copyright (c) 2019 This file is confidential and proprietary.
# All Rights Resrved, Prophet Tech (Shanghai) Ltd (http://www.prophetech.cn).

"""Use yaml as config file"""

import csv
import logging
import os
import yaml
import json
import sys

reload(sys)
sys.setdefaultencoding("utf-8")


class ConfigFile(object):

    def __init__(self, config_file):
        logging.info("Reading config file %s ..." % config_file)
        self.config_file = str(config_file)

        self.cfg = {}
        if os.path.exists(self.config_file):
            with open(self.config_file, "r") as ymlfile:
                self.cfg = yaml.load(ymlfile)

    def list(self):
        return self.cfg

    def get(self, key):
        return self.cfg[key]

    def set(self, key, values):
        if key not in self.cfg:
            self.cfg[key] = {}
        self.cfg[key] = values
        with open(self.config_file, "w") as outfile:
            yaml.safe_dump(self.cfg,
                           outfile,
                           default_flow_style=False)

    def convert_json_to_yaml(self, values):
        json_datas = json.dumps(values)
        data_values = json.loads(json_datas)
        with open(self.config_file, "w") as yamlfile:
            yaml.safe_dump(data_values, yamlfile, default_flow_style=False)


class CsvDataFile(object):

    def __init__(self, host_data, output_file):
        self.host_data = host_data
        self.output_file = output_file

    def write_data_to_csv(self):
        header = [
                'host_type',
                'hostname',
                'address',
                'macaddr',
                'version',
                'cpu_num',
                'tol_mem(G)',
                'disk_info',
                'boot_type',
                'support_synchronization',
                'support_increment',
                'migration_proposal'
                ]
        with open(self.output_file, 'ab+') as f:
            writer = csv.DictWriter(f, header)
            with open(self.output_file, 'ab+') as f:
                reader = csv.reader(f)
                if not [head_data for head_data in reader]:
                    writer.writeheader()
                    for row in self.host_data:
                        writer.writerow(row)
                else:
                    for row in self.host_data:
                        writer.writerow(row)
