# -*- coding=utf8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2019 OnePro Cloud (Shanghai) Ltd.
#
# Authors: Ray <ray.sun@oneprocloud.com>
#
# Copyright (c) 2019 This file is confidential and proprietary.
# All Rights Resrved, OnePro Cloud (Shanghai) Ltd (http://www.oneprocloud.com).

from prophet.controller.analysis.host_base import HostBase

BIOS_BOOT = "bios"
EFI_BOOT = "efi"


class WindowsHost(HostBase):

    def __init__(self, payload):
        # Not support options
        self.vm_name = None
        self.vt_platform = None
        self.vt_platform_ver = None
        self.vt_drs_on = None
        self.vt_ha_on = None
        self.tcp_ports = None
        self.support_agentless = None

        super(WindowsHost, self).__init__()

        self._analysis(payload)

    def get_info(self):
        self.host_type = "Physical"
        return super(WindowsHost, self).get_info()

    def _analysis(self, payload):
        for _, info in payload.items():
            _computer_system = info['Win32_ComputerSystem'][0]
            self._get_computer_system(_computer_system)

            _operating_system = info['Win32_OperatingSystem'][0]
            self._get_operating_system(_operating_system)

            _disk_drive = info['Win32_DiskDrive'][0]
            self._get_disk_drive(_disk_drive)

            _disk_partition = info['Win32_DiskPartition']
            self._get_disk_partition(_disk_partition)

            _processor = info['Win32_Processor']
            self._get_processor(_processor)

            _physical_memory = info['Win32_PhysicalMemory'][0]
            self._get_physical_memory(_physical_memory)

            _network_info = info['Win32_NetworkAdapterConfiguration']
            self._get_network_info(_network_info)

            _logical_disk = info['Win32_LogicalDisk']
            self._get_logical_disk(_logical_disk)

            _process = info['Win32_Process'][0]
            self._get_process(_process)

        self._migration_check()

    def _get_computer_system(self, data):
        self.hostname = data["Name"]
        self.total_mem = int(data["TotalPhysicalMemory"]) / (1024 * 1024)

    def _get_operating_system(self, data):
        self.free_mem = int(data["FreePhysicalMemory"]) / (1024 * 1024)
        os = data["Name"].split("|")[0].strip()
        self.os = os
        self.os_version = os
        self.os_bit = data["OSArchitecture"]
        self.os_kernel = data["Version"]

    def _get_disk_drive(self, data):
        pass

    def _get_disk_partition(self, data):
        partition_info = []
        boot_type = BIOS_BOOT
        for part in data:
            partition_info.append({
                'DeviceID': part['DeviceID'],
                'Bootable': part['Bootable'],
                'NumberOfBlocks': part['NumberOfBlocks'],
                'PrimaryPartition': part['PrimaryPartition'],
                'Size': part['Size'],
                'Type': part['Type']})
            if 'GPT' in part['Type'] and part['Bootable'] == 'True':
                boot_type = EFI_BOOT
        self.partition_info = partition_info
        self.boot_type = boot_type

    def _get_logical_disk(self, data):
        disk_info = {}
        disk_count = 0
        disk_total_size = 0
        disk_used_size = 0
        for disk in data:
            free_size = \
                round(int(disk['FreeSpace']) / (1024.0 * 1024 * 1024), 2)
            size = round(int(disk['Size']) / (1024.0 * 1024 * 1024), 2)
            disk_total_size += size
            fs = disk['FileSystem']
            disk_info[disk['DeviceID']] = (size-free_size, size, fs)
            disk_used_size += size - free_size
            disk_count += 1

        self.disk_info = disk_info
        self.disk_count = disk_count
        self.disk_total_size = disk_total_size
        self.disk_used_size = disk_used_size

    def _get_network_info(self, data):
        self.conn_ip = data[0]["IPAddress"].strip("(").strip(")")
        self.conn_mac = data[0]["MACAddress"].lower()

        network_info = []
        for net in data:
            network_info.append({
                'DefaultIPGateway': net['DefaultIPGateway'],
                'IPAddress': net['IPAddress'],
                'IPSubnet': net['IPSubnet'],
                'MACAddress': net['MACAddress']})
        self.nic_info = network_info

    def _get_physical_memory(self, data):
        self.memory_info = data

    def _get_process(self, data):
        pass

    def _get_processor(self, data):
        self.cpu_info = data[0]["Name"]
        cpu_cores = 0
        for proc in data:
            cpu_cores += int(proc["NumberOfCores"])
        self.cpu_cores = cpu_cores

    def _get_service(self, data):
        pass

    def _migration_check(self):
        self.support_full_sync = "Yes"
        self.support_delta_sync = "Yes"
        self.support_agent = "Windows Agent"
        self.check_result = []

        # Check boot type
        if "efi" in self.boot_type:
            self.support_full_sync = "No"
            self.support_delta_sync = "No"
            result = ("Boot type:EFI, cloud not supported, "
                      "so migrate to the cloud start system "
                      "failed, need fix boot type is BIOS.")
            self.check_result.append(result)

        # Check version
        support_versions = ["2003", "2008", "2012", "2016"]
        support = False
        for sup in support_versions:
            if self.os_version.find(sup) > 0:
                support = True
                break
        if not support:
            self.support_full_sync = "No"
            self.support_delta_sync = "No"
            result = ("Host file system %s not support migration."
                      % self.os_version)
            self.check_result.append(result)

        if not self.check_result:
            self.check_result = "Check successful."
