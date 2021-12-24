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

import logging

from prophet import utils
from prophet.collector.base import BaseHostCollector

WMI_COMMANDS = [
    "Win32_ComputerSystem",
    "Win32_OperatingSystem",
    "Win32_DiskPartition",
    "Win32_Processor",
    "Win32_PhysicalMemory",
    "Win32_NetworkAdapterConfiguration WHERE IPEnabled=True",
    "Win32_LogicalDisk WHERE DriveType = 3",
    "Win32_DiskDrive",
    "Win32_Process",
    "Win32_PerfFormattedData_Tcpip_NetworkInterface",
    "Win32_PerfRawData_Tcpip_NetworkInterface"
]
WMI_DELIMITER = "|ONEPROCLOUD|"


class WindowsCollector(BaseHostCollector):
    """Collect windows hosts info"""

    def collect(self):
        """Collect information from WMI interface"""
        collect_infos = {}
        for command in WMI_COMMANDS:
            logging.info("Running Windows command %s..." % command)
            stdout, stderr = utils.execute(
                'wmic --delimiter "{}" '
                '-U {}%{} //{} "SELECT * FROM {}"'.format(
                    WMI_DELIMITER, self.username,
                    self.password, self.ip, command),
                shell=True
            )
            if stderr:
                logging.warn("Skip to save result of command %s, "
                             "return error message: %s" % (
                                 command, stderr))
            else:
                logging.info(
                        "Running Windows command %s success" % command)
                collect_infos.update(self._parse_result(stdout))

        # Save to yaml file
        save_values = {self.root_key: collect_infos}
        self.save_to_yaml(self.collect_path, save_values)

        return [collect_infos]

    def _parse_result(self, result):
        """Save wmi result in dict
        
        The structure is ClassName: Result, the classname is the
        first line of the returns. Save the other lines as a list.
        """

        lines = result.split("\n")
        if not lines:
            logging.warn("Can not split result to lines, "
                         "please check the command returns.")
            return

        logging.debug("Trying to parser result: %s" % lines)

        # return payload: classname: lines
        payload = {}

        class_line = lines.pop(0)
        class_line_split = class_line.split(":")
        if not class_line_split[0] == "CLASS":
            logging.warn(
                    "Can not find CLASS "
                    "in class line: %s" % class_line)
            class_name = class_line
        else:
            class_name = class_line_split[1].strip()
            logging.info("Found class name %s." % class_name)
        payload[class_name] = []

        title_line = lines.pop(0)
        keys = title_line.split(WMI_DELIMITER)
        for line in lines:
            values = line.split(WMI_DELIMITER)
            if len(values) == len(keys):
                payload[class_name].append(dict(zip(keys, values)))
            else:
                logging.debug("Not enough value in this "
                              "line %s, ignore." % line)

        return payload
