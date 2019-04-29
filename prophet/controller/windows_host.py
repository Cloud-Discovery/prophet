#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2017 Prophet Tech (Shanghai) Ltd.
#
# Authors: Li ZengYuan <lizengyuan@prophetech.cn>
#
# Copyright (c) 2017. This file is confidential and proprietary.
# All Rights Reserved, Prophet Tech (Shanghai) Ltd(http://www.prophetech.cn).
#

import logging
import os
import yaml

from config_file import ConfigFile, CsvDataFile
from prophet import utils


class WindowsHostCollector(object):
    """Collect windows hosts info"""

    def __init__(self, ip, username, password, data_path):
        self.ip = ip
        self.username = username
        self.password = password
        self.data_path = os.path.join(data_path, self.ip +
                                      '_windows' + '.yaml')

    def get_windows_host_info(self):
        self._save_host_conn_info()
        self._save_info_to_yaml()

    def _save_host_conn_info(self):
        logging.info("Writing ip:%s, username:%s, password:%s..." % (
            self.ip, self.username, self.password))
        config_path = os.path.join(os.path.dirname(self.data_path),
                                   'hosts.cfg')
        config = ConfigFile(config_path)
        host_info = {
                'username': self.username,
                'password': self.password
                }
        header = 'Windows_' + self.ip
        config.set(header, host_info)
        logging.info("Write SSH info succeed To %s" % self.data_path)

    def _host_name(self):
        """get the os hostname"""
        try:
            logging.info("Geting hostname...")
            stdout, stderr = utils.execute(
                    'wmic -U {}%{} //{} "SELECT * FROM '
                    'Win32_Computersystem"'.format(self.username,
                                                   self.password,
                                                   self.ip),
                    shell=True)
            name = stdout.split("\n")
            name_index = name[1].split('|').index("Name")
            name = name[2].split("|")[name_index]
            return name
        except Exception as err:
            logging.error("failed to connect %s %s" % (self.ip, err))
            raise

    def _version(self):
        """get the os version"""
        try:
            logging.info("Geting version...")
            stdout, stderr = utils.execute(
                    'wmic -U {}%{} //{} "SELECT * FROM '
                    'Win32_Operatingsystem"'.format(self.username,
                                                    self.password,
                                                    self.ip),
                    shell=True)
            name = stdout.split("\n")
            name_index = name[1].split('|').index("Caption")
            name = name[2].split("|")[name_index]
            return name
        except Exception:
            logging.error("failed to get version of host.")
            raise

    def _boot_mode(self):
        """get the boot mode, bios/efi"""
        try:
            logging.info("Geting boot mode...")
            stdout, stderr = utils.execute(
                    'wmic -U {}%{} //{} "SELECT * FROM '
                    'Win32_DiskPartition"'.format(self.username,
                                                  self.password,
                                                  self.ip),
                    shell=True)
            name = stdout.split("\n")[2].split("|")[-1]
            if name.find('GPT') >= 0:
                return 'efi'
            else:
                return 'bios'
            logging.info("Get boot_type:%s" % name)
        except Exception:
            logging.error("failed to get boot mode.")
            raise

    def _get_cpu(self):
        """get the cpu information"""
        try:
            logging.info("Geting cpu cores...")
            stdout, stderr = utils.execute(
                    'wmic -U {}%{} //{} "SELECT * FROM '
                    'Win32_Processor"'.format(self.username,
                                              self.password,
                                              self.ip),
                    shell=True)
            base_str = stdout.split("\n")
            number_of_cores = len(base_str) / 3
            return number_of_cores
        except Exception:
            logging.error("failed to get cpu.")
            raise

    def _get_memory(self):
        """get memory of this machine."""
        try:
            logging.info("Geting memory...")
            stdout, stderr = utils.execute(
                    'wmic -U {}%{} //{} "SELECT * FROM '
                    'Win32_PhysicalMemory"'.format(self.username,
                                                   self.password,
                                                   self.ip),
                    shell=True)
            base_str = stdout.split("\n")
            memory_index = base_str[1].split('|').index('Capacity')
            memory = base_str[2].split('|')[memory_index]
            memory = round(int(memory) / (1024 * 1024 * 1024), 2)
            return memory
        except Exception:
            logging.error("failed to get memory.")
            raise

    def _network(self):
        """get the network information"""
        try:
            logging.info("Geting network info...")
            ip = []
            mac = []
            stdout, stderr = utils.execute(
                    'wmic -U {}%{} //{} "SELECT * FROM '
                    'win32_NetworkAdapterConfiguration WHERE '
                    'IPEnabled=True"'.format(self.username,
                                             self.password,
                                             self.ip),
                    shell=True)
            n = len(stdout.split("\n")) / 3
            for i in range(n):
                num = i * 3 + 1
                ip_index = (stdout.split("\n")[num].split('|').index
                            ("IPAddress"))
                ip_address = (stdout.split("\n")[num + 1].split('|')
                              [ip_index].replace('(', '').replace
                              (')', '').split(',')[0])
                ip.append(ip_address)
                mac_index = (stdout.split("\n")[num].split('|').index
                             ("MACAddress"))
                mac_address = (stdout.split("\n")[num + 1].split('|')
                               [mac_index])
                mac.append(mac_address)
            return [ip, mac]
        except Exception:
            logging.error("failed to get the network information host.")
            raise

    def _w_disk(self):
        """get the disk details"""
        try:
            logging.info("Geting disk info...")
            total_used_size = 0
            total_size = 0
            disk_info = {}
            stdout, stderr = utils.execute(
                    'wmic -U {}%{} //{} "SELECT * FROM '
                    'win32_LogicalDisk WHERE '
                    'DriveType = 3"'.format(self.username,
                                            self.password,
                                            self.ip),
                    shell=True)
            n = len(stdout.split("\n")) / 3
            for i in range(n):
                num = i * 3 + 1
                base_str = stdout.split("\n")
                fs_index = base_str[num].split('|').index('FileSystem')
                free_space_index = base_str[num].split('|').index('FreeSpace')
                size_index = base_str[num].split('|').index('Size')
                device_id_index = base_str[num].split('|').index('DeviceID')
                size = int(base_str[num + 1].split('|')[size_index])
                used_size = (size - int(base_str[num + 1].split('|')
                             [free_space_index]))
                total_size += size
                total_used_size += used_size
                device_id = base_str[num + 1].split('|')[device_id_index]
                file_system = base_str[num + 1].split('|')[fs_index]
                used_size = round(used_size / (1024.0 * 1024 * 1024), 2)
                size = round(size / (1024.0 * 1024 * 1024), 2)
                disk_info[device_id] = (used_size, size, file_system)
            return disk_info
        except Exception:
            logging.error("failed to get the disk information of host.")
            raise

    def _save_info_to_yaml(self):
        logging.info("Starting get host %s data info and Writing host "
                     "info to %s..." % (self.ip, self.data_path))
        config = ConfigFile(self.data_path)
        network_info = self._network()
        host_info = {
                'hostname': self._host_name(),
                'mac': network_info[1],
                'ip': network_info[0],
                'version': self._version(),
                'cpu_num': self._get_cpu(),
                'tol_mem': self._get_memory(),
                'diso_info': self._w_disk(),
                'boot_type': self._boot_mode()
                }
        header = 'windows_' + self.ip
        config.set(header, host_info)
        logging.info("Writed host info to %s successed." % self.data_path)


