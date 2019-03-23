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

from pyVim import connect
from pyVmomi import vmodl
from pyVmomi import vim

from config_file import ConfigFile


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
        self._get_vcenter_info()
        self._get_esxi_info()
        self._vc_info[self.host]["esxi"] = self._esxis_info
        self._write_file_yaml(self._data_path,
                              "host",
                              self._connect_info,
                              filetype="cfg")
        self._write_file_yaml(self._data_path,
                              self.host,
                              self._vc_info)
        self._get_vms_info()

    def _get_disk_info(self, vm):
        disk_info = {}
        logging.info("Start get %s vm info." % vm)
        for dev in vm.config.hardware.device:
            if not isinstance(dev, vim.VirtualDisk):
                continue
            back_info = dev.backing
            if not isinstance(back_info, vim.VirtualDeviceFileBackingInfo):
                result = "non-file backing virtual disk exists"
                logging.info(result)
            disk_info["fileName"] = dev.backing.fileName
            disk_info["diskMode"] = dev.backing.diskMode
            disk_info["thinProvisioned"] = dev.backing.thinProvisioned
            disk_info["uuid"] = dev.backing.uuid
            disk_info["contentId"] = dev.backing.contentId
            disk_info["changeId"] = dev.backing.changeId
            disk_info["deltaDiskFormat"] = dev.backing.deltaDiskFormat
            logging.debug("Get %s vm disk %s info." % (
                    vm.config.name, disk_info))
        logging.info("Get %s vm all disks info successful." % vm.config.name)

        return disk_info

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

                logging.info("Start get %s vm network info." % vm.config.name)
                for nt in vm.network:
                    self._vms_info[vmid]["network"] = {}
                    self._vms_info[vmid][
                        "network"]["name"] = nt.summary.name
                    self._vms_info[vmid][
                        "network"]["accessible"] = nt.summary.accessible
                    logging.debug("Start get %s vm network info %s." %
                                  (vm.config.name,
                                   self._vms_info[vmid]["network"]))
                logging.info("Get %s vm network successful." % vm.config.name)

                for dsurl in vm.config.datastoreUrl:
                    self._vms_info[vmid]["datastoreurl"] = {}
                    self._vms_info[vmid][
                        "datastoreurl"]["url"] = dsurl.url
                    self._vms_info[vmid][
                        "datastoreurl"]["name"] = dsurl.name
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

    def _write_file_yaml(self, data_path, filename, values, filetype="yaml"):
        yamlfile = os.path.join(data_path, filename + "." + filetype)
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
