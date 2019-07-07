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
import uuid
import telnetlib
import yaml

from pyVim import connect
from pyVmomi import vmodl
from pyVmomi import vim

from config_file import ConfigFile, CsvDataFile


class VMwareHostController(object):
    """ VMware host api """

    def __init__(self,
                 host,
                 port,
                 username,
                 password,
                 data_path,
                 disable_ssl_verification=True):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.disable_ssl_verification = disable_ssl_verification
        self._data_path = data_path
        self._content = None
        self._check_connect()
        self.connect()
        self._esxis_info = {}
        self._vms_info = {}
        self._vc_info = {}
        self._connect_info = {
            "VMware_" + self.host: {"ipaddr": self.host,
                                    "port": self.port,
                                    "username": self.username,
                                    "password": self.password}}

    def _check_connect(self):
        try:
            logging.info("Check %s:%s host network..." % (self.host,
                         self.port))
            telnetlib.Telnet(self.host, port=self.port, timeout=5)
        except Exception as error:
            logging.error("Connecton refrush, %s", error)
            sys.exit()
        else:
            logging.info("Host %s:%s connect successful." % (
                self.host, self.port))

    def connect(self):
        logging.debug("Start connect [%s] vmware host with port [%s],"
                      "username [%s], password [%s]..." % (self.host,
                                                           self.port,
                                                           self.username,
                                                           self.password))
        try:
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

        except vmodl.MethodFault as error:
            logging.error("Caught vmodel fault: %s", error.msg)
            return -1

    def _get_content_obj(self, content, viewtype, name=None):
        recursive = True
        containerView = content.viewManager.CreateContainerView(
            content.rootFolder, viewtype, recursive)
        obj = [view for view in containerView.view]
        return obj

    def _get_vcenter_info(self):
        logging.info("Begin get %s VCenter server info." % self.host)
        try:
            self._vc_info[self.host] = {}
            self._vc_info[self.host][
                "name"] = self._content.about.name
            self._vc_info[self.host][
                "fullName"] = self._content.about.fullName
            self._vc_info[self.host][
                "vendor"] = self._content.about.vendor
            self._vc_info[self.host][
                "version"] = self._content.about.version
            self._vc_info[self.host][
                "build"] = self._content.about.build
            self._vc_info[self.host][
                "localeVersion"] = self._content.about.localeVersion
            self._vc_info[self.host][
                "localeBuild"] = self._content.about.localeBuild
            self._vc_info[self.host][
                "osType"] = self._content.about.osType
            self._vc_info[self.host][
                "productLineId"] = self._content.about.productLineId
            self._vc_info[self.host][
                "apiType"] = self._content.about.apiType
            self._vc_info[self.host][
                "apiVersion"] = self._content.about.apiVersion
            self._vc_info[self.host][
                "instanceUuid"] = self._content.about.instanceUuid
            self._vc_info[self.host][
                "licenseProductName"] = self._content.about.licenseProductName
            self._vc_info[self.host][
                "licenseProductVersion"] = \
                self._content.about.licenseProductVersion
            logging.debug("Get %s VCenter server info %s." % (self.host,
                                                              self._vc_info))

        except AttributeError as err:
            logging.error(err)
            return -1

    def get_all_info(self):
        if self._content.about.name == "VMware vCenter Server":
            self._get_vcenter_info()
            server_type = "_vcenter"
            self._get_esxi_info()
            self._vc_info[self.host]["esxi"] = self._esxis_info
            self._write_file_yaml(self._data_path,
                                  self.host,
                                  self._vc_info,
                                  suffix=server_type)
        else:
            server_type = "_exsi"
            self._get_esxi_info()
            self._write_file_yaml(self._data_path,
                                  self.host,
                                  self._esxis_info,
                                  suffix=server_type)

        self._write_file_yaml(self._data_path,
                              "host",
                              self._connect_info,
                              suffix=server_type,
                              filetype="cfg")
        self._get_vms_info()

    def _get_disk_info(self, vm):
        disk_info = {}
        vdisk_types = [
            vim.VirtualDiskFlatVer1BackingInfo,
            vim.VirtualDiskFlatVer2BackingInfo,
            vim.VirtualDiskSparseVer1BackingInfo,
            vim.VirtualDiskSparseVer2BackingInfo,
            vim.VirtualDiskRawDiskMappingVer1BackingInfo,
        ]
        logging.info("Start get %s vm disk info." % vm.config.name)
        for dev in vm.config.hardware.device:
            if not isinstance(dev, vim.VirtualDisk):
                continue
            back_info = dev.backing
            if not isinstance(back_info, vim.VirtualDeviceFileBackingInfo):
                result = "non-file backing virtual disk exists"
                logging.warning(result)
                disk_info["backing"] = result
                continue
            if not any(map(lambda ty: isinstance(back_info, ty),
                           vdisk_types)):
                result = ("Contain unsuported backing type: "
                          "%s" % back_info.__name__)
                disk_info["backing"] = result
                continue
            diskuuid = dev.backing.uuid
            disk_info[diskuuid] = {}
            disk_info[diskuuid]["capacityInKB"] = \
                dev.capacityInKB
            disk_info[diskuuid]["fileName"] = \
                dev.backing.fileName
            disk_info[diskuuid]["diskMode"] = \
                dev.backing.diskMode
            disk_info[diskuuid]["thinProvisioned"] = \
                dev.backing.thinProvisioned
            disk_info[diskuuid]["contentId"] = \
                dev.backing.contentId
            disk_info[diskuuid]["changeId"] = \
                dev.backing.changeId
            disk_info[diskuuid]["deltaDiskFormat"] = \
                dev.backing.deltaDiskFormat
            logging.debug("Get %s vm disk %s info." % (
                vm.config.name, disk_info))

        logging.info("Get %s vm all disks info successful." % vm.config.name)

        return disk_info

    def _get_network_info(self, vm):
        network_info = {}
        logging.info("Start get %s network info." % vm.config.name)
        for dev in vm.config.hardware.device:
            if isinstance(dev, vim.VirtualE1000) or \
                    isinstance(dev, vim.VirtualE1000e) or \
                    isinstance(dev, vim.VirtualVmxnet3) or \
                    isinstance(dev, vim.VirtualVmxnet2):
                back_info = dev.backing
                nt_uuid = uuid.uuid1().hex
                network_info[nt_uuid] = {}
                if not isinstance(back_info,
                                  vim.VirtualEthernetCard.NetworkBackingInfo):
                    result = "non-network backing virtual network exists"
                    logging.warning(result)
                    network_info[nt_uuid]["backing"] = result
                    continue
                nt = dev.backing.network
                network_info[nt_uuid]["macAddress"] = \
                    dev.macAddress
                network_info[nt_uuid]["accessible"] = \
                    nt.summary.accessible
                network_info[nt_uuid]["deviceName"] = \
                    nt.summary.name
                logging.debug("Get %s vm network %s info." % (
                    vm.config.name, network_info))
            else:
                continue

        logging.info("Get %s vm all nets info successful." % vm.config.name)

        return network_info

    def _get_vms_info(self):
        esxi_obj = self._get_content_obj(self._content, [vim.HostSystem])
        vms_obj = self._get_content_obj(self._content, [vim.VirtualMachine])
        logging.info("Start get %s esxi all vms info." % esxi_obj)
        logging.debug("Get %s number vm in VCenter." % len(vms_obj))
        for vm in vms_obj:
            if vm.summary.runtime.host in esxi_obj:
                obj_index = esxi_obj.index(vm.summary.runtime.host)
                esxi_host = esxi_obj[obj_index].name
                vmid = vm.config.instanceUuid
                self._vms_info[vmid] = {"esxi_host": esxi_host}
                self._vms_info[vmid][
                    "name"] = vm.config.name
                self._vms_info[vmid][
                    "memoryMB"] = vm.config.hardware.memoryMB
                self._vms_info[vmid][
                    "numCpu"] = vm.config.hardware.numCPU
                self._vms_info[vmid][
                    "numCoresPerSocket"] = \
                    vm.config.hardware.numCoresPerSocket
                self._vms_info[vmid][
                    "numEthernetCards"] = vm.summary.config.numEthernetCards
                self._vms_info[vmid][
                    "powerState"] = vm.runtime.powerState
                self._vms_info[vmid][
                    "numVirtualDisks"] = vm.summary.config.numVirtualDisks
                self._vms_info[vmid][
                    "uuid"] = vm.config.uuid
                self._vms_info[vmid][
                    "locationId"] = vm.config.locationId
                self._vms_info[vmid][
                    "guestId"] = vm.config.guestId
                self._vms_info[vmid][
                    "guestFullName"] = vm.config.guestFullName
                self._vms_info[vmid][
                    "version"] = vm.config.version
                self._vms_info[vmid][
                    "firmware"] = vm.config.firmware
                self._vms_info[vmid][
                    "vmPathName"] = vm.config.files.vmPathName
                self._vms_info[vmid][
                    "toolsStatus"] = vm.summary.guest.toolsStatus
                self._vms_info[vmid][
                    "ipAddress"] = vm.summary.guest.ipAddress
                self._vms_info[vmid][
                    "hostName"] = vm.summary.guest.hostName
                self._vms_info[vmid][
                    "toolsVersion"] = vm.config.tools.toolsVersion
                self._vms_info[vmid][
                    "snapshotDirectory"] = vm.config.files.snapshotDirectory
                self._vms_info[vmid][
                    "suspendDirectory"] = vm.config.files.suspendDirectory
                self._vms_info[vmid][
                    "logDirectory"] = vm.config.files.logDirectory
                self._vms_info[vmid][
                    "changeTrackingSupported"] = \
                    vm.capability.changeTrackingSupported
                networks_info = self._get_network_info(vm)
                self._vms_info[vmid]["network"] = networks_info
                for dsurl in vm.config.datastoreUrl:
                    datastore_name = dsurl.name
                    self._vms_info[vmid][
                        "datastoreurl"] = {datastore_name: {}}
                    self._vms_info[vmid][
                        "datastoreurl"][datastore_name]["url"] = dsurl.url
                    logging.debug("Get %s esxi vm info %s." % (
                        esxi_host, self._vms_info[vmid]["datastoreurl"]))
                disks_info = self._get_disk_info(vm)
                self._vms_info[vmid][
                    "disks_info"] = disks_info
            logging.info("Get %s esxi host %s vms info successful." %
                         (esxi_host, vm.config.name))

            self._write_file_yaml(self._data_path,
                                  vm.config.name,
                                  self._vms_info)
            self._vms_info = {}

    def _write_file_yaml(self, data_path, filename, values, suffix="_vmware",
                         filetype="yaml"):
        yamlfile = os.path.join(data_path, filename + suffix +
                                "." + filetype)
        config = ConfigFile(yamlfile)
        logging.info("Write %s info to %s yaml file..." % (
            filename,
            yamlfile))
        try:
            config.convert_json_to_yaml(values)
            logging.info("Write %s info to file successful." % (
                filename))
        except Exception as e:
            logging.error("Write %s info to file failed %s." % (
                filename, e))
            return -1

    def _get_esxi_info(self):
        esxi_obj = self._get_content_obj(self._content, [vim.HostSystem])
        logging.info("start get %s exsi info." % esxi_obj)
        for esxi in esxi_obj:
            logging.info("start get %s exsi info." % esxi.name)
            self._esxis_info[esxi.name] = {"esxi_info": {},
                                           'datastore': {},
                                           'network': {}}
            self._esxis_info[esxi.name][
                "esxi_info"]["vendor"] = esxi.summary.hardware.vendor
            self._esxis_info[esxi.name][
                "esxi_info"]["model"] = esxi.summary.hardware.model
            self._esxis_info[esxi.name][
                "esxi_info"]["port"] = esxi.summary.config.port
            for i in esxi.summary.hardware.otherIdentifyingInfo:
                if isinstance(i, vim.host.SystemIdentificationInfo):
                    self._esxis_info[esxi.name][
                        "esxi_info"]["SN"] = i.identifierValue
            self._esxis_info[esxi.name][
                "esxi_info"]["fullName"] = \
                esxi.summary.config.product.fullName
            self._esxis_info[esxi.name][
                "esxi_info"]["version"] = esxi.summary.config.product.version
            self._esxis_info[esxi.name][
                "esxi_info"]["build"] = esxi.summary.config.product.build
            self._esxis_info[esxi.name][
                "esxi_info"]["osType"] = esxi.summary.config.product.osType
            self._esxis_info[esxi.name][
                "esxi_info"]["licenseProductName"] = \
                esxi.summary.config.product.licenseProductName
            self._esxis_info[esxi.name][
                "esxi_info"]["licenseProductVersion"] = \
                esxi.summary.config.product.licenseProductVersion
            self._esxis_info[esxi.name][
                "esxi_info"]["MemorySize"] = \
                esxi.summary.hardware.memorySize/1024/1024
            self._esxis_info[esxi.name][
                "esxi_info"]["cpuModel"] = esxi.summary.hardware.cpuModel
            self._esxis_info[esxi.name][
                "esxi_info"]["cpuMhz"] = esxi.summary.hardware.cpuMhz
            self._esxis_info[esxi.name][
                "esxi_info"]["numCpuPkgs"] = esxi.summary.hardware.numCpuPkgs
            self._esxis_info[esxi.name][
                "esxi_info"]["numCpuCores"] = \
                esxi.summary.hardware.numCpuCores
            self._esxis_info[esxi.name][
                "esxi_info"]["numCpuThreads"] = \
                esxi.summary.hardware.numCpuThreads
            self._esxis_info[esxi.name][
                "esxi_info"]["numNics"] = esxi.summary.hardware.numNics
            self._esxis_info[esxi.name][
                "esxi_info"]["numHBAs"] = esxi.summary.hardware.numHBAs

            self._get_esxi_datastore_info(esxi)
            self._get_esxi_network_info(esxi)
        logging.info("Get %s esxis host info successful." % esxi.name)

    def _get_esxi_network_info(self, esxi):
        logging.info("Start get %s esxi host network info." % esxi.name)
        for nt in esxi.network:
            self._esxis_info[esxi.name][
                "network"][nt.name] = {}
            self._esxis_info[esxi.name][
                "network"][nt.name]["name"] = nt.summary.name
            self._esxis_info[esxi.name][
                "network"][nt.name]["accessible"] = nt.summary.accessible
            self._esxis_info[esxi.name][
                "network"][nt.name]["ipPoolName"] = nt.summary.ipPoolName
            logging.debug("Get %s esxi host network info %s." % (
                esxi.name, self._esxis_info[esxi.name]["network"]))
        logging.info("Get %s esxi host network info successful." % esxi.name)

    def _get_esxi_datastore_info(self, esxi):
        logging.info("Start get %s esxi host datastore info." % esxi.name)
        for ds in esxi.datastore:
            self._esxis_info[esxi.name][
                "datastore"][ds.name] = {}
            self._esxis_info[esxi.name][
                "datastore"][ds.name]["capacity"] = ds.summary.capacity
            self._esxis_info[esxi.name][
                "datastore"][ds.name]["freeSpace"] = ds.summary.freeSpace
            self._esxis_info[esxi.name][
                "datastore"][ds.name]["type"] = ds.summary.type
            self._esxis_info[esxi.name][
                "datastore"][ds.name]["name"] = ds.summary.name
            self._esxis_info[esxi.name][
                "datastore"][ds.name]["url"] = ds.summary.url
            self._esxis_info[esxi.name][
                "datastore"][ds.name]["accessible"] = ds.summary.accessible
            self._esxis_info[esxi.name][
                "datastore"][ds.name]["uncommitted"] = ds.summary.uncommitted
            self._esxis_info[esxi.name][
                "datastore"][ds.name]["multipleHostAccess"] = \
                ds.summary.multipleHostAccess
            self._esxis_info[esxi.name][
                "datastore"][ds.name]["maintenanceMode"] = \
                ds.summary.maintenanceMode
            self._esxis_info[esxi.name][
                "datastore"][ds.name]["maxVirtualDiskCapacity"] = \
                ds.info.maxVirtualDiskCapacity
            self._esxis_info[esxi.name][
                "datastore"][ds.name]["maxMemoryFileSize"] = \
                ds.info.maxMemoryFileSize
            self._esxis_info[esxi.name][
                "datastore"][ds.name]["maxPhysicalRDMFileSize"] = \
                ds.info.maxPhysicalRDMFileSize
            self._esxis_info[esxi.name][
                "datastore"][ds.name]["maxVirtualRDMFileSize"] = \
                ds.info.maxVirtualRDMFileSize
            self._esxis_info[esxi.name][
                "datastore"][ds.name]["blockSizeMb"] = ds.info.vmfs.blockSizeMb
            self._esxis_info[esxi.name][
                "datastore"][ds.name]["maxFileSize"] = ds.info.maxFileSize
            self._esxis_info[esxi.name][
                "datastore"][ds.name]["ssd"] = ds.info.vmfs.ssd
            self._esxis_info[esxi.name][
                "datastore"][ds.name]["local"] = ds.info.vmfs.local
            logging.debug("Get %s esxi host datastore info %s." %
                          (esxi.name,
                           self._esxis_info[esxi.name]["datastore"]))
        logging.info("Get %s esxi host datastore info successful." %
                     esxi.name)


