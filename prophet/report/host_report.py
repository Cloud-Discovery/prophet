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

"""Host report generation class"""

import glob
import logging
import shutil
import tempfile
import os
import yaml
import zipfile

import pandas as pd
from stevedore import driver

HOST_PARSER_NAMESPACE = "host_parser"

# Size define
MB = 1024 * 1024

# TODO(Ray): This should be placed in seperate config files that we can
# generate different report based on mapping
MAPPING = (
    ("basic.host_type", "平台类型"),
    ("basic.hostname", "主机名"),
    ("basic.vm_name", "VMware主机名"),
    ("basic.conn_ip", "IP"),
    ("basic.conn_mac", "Mac"),
    ("os.os", "操作系统类型"),
    ("os.os_version", "操作系统版本"),
    ("os.os_bit", "操作系统位数"),
    ("os.os_kernel", "操作系统内核版本"),
    ("disks.boot_type", "启动方式"),
    ("cpu.cpu_info", "CPU"),
    ("cpu.cpu_cores", "CPU核数"),
    ("memory.memory_info", "内存"),
    ("memory.total_mem", "总内存(GB)"),
    ("memory.free_mem", "剩余内存(GB)"),
    ("disks.count", "磁盘数量"),
    ("disks.total_size", "磁盘总容量(GB)"),
    ("disks.disks", "磁盘信息"),
    ("disks.partitions", "分区信息"),
    ("networks.count", "网卡数量"),
    ("networks.nics", "网卡信息"),
    ("vt.vt_platform", "虚拟化类型"),
    ("vt.vt_platform_ver", "虚拟化版本"),
    ("vt.vt_esxi", "ESXi服务器")
)

# When generate report, all these fields value will converted to GB
SIZE_FIELDS = ["total_mem", "free_mem", "total_size", "size"]

# default report name
REPORT_NAME = "analysis_report.csv"


class HostReporter(object):

    def __init__(self, package_file, output_path, clean, report_name=REPORT_NAME):
        self.package_file = package_file
        self.output_path = output_path
        self.clean = clean
        self.report_name = report_name

        # Report lines
        self._report_lines = []

        # Tmp dir to unzip files
        self.work_path = tempfile.mktemp()

    @property
    def report_path(self):
        return os.path.join(self.output_path, self.report_name)

    def analysis(self):
        logging.info("Precheck for packages...")
        self._precheck()

        logging.info("Uncompress package file to analysis")
        self._unzip()

        yaml_files = glob.glob("%s/**/*.yaml" % self.work_path)
        for yaml_file in yaml_files:
            logging.info("Parsing yaml file %s..." % yaml_file)
            # In yaml, root key is the filename without extension
            root_key = os.path.splitext(
                    os.path.basename(yaml_file))[0]
            with open(yaml_file, "r") as yf:
                content = yaml.safe_load(yf.read())

                for root_key, infos in content.items():
                    os_type = None
                    if "os_type" in infos:
                        os_type = infos["os_type"]
                        payload = infos["results"]
                        logging.info("Load host parser driver %s" % os_type)
                        driver_manager = driver.DriverManager(
                            namespace=HOST_PARSER_NAMESPACE,
                            name=os_type,
                            invoke_on_load=False
                        )
                        try:
                            parser = driver_manager.driver(payload)
                            values = parser.parse()
                            self._generate_report_lines(values)
                        except Exception as e:
                            logging.warning("Skip to parse %s, "
                                            "due to:" % yaml_file)
                            logging.exception(e)
                    else:
                        logging.info("Skip to parser %s" % yaml_file)
                        continue

        logging.info("Generating report in %s..." % self.report_path)
        self._generate_report()

        if self.clean:
            self._clean()

    def _precheck(self):
        logging.info("Checking package file %s is exists..."
                     % self.package_file)
        if not os.path.exists(self.package_file):
            raise FileNotFoundError("Package file %s is "
                                    "not found." % self.package_file)
        logging.info("Package file %s is exists." % self.package_file)

        logging.info("Checking package file %s "
                     "is zip format..." % self.package_file)
        self.zip_package_file = zipfile.ZipFile(self.package_file)
        if self.zip_package_file.testzip():
            raise zipfile.BadZipFile("Package file %s is bad zip file."
                                     % self.package_file)
        logging.info("Package file %s is zip format" % self.package_file)

    def _unzip(self):
        logging.info("Unzipping package file %s into %s..." % (
            self.package_file, self.work_path))
        for names in self.zip_package_file.namelist():
            self.zip_package_file.extract(names, self.work_path)
        logging.info("Unzip package file %s into %s done." % (
            self.package_file, self.work_path))

    def _generate_report_lines(self, values):
        """Generate report"""
        lines = []
        for x in MAPPING:
            field = x[0]
            lines.append(self._get_value(field, values))

        self._report_lines.append(lines)

    def _get_value(self, path, values):
        paths = path.split(".")

        data = values
        for p in paths:
            data = data.get(p, None)

            # break loop if data is None
            if not data:
                break

            if p in SIZE_FIELDS:
                data = self._convert_size(data)

            if isinstance(data, list):
                data = self._format_output_list(data)
                break

        return data

    def _format_output_list(self, data):
        """Format list type with | seperate in report"""
        ret_lines = []
        for d in data:
            lines = []
            for key, item in d.items():
                value = d[key]
                if key in SIZE_FIELDS:
                    value = self._convert_size(value)
                lines.append(str(value))
            ret_lines.append("|".join(lines))

        return "\n".join(ret_lines)

    def _convert_size(self, value, unit=MB):
        return '{0:.2f}'.format(value / MB)

    def _generate_report(self):
        columns = [x[1] for x in MAPPING]
        dt = pd.DataFrame(self._report_lines, columns=columns)
        dt.to_csv(self.report_path, encoding="utf-8-sig", index=False)

    def _clean(self):
        logging.info("Deleting temp dir %s..." % self.work_path)
        shutil.rmtree(self.work_path)
        logging.info("Temp dir %s deleted." % self.work_path)
