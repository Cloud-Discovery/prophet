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

import glob
import logging
import os
import pandas as pd
import shutil
import time

from flask_script import Manager

from prophet import app
from prophet.controller.linux_host import LinuxHostController, LinuxHostReport
from prophet.controller.vmware import VMwareHostController, VMwareHostReport
from prophet.controller.network import NetworkController
from prophet.controller.windows_host import WindowsHostCollector, \
                                            WindowsHostReport
from prophet.cmd.test_openstack_api import TestOpenStackDriver

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
host_report_manager = Manager(app, usage="Host reports management")
manager.add_command("host_report", host_report_manager)

# Import hosts info file management command
import_file_manager = Manager(app, usage="Import host info files management")
manager.add_command("import_file", import_file_manager)

# Scan network and generate initial hosts report
network_manager = Manager(app, usage="Scan network with single ip or cidr")
manager.add_command("network", network_manager)

# Check Cloud APIs(OpenStack) command
check_cloud_manager = Manager(app, usage="Check Cloud APIs")
manager.add_command("check", check_cloud_manager)


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
@linux_host_manager.option("-o",
                           "--output-path",
                           dest="output_path",
                           default=None,
                           required=True,
                           help="Input Info File Path")
def create_linux_host(ip, port, username, password, key_path, output_path):
    config_file_path = os.path.abspath(
        os.path.join(output_path,
                     "collect_infos",
                     "linux_hosts")
    )
    if not os.path.exists(config_file_path):
        logging.info("Cannot found %s directory in system, "
                     "create it." % config_file_path)
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
@windows_host_manager.option("-o",
                             "--output-path",
                             dest="output_path",
                             default=None,
                             required=True,
                             help="Input Info File Path")
def create_windows_host(ip, username, password, output_path):
    config_file_path = os.path.abspath(
        os.path.join(
            output_path,
            "collect_infos",
            "windows_hosts")
    )
    if not os.path.exists(config_file_path):
        logging.info("Cannot found %s directory in system, "
                     "create it." % config_file_path)
        os.makedirs(config_file_path)
    host_info = WindowsHostCollector(ip,
                                     username,
                                     password,
                                     config_file_path)
    host_info.get_windows_host_info()


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
@vmware_host_manager.option("-o",
                            "--output-path",
                            dest="output_path",
                            required=True,
                            help="Collect VMS info path")
def create_vmware_host(ip, port, username, password, output_path):
    config_file_path = os.path.abspath(
        os.path.join(
            output_path,
            "collect_infos",
            "vmware_hosts")
    )
    if not os.path.exists(config_file_path):
        logging.info("Cannot found %s directory in system, "
                     "create it." % config_file_path)
        os.makedirs(config_file_path)
    host_info = VMwareHostController(ip,
                                     port,
                                     username,
                                     password,
                                     config_file_path)
    host_info.get_all_info()


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
    if not os.path.exists(input_path):
        raise OSError("Input path %s is not exists."
                      % input_path)
    if not os.path.exists(output_path):
        raise OSError("Output path %s is not exists."
                      % output_path)
    if len(glob.glob("%s/*.yaml" % input_path)) == 0:
        raise Exception("Files of yaml not exist in path %s."
                        % input_path)
    input_abspath = os.path.abspath(input_path)
    output_abspath = os.path.abspath(output_path)
    host_reports = {
        "linux": LinuxHostReport,
        "windows": WindowsHostReport,
        "vmware": VMwareHostReport
    }
    logging.info("Begain make host reports.")
    for host_type, host_obj in host_reports.items():
        host_files = glob.glob(
            "%s/*_%s.yaml"
            % (input_abspath, host_type)
        )
        if len(host_files) != 0:
            logging.info(
                "Found %s %s files: %s."
                % (len(host_files), host_type, host_files)
            )
            run_analysis = host_obj(input_abspath,
                                    output_abspath,
                                    host_files)
            run_analysis.get_report()
    logging.info("Make host reports completed.")


def host_collection(host_type, ip, username, output_path,
                    port=None, password=None, key_path=None):
    logging.info("Collect %s (%s) infomation."
                 % (ip, host_type))
    logging.debug(
        "host_type=%s "
        "ip=%s "
        "username=%s "
        "output_path=%s "
        "port=%s "
        "password=%s "
        "key_path=%s "
        % (host_type,
           ip,
           username,
           output_path,
           port,
           password,
           key_path)
    )
    if "Linux" == host_type:
        create_linux_host(
            ip, port, username,
            password, key_path, output_path
        )
    elif "Windows" == host_type:
        create_windows_host(
            ip, username,
            password, output_path
        )
    elif "VMware" == host_type:
        if not port:
            port = "443"
        create_vmware_host(
            ip, port, username,
            password, output_path
        )
    else:
        raise OSError("Error %s os type is invalid." % ip)


def empty_str_to_none(string):
    if not string:
        return None
    return string


def pandas_value_to_python_value(pd_value):
    if pd.isnull(pd_value):
        return ""
    elif float == type(pd_value):
        return int(pd_value)
    else:
        return str(pd_value)


