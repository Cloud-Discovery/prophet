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

"""Base parser class for different resources

Inherit this class and implement each `parser` method in sub class.

"""

import logging

# Boot type
BIOS_BOOT = "bios"
EFI_BOOT = "efi"

# Default sign for uefi boot
LINUX_EFI_MOUNT_POINT = "/boot/efi"

# Virtualization Platform
VMWARE_DISK_VENDOR = "VMWARE"
KVM_DISK_VENDOR = "QEMU"
VT_VENDORS = [VMWARE_DISK_VENDOR, KVM_DISK_VENDOR]


class BaseHostParser(object):

    def __init__(self, payload):
        self.payload = payload

        self.vt_platform = None
        self.vt_platform_ver = None

    def parse(self):
        """Return dict with all host information"""
        return {
            "basic": self.parse_basic(),
            "os": self.parse_os(),
            "cpu": self.parse_cpu(),
            "memory": self.parse_memory(),
            "disks": self.parse_disks(),
            "networks": self.parse_nics(),
            "vt": self.parse_vt()
        }

    def parse_basic(self):
        """Return a dict with basic host information

        Basic host information sample dict:
            {
                host_type: Physical/VMware/OpenStack/...
                hostname: Hostname
                vm_name: Virtual Machine name
                conn_ip: IP for connecting
                conn_mac: NIC for conneting
            }
        """
        raise NotImplementedError

    def parse_os(self):
        """Return a dict with OS information

        OS information sample dict:
            {
                os: Windows or Linux
                os_version: OS version, Linux
                os_bit: 32 or 64
                os_kernel: Kernel version of OS
            }
        """
        raise NotImplementedError

    def parse_cpu(self):
        """Return a dict with CPU information

        CPU information sample dict:
            {
                cpu_info: Name of cpu
                cpu_cores: How many cores of CPU
            }
        """
        raise NotImplementedError

    def parse_memory(self):
        """Return a dict with Memory information

        NOTE: All memory unit should be bytes by default

        Memory information sample dict:
            {
                memory_info: Memory model
                total_mem: Total memory
                free_mem: Free memory
            }
        """
        raise NotImplementedError

    def parse_disks(self):
        """Return a list of Disk and partition information

        NOTE: All size unit should be bytes by default

        Return sample dict:

            {
                "disks": (list)List of disk dict,
                "partitions": (list)List of partition dict,
                "boot_type": (str)BIOS or UEFI,
                "total_size": (int)Disk total size,
                "count": (int)Total count of disks
            }

        Disk dict smaple:

            {
                "device": (str)Name of disk,
                "size": (int)Total size of disk,
                "vendor": (str)Vendor provider of disk,
                "model": (str)Model of disk
            }

        Partition dict sample:

            {
                "device": (str)Name of partition,
                "size_total": (int)Total size of this partition,
                "size_available": (int)Avaliabe size of this partition,
                "size_available_ratio": (float)Percent of free space,
                "fstype": (str)Filesystem type
            }
        """
        raise NotImplementedError

    def parse_nics(self):
        """Return all network information:

        Return sample of nic:

            {
                "nics": List of nic dict,
                "interface": Default connect interface name,
                "address": Default connect ip address,
                "gateway": Default gateway,
                "macaddress": Default Mac address of interface,
                "netmask": Default netmask,
                "count": Count of all nic
            }

        Nic dict sample:

            {
                "interface": Name of interface,
                "macaddress": Mac of this nic,
                "active": Active or not,
                "mtu": mtu value of this network,
                "speed": speed of this nic,
                "ipv4_address": ipv4 address,
                "ipv4_netmask": netmask,
                "ipv4_broadcast": broadcast address,
                "ipv6_address": ipv6 address
            }
        """
        raise NotImplementedError

    def parse_vt(self):
        """Return a dict with Virtualization features

        Return sample:

            {
                "vt_platform": Virtualzation platform, ex: VMware,
                "vt_platform_ver": Version,
                "features": Dict of VT platform features
            }

        For VMWare platform, the features are:

            {
                "drs": If DRS is enabled,
                "ha": If HA is enabled
            }
        """
        return {
            "vt_platform": self.vt_platform,
            "vt_platform_ver": self.vt_platform_ver
        }

    def _get_disk_total_size(self, disk_info):
        """Common method to calculate disk total size"""
        total_size = 0
        for disk in disk_info:
            logging.debug("Current disk info: %s" % disk)
            total_size = total_size + disk["size"]
        return total_size
