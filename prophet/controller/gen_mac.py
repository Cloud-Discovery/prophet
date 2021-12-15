# -*- coding=utf8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2019 OnePro Cloud (Shanghai) Ltd.
#
# Authors: Chenchunzai <chenchunzai@oneprocloud.com>
#
# Copyright (c) 2019 This file is confidential and proprietary.
# All Rights Resrved, OnePro Cloud (Shanghai) Ltd (http://www.oneprocloud.com).

"""Generate index file index by host MAC"""

import os
import yaml
import logging
import pandas as pd

LINUX_YAML_FORMAT = 'linux'
WIN_YAML_FORMAT = 'windows'
VMWARE_YAML_FORMAT = 'vmware'

MAC_FILE_NAME = 'mac_info.yaml'
SCAN_FILE_NAME = 'scan_hosts.csv'

class GenerateMac(object):

    def __init__(self, search_dir):
        self.mac_info = dict()
        self.dirname = search_dir
        self._tcp_ports = {}

    def save_to_yaml(self):
        logging.info("Saving file %s...", self.dirname + MAC_FILE_NAME)
        os.walk(self.dirname, self._find_file, ())
        yamlfile = os.path.join(self.dirname, MAC_FILE_NAME)
        with open(yamlfile, "w") as yf:
            yaml.safe_dump(self.mac_info, yf, default_flow_style=False)
        logging.info('Sucessfully save file %s.', self.dirname + MAC_FILE_NAME)

    @property
    def tcp_ports(self):
        if not self._tcp_ports:
            csv_file = os.path.join(self.dirname, SCAN_FILE_NAME)
            data = pd.read_csv(csv_file)
            for index, row in data.iterrows():
                logging.info('Read row mac tcp_ports is %s' % row)
                if row['mac']:
                    mac = str(row['mac']).lower()
                    ip = row['ip']
                    self._tcp_ports[mac] = {
                        'tcp_ports': str(row['tcp_ports']),
                        'ip': row['ip']}
                    logging.info('Read tcp_ports is %s' % self._tcp_ports)
        return self._tcp_ports

    def _find_file(self, arg, dirname, files):
        for file in files:
            file_path = os.path.join(dirname, file)
            if not file_path.endswith('.yaml'):
                continue

            with open(file_path, "r") as yf:
                logging.debug("Loading file %s...", file_path)
                try:
                    data = yaml.safe_load(yf.read())
                except Exception as ex:
                    logging.error("Load failed, ignored file %s. reason is %s.",
                        file_path, ex.message)
                    continue
                data_type = self._get_type(file_path)
                mac, ip = self._get_mac_ip(data, data_type)
                if not mac:
                    logging.warn("Can't find MacAddress in %s with data_type is %s",
                        file_path, data_type)
                    continue
                if mac not in self.mac_info:
                    self.mac_info[mac] = {}
                    self.mac_info[mac]['ip'] = ip
                    self.mac_info[mac]['yamls'] = []
                    if mac in self.tcp_ports.keys():
                        self.mac_info[mac]['tcp_ports'] = self.tcp_ports[mac]['tcp_ports']
                        if self.tcp_ports[mac]['ip']:
                            self.mac_info[mac]['ip'] = self.tcp_ports[mac]['ip']
                    else:
                        self.mac_info[mac]['tcp_ports'] = None
                dt = dict()
                dt['os_type'] = data_type
                dt['file_path'] = file_path
                self.mac_info[mac]['yamls'].append(dt)
                logging.debug("Sucessfully load file %s.", file_path)
                logging.debug("Update %s to mac_info.", dt)

    def _get_type(self, filename):
        filepath, tempfilename = os.path.split(filename)
        name, ext = os.path.splitext(tempfilename)
        if name.endswith('_windows'):
            return WIN_YAML_FORMAT
        elif name.endswith('_linux'):
            return LINUX_YAML_FORMAT
        elif name.endswith('_vmware'):
            return VMWARE_YAML_FORMAT

    def _get_mac_ip(self, data, data_type):
        mac = None
        ip = None
        if data_type == LINUX_YAML_FORMAT:
            # Fetch mac from ansible result
            data = data.get('success')
            for _, v in data.iteritems():
                networks = v['ansible_facts']['ansible_default_ipv4']
                if isinstance(networks, list):
                    mac = networks[0]['macaddress']
                    ip = networks[0]['address']
                else:
                    mac = networks['macaddress']
                    ip = networks['address']
        elif data_type == WIN_YAML_FORMAT:
            # Fetch mac from winrm result
            for _, val in data.iteritems():
                networkadpt = val['Win32_NetworkAdapterConfiguration']
                if networkadpt:
                    mac = networkadpt[0]['MACAddress'].lower()
                    ip = networkadpt[0]['IPAddress']
                    ip = ip.replace("(", "").replace(")", "")
        elif data_type == VMWARE_YAML_FORMAT:
            for item, values in data.iteritems():
                logging.info("network: %s" % values["network"])
                for uuid, nets in values["network"].iteritems():
                    logging.info("Current network is %s" % nets)
                    mac = nets.get("macAddress")
                    break

        return mac, ip
