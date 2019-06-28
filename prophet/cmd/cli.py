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
import glob
import logging
import os

from flask_script import Manager
from itertools import islice

from prophet import app
from prophet import utils
from prophet.controller.linux_host import LinuxHostController, LinuxHostReport
from prophet.controller.vmware import VMwareHostController, VMwareHostReport
from prophet.controller.network import NetworkController
from prophet.controller.windows_host import WindowsHostCollector, \
                                            WindowsHostReport

# Global settings for logging, default is debug and verbose
log_format = "%(asctime)s %(process)s %(levelname)s [-] %(message)s"
log_level = logging.DEBUG
logging.basicConfig(
    format=log_format,
    level=log_level)

# Global settings for manager
manager = Manager(app)

# Load linux host management command
linux_host_manager = Manager(app, usage="Linux host management")
manager.add_command("linux_host", linux_host_manager)

# Load windows host management command
windows_host_manager = Manager(app, usage="Windows host management")
manager.add_command("windows_host", windows_host_manager)

# Load vmware host management command
vmware_host_manager = Manager(app, usage="VMware host management")
manager.add_command("vmware_host", vmware_host_manager)

# Load host report management command
host_report_manager = Manager(app, usage="Host report management")
manager.add_command("host_report", host_report_manager)

# Import hosts info file management command
import_file_manager = Manager(app, usage="Import hosts info file management")
manager.add_command("import_file", import_file_manager)

# Scan network and generate initial hosts report
network_manager = Manager(app, usage="Scan network with single ip or cidr")
manager.add_command("network", network_manager)


@linux_host_manager.option("-i",
                           "--ip",
                           dest="ip",
                           default=None,
                           required=True,
                           help="Input linux host ip")
@linux_host_manager.option("-u",
                           "--username",
                           dest="username",
                           default=None,
                           required=True,
                           help="Input linux host username")
@linux_host_manager.option("-p",
                           "--password",
                           dest="password",
                           default=None,
                           required=False,
                           help="Input linux host passowrd")
@linux_host_manager.option("-k",
                           "--key",
                           dest="key_path",
                           default=None,
                           required=False,
                           help="Input linux host key path")
@linux_host_manager.option("-P",
                           "--port",
                           dest="port",
                           default=22,
                           required=False,
                           help="Input linux host port")
@linux_host_manager.option("-d",
                           "--data-path",
                           dest="data_path",
                           default=None,
                           required=True,
                           help="Input Info File Path")
def create_linux_host(ip, port, username, password, key_path, data_path):
    config_file_path = os.path.join(data_path,
                                    'collect_infos',
                                    'linux_hosts')

    if not os.path.exists(config_file_path):
        logging.info("Cannot found %s directory in system, create it." %
                     config_file_path)
        os.makedirs(config_file_path)
    host_info = LinuxHostController(ip,
                                    port,
                                    username,
                                    password,
                                    key_path,
                                    config_file_path)
    host_info.get_linux_host_info()


@windows_host_manager.option("-i",
                             "--ip",
                             dest="ip",
                             default=None,
                             required=True,
                             help="Input windows host ip")
@windows_host_manager.option("-u",
                             "--username",
                             dest="username",
                             default=None,
                             required=True,
                             help="Input windows host username")
@windows_host_manager.option("-p",
                             "--password",
                             dest="password",
                             default=None,
                             required=True,
                             help="Input windows host passowrd")
@windows_host_manager.option("-d",
                             "--data-path",
                             dest="data_path",
                             default=None,
                             required=True,
                             help="Input Info File Path")
def create_windows_host(ip, username, password, data_path):
    config_file_path = os.path.join(data_path,
                                    'collect_infos',
                                    'windows_hosts')
    if not os.path.exists(config_file_path):
        logging.info("Cannot found %s directory in system, create it." %
                     config_file_path)
        os.makedirs(config_file_path)
    host_info = WindowsHostCollector(ip,
                                     username,
                                     password,
                                     config_file_path)
    host_info.get_windows_host_info()


@host_report_manager.option("-i",
                            "--input_path",
                            dest="input_path",
                            default=None,
                            required=True,
                            help="Input linux host "
                            "collection info path")
@host_report_manager.option("-o",
                            "--output_path",
                            dest="output_path",
                            default=None,
                            required=True,
                            help="Output linux host "
                            "analysis info path")
