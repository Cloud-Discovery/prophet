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

from prophet.controller.config_file import ConfigFile, CsvDataFile
from prophet import utils


class WindowsHostCollector(object):
    """Collect windows hosts info"""

    def __init__(self, ip, username, password, output_path):
        self.ip = ip
        self.username = username
        self.password = str(password)
        self.output_path = os.path.join(
            output_path, ip + "_windows" + ".yaml")

    def get_windows_host_info(self):
        self._save_host_conn_info()
        self._save_info_to_yaml()

    def _save_host_conn_info(self):
        config_path = os.path.join(
            os.path.dirname(self.output_path),
            "hosts.cfg"
        )
        config = ConfigFile(config_path)
        host_info = {
            "username": self.username,
            "password": self.password
        }
        header = "Windows_" + self.ip
        logging.debug("Writing ip:%s, username:%s, password:%s to %s..."
                      % (self.ip, self.username, self.password, config_path))
        config.set(header, host_info)
        logging.info("Write SSH info sucess to %s." % config_path)

    def _save_info_to_yaml(self):
        logging.info("Starting get host %s info and write to %s..."
                     % (self.ip, self.output_path))
        config = ConfigFile(self.output_path)

        network_info = self._get_network()
        host_info = {
            "hostname": self._get_host_name(),
            "macs": network_info["macs"],
            "ips": network_info["ips"],
            "version": self._get_version(),
            "cpu_num": self._get_cpu_num(),
            "tol_mem": self._get_memory_size(),
            "disk_info": self._get_disk_info(),
            "boot_type": self._get_boot_mode()
        }
        header = 'Windows_' + self.ip
        config.set(header, host_info)
        logging.info("Writed host info sucess to %s." % self.output_path)

    def _get_host_name(self):
        """get the os hostname"""
        stdout, stderr = utils.execute(
            'wmic -U {}%{} //{} "SELECT * FROM Win32_Computersystem"'.format(
                self.username, self.password, self.ip),
            shell=True
        )
        splits = stdout.split("\n")
        index = splits[1].split('|').index("Name")
        return splits[2].split("|")[index]

    def _get_version(self):
        """get the os version"""
        stdout, stderr = utils.execute(
            'wmic -U {}%{} //{} "SELECT * FROM Win32_Operatingsystem"'.format(
                self.username, self.password, self.ip),
            shell=True
        )
        splits = stdout.split("\n")
        index = splits[1].split('|').index("Caption")
        return splits[2].split("|")[index]

    def _get_boot_mode(self):
        """get the boot mode, bios/efi"""
        stdout, stderr = utils.execute(
            'wmic -U {}%{} //{} "SELECT * FROM Win32_DiskPartition"'.format(
                self.username, self.password, self.ip),
            shell=True
        )
        splits = stdout.split("\n")[2].split("|")[-1]
        if splits.find("GPT") >= 0:
            return "efi"
        return "bios"

    def _get_cpu_num(self):
        """get the cpu information"""
        stdout, stderr = utils.execute(
            'wmic -U {}%{} //{} "SELECT * FROM Win32_Processor"'.format(
                self.username, self.password, self.ip),
            shell=True
        )
        splits = stdout.split("\n")
        return len(splits) / 3

    def _get_memory_size(self):
        """get memory of this machine."""
        stdout, stderr = utils.execute(
            'wmic -U {}%{} //{} "SELECT * FROM Win32_PhysicalMemory"'.format(
                self.username, self.password, self.ip),
            shell=True
        )
        splits = stdout.split("\n")
        index = splits[1].split('|').index('Capacity')
        memory = splits[2].split('|')[index]
        return round(int(memory) / (1024 * 1024 * 1024), 2)

    def _get_network(self):
        """get the network information"""
        ips = []
        macs = []
        stdout, stderr = utils.execute(
            'wmic -U {}%{} //{} "SELECT * FROM '
            'win32_NetworkAdapterConfiguration WHERE '
            'IPEnabled=True"'.format(
                self.username, self.password, self.ip),
            shell=True
        )
        splits = stdout.split("\n")
        for i in range(len(splits)/3):
            base_index = i * 3 + 1

            ip_index = splits[base_index].split("|").index("IPAddress")
            ip_address = splits[base_index + 1].split("|")[ip_index].replace(
                "(", "").replace(")", "").split(",")[0]
            ips.append(ip_address)

            mac_index = splits[base_index].split("|").index("MACAddress")
            mac_address = splits[base_index + 1].split("|")[mac_index]
            macs.append(mac_address)
        return {
            "ips": ips,
            "macs": macs
        }

    def _get_disk_info(self):
        """get the disk details"""
        total_used_size = 0
        total_size = 0
        disk_info = {}
        stdout, stderr = utils.execute(
            'wmic -U {}%{} //{} "SELECT * FROM '
            'win32_LogicalDisk WHERE '
            'DriveType = 3"'.format(
                self.username, self.password, self.ip),
            shell=True
        )
        splits = stdout.split("\n")
        for i in range(len(splits) / 3):
            base_index = i * 3 + 1
            fs_index = splits[base_index].split("|").index("FileSystem")
            free_space_index = splits[base_index].split("|").index("FreeSpace")
            size_index = splits[base_index].split("|").index("Size")
            device_id_index = splits[base_index].split("|").index("DeviceID")
            size = int(splits[base_index + 1].split("|")[size_index])
            used_size = size - int(splits[base_index + 1].split("|")[free_space_index])
            total_size += size
            total_used_size += used_size
            device_id = splits[base_index + 1].split("|")[device_id_index]
            file_system = splits[base_index + 1].split("|")[fs_index]
            used_size = round(used_size / (1024.0 * 1024 * 1024), 2)
            size = round(size / (1024.0 * 1024 * 1024), 2)
            disk_info[device_id] = (used_size, size, file_system)
        return disk_info


