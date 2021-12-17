# -*- coding=utf8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2019 OnePro Cloud (Shanghai) Ltd.
#
# Authors: Ray <ray.sun@oneprocloud.com>
#
# Copyright (c) 2019 This file is confidential and proprietary.
# All Rights Resrved, OnePro Cloud (Shanghai) Ltd (http://www.oneprocloud.com).

"""Batch job for running mix host type collection"""

import glob
import logging
import os
import shutil
import time

import pandas as pd

from prophet.controller.linux_host import LinuxHostController
from prophet.controller.windows_host import WindowsHostCollector
from prophet.controller.vmware import VMwareHostController
from prophet.controller.gen_mac import GenerateMac

REPORT_PATH_NAME = "host_collection_info"
REPORT_PREFIX = "host_collection_info"
# Scan report without username and password
SCAN_REPORT_FILENAME = "scan_hosts.csv"

LINUX_REPORT_PATH_NAME = "linux_hosts"
WINDOWS_REPORT_PATH_NAME = "windows_hosts"
VMWARE_REPORT_PATH_NAME = "vmware_hosts"

# os types
LINUX = "LINUX"
WINDOWS = "WINDOWS"
VMWARE = "VMWARE"

# VMware
DEFAULT_VMWARE_PORT = 443

# Sensitive files
SENSITIVE_FILES = ["hosts.cfg", "host_exsi.cfg", "hosts"]

