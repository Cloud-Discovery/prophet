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
import json
import logging
import os
import yaml


class ConfigFile(object):

    def __init__(self, config_file):
        self.config_file = config_file
        self.cfg = {}
        if os.path.exists(self.config_file):
            with open(self.config_file, "r") as ymlfile:
                self.cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)

    def list(self):
        return self.cfg

    def get(self, key):
        return self.cfg[key]

    def set(self, key, values):
        if key not in self.cfg:
            self.cfg[key] = {}
        self.cfg[key] = values
        with open(self.config_file, "w") as outfile:
            yaml.safe_dump(self.cfg, outfile,
                           default_flow_style=False)

    def convert_json_to_yaml(self, values):
        json_datas = json.dumps(values)
        data_values = json.loads(json_datas)
        with open(self.config_file, "w") as yamlfile:
            yaml.safe_dump(data_values, yamlfile,
                           default_flow_style=False)


class CsvDataFile(object):

    def __init__(self, host_data, output_file):
        self.host_data = host_data
        self.output_file = output_file

    def write_data_to_csv(self):
        header = [
            'host_type',
            'hostname',
            'version',
            'address',
            'macaddr',
            'cpu_num',
            'tol_mem(G)',
            'disk_info',
            'boot_type',
            'support_synchronization',
            'support_increment',
            'drs_on',
            'ha_on',
            'migration_proposal'
        ]
        with open(self.output_file, 'a+') as f:
            reader = csv.reader(f)
            writer = csv.DictWriter(f, fieldnames=header)
            if not [row for row in reader]:
                writer.writeheader()
            for row in self.host_data:
                writer.writerow(row)
