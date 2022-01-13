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

"""Collect VMware ESXi and VMs information using VMware lib

 Steps:

     1. Test VMwarer connections.
     2. Get VCenter manager host info.
     3. Get all esxi host info.
     4. Get all vms info for esxi.
     5. Store information to config file for each virtual machine.

"""


import atexit
import logging
import os
import sys
import telnetlib
import uuid
import yaml

from pyVim import connect
from pyVmomi import vmodl
from pyVmomi import vim

#from prophet.controller.config_file import ConfigFile, CsvDataFile
from prophet.collector.base import BaseHostCollector

# default port for vmware connection
DEFAULT_PORT = 443


class VMwareCollector(BaseHostCollector):

    def __init__(self, ip, username, password, ssh_port, key_path,
                 output_path, os_type, **kwargs):

        super(VMwareCollector, self).__init__(
                ip, username, password, ssh_port, key_path,
                output_path, os_type, disable_ssl_verification=True,
                **kwargs)

        if not self.ssh_port:
            self.ssh_port = DEFAULT_PORT

        self._content = None

        # Dict to save different resources
        self._esxis_info = {}
        self._vms_info = {}
        self._vc_info = {}

        # Generate report for vCenter collection
        self.success_vcs = []
        self.failed_vcs = []

        # Generate report for ESXi collection
        self.success_esxis = []
        self.failed_esxis = []

        # Generate report for VM collection
        self.success_vms = []
        self.failed_vms = []

        # Report summary
        self._summary = {
            "info": [],
            "debug": []
        }

    def collect(self):
        """Get all VMware related information

        If the specify ip is vCenter, first get vCenter information,
        then get exsi later. If it's only esxi, then just save the
        esxi information.

        After that get all VMs and save to files.
        """

        # Try to connect to server first
        self.connect()

        vmware_info = {}
        server_type = "exsi"

        # Get ESXi information
        self._get_esxi_info()

        # If the given address is vCenter, also get vCenter infromation
        if self._content.about.name == "VMware vCenter Server":
            server_type = "vcenter"
            self._get_vcenter_info()
            self._vc_info[self.ip]["esxi"] = self._esxis_info
            vmware_info = self._vc_info
        else:
            vmware_info = self._esxis_info

        filename = "%s_%s.yaml" % (self.ip, server_type)
        yamlfile = os.path.join(self.base_path, filename)
        self.save_to_yaml(yamlfile, vmware_info)

        # Begin to collect all VMs
        self._get_vms_info()

    def connect(self):
        """Connect to vCenter or ESXi"""

        # Check connect first
        self._check_connect()

        logging.debug("Start connect [%s] vmware host with port [%s],"
                      "username [%s], password [%s]..."
                      % (self.ip, self.ssh_port,
                         self.username, self.password))
        logging.info("Start connect %s vmware host..." % self.ip)
        if self.disable_ssl_verification:
            service_instance = connect.SmartConnectNoSSL(
                host=self.ip,
                user=self.username,
                pwd=self.password,
                port=int(self.ssh_port))
        else:
            service_instance = connect.SmartConnect(
                host=self.ip,
                user=self.username,
                pwd=self.password,
                port=int(self.ssh_port))
        atexit.register(connect.Disconnect, service_instance)
        logging.info("Connect %s vmware host sucessful." % self.ip)
        self._content = service_instance.RetrieveContent()

    def _check_connect(self):
        try:
            logging.info("Check %s:%s host network..."
                         % (self.ip, self.ssh_port))
            telnetlib.Telnet(self.ip, port=self.ssh_port, timeout=5)
        except Exception as error:
            logging.error("Check %s:%s failed, due to %s"
                          % (self.ip, self.ssh_port, error))
            sys.exit()
        else:
            logging.info("Host %s:%s check successful."
                         % (self.ip, self.ssh_port))


    def _get_content_obj(self, content, viewtype, name=None):
        recursive = True
        containerView = content.viewManager.CreateContainerView(
            content.rootFolder, viewtype, recursive)
        return [view for view in containerView.view]

    def _get_vcenter_info(self):
        logging.info(
                "Trying to get "
                "VMware vCenter %s info..." % self.ip)
        try:
            self._vc_info[self.ip] = {
                "name": getattr(self._content, "about.name", ""),
                "fullName": getattr(self._content, "about.fullName", ""),
                "vendor": getattr(self._content, "about.vendor", ""),
                "version": getattr(self._content, "about.version", ""),
                "build": getattr(self._content, "about.build", ""),
                "localeVersion": getattr(
                    self._content, "about.localeVersion", ""),
                "localeBuild": getattr(
                    self._content, "about.localeBuild", ""),
                "osType": getattr(self._content, "about.osType", ""),
                "productLineId": getattr(
                    self._content, "about.productLineId", ""),
                "apiType": getattr(self._content, "about.apiType", ""),
                "apiVersion": getattr(
                    self._content, "about.apiVersion", ""),
                "instanceUuid": getattr(
                    self._content, "about.instanceUuid", ""),
                "licenseProductName": getattr(
                    self._content, "about.licenseProductName", ""),
                "licenseProductVersion": getattr(
                    self._content, "about.licenseProductVersion", "")
            }
            self.success_vcs.append(self.ip)
        except Exception as e:
            logging.error(
                    "Failed to get vCenter %s "
                    "information, due to:" % self.ip)
            logging.exception(e)
            self.failed_vcs.append(self.ip)
            return

        logging.info(
                "Success to get VMWare vCenter "
                "%s info succesfully: %s" % (
                    self.ip, self._vc_info))

    def get_summary(self):
        logging.info("Get summary detailed for collection")
        self._generate_summary(
                "vCenter", self.success_vcs, self.failed_vcs)
        self._generate_summary(
                "ESXi", self.success_esxis, self.failed_esxis)
        self._generate_summary(
                "VM", self.success_vms, self.failed_vms)

        return self._summary

    def _generate_summary(self, item_name, success_items, failed_items):
        logging.debug("Generate summary for %s" % item_name)
        if success_items or failed_items:
            result = "%s Collection Result: Success %s, Failed %s." % (
                    item_name, len(success_items), len(failed_items))
            self._summary["info"].append(result)

            if len(failed_items) > 0:
                failed_result = "Failed %s: %s" % (
                        item_name, ",".join(failed_items))
                self._summary["info"].append(failed_result)

            if len(success_items) > 0:
                success_result = "Success %s: %s" % (
                        item_name, ",".join(success_items))
                self._summary["debug"].append(success_result)

    def _get_vm_datastore_info(self, vm):
        datastore_info = {}

        logging.info("Trying to get VM %s datastore..." % (
            vm.config.name))
        for dsurl in vm.config.datastoreUrl:
            logging.info("Current datastore: %s" % dsurl)
            datastore_name = dsurl.name
            datastore_info[datastore_name] = {
                "url": dsurl.url
            }
            #self._vms_info[vmid]["datastoreurl"] = {datastore_name: {}}
            #self._vms_info[vmid]["datastoreurl"][datastore_name]["url"] = dsurl.url
        #disks_info = self._get_vm_disk_info(vm)
        #self._vms_info[vmid]["disks_info"] = disks_info
        logging.info("Success to get VM %s datastore: %s" % (
            vm.config.name, datastore_info))

        return datastore_info

    def _get_vm_disks_info(self, vm):
        disk_info = {}
        vdisk_types = [
            vim.VirtualDiskFlatVer1BackingInfo,
            vim.VirtualDiskFlatVer2BackingInfo,
            vim.VirtualDiskSparseVer1BackingInfo,
            vim.VirtualDiskSparseVer2BackingInfo,
            vim.VirtualDiskRawDiskMappingVer1BackingInfo,
        ]
        logging.info("Trying to get %s vm "
                     "disk info..." % vm.config.name)
        for dev in vm.config.hardware.device:
            logging.info("Current disk is %s" % dev)

            # skip if not VirtualDisk
            if not isinstance(dev, vim.VirtualDisk):
                logging.warn("Current disk is not "
                             "instance of VirtualDisk")
                continue

            back_info = dev.backing
            if not isinstance(back_info,
                              vim.VirtualDeviceFileBackingInfo):
                result = "non-file backing virtual disk exists"
                logging.warning(result)
                disk_info["backing"] = result
                continue
            # Query if disks in virtual types
            if not any(map(lambda ty: isinstance(
                back_info, ty), vdisk_types)):
                result = ("Unsuported backing type: %s"
                          % back_info.__name__)
                disk_info["backing"] = result
                continue

            disk_info[dev.backing.uuid] = {
                "capacityInKB": dev.capacityInKB,
                "fileName":  dev.backing.fileName,
                "diskMode":  dev.backing.diskMode,
                "thinProvisioned": getattr(
                    dev.backing, "thinProvisioned", False),
                "contentId":  dev.backing.contentId,
                "changeId": dev.backing.changeId,
                "deltaDiskFormat": getattr(
                    dev.backing, "deltaDiskFormat", False)
            }

        logging.info("Success to get %s disk "
                     "info: %s" % (vm.config.name, disk_info))

        return disk_info

    def _get_vm_network_info(self, vm):
        network_info = {}
        logging.info("Start to get %s "
                     "network info." % vm.config.name)
        logging.debug("vm.config.hardware."
                      "device = %s" % vm.config.hardware.device)

        for dev in vm.config.hardware.device:

            # NOTE(Ray): This code is copied from hamal
            if not isinstance(dev, vim.vm.device.VirtualEthernetCard):
                continue
            logging.debug("Found network device: %s" % dev)
            # if device.baking is not VirtualDeviceNetworkBackingInfo
            # means the vm has no network attribute
            nt_uuid = uuid.uuid1().hex
            network_info[nt_uuid] = {}

            addr = ""
            if isinstance(
                    dev.backing,
                    vim.VirtualEthernetCardNetworkBackingInfo):
                addr = getattr(
                        dev.backing, "network.summary.ipPoolId", None)

            logging.info("Current dev.backing is: %s" % dev.backing)
            device_name = getattr(
                    dev.backing, "deviceName", None)
            # if contains distribution network
            if isinstance(
                    dev.backing,
                    vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo):
                device_name = getattr(
                        dev.backing.port, "portgroupKey", None)

            network_info[nt_uuid] = {
                "macAddress": dev.macAddress,
                "deviceName": device_name,
                "ipPoolId": addr
            }
            logging.debug("Get %s vm network %s info."
                          % (vm.config.name, network_info))

        logging.info("Get %s vm all nets info successful." % vm.config.name)
        return network_info

    def _get_vms_info(self):
        logging.info("Trying to get VMs detail...")

        esxi_obj = self._get_content_obj(
                self._content, [vim.HostSystem])
        cluster_obj = self._get_content_obj(
                self._content, [vim.ClusterComputeResource])
        vms_obj = self._get_content_obj(
                self._content, [vim.VirtualMachine])
        logging.debug("VMs object: %s" % vms_obj)

        logging.info("Trying to get VMs total "
                     "count is %s" % len(vms_obj))
        for vm in vms_obj:
            vms_info = {}
            vm_name = None

            logging.info("Current vm object is %s" % vm)
            # NOTE(Ray): vm.config is very important when we try to
            # get data, we found some fields is missing in some env.
            # So we log this object into log file for further analysis
            logging.info("VM config object is: %s" % vm.config)

            try:
                # NOTE(Ray): Normally instanceUuid should be
                # exsits in vm.config, but we found in some real
                # env, it's not true. To work around, we get this
                # value from vm.config.summary
                # To use vim-cmd vmsvc/getallvms to search the id, return
                # Invalid VM 'id', so we no need to care about this kind
                # of situation, just skip it
                vmid = getattr(vm.config, "instanceUuid", getattr(
                    vm.config, "summary.instanceUuid", None))
                vm_name = getattr(vm.config, "name", vmid)

                vm_host = vm.summary.runtime.host

                logging.info("Trying to get VM %s info..." % vm_name)

                if vm_host in esxi_obj:
                    vms_info[vmid] = self._get_vm_info(
                            esxi_obj, cluster_obj, vm)
                else:
                    logging.warn(
                            "Skip to get VM %s info, due to VM "
                            "is in ESXi host %s" % (vm_name, vm_host))

                logging.info(
                        "Success to get VM %s info" % vm_name)

                filename = "%s_%s.yaml" % (vm.config.name, "vmware")
                yamlfile = os.path.join(self.base_path, filename)
                # NOTE(Ray): The tcp ports is the ports open on VMware
                # vCenter or ESXi, so we don't need to add tcp ports
                # For further development, we may read tcp ports from
                # our scan results to get tcp ports for VMs
                save_values = {
                    self.root_key: {
                        "results": vms_info,
                        "os_type": self.os_type,
                        "tcp_ports": None
                    }
                }
                self.save_to_yaml(yamlfile, save_values)

                self.success_vms.append(vm_name)
            except Exception as e:
                self.failed_vms.append(vm_name)
                logging.warn("Skip to get VM %s info, due to:")
                logging.exception(e)


    def _get_vm_info(self, esxi_obj, cluster_obj, vm):
        """Get VM summary information"""
        vm_info = {}
        drs = False
        ha = False

        obj_index = esxi_obj.index(vm.summary.runtime.host)
        esxi_host = esxi_obj[obj_index].name

        ha, drs = self._is_ha_drs_enabled(cluster_obj)

        vm_info = {
            "esxi_host": {esxi_host: self._esxis_info[esxi_host]},
            "name": vm.config.name,
            "memoryMB": vm.config.hardware.memoryMB,
            "numCpu": vm.config.hardware.numCPU,
            "numCoresPerSocket": vm.config.hardware.numCoresPerSocket,
            "numEthernetCards": vm.summary.config.numEthernetCards,
            "powerState": vm.runtime.powerState,
            "numVirtualDisks": vm.summary.config.numVirtualDisks,
            "uuid": vm.config.uuid,
            "locationId": vm.config.locationId,
            "guestId": vm.config.guestId,
            "guestFullName": vm.config.guestFullName,
            "version": vm.config.version,
            "firmware": vm.config.firmware,
            "vmPathName": vm.config.files.vmPathName,
            "toolsStatus": vm.summary.guest.toolsStatus,
            "ipAddress": vm.summary.guest.ipAddress,
            "hostName": vm.summary.guest.hostName,
            "toolsVersion": vm.config.tools.toolsVersion,
            "snapshotDirectory": vm.config.files.snapshotDirectory,
            "suspendDirectory": vm.config.files.suspendDirectory,
            "logDirectory": vm.config.files.logDirectory,
            "changeTrackingSupported": vm.capability.changeTrackingSupported,
            "network": self._get_vm_network_info(vm),
            "datastoreurl": self._get_vm_datastore_info(vm),
            "disks_info": self._get_vm_disks_info(vm),
            "ha": ha,
            "drs": drs
        }

        return vm_info

    def _is_ha_drs_enabled(self, cluster_obj):
        # TODO(Ray): Check if HA or DRS is enable, but seems it's not
        # correct if there are multiple clusters, need to double check
        # this logical
        ha = False
        drs = False

        logging.info("Checking if cluster HA or DRS is enabled...")
        for c in cluster_obj:
            logging.info("Current cluster detailed: %s" % c)
            if hasattr(c, "configuration"):
                if c.configuration.drsConfig.enabled:
                    drs = True
                if c.configuration.dasConfig.enabled:
                    ha = True
                break
        logging.info("HA enable is %s, DRS enable is %s" % (ha, drs))
        return ha, drs

    def _get_esxi_info(self):
        """Get ESXi information"""

        esxi_obj = self._get_content_obj(self._content,
                                         [vim.HostSystem])

        logging.info("Trying to get ESXi info...")
        for esxi in esxi_obj:
            try:
                logging.info("Trying to get ESXi %s "
                             "info: %s" % (esxi.name, esxi))

                self._esxis_info[esxi.name] = {
                    "esxi_info": self._get_esxi_summary(esxi),
                    "datastore": self._get_esxi_datastore_info(esxi),
                    "network": self._get_esxi_network_info(esxi)
                }
                self.success_esxis.append(esxi.name)
            except Exception as e:
                logging.info("Failed to get ESXi %s" % esxi.name)
                logging.exception(e)
                self.failed_esxis.append(esxi.name)

        logging.info("Get %s esxis host info successful." % esxi.name)

    def _get_esxi_summary(self, esxi):
        summary = esxi.summary
        logging.info("Trying to get ESXi %s "
                     "summary %s..." % (esxi.name, summary))

        esxi_info = {
            "vendor": summary.hardware.vendor,
            "model" : summary.hardware.model,
            "port" : summary.config.port,
            "fullName" : summary.config.product.fullName,
            "version" : summary.config.product.version,
            "build" : summary.config.product.build,
            "osType" : summary.config.product.osType,
            "licenseProductName" : summary.config.product.licenseProductName,
            "licenseProductVersion" : summary.config.product.licenseProductVersion,
            "MemorySize" : summary.hardware.memorySize / 1024 / 1024,
            "cpuModel" : summary.hardware.cpuModel,
            "cpuMhz" : summary.hardware.cpuMhz,
            "numCpuPkgs" : summary.hardware.numCpuPkgs,
            "numCpuCores" : summary.hardware.numCpuCores,
            "numCpuThreads" : summary.hardware.numCpuThreads,
            "numNics" : summary.hardware.numNics,
            "numHBAs" : summary.hardware.numHBAs
        }

        for i in esxi.summary.hardware.otherIdentifyingInfo:
            if isinstance(i, vim.host.SystemIdentificationInfo):
                esxi_info["SN"] = i.identifierValue

        logging.info("Success to get ESXi %s "
                     "summary: %s" % (esxi.name, esxi_info))

        return esxi_info

    def _get_esxi_network_info(self, esxi):
        logging.info("Trying to get ESXi %s "
                     "network info: %s" % (esxi.name, esxi.network))

        # TODO(Ray): Need to double check if this works for
        # distribution network type
        network_info = {}
        for nt in esxi.network:
            logging.debug("Current network is %s" % nt)
            network_info[nt.name] = {
                "name" : nt.summary.name,
                "accessible" : nt.summary.accessible,
                "ipPoolName" : nt.summary.ipPoolName
            }
            logging.debug("Success to get current "
                          "network info: %s" % network_info[nt.name])

        logging.info("Success to get ESXi %s "
                     "network %s" % (esxi.name, network_info))

        return network_info

    def _get_esxi_datastore_info(self, esxi):
        logging.info("Trying to get ESXi %s "
                     "datastore info: %s" % (
                         esxi.name, esxi.datastore))

        # TODO(Ray): Need to double check if the logical works for
        # RDM or other storage types
        datastore_info = {}
        for ds in esxi.datastore:
            logging.debug("Current datastore is %s" % ds)
            datastore_info[ds.name] = {
                "capacity" : ds.summary.capacity,
                "freeSpace" : ds.summary.freeSpace,
                "type" : ds.summary.type,
                "name" : ds.summary.name,
                "url" : ds.summary.url,
                "accessible" : ds.summary.accessible,
                "uncommitted" : ds.summary.uncommitted,
                "multipleHostAccess" : ds.summary.multipleHostAccess,
                "maintenanceMode" : ds.summary.maintenanceMode,
                "maxVirtualDiskCapacity" : ds.info.maxVirtualDiskCapacity,
                "maxMemoryFileSize" : ds.info.maxMemoryFileSize,
                "maxPhysicalRDMFileSize" : getattr(ds.info, "getkmaxPhysicalRDMFileSize", ""),
                "maxVirtualRDMFileSize" : getattr(ds.info, "maxVirtualRDMFileSize", ""),
                "blockSizeMb" : getattr(ds.info, "vmfs.blockSizeMb", ""),
                "maxFileSize" : ds.info.maxFileSize,
                "ssd" : getattr(ds.info, "vmfs.ssd", ""),
                "local" : getattr(ds.info, "vmfs.local", "")
            }
            logging.debug("Success to get current datastore "
                          "info: %s" % datastore_info[ds.name])

        logging.info("Success to get ESXi %s datastore "
                     "info: %s" % (esxi.name, datastore_info))

        return datastore_info
