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

"""VMware host parser for pyvomi collection"""

import re

from prophet.parser.hosts.base import (BaseHostParser,
                                       VMWARE_DISK_VENDOR,
                                       BIOS_BOOT,
                                       EFI_BOOT)

# Convert all size to Bytes
KB = 1024
MB = 1024 * 1024


class VMwareParser(BaseHostParser):

    def __init__(self, payload):
        super(VMwareParser, self).__init__(payload)

        # Initial host info
        self._host_info = None
        self._host_mac = None

        # Intial esxi info
        self._esxi_info = None
        self._esxi_name = None

        self._pre_parse()

    @property
    def host_ip(self):
        return self._host_info["ipAddress"]

    @property
    def host_mac(self):
        if not self._host_mac:
            for i in sorted(self._host_info["network"].keys()):
                self._host_mac = self._host_info["network"][i]["macAddress"]
                break

        return self._host_mac

    def _pre_parse(self):
        for key, info in self.payload.items():
            self._host_info = info

        for name, info in self._host_info["esxi_host"].items():
            self._esxi_name = name
            self._esxi_info = info["esxi_info"]

    def parse_basic(self):
        return {
            "host_type": "VMware",
            "hostname": self._host_info["hostName"],
            "conn_ip": self.host_ip,
            "conn_mac": self.host_mac
        }

    def parse_os(self):
        """Parser OS from guestFullName

        Sample data:
        guestFullName: Other Linux (64-bit)
        """
        os_name = self._host_info["guestFullName"]

        os = None
        os_bit = None
        matchObj = re.match(r"(.*)\s+\((.*)\)", os_name)
        if matchObj:
            os = matchObj.group(1)
            os_bit = matchObj.group(2)

        if "64" in os_bit:
            os_bit = "64-bit"
        else:
            os_bit = "32-bit"

        return {
            "os": os,
            "os_version": os,
            "os_bit": os_bit
        }

    def parse_cpu(self):
        return {
            "cpu_info": self._esxi_info["cpuModel"],
            "cpu_cores": self._host_info["numCpu"]
        }

    def parse_memory(self):
        return {
            "total_mem": self._host_info["memoryMB"] * MB
        }

    def parse_disks(self):
        disk_info = {}

        disks = []
        for d, info in self._host_info["disks_info"].items():
            disk_size = int(info.get("capacityInKB")) * KB
            disk = {
                "device": info.get("fileName"),
                "size": disk_size
            }
            disks.append(disk)

        return {
            "disks": disks,
            "boot_type": self._get_boot_type(),
            "total_size": self._get_disk_total_size(disks),
            "count": len(disks)
        }

    def _get_boot_type(self):
        boot_type = self._host_info["firmware"].upper()
        if boot_type == BIOS_BOOT:
            return BIOS_BOOT
        else:
            return EFI_BOOT

    def parse_nics(self):

        nics = []
        for id, info in self._host_info["network"].items():
            name = info["deviceName"]
            nic_info = {
                "interface": name,
                "macaddress": info["macAddress"]
            }
            nics.append(nic_info)

        return {
            "nics": nics,
            "address": self.host_ip,
            "macaddress": self.host_mac,
            "count": len(nics)
        }

    def parse_vt(self):
        return {
            "vt_platform": self._esxi_info["licenseProductName"],
            "vt_platform_ver": self._esxi_info["fullName"],
            "vt_esxi": self._esxi_name,
            "vt_cbt": self._host_info["changeTrackingSupported"]
        }
