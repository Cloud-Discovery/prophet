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
