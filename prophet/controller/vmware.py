#!/usr/bin/env python
# -*- coding=utf8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2019 Prophet Tech (Shanghai) Ltd.
#
# Authors: Ray <sunqi@prophetech.cn>
# Authors: Xu XingZhuang <xuxingzhuang@prophetech.cn>
#
# Copyright (c) 2019 This file is confidential and proprietary.
# All Rights Resrved, Prophet Tech (Shanghai) Ltd (http://www.prophetech.cn).
#
# Collection VMware host info
#
# Steps:
#
#     1. Test VMwarer connections.
#     2. Get VCenter manager host info.
#     3. Get all esxi host info.
#     4. Get all vms info for esxi.
#     5. Store information to config file for each virtual machine.
#

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

from prophet.controller.config_file import ConfigFile, CsvDataFile


class VMwareHostController(object):
    """ VMware host api """

    def __init__(self,
                 host,
                 port,
                 username,
                 password,
                 output_path,
                 disable_ssl_verification=True):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.output_path = output_path
        self.disable_ssl_verification = disable_ssl_verification

        self._content = None
        self._check_connect()
        self.connect()

        self._esxis_info = {}
        self._vms_info = {}
        self._vc_info = {}

        self._connect_info = {
            "VMware_" + self.host: {
                "ipaddr": self.host,
                "port": self.port,
                "username": self.username,
                "password": self.password
            }
        }

        # Generate report for vCenter collection
        self.success_vcs = []
        self.failed_vcs = []

        # Generate report for ESXi collection
        self.success_esxis = []
        self.failed_esxis = []

        # Generate report for VM collection
        self.success_vms = []
        self.failed_vms = []

    def _check_connect(self):
        try:
            logging.info("Check %s:%s host network..."
                         % (self.host, self.port))
            telnetlib.Telnet(self.host, port=self.port, timeout=5)
        except Exception as error:
            logging.error("Check %s:%s failed, due to %s"
                          % (self.host, self.port, error))
            sys.exit()
        else:
            logging.info("Host %s:%s check successful."
                         % (self.host, self.port))

    def connect(self):
        logging.debug("Start connect [%s] vmware host with port [%s],"
                      "username [%s], password [%s]..."
                      % (self.host, self.port, self.username, self.password))
        logging.info("Start connect %s vmware host..." % self.host)
        if self.disable_ssl_verification:
            service_instance = connect.SmartConnectNoSSL(
                host=self.host,
                user=self.username,
                pwd=self.password,
                port=int(self.port))
        else:
            service_instance = connect.SmartConnect(
                host=self.host,
                user=self.username,
                pwd=self.password,
                port=int(self.port))
        atexit.register(connect.Disconnect, service_instance)
        logging.info("Connect %s vmware host sucessful." % self.host)
        self._content = service_instance.RetrieveContent()

    def _get_content_obj(self, content, viewtype, name=None):
        recursive = True
        containerView = content.viewManager.CreateContainerView(
            content.rootFolder, viewtype, recursive)
        return [view for view in containerView.view]

    def _get_vcenter_info(self):
        logging.info(
                "Trying to get "
                "VMware vCenter %s info..." % self.host)
        try:
            self._vc_info[self.host] = {
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
            self.success_vcs.append(self.host)
        except Exception as e:
            logging.error(
                    "Failed to get vCenter %s "
                    "information, due to:" % self.host)
            logging.exception(e)
            self.failed_vcs.append(self.host)
            return

        logging.info(
                "Success to get VMWare vCenter "
                "%s info succesfully: %s" % (
                    self.host, self._vc_info))

    def get_all_info(self):
        """Get all VMware related information

        If the specify ip is vCenter, first get vCenter information,
        then get exsi later. If it's only esxi, then just save the
        esxi information.

        After that get all VMs and save to files.
        """

        vmware_info = {}
        server_type = "_exsi"

        # Get ESXi information
        self._get_esxi_info()

        # If the given address is vCenter, also get vCenter infromation
        if self._content.about.name == "VMware vCenter Server":
            server_type = "_vcenter"
            self._get_vcenter_info()
            self._vc_info[self.host]["esxi"] = self._esxis_info
            vmware_info = self._vc_info
        else:
            vmware_info = self._esxis_info

        # Write connection information to host_<type>.cfg
        self._write_file_yaml(
            self.output_path, "host",
            self._connect_info,
            suffix=server_type,
            filetype="cfg")

        # Save vCenter and ESxi into yaml file
        self._write_file_yaml(
            self.output_path, self.host,
            vmware_info, suffix=server_type)

        # Begin to collect all VMs
        self._get_vms_info()

    def show_collection_report(self):
        logging.info("----------VMware Summary----------")
        self._generate_report(
                "vCenter", self.success_vcs, self.failed_vcs)
        self._generate_report(
                "ESXi", self.success_esxis, self.failed_esxis)
        self._generate_report(
                "VM", self.success_vms, self.failed_vms)

    def _generate_report(self, item_name, success_items, failed_items):
        if success_items or failed_items:
            logging.info(
                    "%s Collection Result: "
                    "Success %s, Failed %s" % (
                        item_name,
                        len(success_items),
                        len(failed_items)))
            logging.debug("Success Detailed: %s" % success_items)
            logging.info("Failed Detailed: %s" % failed_items)
            logging.info("----------------------------------")

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
                "thinProvisioned": dev.backing.thinProvisioned,
                "contentId":  dev.backing.contentId,
                "changeId": dev.backing.changeId,
                "deltaDiskFormat": dev.backing.deltaDiskFormat
            }
            #diskuuid = dev.backing.uuid
            #disk_info[diskuuid] = {}
            #disk_info[diskuuid]["capacityInKB"] = \
            #    dev.capacityInKB
            #disk_info[diskuuid]["fileName"] = \
            #    dev.backing.fileName
            #disk_info[diskuuid]["diskMode"] = \
            #    dev.backing.diskMode
            #disk_info[diskuuid]["thinProvisioned"] = \
            #    dev.backing.thinProvisioned
            #disk_info[diskuuid]["contentId"] = \
            #    dev.backing.contentId
            #disk_info[diskuuid]["changeId"] = \
            #    dev.backing.changeId
            #disk_info[diskuuid]["deltaDiskFormat"] = \
            #    dev.backing.deltaDiskFormat

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
                self._write_file_yaml(
                    self.output_path, vm.config.name, vms_info)

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
            "esxi_host": esxi_host,
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

    def _write_file_yaml(self, output_path, filename, values,
                         suffix="_vmware", filetype="yaml"):
        yamlfile = os.path.join(
            output_path,
            filename + suffix + "." + filetype
        )
        config = ConfigFile(yamlfile)
        logging.info("Write %s info to %s yaml file..."
                     % (filename, yamlfile))
        config.convert_json_to_yaml(values)
        logging.info("Write %s info to file successful."
                     % (filename))

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


