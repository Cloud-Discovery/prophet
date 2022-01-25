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

"""Batch job for running mix host type collection"""

import glob
import logging
import os
import shutil
import time

import numpy as np
import pandas as pd
from stevedore import driver

# VMware
DEFAULT_VMWARE_PORT = 443

# Sensitive files
SENSITIVE_FILES = ["hosts.cfg", "host_exsi.cfg", "hosts"]

# Collection result report
COLLECTION_REPORT = "collection_report.csv"

# Driver namespace
HOST_COLLECTOR_NAMESPACE = "host_collector"

class HostCollector(object):

    def __init__(self, host_file, output_path,
                 force_check, package_name):
        self.host_file = host_file
        self.output_path = output_path
        self.force_check = force_check
        self.package_name = package_name

        # Generate compressed pacakge name
        self._zip_package_name = None

        # For summary display for each collection
        self.total_check_hosts = []
        self.success_hosts = []
        self.failed_hosts = []

        # For summary detailed display
        self.summaries = []


    @property
    def collection_path(self):
        """Base path to save all files"""
        return os.path.join(self.output_path, self.package_name)

    @property
    def collection_report_path(self):
        """Path to save collection result"""
        return os.path.join(self.collection_path, COLLECTION_REPORT)

    @property
    def zip_package_name(self):
        """Compressed pacakge path for final collections"""
        if not self._zip_package_name:
            timestamp = time.strftime(
                    "%Y%m%d%H%M%S", time.localtime(time.time()))
            self._zip_package_name = "%s_%s" % (
                    self.package_name, timestamp)

        return self._zip_package_name


    def collect_hosts(self):
        """Collect hosts detailed based on given host list file

        Host with check status and do status is not success will be
        collected. If force check is given, do status is ignored.
        """

        # Validation and prepare
        self._prepare()

        logging.info("Collecting hosts information "
                     "from %s..." %  self.host_file)

        # NOTE(Ray): Use pandas to load csv file, use
        # keep_default_na to keep empty cell value, reference
        # github issues:
        #
        # https://github.com/pandas-dev/pandas/issues/1450
        hosts = pd.read_csv(self.host_file, keep_default_na=False)

        logging.info("Found %s host(s) in csv..." % len(hosts))
        for index, row in hosts.iterrows():
            logging.debug("Current row is: %s" % row.to_dict())

            try:
                host_ip      = row["ip"]
                username     = row["username"]
                password     = row["password"]
                ssh_port     = row["ssh_port"]
                key_path     = row["key_path"]
                host_mac     = row["mac"]
                check_status = row["check_status"]
                os_type      = row["os"].upper()
                version      = row["version"]
                tcp_ports    = row["tcp_ports"]
                do_status    = row["do_status"]

                # host tag for display in log
                host_tag = "[%s]%s" % (os_type, host_ip)

                # Validate if host need to collect
                if not self._is_need_check(check_status, do_status):
                    logging.info("Skip to check host %s" % host_tag)
                    continue

                # Check if host can be check with authentication
                if not self._can_check(
                        host_ip, username, password, key_path):
                    continue

                logging.info("Collecting host %s..." % host_tag)
                self.total_check_hosts.append(host_tag)

                # Run collect method from each driver
                driver_manager = driver.DriverManager(
                        namespace=HOST_COLLECTOR_NAMESPACE,
                        name=os_type,
                        invoke_on_load=False)
                # TODO(Ray): tcp ports should be saved into yaml file
                c = driver_manager.driver(
                        ip=host_ip,
                        username=username,
                        password=password,
                        ssh_port=ssh_port,
                        key_path=key_path,
                        os_type=os_type,
                        tcp_ports=tcp_ports,
                        output_path=self.collection_path)
                c.collect()

                collect_summary = c.get_summary()

                if collect_summary:
                    self.summaries.append(collect_summary)

                hosts.loc[index, "do_status"] = "success"
                hosts.to_csv(self.host_file, index=False)
                self.success_hosts.append(host_tag)

                logging.info("Collect host %s success" % host_tag)
            except Exception as e:
                logging.error("Host %s check failed "
                              "due to:" % host_ip)
                logging.exception(e)
                hosts.loc[index, "do_status"] = "failed"
                hosts.to_csv(self.host_file, index=False)
                self.failed_hosts.append(host_tag)

            # Save collection report and index file
            try:
                self._save_collection_report(row)
            except Exception as e:
                logging.error("Saving report failed due to:")
                logging.exception(e)

        self._show_summary()

    def package(self):
        """Create compressed pacakge for hosts collection"""
        # NOTE(Ray): Because of the complex of user environment, we
        # collect running logs to help us improve our project
        logging.info("Copying log file into collection info path...")

        log_files = "%s/*.log" % self.output_path

        for f in glob.glob(log_files):
            logging.info("Copying %s to %s..." % (
                f, self.collection_path))
            shutil.copy(f, self.collection_path)

        logging.info("Compressed pacakge in %s, "
                     "filename is %s.zip..." % (
                         self.output_path, self.zip_package_name))
        os.chdir(self.output_path)
        shutil.make_archive(self.zip_package_name, "zip",
                            self.collection_path)

    def _save_collection_report(self, row):
        """Save collection result to csv"""
        logging.info("Saving collection report "
                     "to %s" % self.collection_report_path)
        # TODO(Ray): This method should be implemented, the original
        # logical save the whole hosts here, but we only want our
        # collection hosts
        logging.info("Saved collection "
                     "report to %s" % self.collection_report_path)

    def _prepare(self):
        # Validate host file is exists
        if not os.path.exists(self.host_file):
            raise OSError("Host file %s is "
                          "not exists." % self.host_file)

        # Create output path if not exists
        if not os.path.exists(self.output_path):
            logging.info("Creating output path %s...")
            os.makedirs(self.output_path)
            logging.info("Created output path %s success")

        # Clean host collection base path if force check, otherwise
        # elder collection path will be kept
        if os.path.exists(self.collection_path) and self.force_check:
            logging.info("Deleting existing host "
                    "collection path %s..." % self.collection_path)
            shutil.rmtree(self.collection_path)
            logging.info("Delete existing host collection "
                         "path %s Succesfully" % self.collection_path)

        if not os.path.exists(self.collection_path):
            logging.info("Creating collection path %s..." % self.collection_path)
            os.makedirs(self.collection_path)

    def _is_need_check(self, check_status, do_status):
        """Return True is host need to do collection"""
        logging.debug("Current host check status is %s, do status "
                      "is %s, force check is %s" % (
                      check_status, do_status, self.force_check))
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

    def _show_summary(self):
        """Show summary after each running"""
        logging.info("===========Summary==========")
        logging.info(
                "Need to check %s host(s), "
                "success %s hosts, "
                "failed %s hosts." % (
                    len(self.total_check_hosts),
                    len(self.success_hosts),
                    len(self.failed_hosts)))

        if self.success_hosts:
            logging.debug("Success hosts: %s" % self.success_hosts)

        if self.failed_hosts:
            logging.info("Failed hosts: %s" % self.failed_hosts)

        # Show summary detailed message if have
        if self.summaries:
            logging.info("===========Detailed==========")
            for s in self.summaries:
                if s["info"]:
                    for info in s["info"]:
                        logging.info(info)
                logging.info("------------------------------")
                if s["debug"]:
                    for info in s["debug"]:
                        logging.debug(info)
        logging.info("============================")