class WindowsHostReport(object):

    def __init__(self, input_path, output_path, windows_file):
        self.windows_file = windows_file
        self.input_path = input_path
        self.output_path = output_path

    def get_report(self):
        for i in self.windows_file:
            self.data = self._get_data_info(i)
            self.hostname = self._get_hostname(self.data)
            self.address = self._get_address(self.data)
            self.version = self._get_version(self.data)
            self.cpu_num = self._get_cpu_num(self.data)
            self.tol_mem = self._get_total_mem(self.data)
            self.macaddr = self._get_macaddr(self.data)
            self.volume_info = self._get_volume_info(self.data)
            self.boot_type = self._get_boot_type(self.data)
            self.migration_check = self._migration_check(self.boot_type,
                                                         self.version)
            self._yaml_to_csv(i, self.hostname, self.address, self.version,
                              self.cpu_num, self.tol_mem, self.macaddr,
                              self.volume_info, self.boot_type,
                              self.migration_check)

    def _get_data_info(self, i):
        file_path = os.path.join(self.input_path, i)
        logging.info("Opening %s....." % i)
        with open(file_path) as host_info:
            data = yaml.load(host_info)
        logging.info("Geting designated data.....")
        return data

    def _yaml_to_csv(self, i, hostname, address, version,
                     cpu_num, tol_mem, macaddr, volume_info,
                     boot_type, migration_check):
        host_data = [
                {'host_type': 'Windows',
                 'hostname': self.hostname,
                 'address': self.address,
                 'version': self.version,
                 'cpu_num': self.cpu_num,
                 'tol_mem(G)': self.tol_mem,
                 'macaddr': self.macaddr,
                 'disk_info': self.volume_info,
                 'boot_type': self.boot_type,
                 'support_synchronization': self.migration_check[0],
                 'support_increment': self.migration_check[1],
                 'migration_proposal': self.migration_check[2]}
                ]
        logging.info("Writing migration proposal.....")
        file_name = 'analysis' + '.csv'
        output_file = os.path.join(self.output_path, file_name)
        csv_config = CsvDataFile(host_data, output_file)
        csv_config.write_data_to_csv()
        logging.info("%s migration proposal completed" % i)

    def _get_hostname(self, data):
        logging.info("Analysising hostname...")
        hostname = self.data.values()[0]['hostname']
        return hostname

    def _get_address(self, data):
        logging.info("Analysising ip address...")
        address = self.data.values()[0]['ip']
        return address

    def _get_version(self, data):
        logging.info("Analysising host version...")
        versions = self.data.values()[0]['version']
        return versions

    def _get_cpu_num(self, data):
        logging.info("Analysising cpu cores...")
        cpu_num = str(self.data.values()[0]['cpu_num'])
        return cpu_num

    def _get_total_mem(self, data):
        logging.info("Analysising memory...")
        host_tolal_mem = str(self.data.values()[0]['tol_mem'])
        return host_tolal_mem

    def _get_macaddr(self, data):
        logging.info("Analysising ip macaddr...")
        host_macaddr = self.data.values()[0]['mac']
        return host_macaddr

    def _get_volume_info(self, data):
        logging.info("Analysising volume info...")
        volume_info = {}
        all_volume = self.data.values()[0]['diso_info'].keys()
        for i in range(len(all_volume)):
            device_name = data.values()[0]['diso_info'].keys()[i]
            device_info = data.values()[0]['diso_info'][device_name]
            used_size = device_info[0]
            size = device_info[1]
            file_system = device_info[2]
            volume_info[device_name] = [
                    'filesystem:%s' % file_system,
                    'tol_size(G):%s' % size,
                    'use_size(G):%s' % used_size
                    ]
        return volume_info

    def _get_boot_type(self, data):
        logging.info("Analysising boot mode...")
        boot_type = self.data.values()[0]['boot_type']
        return boot_type

    def _migration_check(self, boot_type, version):
        logging.info("Geted host data successful.")
        logging.info("Checking host data.....")
        support_synchronization = 'Yes'
        support_increment = 'Yes'
        migration_proposal = ''
        support_version = ["2003", "2008", "2012", "2016"]
        for i in support_version:
            if self.version.find(i) > 0:
                break
        else:
            support_synchronization = 'No'
            support_increment = 'No'
            migration_proposal = ('Host file system %s not support '
                                  'migration. ' % self.version)
        if 'efi' in self.boot_type:
            support_synchronization = 'No'
            support_increment = 'No'
            migration_proposal = (migration_proposal +
                                  'Boot type:EFI, cloud not supported, '
                                  'so migrate to the cloud start system '
                                  'failed, need fix boot type is BIOS.')
        if migration_proposal.strip() == '':
            migration_proposal = 'Check successful'
        logging.info("Host data check completed.")
        return (support_synchronization,
                support_increment,
                migration_proposal)