class VMwareHostReport(object):

    def __init__(self, input_path, output_path, vmware_files):
        self.input_path = input_path
        self.output_path = output_path
        self.vmware_files = vmware_files

    def get_report(self):
        for file in self.vmware_files:
            data = list(self._get_data_info(file).values())[0]
            hostname = self._get_hostname(data)
            version = self._get_version(data)
            cpu_num = self._get_cpu_num(data)
            tol_mem = self._get_total_mem(data)
            macaddr = self._get_macaddr(data)
            volume_info = self._get_volume_info(data)
            boot_type = self._get_boot_type(data)
            migration_check = self._migration_check(data, boot_type)
            self._yaml_to_csv(
                file, hostname, version,
                cpu_num, tol_mem, macaddr,
                volume_info, boot_type, migration_check
            )

    def _get_data_info(self, file):
        file_path = os.path.join(self.input_path, file)
        with open(file_path) as host_info:
            return yaml.load(host_info, Loader=yaml.FullLoader)

    def _get_hostname(self, data):
        return data["name"]

    def _get_version(self, data):
        return data["guestFullName"]

    def _get_cpu_num(self, data):
        return str(data["numCpu"])

    def _get_total_mem(self, data):
        return str(int(data["memoryMB"]) / 1024)

    def _get_macaddr(self, data):
        host_macaddr = []
        for mac in data["network"].values():
            host_macaddr.append(mac["macAddress"])
        return host_macaddr

    def _get_volume_info(self, data):
        volume_info = {}
        for disk_info in data["disks_info"].values():
            disk_name = disk_info["fileName"]
            disk_size = int(disk_info["capacityInKB"]) / 1024 / 1024
            volume_info["disk_name:%s" % disk_name] = [
                "disk_size:%s" % disk_size
            ]
        return volume_info

    def _get_boot_type(self, data):
        return data["firmware"]

    def _migration_check(self, data, boot_type):
        support_synchronization = "Yes"
        support_increment = "Yes"
        migration_proposal = ""
        if "efi" in boot_type:
            support_synchronization = "No"
            support_increment = "No"
            migration_proposal = ("Boot type:EFI, cloud not supported, "
                                  "so migrate to the cloud start system "
                                  "failed, need fix boot type is BIOS.")
        for disk_info in data["disks_info"].values():
            disk_mode = disk_info["diskMode"]
            if "independent_persistent" == disk_mode:
                support_synchronization = "No"
                support_increment = "No"
                migration_proposal = (migration_proposal +
                                      "Disk is independent mode, cloud "
                                      "not support migrate")
        if int(data["version"].split('-')[1]) < 7:
            support_increment = "No"
            migration_proposal = (migration_proposal +
                                  "VM version <7, not support CBT, "
                                  "cannot support incremental backup.")
        if not data["changeTrackingSupported"]:
            support_increment = "No"
            migration_proposal = (
                migration_proposal + "VM not support CBT.")
        if migration_proposal.strip() == "":
            migration_proposal = "Check successful"
        is_drs = 'Off'
        is_ha = 'Off'
        if data['drs']:
            is_drs = 'On'
        if data['ha']:
            is_ha = 'On'

        return (
            support_synchronization,
            support_increment,
            is_drs,
            is_ha,
            migration_proposal
        )

    def _yaml_to_csv(self, file, hostname, version,
                     cpu_num, tol_mem, macaddr,
                     volume_info, boot_type, migration_check):
        logging.info("hostname %s" % hostname)
        host_data = [
            {
                "host_type": "VMware",
                "hostname": hostname.decode('utf-8').encode('gbk'),
                "address": "",
                "version": version.decode('utf-8').encode('gbk'),
                "cpu_num": cpu_num,
                "tol_mem(G)": tol_mem,
                "macaddr": macaddr,
                "disk_info": volume_info,
                "boot_type": boot_type,
                "support_synchronization": migration_check[0],
                "support_increment": migration_check[1],
                "drs_on": migration_check[2],
                "ha_on": migration_check[3],
                "migration_proposal": migration_check[4]
            }
        ]
        logging.info("Writing %s migration proposal..." % file)
        file_name = 'analysis' + '.csv'
        output_file = os.path.join(self.output_path, file_name)
        csv_config = CsvDataFile(host_data, output_file)
        csv_config.write_data_to_csv()
        logging.info("Write to %s finish." % output_file)
