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

"""Windows host parser for WMI collection

For WMI detailed description document:
https://docs.microsoft.com/en-us/windows/win32/cimwin32prov/win32-provider

Currently we mainly use this class for Windows Parser:

  * Win32_ComputerSystem
  * Win32_OperatingSystem
  * Win32_DiskDrive
  * Win32_DiskPartition
  * Win32_Processor
  * Win32_PhysicalMemory
  * Win32_NetworkAdapterConfiguration
  * Win32_LogicalDisk
"""

import logging

from prophet.parser.hosts.base import (BaseHostParser,
                                       BIOS_BOOT,
                                       EFI_BOOT)


class WindowsParser(BaseHostParser):

    def __init__(self, payload):
        super(WindowsParser, self).__init__(payload)

        # Pre analysis of payload variables
        self._computer_system = None
        self._operating_system = None
        self._disk_drive = None
        self._disk_partition = None
        self._processor = None
        self._physical_memory = None
        self._network_info = None
        self._logical_disk = None
        self._process = None

        # Pre parse payload to save into variables
        self._pre_parse(payload)

    def _pre_parse(self, payload):
        self._computer_system = payload['Win32_ComputerSystem'][0]
        self._operating_system = payload['Win32_OperatingSystem'][0]
        self._processor = payload['Win32_Processor']
        self._physical_memory = payload['Win32_PhysicalMemory'][0]
        self._disk_drives = payload['Win32_DiskDrive']
        self._disk_partition = payload['Win32_DiskPartition']
        self._logical_disk = payload['Win32_LogicalDisk']
        self._network_info = payload['Win32_NetworkAdapterConfiguration']
        self._process = payload['Win32_Process'][0]

    def parse_basic(self):
        hostname = self._computer_system["Name"]

        # Try to get connection ip and mac address
        ipaddress = self._network_info[0]["IPAddress"]
        ips = self._get_value(ipaddress)
        conn_ip = ips[0]
        conn_mac = self._network_info[0]["MACAddress"].lower()

        return {
            "host_type": "Physical",
            "hostname": hostname,
            "conn_ip": conn_ip,
            "conn_mac": conn_mac
        }

    def parse_os(self):
        os = self._operating_system["Name"].split("|")[0].strip()
        os_bit = self._operating_system["OSArchitecture"]
        os_kernel = self._operating_system["Version"]

        return {
            "os": os,
            "os_version": os,
            "os_bit": os_bit,
            "os_kernel": os_kernel
        }

    def parse_cpu(self):
        cpu_info = self._processor[0]["Name"]
        cpu_cores = 0
        for proc in self._processor:
            cpu_cores += int(proc["NumberOfCores"])

        return {
            "cpu_info": cpu_info,
            "cpu_cores": cpu_cores
        }

    def parse_memory(self):
        memory_info = self._physical_memory["Caption"]
        total_mem = int(self._computer_system["TotalPhysicalMemory"])
        free_mem = int(self._operating_system["FreePhysicalMemory"])
        return {
            "memory_info": memory_info,
            "total_mem": total_mem,
            "free_mem": free_mem
        }

    def parse_disks(self):
        """Parse disk detailed

        Sample Data:
        Win32_DiskDrive:
          - Availability: '0'
            BytesPerSector: '512'
            Capabilities: (3,4)
            CapabilityDescriptions: (Random Access,Supports Writing)
            Caption: VMware Virtual disk SCSI Disk Device
            CompressionMethod: (null)
            ConfigManagerErrorCode: '0'
            ConfigManagerUserConfig: 'False'
            CreationClassName: Win32_DiskDrive
            DefaultBlockSize: '0'
            Description: "\u78C1\u76D8\u9A71\u52A8\u5668"
            DeviceID: \\.\PHYSICALDRIVE0
            ErrorCleared: 'False'
            ErrorDescription: (null)
            ErrorMethodology: (null)
            FirmwareRevision: '1.0 '
            Index: '0'
            InstallDate: (null)
            InterfaceType: SCSI
            LastErrorCode: '0'
            Manufacturer: "(\u6807\u51C6\u78C1\u76D8\u9A71\u52A8\u5668)"
            MaxBlockSize: '0'
            MaxMediaSize: '0'
            MediaLoaded: 'True'
            MediaType: Fixed hard disk media
            MinBlockSize: '0'
            Model: VMware Virtual disk SCSI Disk Device
            Name: \\.\PHYSICALDRIVE0
            NeedsCleaning: 'False'
            NumberOfMediaSupported: '0'
            PNPDeviceID: SCSI\DISK&VEN_VMWARE&PROD_VIRTUAL_DISK\5&1982005&0&000000
            Partitions: '2'
            PowerManagementCapabilities: 'NULL'
            PowerManagementSupported: 'False'
            SCSIBus: '0'
            SCSILogicalUnit: '0'
            SCSIPort: '2'
            SCSITargetId: '0'
            SectorsPerTrack: '63'
            SerialNumber: (null)
            Signature: '2165710240'
            Size: '53686402560'
            Status: OK
            StatusInfo: '0'
            SystemCreationClassName: Win32_ComputerSystem
            SystemName: COMPUTER-PC
            TotalCylinders: '6527'
            TotalHeads: '255'
            TotalSectors: '104856255'
            TotalTracks: '1664385'
            TracksPerCylinder: '255'
        """
        disk_info = {}

        # Get disks
        disks = []
        for drive in self._disk_drives:
            disk = {
                "device": drive.get("Index"),
                "size": int(drive.get("Size")),
                "vendor": drive.get("Caption"),
                "model": drive.get("Model")
            }
            disks.append(disk)

        partitions = self._get_disk_partitions()
        boot_type = self._get_boot_type()

        return {
            "disks": disks,
            "partitions": partitions,
            "boot_type": boot_type,
            "total_size": self._get_disk_total_size(disks),
            "count": len(disks)
        }

    def _get_disk_partitions(self):
        """Get disk partitions

           Sample Win32_DiskPartition Data:
             Access: '0'
             Availability: '0'
             BlockSize: '512'
             BootPartition: 'True'
             Bootable: 'True'
             Caption: 'Disk #0, Partition #0'
             ConfigManagerErrorCode: '0'
             ConfigManagerUserConfig: 'False'
             CreationClassName: Win32_DiskPartition
             Description: Installable File System
             DeviceID: 'Disk #0, Partition #0'
             DiskIndex: '0'
             ErrorCleared: 'False'
             ErrorDescription: (null)
             ErrorMethodology: (null)
             HiddenSectors: '0'
             Index: '0'
             InstallDate: (null)
             LastErrorCode: '0'
             Name: 'Disk #0, Partition #0'
             NumberOfBlocks: '204800'
             PNPDeviceID: (null)
             PowerManagementCapabilities: 'NULL'
             PowerManagementSupported: 'False'
             PrimaryPartition: 'True'
             Purpose: (null)
             RewritePartition: 'False'
             Size: '104857600'
             StartingOffset: '1048576'
             Status: (null)
             StatusInfo: '0'
             SystemCreationClassName: Win32_ComputerSystem
             SystemName: COMPUTER-PC
             Type: Installable File System
        """
        partitions = []
        for part in self._logical_disk:
            size_total = int(part.get("Size", 0))
            size_available = int(part.get("FreeSpace", 0))
            size_used = size_total - size_available
            size_available_ratio = round(
                float(size_available) / float(size_total), 2)
            part_info = {
                "device": part["DeviceID"],
                "size_total": size_total,
                "size_available": size_available,
                "size_available_ratio": size_available_ratio,
                "fstype": part["FileSystem"]
            }
            partitions.append(part_info)

        return partitions

    def _get_boot_type(self):
        """Get boot type from Win32_DiskPartition"""
        boot_type = BIOS_BOOT

        for part in self._disk_partition:
            if "GPT" in part["Type"] and part["Bootable"] == "True":
                boot_type = EFI_BOOT
                break

        return boot_type

    def parse_nics(self):
        """Parse each nic based on Win32_NetworkAdaptorConfiguration

        Sample Win32_NetworkAdaptorConfiguration:
          - ArpAlwaysSourceRoute: 'False'
            ArpUseEtherSNAP: 'False'
            Caption: '[00000007] Intel(R) PRO/1000 MT Network Connection'
            DHCPEnabled: 'False'
            DHCPLeaseExpires: (null)
            DHCPLeaseObtained: (null)
            DHCPServer: (null)
            DNSDomain: (null)
            DNSDomainSuffixSearchOrder: ()
            DNSEnabledForWINSResolution: 'False'
            DNSHostName: computer-PC
            DNSServerSearchOrder: (114.114.114.114)
            DatabasePath: '%SystemRoot%\System32\drivers\etc'
            DeadGWDetectEnabled: 'False'
            DefaultIPGateway: (192.168.10.1)
            DefaultTOS: '0'
            DefaultTTL: '0'
            Description: Intel(R) PRO/1000 MT Network Connection
            DomainDNSRegistrationEnabled: 'False'
            ForwardBufferMemory: '0'
            FullDNSRegistrationEnabled: 'True'
            GatewayCostMetric: (256)
            IGMPLevel: '0'
            IPAddress: (192.168.10.62,fe80::7dc4:c6d7:3df:a639)
            IPConnectionMetric: '10'
            IPEnabled: 'True'
            IPFilterSecurityEnabled: 'False'
            IPPortSecurityEnabled: 'False'
            IPSecPermitIPProtocols: ()
            IPSecPermitTCPPorts: ()
            IPSecPermitUDPPorts: ()
            IPSubnet: (255.255.255.0,64)
            IPUseZeroBroadcast: 'False'
            IPXAddress: (null)
            IPXEnabled: 'False'
            IPXFrameType: 'NULL'
            IPXMediaType: '0'
            IPXNetworkNumber: 'NULL'
            IPXVirtualNetNumber: (null)
            Index: '7'
            InterfaceIndex: '11'
            KeepAliveInterval: '0'
            KeepAliveTime: '0'
            MACAddress: 00:0C:29:9A:59:73
            MTU: '0'
            NumForwardPackets: '0'
            PMTUBHDetectEnabled: 'False'
            PMTUDiscoveryEnabled: 'False'
            ServiceName: E1G60
            SettingID: '{D918B103-2484-4B8F-910F-19FC08C014EA}'
            TcpMaxConnectRetransmissions: '0'
            TcpMaxDataRetransmissions: '0'
            TcpNumConnections: '0'
            TcpUseRFC1122UrgentPointer: 'False'
            TcpWindowSize: '0'
            TcpipNetbiosOptions: '0'
            WINSEnableLMHostsLookup: 'True'
            WINSHostLookupFile: (null)
            WINSPrimaryServer: (null)
            WINSScopeID: ''
            WINSSecondaryServer: (null)
        """
        default_ipv4 = None
        default_mac = None
        default_gateway = None
        default_netmask = None

        nics = []
        for index, net in enumerate(self._network_info):
            name = net["Caption"]
            address = self._get_value(net["IPAddress"])[0]
            netmask = self._get_value(net["IPSubnet"])[0]
            gateway = self._get_value(net["DefaultIPGateway"])[0]
            macaddress = net["MACAddress"].lower()

            if index == 0:
                default_name = name
                default_ipv4 = address
                default_mac = macaddress
                default_gateway = gateway
                default_netmask = netmask

            nic_info = {
                "interface": name,
                "macaddress": macaddress,
                "gateway": gateway,
                "ipv4_address": address,
                "ipv4_netmask": netmask
            }

            nics.append(nic_info)

        return {
            "nics": nics,
            "address": default_ipv4,
            "gateway": default_gateway,
            "macaddress": default_mac,
            "netmask": default_netmask,
            "count": len(nics),
        }

    def _get_value(self, value, separator=","):
        """Remove () and return values in list if multiple

        In WMI returns, multiple values would be:

          IPAddress: (192.168.10.62,fe80::7dc4:c6d7:3df:a639)

        Return list:

          ['192.168.10.62', 'fe80::7dc4:c6d7:3df:a639']
        """
        if "(" in value and ")" in value:
            return value.strip("(").strip(")").split(separator)
        else:
            return value