class BatchJob(object):

    def __init__(self, host_file, output_path, force_check):
        if not os.path.exists(host_file):
            raise OSError("Input path %s is not exists." % host_file)

        if not os.path.exists(output_path):
            raise OSError("Output path %s is not exists." % output_path)

        self.host_file = host_file
        self.output_path = output_path
        self.force_check = force_check

        self._prepare()

    @property
    def report_full_path(self):
        return os.path.join(self.output_path, self.report_filename)

    @property
    def report_filename(self):
        return self.report_basename + ".zip"

    @property
    def report_basename(self):
        timestamp = time.strftime(
            "%Y%m%d%H%M%S",
            time.localtime(time.time())
        )
        return REPORT_PREFIX + "_" + timestamp

    @property
    def scan_report_path(self):
        return os.path.join(self.coll_path, SCAN_REPORT_FILENAME)

    @property
    def linux_report_path(self):
        return os.path.join(self.coll_path, LINUX_REPORT_PATH_NAME)

    @property
    def windows_report_path(self):
        return os.path.join(self.coll_path, WINDOWS_REPORT_PATH_NAME)

    @property
    def vmware_report_path(self):
        return os.path.join(self.coll_path, VMWARE_REPORT_PATH_NAME)

    @property
    def coll_path(self):
        return os.path.join(self.output_path, REPORT_PATH_NAME)

    def collect(self):
        """Collect host information

        Host with check status and do status is not success will be
        collected. If force check is given, do status is ignored.
        """
        logging.info("Collecting hosts information "
                     "from %s, generate report "
                     "in %s..." % (self.host_file, self.report_filename))
        hosts = self._parse_host_file()

        total_check_hosts = []
        success_hosts = []
        failed_hosts = []
        logging.info("Trying to collect %s host(s)..." % len(hosts))

        for index, row in hosts.iterrows():
            logging.debug("Current row is\n%s" % row)
            try:
                hostname     = self._to_empty_or_int(row["hostname"])
                host_ip      = self._to_empty_or_int(row["ip"])
                username     = self._to_empty_or_int(row["username"])
                password     = self._to_empty_or_int(row["password"])
                ssh_port     = self._to_empty_or_int(row["ssh_port"])
                key_path     = self._to_empty_or_int(row["key_path"])
                host_mac     = self._to_empty_or_int(row["mac"])
                vendor       = self._to_empty_or_int(row["vendor"])
                check_status = self._to_empty_or_int(row["check_status"])
                os_type      = self._to_empty_or_int(row["os"])
                version      = self._to_empty_or_int(row["version"])
                tcp_ports    = self._to_empty_or_int(row["tcp_ports"])
                do_status    = self._to_empty_or_int(row["do_status"])

                if not self._is_need_check(check_status, do_status):
                    logging.info("Skip to check host %s." % host_ip)
                    logging.debug("Host %s status: "
                                 "check status is %s, do status "
                                 "is %s, force check is %s" % (
                                     host_ip, check_status,
                                     do_status, self.force_check))
                    continue

                if not self._can_check(
                        host_ip, username, password, key_path):
                    continue

                logging.info("Beginning to collect %s "
                             "information..." % host_ip)

                collect_os_type = os_type.upper()

                total_check_hosts.append("[%s]%s" % (
                        collect_os_type, host_ip))

                try:
                    if collect_os_type == LINUX:
                        host_info = LinuxHostController(
                            host_ip, ssh_port, username,
                            password, key_path,
                            self.linux_report_path)
                        host_info.get_linux_host_info()
                    elif collect_os_type == WINDOWS:
                        host_info = WindowsHostCollector(
                            host_ip, username, password,
                            self.windows_report_path)
                        host_info.get_windows_host_info()
                    elif collect_os_type == VMWARE:
                        if not ssh_port:
                            ssh_port = 443
                        host_info = VMwareHostController(
                            host_ip, ssh_port, username, password,
                            self.vmware_report_path)
                        host_info.get_all_info()
                    else:
                        raise OSError("Unsupport os type %s "
                                      "if host %s" % (
                                          collect_os_type, host_ip))

                    success_hosts.append("[%s]%s" % (
                        collect_os_type, host_ip))
                except Exception as e:
                    logging.warn(
                            "Hosts [%s]%s collect failed, "
                            "due to:" % (collect_os_type, host_ip))
                    logging.exception(e)
                    failed_hosts.append("[%s]%s" % (
                        collect_os_type, host_ip))

                hosts.loc[index, "do_status"] = "success"
                hosts.to_csv(self.host_file, index=False)
                logging.info("Sucessfully collect %s "
                             "information." % host_ip)

                if collect_os_type == VMWARE:
                    host_info.show_collection_report()

            except Exception as e:
                logging.exception(e)
                logging.error("Check %s failed, please check it host info."
                              % host_ip)
                hosts.loc[index, "do_status"] = "failed"
                hosts.to_csv(self.host_file, index=False)

        logging.info("Sucessfully collect hosts info.")

        self._save_insensitive_scan_report(hosts)
        output_path = os.path.join(self.output_path, REPORT_PATH_NAME)
        macs = GenerateMac(output_path)
        macs.save_to_yaml()

        logging.info("===========Summary==========")

        logging.info(
                "Total %s host(s) in list, "
                "Need to check %s host(s), "
                "success %s hosts, "
                "failed %s hosts." % (
                    len(hosts),
                    len(total_check_hosts),
                    len(success_hosts),
                    len(failed_hosts)))

        if success_hosts:
            logging.debug("Success hosts: %s" % success_hosts)

        if failed_hosts:
            logging.info("Failed hosts: %s" % failed_hosts)

        logging.info("============================")

    def package(self):
        # Clean sensitive file before package
        self._clean()

        # Also package runtime log file into package
        logging.info("Copying log file into collection info path...")
        log_path = os.path.abspath(
                os.path.join(self.coll_path, os.pardir))
        log_files = "%s/*.log" % log_path
        for f in glob.glob(log_files):
            logging.info("Copying %s to %s..." % (f, self.coll_path))
            shutil.copy(f, self.coll_path)

        logging.info("Packing of collection info path %s to %s..."
                     % (self.coll_path, self.report_full_path))
        os.chdir(self.output_path)
        shutil.make_archive(self.report_basename, "zip", self.coll_path)

    def _save_insensitive_scan_report(self, hosts):
        logging.info("Saving insensitive scan "
                     "report in %s" % self.scan_report_path)
        hosts[["hostname",
               "ip",
               "mac",
               "vendor",
               "os",
               "version",
               "tcp_ports",
               "check_status",
               "do_status"]].to_csv(self.scan_report_path, index=False)
        logging.info("Save insensitive scan report done.")

    def _prepare(self):
        # Clean host collection base path if force check
        if os.path.exists(self.coll_path) and self.force_check:
            logging.info("Deleting existing host "
                    "collection path %s..." % self.coll_path)
            shutil.rmtree(self.coll_path)
            logging.info("Delete existing host "
                    "collection path %s Succesfully" % self.coll_path)

        # Prepare to create report directories
        for report_path in [self.linux_report_path,
                            self.windows_report_path,
                            self.vmware_report_path]:
            if not os.path.exists(report_path):
                logging.info("Creating directory %s..." % report_path)
                os.makedirs(report_path)

    def _clean(self):
        """Remove senstive files"""
        logging.info("Cleanning sensitive file before package...")
        for clean_path in [self.linux_report_path,
                           self.windows_report_path,
                           self.vmware_report_path]:
            for filename in SENSITIVE_FILES:
                clean_file = os.path.join(clean_path, filename)
                if os.path.exists(clean_file):
                    logging.info("Deleting file %s..." % clean_file)
                    os.remove(clean_file)
                    logging.info("Delete file %s done." % clean_file)
        logging.info("Clean sensitive file Succesfully.")

    def _parse_host_file(self):
        data = pd.read_csv(self.host_file)
        return data

    def _to_empty_or_int(self, value):
        """Convert to none or int

        Convert float nan to None
        Convert float type to integer
        Return string as it is
        """
        if pd.isnull(value):
            return ""
        elif isinstance(value, float):
            return int(value)
        else:
            return value

    def _is_need_check(self, check_status, do_status):
        if check_status.upper() == "CHECK":
            if do_status.upper() == "SUCCESS" and not self.force_check:
                return False
            else:
                return True
        else:
            return False

    def _can_check(self, host_ip, username, password, key_path):
        """Return True if authentication fields is enough"""
        if not username:
            logging.warn("Skip to collect %s information due to "
                         "username is not given." % (host_ip, username))
            return False

        if not password and not key_path:
            logging.warn("Skip to collect %s information due to "
                         "password or key is not given." % host_ip)
            return False

        return True
