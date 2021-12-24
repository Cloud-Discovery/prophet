# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2019 OnePro Cloud (Shanghai) Ltd.
#
# Authors: Ray <ray.sun@oneprocloud.com>
#
# Copyright (c) 2019 This file is confidential and proprietary.
# All Rights Resrved, OnePro Cloud (Shanghai) Ltd (http://www.oneprocloud.com).


"""Central task schedule class"""

import logging
import tempfile
import os
import shutil
import yaml
import zipfile

import pandas as pd

from prophet import exceptions
from prophet.controller.analysis.linux_host import LinuxHost
from prophet.controller.analysis.vmware_host import VMwareHost
from prophet.controller.analysis.windows_host import WindowsHost
from prophet.controller.analysis.report import Record, Report

SCAN_REPORT_FILENAME = "scan_hosts.csv"
LINUX_REPORT_PATH_NAME = "linux_hosts"
WINDOWS_REPORT_PATH_NAME = "windows_hosts"
VMWARE_REPORT_PATH_NAME = "vmware_hosts"
MAC_INFO_FILENAME = "mac_info.yaml"

# In mac list, we use absolute path, but when we try to analysis,
# maybe the difference path, so we need to split path according to
# prefix path name
SPLIT_PATH_PREFIX = "host_collection_info"

# os types
LINUX = "LINUX"
WINDOWS = "WINDOWS"
VMWARE = "VMWARE"

# default extension
YAML = "yaml"


class ReportJob(object):

    def __init__(self, package_file, output_path, clean=True):
        self.package_file = package_file
        self.output_path = output_path
        self.clean = clean

        self._precheck()

    @property
    def linux_yaml_files(self):
        return os.path.join(self.tmp_dir,
                            LINUX_REPORT_PATH_NAME,
                            "*.%s" % YAML)

    @property
    def windows_yaml_files(self):
        return os.path.join(self.tmp_dir,
                            WINDOWS_REPORT_PATH_NAME,
                            "*.%s" % YAML)

    @property
    def vmware_yaml_path(self):
        return os.path.join(self.tmp_dir,
                            VMWARE_REPORT_PATH_NAME)

    @property
    def vmware_yaml_files(self):
        return os.path.join(self.vmware_yaml_path,
                            "*.%s" % YAML)

    def _precheck(self):
        logging.info("Checking package file %s is exists..."
                     % self.package_file)
        if not os.path.exists(self.package_file):
            raise exceptions.FileNotFoundError("Package file %s is "
                                    "not found." % self.package_file)
        logging.info("Package file %s is exists." % self.package_file)

        logging.info("Checking package file %s "
                     "is zip format..." % self.package_file)
        self.zip_package_file = zipfile.ZipFile(self.package_file)
        if self.zip_package_file.testzip():
            raise zipfile.BadZipFile("Package file %s is bad zip file."
                                     % self.package_file)
        logging.info("Package file %s is zip format" % self.package_file)

    def _prepare(self):
        logging.info("Creating temp dir for zip uncompressed...")
        self.tmp_dir = tempfile.mktemp()
        if not os.path.exists(self.tmp_dir):
            os.makedirs(self.tmp_dir)
        logging.info("Temp dir %s created." % self.tmp_dir)

        self._unzip()

    def _clean(self):
        logging.info("Deleting temp dir %s..." % self.tmp_dir)
        shutil.rmtree(self.tmp_dir)
        logging.info("Temp dir %s deleted." % self.tmp_dir)

    def _unzip(self):
        logging.info("Unzipping package file %s into %s..." % (
            self.package_file, self.tmp_dir))
        for names in self.zip_package_file.namelist():
            self.zip_package_file.extract(names, self.tmp_dir)
        logging.info("Unzip package file %s into %s done." % (
            self.package_file, self.tmp_dir))

    def analysis(self):
        self._prepare()

        mac_file = os.path.join(self.tmp_dir, MAC_INFO_FILENAME)
        basic_csv_file = os.path.join(self.output_path, "basic_info.csv")

        logging.info("Open mac file %s for analysis..." % mac_file)
        with open(mac_file, "r") as yf:
            data = yaml.safe_load(yf.read())
            logging.debug("Get data %s" % data)

        for _, i in data.items():
            yamls = i['yamls']
            for y in yamls:
                yaml_file_path = y['file_path']
                file_paths = yaml_file_path.split(SPLIT_PATH_PREFIX)
                yaml_real_path = "%s%s" % (
                        self.tmp_dir, file_paths[1])
                logging.info("Parsing yaml "
                             "file %s..." % yaml_real_path)
                logging.debug(yaml_real_path.__class__)
                with open(yaml_real_path, "r") as yf:
                    yd = yaml.safe_load(yf.read())
                logging.info("Parse yaml file %s "
                             "succesfully" % yaml_real_path)

                if y['os_type'] == 'vmware':
                    host_data = VMwareHost(yd).get_info()
                elif y['os_type'] == 'linux':
                    host_data = LinuxHost(yd).get_info()
                elif y['os_type'] == 'windows':
                    host_data = WindowsHost(yd).get_info()
                host_data["tcp_ports"] = i['tcp_ports']
                Record(host_data).append_to_csv(basic_csv_file)
        # Save to csv and pdf
        Report(self.output_path).save_to_xlsx()

        if self.clean:
            self._clean()

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
