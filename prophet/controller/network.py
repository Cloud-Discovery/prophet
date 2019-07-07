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
import os

import nmap

DEFAULT_ARGS = "-sS -O"
DATA_FILE = "scan_hosts.csv"
HEADERS = ["hostname", "ip", "username", "password", "ssh_port",
           "key_path", "mac", "vendor", "check_status", "os", "version",
           "tcp_ports"]
DEFAULT_LINUX_USER = "root"
DEFAULT_WINDOWS_USER = "Administrator"
DEFAULT_USER = "enter_your_username"
DEFAULT_PASSWORD = ""
DEFAULT_KEY_PATH = ""
DEFAULT_CHECK = "check"
DEFAULT_NO_CHECK = ""


class NetworkController(object):

    def __init__(self, host, arg, data_path):
        self.host = host
        self.data_path = data_path
        self.arg = arg if arg else DEFAULT_ARGS
        self.nm = nmap.PortScanner()

    def gen_report(self):
        report_path = os.path.join(self.data_path, DATA_FILE)
        with open(report_path, "w") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=HEADERS)
            writer.writeheader()
            hosts = self._scan()
            for host in hosts:
                try:
                    host_info = self.nm[host]
                    logging.debug("Analysis %s: %s ..." % (
                                  host, host_info))
                    hostname = host_info.hostname()
                    mac = self._get_mac(
                            host_info.get("addresses"))
                    ops, version = self._get_os(
                            host_info.get("osmatch"))
                    vendor = self._get_vendor(
                            host_info.get("vendor"), mac)
                    ssh_port = self._get_ssh_port(ops)
                    all_tcp = ",".join(
                            [str(x) for x in self.nm[host].all_tcp()])
                    username = self._get_username(ops)
                    password = DEFAULT_PASSWORD
                    check = self._get_check_status(vendor, ops)
                    row_data = {
                        "hostname": hostname,
                        "ip": host,
                        "username": username,
                        "password": password,
                        "ssh_port": ssh_port,
                        "key_path": DEFAULT_KEY_PATH,
                        "mac": mac,
                        "vendor": vendor,
                        "check_status": check,
                        "os": ops,
                        "version": version,
                        "tcp_ports": all_tcp,
                    }
                    logging.debug("Writing row %s" % row_data)
                    writer.writerow(row_data)
                except Exception as e:
                    logging.warn("Analysis host %s failed, "
                                 "due to %s." % (host, e.message))

    def _scan(self):
        self.nm.scan(hosts=self.host, arguments=self.arg)
        return self.nm.all_hosts()

    def _get_mac(self, addresses):
        if addresses:
            return addresses.get("mac")

    def _get_vendor(self, vendor, mac):
        if vendor:
            return vendor.get(mac)

    def _get_ssh_port(self, os):
        if os == "Linux":
            DEFAULT_SSH_PORT = "22"
        elif os == "VMware":
            DEFAULT_SSH_PORT = "443"
        else:
            DEFAULT_SSH_PORT = "None"
        return DEFAULT_SSH_PORT

    def _get_check_status(self, vendor, os):
        if vendor != "VMware" and \
           (os == "Linux" or os == "Windows" or os == "VMware"):
            return DEFAULT_CHECK
        else:
            return DEFAULT_NO_CHECK

    def _get_os(self, osmatch):
        osfamily = None
        version = None

        # if only one match return osfamily and name
        if len(osmatch) == 1:
            first_osclass = osmatch[0]["osclass"][0]
            osfamily = first_osclass.get("osfamily")
            version = osmatch[0].get("name")

        # if the first two osfamily are embedded, maybe the device is
        # switch or router, return the first one, otherwise it's a
        # phhsical machine
        if len(osmatch) > 1:
            first_osclass = osmatch[0]["osclass"][0]
            second_osclass = osmatch[1]["osclass"][0]
            logging.debug("First osclass is %s" % first_osclass)
            logging.debug("Second osclass is %s" % second_osclass)

            first_osfamily = first_osclass.get("osfamily")
            second_osfamily = second_osclass.get("osfamily")
            logging.debug("Compre osfamily first is %s, second is %s." % (
                first_osfamily, second_osfamily))
            if first_osfamily == "embedded" and \
               second_osfamily == "embedded":
                logging.debug("osfamily is embedded.")
                osfamily = first_osfamily
                version = osmatch[0].get("name")
            elif first_osfamily != "embedded":
                osfamily = first_osfamily
                version = osmatch[0].get("name")
            else:
                osfamily = second_osfamily
                version = osmatch[1].get("name")

        logging.debug("osfamily is %s, version is %s." % (
                      osfamily, version))
        if osfamily == "ESX Server":
            osfamily = "VMware"
        return osfamily, version

    def _get_username(self, ops):
        if "linux" in ops.lower():
            return DEFAULT_LINUX_USER

        if "windows" in ops.lower():
            return DEFAULT_WINDOWS_USER

        return DEFAULT_USER
