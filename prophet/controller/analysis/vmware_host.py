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

VMWARE_DISK_VENDOR = "VMware"


class VMwareHost(HostBase):

    def __init__(self, payload):
        # Not support options
        self.hostname = None
        self.memory_info = None
        self.free_mem = None
        self.partition_info = None
        self.os_kernel = None
        self.cpu_info = None
        self.tcp_ports = None
        self.vt_platform_ver = None
        self.support_agent = None

        super(VMwareHost, self).__init__()

        self._analysis(payload)

    def get_info(self):
        self.host_type = "VMware"
        return super(VMwareHost, self).get_info()

    def _analysis(self, payload):
        for _, info in payload.items():
            self._get_vm_info(info)
            self._migration_check(info)

    def _get_vm_info(self, data):
        self.vm_name = data["name"]
        full_name = data["guestFullName"]
        name_slice = full_name.split(" ")
        self.conn_ip = data["ipAddress"]
        for i in sorted(data["network"].keys()):
            self.conn_mac = data["network"][i]["macAddress"]
            break

        # Parse os
        self.os = ' '.join([x for x in name_slice[:2]])

        # Parse os_bit
        os_bit = name_slice[-1]
        if '64' in os_bit:
            self.os_bit = '64-bit'
        else:
            self.os_bit = '32-bit'

        # Parse os_version
        self.os_version = ' '.join([x for x in name_slice[:-1]])
        self.cpu_cores = data["numCpu"]
        self.total_mem = data["memoryMB"]

        # Parse disk info
        self._get_disk_info(data["disks_info"].values())

        self.nic_info = data["network"]
        self.boot_type = data["firmware"]
        self.vt_drs_on = data["drs"]
        self.vt_ha_on = data["ha"]
        self.vt_platform = VMWARE_DISK_VENDOR

    def _get_disk_info(self, data):
        self.disk_info = data
        self.disk_count = len(data)
        self.disk_total_size = 0
        self.disk_used_size = -1
        for info in data:
            self.disk_total_size += \
                info["capacityInKB"] / 1024 / 1024

    def _migration_check(self, data):
        boot_type = data["firmware"]
        self.support_full_sync = "Yes"
        self.support_delta_sync = "Yes"
        self.support_agentless = VMWARE_DISK_VENDOR
        self.check_result = []

        # Check boot type
        if "efi" in boot_type:
            self.support_full_sync = "No"
            self.support_delta_sync = "No"
            result = ("Boot type:EFI, cloud not supported, "
                      "so migrate to the cloud start system "
                      "failed, need fix boot type is BIOS.")
            self.check_result.append(result)

        # Check disk mode
        for disk_info in data["disks_info"].values():
            disk_mode = disk_info["diskMode"]
            if "independent_persistent" == disk_mode:
                self.support_full_sync = "No"
                self.support_delta_sync = "No"
                result = ("Disk is independent mode, cloud "
                          "not support migrate.")
                self.check_result.append(result)

        # Check vmware version
        if int(data["version"].split('-')[1]) < 7:
            self.support_delta_sync = "No"
            result = ("VM version <7, not support CBT, "
                      "cannot support incremental backup.")
            self.check_result.append(result)

        # Check option "changeTrackingSupported"
        if not data["changeTrackingSupported"]:
            self.support_delta_sync = "No"
            result = "VM not support CBT."
            self.check_result.append(result)
        if not self.check_result:
            self.check_result = "Check successful."
        # else:
        #     self.support_agentless = None