class VMwareHostReport(object):

    def __init__(self, input_path, output_path, vmware_file):
        self.vmware_file = vmware_file
        self.input_path = input_path
        self.output_path = output_path

    def get_report(self):
        for i in self.vmware_file:
            self.data = self._get_data_info(i)
            self.hostname = self._get_hostname(self.data)
            self.version = self._get_version(self.data)
            self.cpu_num = self._get_cpu_num(self.data)
            self.tol_mem = self._get_total_mem(self.data)
            self.macaddr = self._get_macaddr(self.data)
            self.volume_info = self._get_volume_info(self.data)
            self.boot_type = self._get_boot_type(self.data)
            self.migration_check = self._migration_check(self.boot_type)
            self._yaml_to_csv(i, self.hostname, self.version,
                              self.cpu_num, self.tol_mem, self.macaddr,
                              self.volume_info, self.boot_type,
                              self.migration_check)

    def _get_data_info(self, i):
        file_path = os.path.join(self.input_path, i)
        logging.info("Opening %s....." % i)
        with open(file_path) as host_info:
            data = yaml.load(host_info)
        logging.info("Geting designated data.....")
        return data

    def _yaml_to_csv(self, i, hostname, version,
                     cpu_num, tol_mem, macaddr, volume_info,
                     boot_type, migration_check):
        host_data = [
                {'host_type': 'VMware',
                 'hostname': self.hostname.decode('utf-8').encode('gbk'),
                 'address': 'Null',
                 'version': self.version.decode('utf-8').encode('gbk'),
                 'cpu_num': self.cpu_num,
                 'tol_mem(G)': self.tol_mem,
                 'macaddr': self.macaddr,
                 'disk_info': self.volume_info,
                 'boot_type': self.boot_type,
                 'support_synchronization': self.migration_check[0],
                 'support_increment': self.migration_check[1],
                 'migration_proposal': self.migration_check[2]}
                ]
        logging.info("Writing migration proposal.....")
        file_name = 'analysis' + '.csv'
        output_file = os.path.join(self.output_path, file_name)
        csv_config = CsvDataFile(host_data, output_file)
        csv_config.write_data_to_csv()
        logging.info("%s migration proposal completed" % i)

    def _get_hostname(self, data):
        logging.info("Analysising host name...")
        hostname = self.data.values()[0]['name']
        return hostname

    def _get_version(self, data):
        logging.info("Analysising host version...")
        versions = self.data.values()[0]['guestFullName']
        return versions

    def _get_cpu_num(self, data):
        logging.info("Analysising cpu cores...")
        cpu_num = str(self.data.values()[0]['numCpu'])
        return cpu_num

    def _get_total_mem(self, data):
        logging.info("Analysising memory...")
        host_tolal_mem = str(self.data.values()[0]['memoryMB'] / 1024)
        return host_tolal_mem

    def _get_macaddr(self, data):
        host_macaddr = []
        logging.info("Analysising ip macaddr...")
        for i in range(len(self.data.values()[0]['network'].values())):
            one_mac = (self.data.values()[0]['network'].values()[i]
                       ['macAddress'])
            host_macaddr.append(one_mac)
        return host_macaddr

    def _get_volume_info(self, data):
        logging.info("Analysising volume info...")
        volume_info = {}
        for i in range(len(self.data.values()[0]['disks_info'].values())):
            disk_size = str(self.data.values()[0]['disks_info'].values()[i]
                            ['capacityInKB'] / 1024 / 1024)
            disk_name = (self.data.values()[0]['disks_info'].values()[i]
                         ['fileName'])
            volume_info['disk_name:%s' % disk_name] = [
                    'disk_size:%s' % disk_size
                    ]
        return volume_info

    def _get_boot_type(self, data):
        logging.info("Analysising boot mode...")
        boot_type = self.data.values()[0]['firmware']
        return boot_type

    def _migration_check(self, boot_type):
        logging.info("Geted host data successful.")
        logging.info("Checking host data.....")
        support_synchronization = 'Yes'
        support_increment = 'Yes'
        migration_proposal = ''
        if 'efi' in self.boot_type:
            support_synchronization = 'No'
            support_increment = 'No'
            migration_proposal = ('Boot type:EFI, cloud not supported, '
                                  'so migrate to the cloud start system '
                                  'failed, need fix boot type is BIOS.')
        for i in range(len(self.data.values()[0]['disks_info'].values())):
            disk_mode = (self.data.values()[0]['disks_info'].values()[i]
                         ['diskMode'])
            if "independent_persistent" == disk_mode:
                support_synchronization = 'No'
                support_increment = 'No'
                migration_proposal = (migration_proposal +
                                      'Disk is independent mode, cloud '
                                      'not support migrate')
        if int(self.data.values()[0]['version'].split('-')[1]) < 7:
            support_increment = 'No'
            migration_proposal = (migration_proposal +
                                  'VM version <7, not support CBT, '
                                  'cannot support incremental backup.')
        if not self.data.values()[0]['changeTrackingSupported']:
            support_increment = 'No'
            migration_proposal = (migration_proposal +
                                  'VM not support CBT.')
        if migration_proposal.strip() == '':
            migration_proposal = 'Check successful'
            logging.info("Host data check completed.")
        return (support_synchronization,
                support_increment,
                migration_proposal)
