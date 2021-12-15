# -*- coding=utf8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2019 OnePro Cloud (Shanghai) Ltd.
#
# Authors: Ray <ray.sun@oneprocloud.com>
#
# Copyright (c) 2019 This file is confidential and proprietary.
# All Rights Resrved, OnePro Cloud (Shanghai) Ltd (http://www.oneprocloud.com).


"""Generate report class"""

import os
import logging
import pandas as pd

# DEFAULT_NA = ["N/A", None]
BASIC_INFO_CSV_FILE = "basic_info.csv"
ANALYSIS_XLS_FILE = "analysis.xlsx"

RECORD_FIELDS = (
    ("host_type", "平台类型"),
    ("hostname", "主机名"),
    ("vm_name", "VMware主机名"),
    ("conn_ip", "IP"),
    ("conn_mac", "Mac"),
    ("os", "操作系统类型"),
    ("os_version", "操作系统版本"),
    ("os_bit", "操作系统位数"),
    ("os_kernel", "操作系统内核版本"),
    ("cpu_info", "CPU"),
    ("cpu_cores", "CPU核数"),
    ("memory_info", "内存"),
    ("total_mem", "总内存(MB)"),
    ("free_mem", "剩余内存(MB)"),
    ("disk_info", "磁盘信息"),
    ("disk_count", "磁盘数量"),
    ("disk_total_size", "磁盘总容量(GB)"),
    ("disk_used_size", "磁盘使用量(GB)"),
    ("partition_info", "分区信息"),
    ("nic_info", "网卡信息"),
    ("boot_type", "启动方式"),
    ("vt_platform", "虚拟化类型"),
    ("vt_platform_ver", "虚拟化版本"),
    ("vt_drs_on", "是否开启了DRS(VMware)"),
    ("vt_ha_on", "是否开启了HA(VMware)"),
    ("tcp_ports", "当前开放的端口"),
    ("support_full_sync", "支持全量同步"),
    ("support_delta_sync", "支持增量同步"),
    ("support_agent", "是否支持Agent迁移"),
    ("support_agentless", "是否支持Agentless迁移"),
    ("check_result", "检查成功或失败原因")
)

REPORT_EXT_FIELDS = (
    ("support_agent_or_agentless", "是否支持Agent or Agentless迁移"),
    ("migration_check", "是否支持迁移"),
    ("take_time", "迁移耗时")
)

REPORT_FIELDS = RECORD_FIELDS[:-3] + REPORT_EXT_FIELDS


class Report(object):

    def __init__(self, dirname):
        self.dirname = dirname
        self.frames = pd.DataFrame(columns=[x[0] for x in REPORT_FIELDS])
        self.macs = []

    def save_to_xlsx(self):
        xls_file = os.path.join(self.dirname, ANALYSIS_XLS_FILE)
        logging.info("Saving report to %s..." % xls_file)
        csv_file = os.path.join(self.dirname, BASIC_INFO_CSV_FILE)
        logging.info("Loading %s ..." % csv_file)
        df = pd.read_csv(csv_file)
        self._analye(df)
        # headers = ["MAC", "平台类型", "主机名", "是否支持迁移", "迁移耗时"]
        headers = [x[1] for x in REPORT_FIELDS]
        self.frames.to_excel(xls_file, index=None, header=headers)
        logging.info("Successfully saved %s." % xls_file)

    def _analye(self, frames):
        for _, row in frames.iterrows():
            logging.debug("Analye row %s" % row)
            if row["conn_mac"] not in self.macs:
                self._append_row(row)
                self.macs.append(row["conn_mac"])
            else:
                self._update_row(row, row["conn_mac"])

    def _append_row(self, row):
        if not pd.isnull(row["support_agent"]):
            _agent_tag = row["support_agent"]
        elif not pd.isnull(row["support_agentless"]):
            _agent_tag = row["support_agentless"]
        else:
            logging.warn("Not support agent or agentless.")
            return

        if row["check_result"] == "Check successful.":
            supports = ("Support %s. " % _agent_tag)
        else:
            supports = ("Not support %s, reason is %s. "
                        % (_agent_tag, row["check_result"]))

        # Bandwith 40Mbps to 500Mbps
        _min = round(float(row["disk_total_size"]) * 8 * 1000 / (40 * 60), 2)
        _max = round(float(row["disk_total_size"]) * 8 * 1000 / (500 * 60), 2)
        take_time = "Maybe takes %s to %s mins" % (_max, _min)
        self.frames = self.frames.append([{
            "host_type": row["host_type"],
            "hostname": row["hostname"],
            "vm_name": row["vm_name"],
            "conn_ip": row["conn_ip"],
            "conn_mac": row["conn_mac"],
            "os": row["os"],
            "os_version": row["os_version"],
            "os_bit": row["os_bit"],
            "os_kernel": row["os_kernel"],
            "cpu_info": row["cpu_info"],
            "cpu_cores": row["cpu_cores"],
            "memory_info": row["memory_info"],
            "total_mem": row["total_mem"],
            "free_mem": row["free_mem"],
            "disk_info": row["disk_info"],
            "disk_count": row["disk_count"],
            "disk_total_size": row["disk_total_size"],
            "disk_used_size": row["disk_used_size"],
            "partition_info": row["partition_info"],
            "nic_info": row["nic_info"],
            "boot_type": row["boot_type"],
            "vt_platform": row["vt_platform"],
            "vt_platform_ver": row["vt_platform_ver"],
            "vt_drs_on": row["vt_drs_on"],
            "vt_ha_on": row["vt_ha_on"],
            "tcp_ports": row["tcp_ports"],
            "support_full_sync": row["support_full_sync"],
            "support_delta_sync": row["support_delta_sync"],
            "support_agent_or_agentless": _agent_tag,
            "migration_check": supports,
            "take_time": take_time}], ignore_index=True)

    def _update_row(self, row, mac):
        _agent_tag = None
        if not pd.isnull(row["support_agent"]):
            _agent_tag = row["support_agent"]
        elif not pd.isnull(row["support_agentless"]):
            _agent_tag = row["support_agentless"]
        else:
            logging.warn("Not support agent or agentless.")
            return

        if row["check_result"] == "Check successful.":
            supports = ("Support %s. " % _agent_tag)
        else:
            supports = ("Not support %s, reason is %s. "
                        % (_agent_tag, row["check_result"]))
        self.frames.loc[self.frames.conn_mac == mac, "migration_check"] += supports
        self.frames.loc[self.frames.conn_mac == mac, "support_agent_or_agentless"] += \
            ',' + _agent_tag


class Record(object):

    def __init__(self, info=None):
        self.headers = [x[0] for x in RECORD_FIELDS]
        self.data = dict(zip(
            [x[0] for x in RECORD_FIELDS],
            [None] * len(RECORD_FIELDS)))

        if info and isinstance(info, dict):
            for k, v in info.items():
                if k in self.data.keys():
                    self.data[k] = v
        self.content = self._serialize()

    def _serialize(self):
        content = []
        for head in self.headers:
            content.append(self.data[head])
        return content

    def append_to_csv(self, file_path):
        logging.debug("Appending data %s to %s." % (self.content, file_path))
        df = pd.DataFrame([self.content])
        if not os.path.exists(file_path):
            df.to_csv(file_path,
                      mode="w",
                      header=self.headers,
                      index=False,
                      encoding='utf-8')
        else:
            df.to_csv(file_path,
                      mode="a",
                      header=None,
                      index=False,
                      encoding='utf-8')
