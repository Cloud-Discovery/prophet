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

import lib.ansible_api as getapi
from config_file import ConfigFile


class LinuxHostController(object):

    def __init__(self, ip, port, username, password, key_path, data_path):
        self.ip = ip
        self.port = int(port)
        self.username = username
        self.password = password
        self.key_path = key_path
        self.data_path = os.path.join(data_path, 'hosts.cfg')

    def get_linux_host_info(self):
        self._verify_conn()
        self._save_ssh_info()
        self._ansible_api()

    def _verify_conn(self):
        logging.info("Checking %s SSH info......." % self.ip)
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            if self.key_path is None:
                logging.info("Check input is password")
                ssh.connect(self.ip,
                            self.port,
                            self.username,
                            self.password,
                            timeout=20)
                logging.info("Check %s SSH info succeed" % self.ip)
                return ssh
            if self.password is None:
                logging.info("Check input is key_path")
                private_key = paramiko.RSAKey.from_private_key_file(
                              os.path.expanduser(self.key_path)
                              )
                ssh.connect(self.ip,
                            self.port,
                            self.username,
                            pkey=private_key,
                            timeout=20)
                logging.info("Check %s SSH info succeed" % self.ip)
                return ssh
        except paramiko.AuthenticationException as err:
            logging.error("Host %s input username or password err, "
                          "please check" % self.ip)
            raise err
        except socket.timeout as err:
            logging.error("Host %s connect failed, "
                          "please check input IP info or "
                          "Check host status" % self.ip)
            raise err
        except socket.error as err:
            logging.error("Connect port:%s failed, "
                          "please check host %s port "
                          "num" % (self.port, self.ip))
            raise err
        except IOError as err:
            logging.error("Input private_key_file_path %s "
                          "not found, please check" % self.key_path)
            raise err

    def _save_ssh_info(self):
        # write config_file
        logging.info("Writing ip:%s, port:%s, username:%s, "
                     "password:%s, key_path:%s To %s......." % (
                         self.ip,
                         self.port,
                         self.username,
                         self.password,
                         self.key_path,
                         self.data_path))
        config = ConfigFile(self.data_path)
        host_info = {
                'port': self.port,
                'username': self.username,
                'password': self.password,
                'key_path': self.key_path
                }
        header = 'Linux_' + self.ip
        config.set(header, host_info)
        logging.info("Write SSH info succeed To %s" % self.data_path)

        # write ansible hosts file
        host_path = os.path.join(os.path.dirname(self.data_path),
                                 'hosts')
        logging.info("Writing ip:%s, username:%s, password:%s, "
                     "port:%s, key_path:%s To %s......." % (
                         self.ip,
                         self.username,
                         self.password,
                         self.port,
                         self.key_path,
                         host_path))
        host_info = ("[linux]\n%s ansible_ssh_user=%s "
                     "ansible_ssh_pass=%s "
                     "ansible_ssh_port=%s "
                     "ansible_ssh_private_key_file=%s\n" % (
                         self.ip,
                         self.username,
                         self.password,
                         self.port,
                         self.key_path))

        with open(host_path, "w") as ansible_host:
            ansible_host.write(host_info)
        logging.info("Write SSH info succeed to %s" % host_path)

    def _ansible_api(self):
        logging.info("Geting %s all info, please wait......." % self.ip)
        run_api = getapi.AnsibleApi(self.data_path)
        host_list = self.ip
        task_list = [dict(action=dict(module='setup'))]
        info_path = self.data_path
        run_api.runansible(host_list, task_list, info_path)
        logging.info("%s info collection finished" % self.ip)