def scan_hosts_csv_process(csv_file_path, output_path, force_check):
    data = pd.read_csv(csv_file_path)
    for index, row in data.iterrows():
        try:
            # hostname     = pandas_value_to_python_value(row["hostname"])
            host_ip      = pandas_value_to_python_value(row["ip"])           # noqa
            username     = pandas_value_to_python_value(row["username"])     # noqa
            password     = pandas_value_to_python_value(row["password"])     # noqa
            ssh_port     = pandas_value_to_python_value(row["ssh_port"])     # noqa
            key_path     = pandas_value_to_python_value(row["key_path"])     # noqa
            # host_mac     = pandas_value_to_python_value(row["mac"])
            # vendor       = pandas_value_to_python_value(row["vendor"])
            check_status = pandas_value_to_python_value(row["check_status"])
            os_type      = pandas_value_to_python_value(row["os"]) # noqa
            # version      = pandas_value_to_python_value(row["version"])
            # tcp_ports    = pandas_value_to_python_value(row["tcp_ports"])
            do_status    = pandas_value_to_python_value(row["do_status"])    # noqa

            if "CHECK" == check_status.upper():
                if not username:
                    logging.warning("Skip %s. Username is need."
                                    % host_ip)
                    continue
                if not password and not key_path:
                    logging.warning("Skip %s. Password or key_path is need."
                                    % host_ip)
                    continue
                if "TRUE" == force_check.upper():
                    pass
                else:
                    if "SUCCESS" == do_status.upper():
                        continue
                host_collection(
                    os_type, host_ip, username, output_path,
                    port=empty_str_to_none(ssh_port),
                    password=empty_str_to_none(password),
                    key_path=empty_str_to_none(key_path)
                )
                data.loc[index, "do_status"] = "success"
                data.to_csv(csv_file_path, index=False)
        except Exception as e:
            logging.exception(e)
            logging.error("Check %s failed, please check it host info."
                          % host_ip)
            data.loc[index, "do_status"] = "failed"
            data.to_csv(csv_file_path, index=False)


@import_file_manager.option("-i",
                            "--input_path",
                            dest="input_path",
                            default=None,
                            required=True,
                            help="Input host info file path")
@import_file_manager.option("-o",
                            "--output_path",
                            dest="output_path",
                            default=None,
                            required=True,
                            help="Output info file Path")
@import_file_manager.option("-f",
                            "--force_check",
                            dest="force_check",
                            default="",
                            required=False,
                            help="Force check all host")
def batch_collection(input_path, output_path, force_check):
    if not os.path.exists(input_path):
        raise OSError("Input path %s is not exists." % input_path)
    if not os.path.exists(output_path):
        raise OSError("Output path %s is not exists." % output_path)

    logging.info("Begin collect information of hosts in %s."
                 % input_path)
    scan_hosts_csv_process(input_path, output_path, force_check)
    logging.info("All hosts information is collected.")

    run_time = time.strftime(
        "%Y%m%d%H%M%S",
        time.localtime(time.time())
    )
    coll_path = os.path.join(output_path, "collect_infos")
    zip_file_name = ("collection_info" + '_' + run_time)
    zip_file_path = os.path.join(output_path, zip_file_name)
    logging.info("Packing of collection info path %s to %s..."
                 % (coll_path, output_path))
    shutil.make_archive(zip_file_path, "zip", coll_path)


@network_manager.option("-h",
                        "--host",
                        dest="host",
                        required=True,
                        help="Input host, example: "
                             "192.168.10.0/24, "
                             "192.168.10.1-2")
@network_manager.option("-a",
                        "--arg",
                        dest="arg",
                        default="-O -sS",
                        required=False,
                        help="Arguments for nmap, for more detailed, "
                             "please check nmap document")
@network_manager.option("-o",
                        "--output-path",
                        dest="output_path",
                        required=True,
                        help="Generate initial host report path")
def scan(host, arg, output_path):
    if not os.path.exists(output_path):
        logging.info("Cannot found %s directory in system, "
                     "create it." % output_path)
        os.makedirs(output_path)
    network = NetworkController(host, arg, output_path)
    network.generate_report()


@check_cloud_manager.option("-u",
                            "--username",
                            dest="username",
                            required=True,
                            help="Username or access key")
@check_cloud_manager.option("-p",
                            "--password",
                            dest="password",
                            required=True,
                            help="Password or secret key")
@check_cloud_manager.option("-P",
                            "--projectname",
                            dest="projectname",
                            required=False,
                            help="Projectname, if necessary")
@check_cloud_manager.option("-U",
                            "--auth_url",
                            dest="auth_url",
                            required=True,
                            help="Auth url or endpoint")
@check_cloud_manager.option("-r",
                            "--region",
                            dest="region",
                            required=True,
                            help="Region name")
@check_cloud_manager.option("-d",
                            "--domain",
                            dest="domain",
                            required=False,
                            help="domain-name, example: Default")
def cloud(username, password, projectname, auth_url,
               region, domain):
    params = {
        'os_username': username,
        'os_password': password,
        'os_project_name': projectname,
        'os_auth_url': auth_url,
        'os_region_name': region,
        'os_domain_name': domain,
        'verbose': False,
        'network_id': None,
        'volume_type': None,
        'volume_availability_zone': None,
        'debug': False,
        'flavor_id': None,
    }
    obj = TestOpenStackDriver(params)
    obj.run()


def main():
    manager.run()


if __name__ == "__main__":
    main()
