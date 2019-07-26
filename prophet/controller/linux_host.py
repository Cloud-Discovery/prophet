#!/usr/bin/env python
# -*- coding=utf8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2019 Prophet Tech (Shanghai) Ltd.
#
# Authors: Ray <sunqi@prophetech.cn>
# Authors: Li ZengYuan <lizengyuan@prophetech.cn>
#
# Copyright (c) 2019 This file is confidential and proprietary.
# All Rights Resrved, Prophet Tech (Shanghai) Ltd (http://www.prophetech.cn).
#
# Collection Linux host info
#
# Steps:
#
#     1. Test host connectivity
#     2. Save SSH info
#     3. Get host info by AnsibleApi
#     4. Save AnsibleApi callback to user specified directory
#

import logging
import os
import paramiko
import socket
import yaml

from prophet.controller.config_file import ConfigFile, CsvDataFile
from prophet.controller.lib.ansible_api import AnsibleApi


class LinuxHostController(object):

    def __init__(self, ip, port, username, password, key_path, output_path):
        self.ip = ip
        self.port = int(port)
        self.username = username
        self.password = str(password)
        self.key_path = key_path
        self.output_path = os.path.join(output_path, "hosts.cfg")

    def get_linux_host_info(self):
        self._verify_conn()
        self._save_ssh_info()
        self.data_info = self._get_data_info()
        self._save_data_info(self.data_info)

    def _verify_conn(self):
        logging.info("Checking %s SSH info..." % self.ip)
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            if self.key_path is None:
                logging.info("Checking input password.")
                ssh.connect(self.ip,
                            self.port,
                            self.username,
                            self.password,
                            timeout=20)
                logging.info("Check %s SSH info sucess." % self.ip)
                return ssh
            if self.password is None:
                logging.info("Check input key.")
                private_key = paramiko.RSAKey.from_private_key_file(
                    os.path.expanduser(self.key_path)
                )
                ssh.connect(self.ip,
                            self.port,
                            self.username,
                            pkey=private_key,
                            timeout=20)
                logging.info("Check %s SSH info sucess." % self.ip)
                return ssh
        except paramiko.AuthenticationException as e:
            logging.exception(e)
            logging.error("Host %s input username or password error, "
                          "please check it." % self.ip)
            raise e
        except socket.timeout as e:
            logging.exception(e)
            logging.error("Host %s connect failed, "
                          "please check input ip or "
                          "check host status." % self.ip)
            raise e
        except socket.error as e:
            logging.exception(e)
            logging.error("Connect port:%s failed, "
                          "please check host %s port."
                          % (self.port, self.ip))
            raise e
        except IOError as e:
            logging.exception(e)
            logging.error("Input private_key_file_path %s "
                          "not found, please check it."
                          % self.key_path)
            raise e

    def _save_ssh_info(self):
        # write config_file
        logging.debug("Writing ip:%s, port:%s, username:%s, "
                      "password:%s, key_path:%s to %s..."
                      % (self.ip, self.port, self.username,
                         self.password, self.key_path, self.output_path))
        config = ConfigFile(self.output_path)
        host_info = {
            "port": self.port,
            "username": self.username,
            "password": self.password,
            "key_path": self.key_path
        }
        header = 'Linux_' + self.ip
        config.set(header, host_info)
        logging.info("Write SSH info sucess to %s." % self.output_path)

        # write ansible hosts file
        host_path = os.path.join(
            os.path.dirname(self.output_path),
            'hosts'
        )
        logging.info("Writing ip:%s, port:%s, username:%s, "
                     "password:%s, key_path:%s To %s..."
                     % (self.ip, self.port, self.username,
                        self.password, self.key_path, host_path))
        host_info = ("[linux]\n"
                     "%s "
                     "ansible_ssh_user=%s "
                     "ansible_ssh_pass=%s "
                     "ansible_ssh_port=%s "
                     "ansible_ssh_private_key_file=%s\n"
                     % (self.ip,
                        self.username,
                        self.password,
                        self.port,
                        self.key_path))
        with open(host_path, "w") as ansible_host:
            ansible_host.write(host_info)
        logging.info("Write SSH info sucess to %s" % host_path)

    def _get_data_info(self):
        logging.info("Geting %s all info, please wait..." % self.ip)
        ansible_api = AnsibleApi()
        hosts_file = os.path.join(
            os.path.dirname(self.output_path),
            "hosts"
        )
        tasks = [
            {
                "action": {
                    "module": "setup"
                }
            }
        ]
        ansible_api.set_options(
            hosts_file=hosts_file,
            exec_hosts=self.ip,
            tasks=tasks
        )
        data_info = ansible_api.run_task()
        logging.info("%s info collect finished." % self.ip)
        return data_info

    def _save_data_info(self, data_info):
        host_info_file_name = (self.ip + "_linux" + ".yaml")
        file_path = os.path.join(
            os.path.dirname(self.output_path),
            host_info_file_name
        )
        try:
            logging.info("Writing host %s info to %s..."
                         % (self.ip, file_path))
            with open(file_path, "w") as f:
                f.write(self.data_info)
                logging.info("Write host %s info to %s sucess."
                             % (self.ip, file_path))
            logging.info("Checking %s data info..." % file_path)
            with open(file_path) as host_info:
                data = yaml.load(host_info, Loader=yaml.FullLoader)
            if not data["success"]:
                raise Exception("Check %s data info failed, please "
                                "check the file information."
                                % file_path)
        except IOError as e:
            logging.exception(e)
            logging.error("Input save_file_info_path %s not found, "
                          "please check it." % self.output_path)
            raise e


