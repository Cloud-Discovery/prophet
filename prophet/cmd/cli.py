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

import logging
import os

from flask_script import Manager

from prophet import app
from prophet import utils
from prophet.controller.linux_host import LinuxHostController
from prophet.controller.vmware import VMwareHostController


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

# Load vmware host management command
vmware_host_manager = Manager(app, usage="VMware host management")
manager.add_command("vmware_host", vmware_host_manager)


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


def main():
    manager.run()


if __name__ == "__main__":
    main()