class WindowsHostReport(object):

    def __init__(self, input_path, output_path, windows_files):
        self.input_path = input_path
        self.output_path = output_path
        self.windows_files = windows_files

    def get_report(self):
        for file in self.windows_files:
            data = list(self._get_data_info(file).values())[0]
            hostname = self._get_hostname(data)
            address = self._get_address(data)
            version = self._get_version(data)
            cpu_num = self._get_cpu_num(data)
            tol_mem = self._get_total_mem(data)
            macaddr = self._get_macaddr(data)
            volume_info = self._get_volume_info(data)
            boot_type = self._get_boot_type(data)
            migration_check = self._migration_check(
                boot_type, version)
            self._yaml_to_csv(
                file, hostname, address, version,
                cpu_num, tol_mem, macaddr, volume_info,
                boot_type, migration_check)

    def _get_data_info(self, file):
        file_path = os.path.join(self.input_path, file)
        with open(file_path) as host_info:
            data = yaml.load(host_info, Loader=yaml.FullLoader)
        return data

    def _get_hostname(self, data):
        return data["hostname"]

    def _get_address(self, data):
        return data["ips"]

    def _get_version(self, data):
        return data["version"]

    def _get_cpu_num(self, data):
        return str(data["cpu_num"])

    def _get_total_mem(self, data):
        return str(data["tol_mem"])

    def _get_macaddr(self, data):
        return data["macs"]

    def _get_volume_info(self, data):
        volume_info = {}
        for device_name, device_info in data["disk_info"].items():
            used_size = device_info[0]
            size = device_info[1]
            file_system = device_info[2]
            volume_info[device_name] = [
                "filesystem:%s" % file_system,
                "tol_size(G):%s" % size,
                "use_size(G):%s" % used_size
            ]
        return volume_info

    def _get_boot_type(self, data):
        return data["boot_type"]

    def _migration_check(self, boot_type, version):
        support_synchronization = "Yes"
        support_increment = "Yes"
        migration_proposal = ""

        support = False
        support_versions = ["2003", "2008", "2012", "2016"]
        for support_version in support_versions:
            if version.find(support_version) > 0:
                support = True
                break
        if not support:
            support_synchronization = "No"
            support_increment = "No"
            migration_proposal = (
                "Host file system %s not support migration."
                % version)
        if "efi" in boot_type:
            support_synchronization = "No"
            support_increment = "No"
            migration_proposal = (
                migration_proposal +
                "Boot type:EFI, cloud not supported, "
                "so migrate to the cloud start system "
                "failed, need fix boot type is BIOS.")
        if migration_proposal.strip() == "":
            migration_proposal = "Check successful"
        return (
            support_synchronization,
            support_increment,
            migration_proposal
        )

    def _yaml_to_csv(self, file, hostname, address, version,
                     cpu_num, tol_mem, macaddr, volume_info,
                     boot_type, migration_check):
        host_data = [
            {
                "host_type": "Windows",
                "hostname": hostname,
                "address": address,
                "version": version,
                "cpu_num": cpu_num,
                "tol_mem(G)": tol_mem,
                "macaddr": macaddr,
                "disk_info": volume_info,
                "boot_type": boot_type,
                "support_synchronization": migration_check[0],
                "support_increment": migration_check[1],
                "migration_proposal": migration_check[2]
            }
        ]
        logging.info("Writing %s migration proposal..." % file)
        file_name = 'analysis' + '.csv'
        output_file = os.path.join(self.output_path, file_name)
        csv_config = CsvDataFile(host_data, output_file)
        csv_config.write_data_to_csv()
        logging.info("Write to %s finish." % output_file)
