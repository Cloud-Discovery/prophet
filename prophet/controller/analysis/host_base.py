# -*- coding=utf8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2019 OnePro Cloud (Shanghai) Ltd.
#
# Authors: Ray <ray.sun@oneprocloud.com>
#
# Copyright (c) 2019 This file is confidential and proprietary.
# All Rights Resrved, OnePro Cloud (Shanghai) Ltd (http://www.oneprocloud.com).

DEFAULT_NA = "N/A"


class HostBase(object):

    def __init__(self):
        self.boot_type = "bios"
        self.vt_platform = DEFAULT_NA
        self.vt_platform_ver = DEFAULT_NA
        self.vt_drs_on = DEFAULT_NA
        self.vt_ha_on = DEFAULT_NA

    def get_info(self):
        return {
            "host_type": self.host_type,
            "hostname": self.hostname,
            "vm_name": self.vm_name,
            "conn_ip": self.conn_ip,
            "conn_mac":  self.conn_mac,
            "os": self.os,
            "os_version": self.os_version,
            "os_bit": self.os_bit,
            "os_kernel": self.os_kernel,
            "cpu_info": self.cpu_info,
            "cpu_cores": self.cpu_cores,
            "memory_info": self.memory_info,
            "total_mem": self.total_mem,
            "free_mem": self.free_mem,
            "disk_info": self.disk_info,
            "disk_count": self.disk_count,
            "disk_total_size": self.disk_total_size,
            "disk_used_size": self.disk_used_size,
            "partition_info": self.partition_info,
            "boot_type": self.boot_type,
            "nic_info": self.nic_info,
            "vt_platform": self.vt_platform,
            "vt_platform_ver": self.vt_platform_ver,
            "vt_drs_on": self.vt_drs_on,
            "vt_ha_on": self.vt_ha_on,
            "tcp_ports": self.tcp_ports,
            "support_full_sync": self.support_full_sync,
            "support_delta_sync": self.support_delta_sync,
            "support_agent": self.support_agent,
            "support_agentless": self.support_agentless,
            "check_result": self.check_result
        }