class LinuxHostReport(object):

    def __init__(self, input_path, output_path, linux_files):
        self.input_path = input_path
        self.output_path = output_path
        self.linux_files = linux_files

    def get_report(self):
        for file in self.linux_files:
            data = self._get_data_info(file)
            host_ansible_info = list(
                data["success"].values()
            )[0]["ansible_facts"]
            hostname = self._get_hostname(host_ansible_info)
            address = self._get_address(host_ansible_info)
            version = self._get_version(host_ansible_info)
            cpu_num = self._get_cpu_num(host_ansible_info)
            tol_mem = self._get_total_mem(host_ansible_info)
            macaddr = self._get_macaddr(host_ansible_info)
            all_mount_list = self._get_mount_info(host_ansible_info)
            boot_type = self._get_boot_type(all_mount_list)
            migration_check = self._migration_check(
                host_ansible_info, all_mount_list, boot_type, version)
            self._write_data_to_csv(
                file, hostname, address, version,
                cpu_num, tol_mem, macaddr, all_mount_list,
                boot_type, migration_check)

    def _get_data_info(self, file):
        file_path = os.path.join(self.input_path, file)
        with open(file_path) as file_obj:
            data = yaml.load(file_obj, Loader=yaml.FullLoader)
        return data

    def _get_hostname(self, host_ansible_info):
        return host_ansible_info["ansible_hostname"]

    def _get_address(self, host_ansible_info):
        return host_ansible_info["ansible_default_ipv4"]["address"]

    def _get_version(self, host_ansible_info):
        return [
            host_ansible_info["ansible_distribution"],
            host_ansible_info["ansible_distribution_version"],
            host_ansible_info["ansible_kernel"]
        ]

    def _get_cpu_num(self, host_ansible_info):
        return str(host_ansible_info["ansible_processor_vcpus"])

    def _get_total_mem(self, host_ansible_info):
        return str(int(host_ansible_info["ansible_memtotal_mb"]) / 1024)

    def _get_free_mem(self, host_ansible_info):
        return int(host_ansible_info["ansible_memfree_mb"]) / 1024

    def _get_macaddr(self, host_ansible_info):
        return host_ansible_info["ansible_default_ipv4"]["macaddress"]

    def _get_volume_info(self, host_ansible_info):
        volumes = {}
        for volume_name in host_ansible_info["ansible_devices"].keys():
            str_name = str(volume_name)
            if str_name.startswith("sd") \
               or str_name.startswith("vd") \
               or str_name.startswith("hd"):
                volume_size = host_ansible_info[
                    "ansible_devices"][volume_name]["size"]
                volumes[volume_name] = volume_size
        return volumes

    def _get_mount_info(self, host_ansible_info):
        mount_info = {}
        for mount in host_ansible_info["ansible_mounts"]:
            mount_name = mount["device"]
            if "sd" in mount_name \
               or "hd" in mount_name \
               or "vd" in mount_name \
               or "mapper" in mount_name:
                mount_info["mount_name"] = [
                    "filesystem:%s" % mount["fstype"],
                    "mount_path:%s" % mount["mount"],
                    "tol_size(G):%s" % str(
                        int(mount["size_total"]) / 1024 / 1024 / 1024
                        )[:4],
                    "use_size(G):%s" % str((
                        int(mount["size_total"]) - int(mount["size_available"])
                        ) / 1024 / 1024 / 1024)[:4],
                    "ava_size(G):%s" % str(
                        int(mount["size_available"]) / 1024 / 1024 / 1024
                        )[:4],
                    "ava_ratio:%s" % (
                        "%.0f%%" % (
                            int(mount["size_available"]) / int(mount["size_total"]) * 100  # noqa
                            )
                        )
                ]
        return mount_info

    def _get_boot_type(self, mount_info):
        efi_type = "mount_path:/boot/efi"
        for mount_info in list(mount_info.values()):
            if efi_type in mount_info:
                return "efi"
        return "bios"

    def _migration_check(self, host_ansible_info,
                         mount_info, boot_type, version):
        support_synchronization = "Yes"
        support_increment = "Yes"
        migration_proposal = ""
        # Judge version
        if version[0] == "CentOS" or version[0] == "RedHat":
            # Judge el version
            if int(version[1].split('.', 1)[0]) < 6:
                support_synchronization = "No"
                support_increment = "No"
                migration_proposal = ("Host version %s%s not support "
                                      "migration. "
                                      % (version[0], version[1]))
        elif version[0] == "SLES":
            if int(version[1].split(".", 1)[0]) < 11:
                support_synchronization = "No"
                support_increment = "No"
                migration_proposal = ("Host version %s%s not support "
                                      "migration. "
                                      % (version[0], version[1]))
        else:
            support_synchronization = "No"
            support_increment = "No"
            migration_proposal = ("Host verison %s not support "
                                  "migration. " % version[0])
        # Judge vgs num
        if "ansible_lvm" in list(host_ansible_info.keys()):
            host_vgs = list(host_ansible_info["ansible_lvm"]["vgs"].keys())
            if len(host_vgs) > 1:
                support_synchronization = "No"
                support_increment = "No"
                migration_proposal = ("Host is lvm and has %s vg, not "
                                      "support migration. " % len(host_vgs))
        # Judge partition available
        for mount_info in mount_info.values():
            if int(mount_info[5].split(":", 1)[1].strip("%")) < 13:
                support_synchronization = "No"
                support_increment = "No"
                migration_proposal = (
                    migration_proposal +
                    "Disk %s partition available "
                    "space less than 13%%, migration "
                    "is not supported, please clean "
                    "some data. "
                    % (mount_info[1].split(":", 1)[1]))
            # Judge file system
            if (mount_info[0].split(":", 1)[1]) == "btrfs":
                support_synchronization = "No"
                support_increment = "No"
                migration_proposal = (
                    migration_proposal +
                    "Host file system is btrfs, not "
                    "support migration. ")
        # Judge boot type
        if "efi" in boot_type:
            migration_proposal = (
                migration_proposal +
                "Boot type:EFI, cloud not supported, "
                "so migrate to the cloud start system "
                "failed, need fix boot type is BIOS.")
        if migration_proposal.strip() == "":
            migration_proposal = "Check successful"
        return (
            support_synchronization,
            support_increment,
            migration_proposal
        )

    def _write_data_to_csv(self, file, hostname, address, version,
                           cpu_num, tol_mem, macaddr, all_mount_list,
                           boot_type, migration_check):
        host_data = [{
            "host_type": "Linux",
            "hostname": hostname,
            "version": version,
            "address": address,
            "macaddr": macaddr,
            "cpu_num": cpu_num,
            "tol_mem(G)": tol_mem,
            "disk_info": all_mount_list,
            "boot_type": boot_type,
            "support_synchronization": migration_check[0],
            "support_increment": migration_check[1],
            "migration_proposal": migration_check[2]
        }]
        logging.info("Writing %s migration proposal..." % file)
        logging.debug(host_data)
        output_file = os.path.join(self.output_path, "analysis.csv")
        csv_config = CsvDataFile(host_data, output_file)
        csv_config.write_data_to_csv()
        logging.info("Write to %s finish." % output_file)
