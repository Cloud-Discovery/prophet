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

"""Collect Linux detailed information using ansible

 Steps:

     1. Test host connection
     2. Generate ansible configs and run ansible commands
     3. Save results to yaml file
     
"""


import logging
import os
import paramiko
import socket
import tempfile

from prophet.ansible_api import AnsibleApi
from prophet.collector.base import BaseHostCollector


class LinuxCollector(BaseHostCollector):

    def collect(self):
        logging.info("Precheck for Linux %s connection" % self.ip)
        self._precheck()

        logging.info("Collecting host %s info..." % self.ip)
        host_info = self._collect_data()
        logging.debug("Collect Linux %s returns: %s" % (self.ip,
                                                       host_info))
        logging.info("Collected host %s info" % self.ip)

        if not host_info["success"]:
            raise Exception("Collect Linux %s failed, please "
                            "check yaml file for detailed" % self.ip)
        else:
            logging.info("Collect Linux %s info success" % self.ip)

        save_values = {self.root_key: host_info}
        self.save_to_yaml(self.collect_path, save_values)

        return [host_info]

    def _precheck(self):
        logging.info("Checking %s SSH info..." % self.ip)
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            if self.key_path is None:
                logging.info("Checking input password.")
                ssh.connect(self.ip,
                            self.ssh_port,
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
                            self.ssh_port,
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
            logging.error("Connect port: %s failed, "
                          "please check host %s port."
                          % (self.ssh_port, self.ip))
            raise e
        except IOError as e:
            logging.exception(e)
            logging.error("Input private_key_file_path %s "
                          "not found, please check it."
                          % self.key_path)
            raise e

    def _collect_data(self):
        logging.info("Prepare config file for Linux collection...")

        # NOTE(Ray): For parallel runs, we can't write the temp hosts
        # file into the same path, use tempfile to generate temp dir 
        # and delete the dir after collection
        with tempfile.TemporaryDirectory() as tmpdirname:
            hosts_path = os.path.join(tmpdirname, "hosts")
            logging.info("Write ansible hosts to %s..." % hosts_path)

            content = ("[linux]\n"
                       "%s "
                       "ansible_ssh_user=%s "
                       "ansible_ssh_pass=%s "
                       "ansible_ssh_port=%s "
                       "ansible_ssh_private_key_file=%s\n"
                       % (self.ip,
                          self.username,
                          self.password,
                          self.ssh_port,
                          self.key_path))
            logging.debug("Ansible hosts: %s" % content)

            with open(hosts_path, "w") as fh:
                fh.write(content)

            logging.info("Running ansible command...")
            ansible_api = AnsibleApi()
            ansible_api.set_options(
                hosts_file=hosts_path,
                exec_hosts=self.ip,
                tasks=self._get_ansible_tasks()
            )
            return ansible_api.run_task()

    def _get_ansible_tasks(self):
        tasks = [
            {
                "action": {
                    "module": "setup"
                }
            }
        ]
        return tasks
