# -*- coding=utf8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2019 OnePro Cloud (Shanghai) Ltd.
#
# Authors: Ray <ray.sun@oneprocloud.com>
#
# Copyright (c) 2019 This file is confidential and proprietary.
# All Rights Resrved, OnePro Cloud (Shanghai) Ltd (http://www.oneprocloud.com).


from collections import OrderedDict
import logging
import re

import humanfriendly

from prophet.controller.analysis.host_base import DEFAULT_NA, HostBase

DISK_REGEX = re.compile(r"^[x]{0,1}[svh]d[a-z]")

VMWARE_DISK_VENDOR = "VMWARE"
KVM_DISK_VENDOR = "QEMU"

VT_VENDORS = [VMWARE_DISK_VENDOR, KVM_DISK_VENDOR]

EFI_MOUNT_POINT = "/boot/efi"

BIOS_BOOT = "bios"
EFI_BOOT = "efi"

# If use agent sync, each mount point avaliable space percent need
# greater than this value
AGENT_SYNC_RATIO = float(0.11 * 100)

NIC_TYPE = "ether"


class LinuxHost(HostBase):

    def __init__(self, payload):
        self.vm_name = None
        self.tcp_ports = None
        self.support_agentless = None
        self.vt_platform = None
        self.vt_platform_ver = None
        super(LinuxHost, self).__init__()

        self._analysis(payload)

    def get_info(self):
        self.host_type = "Physical"
        return super(LinuxHost, self).get_info()

    def _analysis(self, payload):
        if payload["failed"]:
            return False

        for ip, info in payload["success"].items():
            self.conn_ip = ip
            ansible_facts = info["ansible_facts"]
            self.hostname = ansible_facts["ansible_hostname"]

            ansible_default_ipv4 = ansible_facts["ansible_default_ipv4"]
            self.conn_mac = ansible_default_ipv4["macaddress"]

            self.os = ansible_facts["ansible_distribution"]
            self.os_version = ansible_facts["ansible_distribution_version"]
            self.os_bit = ansible_facts["ansible_architecture"]
            self.os_kernel = ansible_facts["ansible_kernel"]

            processors = self._get_cpu_info(
                ansible_facts["ansible_processor"])
            self.cpu_info = ",".join(processors)
            self.cpu_cores = ansible_facts["ansible_processor_vcpus"]
            self.memory_info = ansible_facts["ansible_memory_mb"]
            self.total_mem = ansible_facts["ansible_memtotal_mb"]
            self.free_mem = ansible_facts["ansible_memfree_mb"]

            device_info = ansible_facts["ansible_devices"]
            self._set_disk_info(device_info)

            mount_info = ansible_facts["ansible_mounts"]
            self._set_mount_info(mount_info)

            self._set_interface_info(ansible_facts)

            self._migration_check(ansible_facts)

    def _get_cpu_info(self, processor_info):
        # Data Samples:
        # ['0', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2680 0 @ 2.70GHz',
        #  '1', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2680 0 @ 2.70GHz',
        #  '2', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2680 0 @ 2.70GHz',
        #  '3', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2680 0 @ 2.70GHz']
        start_pos = 2
        count = 3
        processors = processor_info[start_pos::count]
        # Return unique value
        return list(set(processors))

    def _set_disk_info(self, device_info):
        disks = self._get_disks(device_info)
        self.disk_count = len(disks.keys())
        self.disk_total_size = self._get_disk_total_size(disks)
        self.disk_info = self._format_output(disks, key_title="disk")

    def _set_mount_info(self, mount_info):
        """Analysis disk usage and mount information"""
        mounts = {}
        size_used = 0
        boot_type = BIOS_BOOT
        for mount in mount_info:
            logging.debug("Found mount info: %s" % mount)
            mount_point = mount.get("mount", None)

            if self._is_uefi_boot(mount_point):
                boot_type = EFI_BOOT

            device = mount.get("device", None)
            size_total = mount.get("size_total", 0)
            size_available = mount.get("size_available", 0)
            size_used = size_used + (size_total - size_available)
            size_available_ratio = round(
                float(size_available) / float(size_total), 2)
            fstype = mount.get("fstype", None)
            payload = [
                ("device", device),
                ("size_total", size_total),
                ("size_available", size_available),
                ("size_available_ratio", size_available_ratio),
                ("fstype", fstype)
            ]
            mounts[mount_point] = OrderedDict(payload)
        self.boot_type = boot_type
        self.disk_used_size = size_used
        self.partition_info = self._format_output(
            mounts, key_title="mount_point")

    def _set_interface_info(self, ansible_facts):
        interfaces = {}
        interface_info = ansible_facts["ansible_interfaces"]
        for interface in interface_info:
            name = ("ansible_" + interface).replace("-", "_")
            interface_detail = ansible_facts[name]

            interface_type = interface_detail["type"]
            if not interface_type == NIC_TYPE:
                continue

            # Only real nic have pciid
            interface_pciid = interface_detail.get("pciid", None)
            if not interface_pciid:
                continue

            ipv4 = interface_detail.get("ipv4", {})
            payload = [
                ("active", interface_detail.get("active", False)),
                ("macaddress", interface_detail.get("macaddress")),
                ("address", ipv4.get("address")),
                ("netmask", ipv4.get("netmask"))
            ]
            interfaces[interface] = OrderedDict(payload)
        self.nic_info = self._format_output(interfaces,
                                            key_title="interface")

    def _get_disks(self, device_info):
        disks = {}
        for device in device_info:
            removable = device_info[device]["removable"]
            if removable == "1":
                logging.debug("Skip removable device %s" % device)
                continue

            if not DISK_REGEX.match(device):
                logging.debug("Skip non disk device %s" % device)
                continue

            curr_disk_info = device_info[device]
            size = self._get_disk_size(curr_disk_info)
            vendor = self._get_disk_vendor(curr_disk_info)
            disks[device] = OrderedDict()
            disks[device] = {
                "size": size,
                "vendor": vendor
            }
            logging.info("Disk info: %s" % disks)
            if self.vt_platform == DEFAULT_NA:
                if vendor.upper() in VT_VENDORS:
                    self.vt_platform = vendor

        return disks

    def _get_disk_size(self, disk_info):
        return humanfriendly.parse_size(disk_info.get("size", 0)) / 1000000000

    def _get_disk_vendor(self, disk_info):
        return disk_info.get("vendor", None)

    def _get_partitions(self, disk_info):
        """Get disk partitions, not used currently"""
        parts = {}
        part_info = disk_info.get("partitions", {})
        logging.debug("Disk partition info: %s" % part_info)
        for part in part_info:
            parts[part] = {
                "size": humanfriendly.parse_size(
                    part_info[part].get("size", 0)) / 1000000000
            }
        return parts

    def _get_disk_total_size(self, disk_info):
        total_size = 0
        for disk in disk_info:
            total_size = total_size + disk_info[disk]["size"]
        return total_size

    def _is_uefi_boot(self, mount_point):
        return EFI_MOUNT_POINT in mount_point

    def _format_output(self, info, key_title="key", delimiter=","):
        """Convert dict to string output

        The first line will be the title of each field. key_title is
        the field name of the key.
        """
        outputs = []
        title_added = False
        for key, value in info.items():
            if not title_added:
                title_value = delimiter.join(str(v) for v in value.keys())
                outputs.append("%s%s%s" % (key_title,
                                           delimiter,
                                           title_value))
            output_value = delimiter.join(str(v) for v in value.values())
            outputs.append("%s%s%s" % (key, delimiter, output_value))
        return "\n".join(outputs)

    def _migration_check(self, data):
        self.support_full_sync = "Yes"
        self.support_delta_sync = "Yes"
        self.support_agent = "Linux Agent"
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
        if self.os in ["CentOS", "RedHat"]:
            ver_prefix = self.os_version.split(".", 1)[0]
            if ver_prefix < 6:
                self.support_full_sync = "No"
                self.support_delta_sync = "No"
                result = ("Host version %s%s not support migration."
                          % (self.os, self.os_version))
                self.check_result.append(result)
            # Check Xen
            if ver_prefix == 6:
                self.support_delta_sync = "No"
                result = ("Xen not support delta sync after reboot.")
                self.check_result.append(result)
        elif self.os == "SLES":
            self.support_full_sync = "No"
            self.support_delta_sync = "No"
            result = ("Host version %s%s not support migration."
                      % (self.os, self.os_version))
            self.check_result.append(result)
        else:
            self.support_full_sync = "No"
            self.support_delta_sync = "No"
            result = ("Host version %s not support migration."
                      % self.os)
            self.check_result.append(result)

        # Check vgs num
        if "ansible_lvm" in data:
            host_vgs = data["ansible_lvm"]["vgs"].keys()
            if len(host_vgs) > 1:
                self.support_full_sync = "No"
                self.support_delta_sync = "No"
                result = ("Host is lvm and has %s vg, not "
                          "support migration. " % len(host_vgs))
                self.check_result.append(result)

        # Check partition available
        for mount_info in data["ansible_mounts"]:
            if not mount_info["uuid"] or mount_info["uuid"] == "N/A":
                continue
            total = float(mount_info["block_total"])
            used = float(mount_info["block_used"])
            percent = (total - used) / total
            if percent < 0.13:
                self.support_full_sync = "No"
                self.support_delta_sync = "No"
                result = ("Disk %s partition available "
                          "space less than 13%%, migration "
                          "is not supported, please clean "
                          "some data. " % mount_info["mount"])
                self.check_result.append(result)
            # Check file system
            if mount_info["fstype"] == "btrfs":
                self.support_full_sync = "No"
                self.support_delta_sync = "No"
                result = ("Host file system is btrfs, not ",
                          "support migration.")
                self.check_result.append(result)

        if not self.check_result:
            self.check_result = "Check successful."
