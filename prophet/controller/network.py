#!/usr/bin/env python
# -*- coding=utf8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2019 Prophet Tech (Shanghai) Ltd.
#
# Authors: Ray <sunqi@prophetech.cn>
#
# Copyright (c) 2019 This file is confidential and proprietary.
# All Rights Resrved, Prophet Tech (Shanghai) Ltd (http://www.prophetech.cn).

import csv
import logging
import nmap
import os

import pandas as pd

DEFAULT_ARGS = "-sS -O"
DEFAULT_FILE_NAME = "scan_hosts.csv"
DEFAULT_HEADERS = ["hostname", "ip", "username", "password", "ssh_port",
                   "key_path", "mac", "vendor", "check_status", "os",
                   "version", "tcp_ports", "do_status"]
DEFAULT_HOSTNAME = ""
DEFAULT_IP = ""
DEFAULT_LINUX_USER = "root"
DEFAULT_WINDOWS_USER = "Administrator"
DEFAULT_USER = "enter_your_username"
DEFAULT_PASSWORD = ""
DEFAULT_PORT = ""
DEFAULT_LINUX_PORT = "22"
DEFAULT_VMWARE_PORT = "443"
DEFAULT_KEY_PATH = ""
DEFAULT_MAC = ""
DEFAULT_VENDOR = ""
DEFAULT_CHECKSTATUS = ""
DEFAULT_OS = ""
DEFAULT_VERSION = ""
DEFAULT_DO_STATUS = ""
CHECKSTATUS_CHECK = "check"


class NetworkController(object):

    def __init__(self, host, arg, report_storage_path):
        self.host = host
        self.arg = arg if arg else DEFAULT_ARGS
        self.report_storage_path = report_storage_path
        self.nm = nmap.PortScanner()

    def generate_report(self):
        report_path = os.path.abspath(
            os.path.join(self.report_storage_path,
                         DEFAULT_FILE_NAME)
        )
        #writer = csv.DictWriter(csvfile, fieldnames=DEFAULT_HEADERS)
        #writer.writeheader()
        hosts = self._scan()
        data = []
        for host in hosts:
            try:
                logging.info("Analysis %s..." % host)
                host_info = self.nm[host]
                logging.debug("Host info %s" % host_info)
                hostname = host_info.hostname()
                mac = self._get_mac(host_info.get("addresses"))
                osfamily, version = self._get_os(host_info.get("osmatch"))
                vendor = self._get_vendor(host_info.get("vendor"), mac)
                ssh_port = self._get_ssh_port(osfamily)
                all_tcp = ",".join(
                    [str(x) for x in self.nm[host].all_tcp()])
                username = self._get_username(osfamily)
                check = self._get_check_status(vendor, osfamily)
                row_data = {
                    "hostname": hostname,
                    "ip": host,
                    "username": username,
                    "password": DEFAULT_PASSWORD,
                    "ssh_port": ssh_port,
                    "key_path": DEFAULT_KEY_PATH,
                    "mac": mac,
                    "vendor": vendor,
                    "check_status": check,
                    "os": osfamily,
                    "version": version,
                    "tcp_ports": all_tcp,
                    "do_status": DEFAULT_DO_STATUS
                }
                logging.debug("Writing row %s" % row_data)
                #writer.writerow(row_data)
                data.append(row_data)
            except Exception as e:
                logging.exception(e)
                logging.warn("Analysis host %s failed." % host)
        hosts_pd = pd.DataFrame(data, columns=DEFAULT_HEADERS)
        hosts_pd.to_csv(report_path, index=False)

    def _scan(self):
        logging.info("Begin scaning %s..." % self.host)
        self.nm.scan(hosts=self.host, arguments=self.arg)
        return self.nm.all_hosts()

    def _get_mac(self, addresses):
        if addresses:
            mac = addresses.get("mac")
            if mac:
                mac = mac.lower()
            return mac

    def _get_vendor(self, vendor, mac):
        if vendor:
            return vendor.get(mac)
        return ""

    def _get_username(self, osfamily):
        if "linux" in osfamily.lower():
            return DEFAULT_LINUX_USER
        if "windows" in osfamily.lower():
            return DEFAULT_WINDOWS_USER
        return DEFAULT_USER

    def _get_ssh_port(self, osfamily):
        if "linux" in osfamily.lower():
            return DEFAULT_LINUX_PORT
        if "vmware" in osfamily.lower():
            return DEFAULT_VMWARE_PORT
        return DEFAULT_PORT

    def _get_check_status(self, vendor, osfamily):
        if vendor and vendor.lower() != "vmware":
            if osfamily.lower() == "linux" \
               or osfamily.lower() == "windows" \
               or osfamily.lower() == "vmware":
                return CHECKSTATUS_CHECK
        return DEFAULT_CHECKSTATUS

    def _get_os(self, osmatch):
        osfamily = ""
        version = ""

        # If only one match return osfamily and name
        if len(osmatch) == 1:
            first_osclass = osmatch[0]["osclass"][0]
            osfamily = first_osclass.get("osfamily")
            version = osmatch[0].get("name")

        # If the first two osfamily are embedded, maybe the device is
        # switch or router, return the first one, otherwise it's a
        # phhsical machine
        if len(osmatch) > 1:
            first_osclass = osmatch[0]["osclass"][0]
            second_osclass = osmatch[1]["osclass"][0]
            logging.debug("First osclass is %s" % first_osclass)
            logging.debug("Second osclass is %s" % second_osclass)

            first_osfamily = first_osclass.get("osfamily")
            second_osfamily = second_osclass.get("osfamily")
            logging.debug("Compre osfamily first is %s, second is %s."
                          % (first_osfamily, second_osfamily))
            if first_osfamily == "embedded" \
               and second_osfamily == "embedded":
                osfamily = first_osfamily
                version = osmatch[0].get("name")
            elif first_osfamily != "embedded":
                osfamily = first_osfamily
                version = osmatch[0].get("name")
            else:
                osfamily = second_osfamily
                version = osmatch[1].get("name")

        logging.debug("osfamily is %s, version is %s."
                      % (osfamily, version))
        if osfamily == "ESX Server":
            osfamily = "VMware"

        return osfamily, version
