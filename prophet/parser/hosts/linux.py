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

"""Linux host parser for ansible collection"""


import logging
import re

import humanfriendly

from prophet.parser.hosts.base import (BaseHostParser,
                                       BIOS_BOOT,
                                       EFI_BOOT,
                                       LINUX_EFI_MOUNT_POINT,
                                       VMWARE_DISK_VENDOR,
                                       KVM_DISK_VENDOR,
                                       VT_VENDORS)

# Regular expression for disk
DISK_REGEX = re.compile(r"^[x]{0,1}[svh]d[a-z]")

# Linux NIC type
NIC_TYPE = "ether"


class LinuxParser(BaseHostParser):

    def __init__(self, payload):
        super(LinuxParser, self).__init__(payload)

        self._conn_ip = None
        self._host_info = None

        self._pre_parse()

    def _pre_parse(self):
        """Save success part to a new dict"""
        if self.payload["failed"]:
            raise Exception("Invalid collection data")

        for ip, info in self.payload["success"].items():
            self._conn_ip = ip
            self._host_info = info["ansible_facts"]
            break

    def parse_basic(self):
        default_ipv4 = self._host_info["ansible_default_ipv4"]
        return {
            "host_type": "Physical",
            "hostname": self._host_info["ansible_hostname"],
            "conn_ip": self._conn_ip,
            "conn_mac": default_ipv4["macaddress"]
        }

    def parse_os(self):
        return {
            "os": self._host_info["ansible_distribution"],
            "os_version": self._host_info["ansible_distribution_version"],
            "os_bit": self._host_info["ansible_architecture"],
            "os_kernel": self._host_info["ansible_kernel"]
        }

    def parse_cpu(self):
        processors = self._get_cpu_info(self._host_info["ansible_processor"])
        return {
            "cpu_info": ",".join(processors),
            "cpu_cores": self._host_info["ansible_processor_vcpus"]
        }

    def _get_cpu_info(self, processor_info):
        """Get cpu info, and return unique value

        In ansible returns, each core processers will be return like this:

            ['0', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2680 0 @ 2.70GHz',
             '1', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2680 0 @ 2.70GHz',
             '2', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2680 0 @ 2.70GHz',
             '3', 'GenuineIntel', 'Intel(R) Xeon(R) CPU E5-2680 0 @ 2.70GHz']

        We parse these data and return unique names of CPU
        """
        # Data Samples:
        start_pos = 2
        count = 3
        processors = processor_info[start_pos::count]
        # Return unique value
        return list(set(processors))

    def parse_memory(self):
        return {
            "memory_info": None,
            "total_mem": int(self._host_info["ansible_memtotal_mb"]) * 1024,
            "free_mem": int(self._host_info["ansible_memfree_mb"]) * 1024
        }

    def parse_disks(self):
        """Parse ansible returns disk information

        Sample data of disk part:
          sdb:
             holders:
             - ceph--pool-osd0.wal
             .......
             host: 'Serial Attached SCSI controller: LSI Logic / Symbios Logic SAS3008
               PCI-Express Fusion-MPT SAS-3 (rev 02)'
             links:
               ids:
               - ata-INTEL_SSDSC2BB240G7_PHDV722200U0240AGN
               - lvm-pv-uuid-x5ZHTc-gqck-3BCF-7qty-U9gE-y3rf-tpRdrG
               - wwn-0x55cd2e414e06a6df
               labels: []
               masters:
               - dm-1
               ......
               uuids: []
             model: INTEL SSDSC2BB24
             partitions: {}
             removable: '0'
             rotational: '0'
             sas_address: '0x4433221100000000'
             sas_device_handle: '0x0009'
             scheduler_mode: deadline
             sectors: '468862128'
             sectorsize: '512'
             size: 223.57 GB
             support_discard: '512'
             vendor: ATA
             virtual: 1
             wwn: '0x55cd2e414e06a6df'
        """
        device_info = self._host_info["ansible_devices"]
        disks = self._get_disks(device_info)

        mount_info = self._host_info["ansible_mounts"]
        partitions, boot_type = self._get_mounts(mount_info)

        return {
            "disks": disks,
            "partitions": partitions,
            "boot_type": boot_type,
            "total_size": self._get_disk_total_size(disks),
            "count": len(disks)
        }

    def _get_disks(self, device_info):
        disks = []
        for device in device_info:
            disk = {}
            logging.debug("Current device is %s" % device)
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
            model = self._get_disk_model(curr_disk_info)
            disk = {
                "device": device,
                "size": size,
                "vendor": vendor,
                "model": model
            }
            disks.append(disk)

            # Try to analysis VT type from disk vendor
            self._get_vt(vendor)

        logging.info("Parsed disk info: %s" % disks)
        return disks

    def _get_vt(self, vendor):
        """Try to get virtualization platform from Disk type"""
        if not self.vt_platform:
            if vendor.upper() in VT_VENDORS:
                self.vt_platform = vendor

    def _get_mounts(self, mount_info):
        """Analysis disk usage and mount information"""
        mounts = []
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
            partitions = {
                "device": device,
                "size_total": size_total,
                "size_available": size_available,
                "size_available_ratio": size_available_ratio,
                "fstype": fstype
            }
            mounts.append(partitions)
        return mounts, boot_type

    def _get_disk_size(self, disk_info):
        return humanfriendly.parse_size(disk_info.get("size", 0))

    def _get_disk_vendor(self, disk_info):
        return disk_info.get("vendor", None)

    def _get_disk_model(self, disk_info):
        """Return disk model, we can know disk type from this attribute"""
        return disk_info.get("model", None)

    def _get_partitions(self, disk_info):
        """Get disk partitions, not used currently"""
        parts = {}
        part_info = disk_info.get("partitions", {})
        logging.debug("Disk partition info: %s" % part_info)
        for part in part_info:
            parts[part] = {
                "size": humanfriendly.parse_size(
                    part_info[part].get("size", 0))
            }
        return parts

    def _get_disk_total_size(self, disk_info):
        total_size = 0
        for disk in disk_info:
            logging.debug("Current disk info: %s" % disk)
            total_size = total_size + disk["size"]
        return total_size

    def _is_uefi_boot(self, mount_point):
        return LINUX_EFI_MOUNT_POINT in mount_point

    def parse_nics(self):
        """Parse network related information

           Sample ansbile data:
           ansible_default_ipv4:
               address: 192.168.10.203
               alias: ens2f0
               broadcast: 192.168.10.255
               gateway: 192.168.10.1
               interface: ens2f0
               macaddress: ac:1f:6b:25:b4:28
               mtu: 1500
               netmask: 255.255.255.0
               network: 192.168.10.0
               type: ether
        """
        default_ipv4 = self._host_info["ansible_default_ipv4"]
        interface_name = default_ipv4.get("interface")
        gateway = default_ipv4.get("gateway")
        ipv4_gateway = {interface_name: gateway}
        nics = self._get_nics(ipv4_gateway)
        return {
            "nics": nics,
            "interface": interface_name,
            "address": default_ipv4.get("address"),
            "gateway": gateway,
            "macaddress": default_ipv4.get("macaddress"),
            "netmask": default_ipv4.get("netmask"),
            "count": len(nics)
        }

    def _get_nics(self, ipv4_gateway=None):
        """Return a list with all nics on this host

        Ansible returns sample data:
        ansible_eno1:
          active: true
          device: eno1
          features:
            busy_poll: off [fixed]
            fcoe_mtu: off [fixed]
            generic_receive_offload: 'on'
            ......
          hw_timestamp_filters:
          - none
          - ptp_v1_l4_sync
          - ptp_v1_l4_delay_req
          - ptp_v2_event
          ipv4:
            address: 10.0.100.201
            broadcast: 10.0.100.255
            netmask: 255.255.255.0
            network: 10.0.100.0
          ipv6:
          - address: fe80::ec4:7aff:fea5:293a
            prefix: '64'
            scope: link
          macaddress: 0c:c4:7a:a5:29:3a
          module: ixgbe
          mtu: 1500
          pciid: '0000:02:00.0'
          phc_index: 4
          promisc: false
          speed: 10000
          timestamping:
          - tx_hardware
          ......
          type: ether
        """
        nics = []

        interface_info = self._host_info["ansible_interfaces"]
        for interface in interface_info:
            nic_info = {}
            name = ("ansible_" + interface).replace("-", "_")

            interface_detail = self._host_info[name]
            interface_type = interface_detail["type"]
            if not interface_type == NIC_TYPE:
                continue

            # Only real nic have pciid
            interface_pciid = interface_detail.get("pciid", None)
            if not interface_pciid:
                continue

            ipv4 = interface_detail.get("ipv4", {})
            nic_info = {
                "interface": interface,
                "macaddress": interface_detail.get("macaddress", None),
                "active": interface_detail.get("active", False),
                "mtu": interface_detail.get("mtu", None),
                "speed": interface_detail.get("speed", None),
                "ipv4_address": ipv4.get("address"),
                "ipv4_netmask": ipv4.get("netmask"),
                "ipv4_network": ipv4.get("network"),
                "ipv4_broadcast": ipv4.get("broadcast"),
            }

            # if this is gateway interface, also save gateway
            if ipv4_gateway.get(interface, None):
                nic_info["gateway"] = ipv4_gateway[interface]

            ipv6 = interface_detail.get("ipv6", [])
            if ipv6:
                address = ipv6[0]["address"]
                logging.info("Get %s ipv6 address: %s" % (name, address))
                nic_info["ipv6_address"] = address
                nics.append(nic_info)

        return nics

    def parse_vt(self):
        return {
            "vt_platform": self.vt_platform,
            "vt_platform_ver": None
        }
