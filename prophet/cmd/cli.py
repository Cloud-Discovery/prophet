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
from prophet.controller.linux_host import LinuxHostController


# Global settings for logging, default is debug and verbose
log_format = "%(asctime)s %(process)s %(levelname)s [-] %(message)s"
log_level = logging.DEBUG
logging.basicConfig(
    format=log_format,
    level=log_level)

# Global settings for manager
manager = Manager()
manager.add_option("-d", "--data-path", dest="data_path", required=True)

# Load user management command
linux_host_manager = Manager(app, usage="Linux host management")
manager.add_command("linux_host", linux_host_manager)

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
                           help="Input linux host password")
def create_linux_host(ip, username, password):
    LinuxHostController.create_connection(ip, username, password)


def main():
    manager.run()


if __name__ == "__main__":
    main()