def create_host_report(input_path, output_path):
    logging.info("Checking input_path:%s......" % input_path)
    if not os.path.exists(input_path):
        raise OSError("Input path %s is not exists" % input_path)

    if not os.path.exists(output_path):
        raise OSError("Output path %s is not exists" % output_path)

    if len(glob.glob("%s/*.yaml" % input_path)) == 0:
        raise Exception("Input path:%s, not exists .yaml "
                        "host data file" % input_path)
    logging.info("Check input path completed")
    host_reports = {"linux": LinuxHostReport,
                    "windows": WindowsHostReport,
                    "vmware": VMwareHostReport}
    for host_type in host_reports:
        all_files = glob.glob("%s/*_%s.yaml" % (input_path, host_type))
        if len(all_files) != 0:
            logging.info("Found %s %s files: %s" % (len(all_files),
                                                    host_type,
                                                    all_files))
            run_analysis = host_reports[host_type](input_path,
                                                   output_path,
                                                   all_files)
            run_analysis.get_report()
    logging.info("Host report completed.")


@import_file_manager.option("-i",
                            "--input_path",
                            dest="input_path",
                            default=None,
                            required=True,
                            help="Input hosts info file path")
@import_file_manager.option("-o",
                            "--output_path",
                            dest="data_path",
                            default=None,
                            required=True,
                            help="Output info File Path")
def import_file(input_path, data_path):
    logging.info("Checking input_path:%s......" % input_path)
    if not os.path.exists(input_path):
        raise OSError("Input path %s is not exists." % input_path)

    if not os.path.exists(data_path):
        raise OSError("Output path %s is not exists." % data_path)

    with open(input_path) as f:
        reader = csv.reader(f)
        for line in islice(reader, 1, None):
            ip = line[0]
            port = line[4]
            username = line[1]
            password = line[2]
            key_path = line[3]
            if line[5] == 'linux':
                if len(port) == 0:
                    port = '22'
                if len(password) == 0:
                    password = None
                if len(key_path) == 0:
                    key_path = None
                create_linux_host(ip, port, username, password,
                                  key_path, data_path)
            elif line[5] == 'windows':
                create_windows_host(ip, username, password, data_path)
            elif line[5] == 'vmware':
                if len(port) == 0:
                    port = '443'
                create_vmware_host(ip, port, username, password,
                                   data_path)
            else:
                logging.warning("%s type error, please check." % ip)


@vmware_host_manager.option("-i",
                            "--ip",
                            dest="ip",
                            default=None,
                            required=True,
                            help="Input vcenter host ip")
@vmware_host_manager.option("-P",
                            "--port",
                            dest="port",
                            default=443,
                            required=False,
                            help="Input vcenter host port")
@vmware_host_manager.option("-u",
                            "--username",
                            dest="username",
                            default=None,
                            required=True,
                            help="Input vcenter host username")
@vmware_host_manager.option("-p",
                            "--password",
                            dest="password",
                            default=None,
                            required=True,
                            help="Input vcenter host password")
@vmware_host_manager.option("-d",
                            "--data-path",
                            dest="data_path",
                            required=True,
                            help="Collect VMS info path")
def create_vmware_host(ip, port, username, password, data_path):
    collect_vms_path = os.path.join(data_path,
                                    "collect_infos",
                                    "vmware_hosts")
    if not os.path.exists(collect_vms_path):
        logging.info("Cannot found %s directory in system, create it." %
                     collect_vms_path)
        utils.mkdir_p(collect_vms_path)
    vmware = VMwareHostController(ip,
                                  port,
                                  username,
                                  password,
                                  collect_vms_path)
    vmware.get_all_info()
    logging.info("Collect all VCenter infos sucessful.")

@network_manager.option("-h",
                        "--host",
                        dest="host",
                        required=True,
                        help="Input host, ex: 192.168.10.0/24, "
                             "192.168.10.1-2")
@network_manager.option("-a",
                        "--arg",
                        dest="arg",
                        default="-O -sS",
                        required=False,
                        help="Arguments for nmap, for more detailed, "
                             "please check nmap document")
@network_manager.option("-d",
                        "--data-path",
                        dest="data_path",
                        required=True,
                        help="Generate initial host report path")
def scan(host, arg, data_path):
    if not os.path.exists(data_path):
        logging.info("Creating data path %s..." % data_path)
        utils.mkdir_p(data_path)
    network = NetworkController(host, arg, data_path)
    network.gen_report()
    #vmware = VMwareHostController(ip,
    #                              port,
    #                              username,
    #                              password,
    #                              collect_vms_path)
    #vmware.get_all_info()
    #logging.info("Collect all VCenter infos sucessful.")


def main():
    manager.run()


if __name__ == "__main__":
    main()
