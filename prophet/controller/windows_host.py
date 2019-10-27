#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2017 Prophet Tech (Shanghai) Ltd.
#
# Authors: Li ZengYuan <lizengyuan@prophetech.cn>
#
# Copyright (c) 2017. This file is confidential and proprietary.
# All Rights Reserved, Prophet Tech (Shanghai) Ltd(http://www.prophetech.cn).
#

import csv
import logging
import os
import yaml

from prophet.controller.config_file import ConfigFile, CsvDataFile
from prophet import utils

WMI_COMMANDS = [
    "Win32_Computersystem",
    "Win32_Operatingsystem",
    "Win32_DiskPartition",
    "Win32_Processor",
    "Win32_PhysicalMemory",
    "win32_NetworkAdapterConfiguration WHERE IPEnabled=True",
    "win32_LogicalDisk WHERE DriveType = 3",
    "win32_DiskDrive",
    "Win32_Process"
]
WMI_DELIMITER = "|ONEPROCLOUD|"


class WindowsHostCollector(object):
    """Collect windows hosts info"""

    def __init__(self, ip, username, password, output_path):
        self.ip = ip
        self.username = username
        self.password = str(password)
        self.output_path = os.path.join(
            output_path, ip + "_windows" + ".yaml")

    def get_windows_host_info(self):
        self._save_host_conn_info()
        self._save_info_to_yaml()

    def _save_host_conn_info(self):
        config_path = os.path.join(
            os.path.dirname(self.output_path),
            "hosts.cfg"
        )
        config = ConfigFile(config_path)
        host_info = {
            "username": self.username,
            "password": self.password
        }
        header = "Windows_" + self.ip
        logging.debug("Writing ip:%s, username:%s, password:%s to %s..."
                      % (self.ip, self.username, self.password, config_path))
        config.set(header, host_info)
        logging.info("Write SSH info sucess to %s." % config_path)

    def _save_info_to_yaml(self):
        logging.info("Starting get host %s info and write to %s..."
                     % (self.ip, self.output_path))
        config = ConfigFile(self.output_path)

        host_info = self._collect()
        header = 'Windows_' + self.ip
        config.set(header, host_info)
        logging.info("Writed host info sucess to %s." % self.output_path)

    def _collect(self):
        """Collect information from WMI interface"""
        collect_infos = {}
        for command in WMI_COMMANDS:
            logging.info("Running command %s..." % command)
            stdout, stderr = utils.execute(
                'wmic --delimiter "{}" -U {}%{} //{} "SELECT * FROM {}"'.format(
                    WMI_DELIMITER, self.username, self.password, self.ip, command),
                shell=True
            )
            if stderr:
                logging.warn("Skip to save result of command %s, "
                             "return error message: %s" % (
                                 command, stderr))
            else:
                collect_infos.update(self._parse_result(stdout))

        return collect_infos

    def _parse_result(self, result):
        """Save wmi result in dict
        
        The structure is ClassName: Result, the classname is the first line
        of the returns. Save the other lines as a list.
        """
        logging.debug("Trying to parser result: %s" % result)

        lines = result.split("\n")
        if not lines:
            logging.warn("Can not split result to lines, "
                         "please check the command returns.")
            return

        # return payload: classname: lines
        payload = {}

        class_line = lines.pop(0)
        class_line_split = class_line.split(":")
        if not class_line_split[0] == "CLASS":
            logging.warn("Can not find CLASS in class line: %s" % class_line)
            class_name = class_line
        else:
            class_name = class_line_split[1].strip()
            logging.info("Found class name %s." % class_name)
        payload[class_name] = []

        title_line = lines.pop(0)
        titles = title_line.split(WMI_DELIMITER)
        payload[class_name].append(titles)
        for line in lines:
            values = line.split(WMI_DELIMITER)
            if len(values) == len(titles):
                payload[class_name].append(values)
            else:
                logging.debug("Not enough value in this "
                              "line %s, ignore." % line)

        return payload
