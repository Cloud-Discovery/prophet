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
# import time
import yaml

import paramiko
import socket

from config_file import ConfigFile, CsvDataFile
import lib.ansible_api as getapi

status = 'success'
host_facts = 'ansible_facts'


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
        self.data_info = self._ansible_api()
        self._save_data_info(self.data_info)

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

    def _save_data_info(self, data_info):
        # save host data info to yaml
        # run_time = time.strftime("%Y%m%d%H%M%S",
        #                         time.localtime(time.time()))
        # host_info_file_name = (self.ip + '_' + run_time +
        #                       '_linux' + '.yaml')
        host_info_file_name = (self.ip + '_linux' + '.yaml')
        file_path = os.path.join(os.path.dirname(self.data_path),
                                 host_info_file_name)
        try:
            logging.info("Writing host %s info to "
                         "%s......." % (self.ip, file_path))
            with open(file_path, 'w') as f:
                f.write(self.data_info)
                logging.info("Write host %s info to %s "
                             "succeed" % (self.ip, file_path))
            logging.info("Checking %s data info" % file_path)
            with open(file_path) as host_info:
                data = yaml.load(host_info)
            if not data['success']:
                raise Exception("Check %s data info failed, please "
                                "check the file information" % file_path)
        except IOError as err:
            logging.error("Input save_file_info_path %s "
                          "not found, please check" % self.data_path)
            raise err

    def _ansible_api(self):
        logging.info("Geting %s all info, please wait......." % self.ip)
        run_api = getapi.AnsibleApi(self.data_path)
        host_list = self.ip
        task_list = [dict(action=dict(module='setup'))]
        data_info = run_api.runansible(host_list, task_list)
        logging.info("%s info collection finished" % self.ip)
        return data_info


class LinuxHostReport(object):

    def __init__(self, input_path, output_path, linux_file):
        self.linux_file = linux_file
        self.input_path = input_path
        self.output_path = output_path

    def get_report(self):
        for i in self.linux_file:
            self.data = self._get_data_info(i)
            self.hostname = self._get_hostname(self.data)
            self.address = self._get_address(self.data)
            self.version = self._get_version(self.data)
            self.cpu_num = self._get_cpu_num(self.data)
            self.tol_mem = self._get_total_mem(self.data)
            self.macaddr = self._get_macaddr(self.data)
            self.all_mount_list = self._get_mount_info(self.data)
            self.boot_type = self._get_boot_type(self.all_mount_list)
            self.migration_check = self._migration_check(
                    self.data, self.all_mount_list,
                    self.boot_type, self.version)
            self._write_data_to_csv(i, self.hostname,
                                    self.address, self.version,
                                    self.cpu_num, self.tol_mem,
                                    self.macaddr,
                                    self.all_mount_list, self.boot_type,
                                    self.migration_check)

    def _get_data_info(self, i):
        file_path = os.path.join(self.input_path, i)
        logging.info("Opening %s....." % i)
        with open(file_path) as host_info:
            data = yaml.load(host_info)
        logging.info("Geting designated data.....")
        return data

    def _write_data_to_csv(self, i, hostname, address, version,
                           cpu_num, tol_mem, macaddr,
                           all_mount_list, boot_type, migration_check):
        host_data = [
                {'host_type': 'Linux',
                 'hostname': self.hostname,
                 'address': self.address,
                 'version': self.version,
                 'cpu_num': self.cpu_num,
                 'tol_mem(G)': self.tol_mem,
                 'macaddr': self.macaddr,
                 'disk_info': self.all_mount_list,
                 'boot_type': self.boot_type,
                 'support_synchronization': self.migration_check[0],
                 'support_increment': self.migration_check[1],
                 'migration_proposal': self.migration_check[2]}
                ]
        logging.info("Writing migration proposal.....")
        file_name = 'analysis' + '.csv'
        output_file = os.path.join(self.output_path, file_name)
        csv_config = CsvDataFile(host_data, output_file)
        csv_config.write_data_to_csv()
        logging.info("%s migration proposal completed" % i)

    def _get_hostname(self, data):
        logging.info("Geting hostname info.....")
        hostname = (self.data[status].values()[0][host_facts]
                    ['ansible_hostname'])
        logging.info("Geted hostname:%s" % hostname)
        return hostname

    def _get_address(self, data):
        logging.info("Geting address info.....")
        address = (self.data[status].values()[0][host_facts]
                   ['ansible_default_ipv4']['address'])
        logging.info("Geted address:%s" % address)
        return address

    def _get_version(self, data):
        logging.info("Geting version info.....")
        versions = (self.data[status].values()[0][host_facts]
                    ['ansible_distribution'])
        el_version = (self.data[status].values()[0]
                      [host_facts]['ansible_distribution_version'])
        kernel = (self.data[status].values()[0][host_facts]
                  ['ansible_kernel'])
        logging.info("Geted version:%s, el_version:%s, "
                     "kernel:%s" % (versions,
                                    el_version,
                                    kernel))
        return [versions, el_version, kernel]

    def _get_cpu_num(self, data):
        logging.info("Geting cpu num.....")
        cpu_num = (str(self.data[status].values()[0]
                   [host_facts]['ansible_processor_vcpus']))
        logging.info("Geted cpu num:%s" % cpu_num)
        return cpu_num

    def _get_total_mem(self, data):
        logging.info("Geting tolal mem.....")
        host_tolal_mem = (str(self.data[status].values()[0]
                          [host_facts]['ansible_memtotal_mb'] / 1024))
        logging.info("Geted tolal mem:%sG" % host_tolal_mem)
        return host_tolal_mem

    def _get_free_mem(self, data):
        logging.info("Geting free mem.....")
        host_free_mem = (self.data[status].values()[0]
                         [host_facts]['ansible_memfree_mb'] / 1024)
        logging.info("Geted free mem:%sG" % host_free_mem)
        return host_free_mem

    def _get_macaddr(self, data):
        logging.info("Geting macaddr info.....")
        host_macaddr = (self.data[status].values()[0]
                        [host_facts]['ansible_default_ipv4']
                        ['macaddress'])
        logging.info("Geted macaddr:%s" % host_macaddr)
        return host_macaddr

    def _get_volume_info(self, data):
        logging.info("Geting volume info.....")
        all_volume_list = {}
        all_volume_info = (self.data[status].values()[0]
                           [host_facts]['ansible_devices'].keys())
        for all_volume in all_volume_info:
            if str(all_volume).startswith('sd') or \
                    str(all_volume).startswith('vd') or \
                    str(all_volume).startswith('hd'):
                one_volume_size = (self.data[status].values()[0]
                                   [host_facts]['ansible_devices']
                                   [all_volume]['size'])
                all_volume_list[all_volume] = one_volume_size
        logging.info("Geted volume info:%s" % all_volume_list)
        return all_volume_list

    def _get_mount_info(self, data):
        logging.info("Geting volume mount info.....")
        all_mount_list = {}
        all_mount_info = (self.data[status].values()[0]
                          [host_facts]['ansible_mounts'])
        for mount_num in range(len(all_mount_info)):
            mount_name = all_mount_info[mount_num]['device']
            if 'sd' in mount_name or 'hd' in mount_name or \
                    'vd' in mount_name or 'mapper' in mount_name:
                all_mount_list[mount_name] = [
                        'filesystem:%s' % all_mount_info
                        [mount_num]['fstype'],
                        'mount_path:%s' % all_mount_info
                        [mount_num]['mount'],
                        'tol_size(G):%s' % str(all_mount_info[mount_num]
                                               ['size_total']
                                               / 1024.0 / 1024
                                               / 1024)[:4],
                        'use_size(G):%s' % str((all_mount_info[mount_num]
                                                ['size_total'] / 1024.0
                                                / 1024 / 1024) - (
                                                all_mount_info[mount_num]
                                                ['size_available']
                                                / 1024.0 / 1024
                                                / 1024))[:4],
                        'ava_size(G):%s' % str(all_mount_info
                                               [mount_num]
                                               ['size_available']
                                               / 1024 / 1024.0
                                               / 1024)[:4],
                        'ava_ratio:%s' % ("%.0f%%" % ((
                                          all_mount_info
                                          [mount_num]
                                          ['size_available']
                                          / 1024 / 1024.0 / 1024) /
                                          (all_mount_info[mount_num]
                                           ['size_total'] / 1024.0
                                           / 1024 / 1024) * 100))
                        ]
        logging.info("Geted volume mount info:%s" % all_mount_list)
        return all_mount_list

    def _get_boot_type(self, all_mount_list):
        logging.info("Geting boot type.....")
        efi_type = "mount_path:/boot/efi"
        for efi_num in range(len(self.all_mount_list)):
            if efi_type in self.all_mount_list.values()[efi_num]:
                boot_type = "efi"
                break
            else:
                boot_type = "bios"
        logging.info("Geted boot type:%s" % boot_type)
        return boot_type

    def _migration_check(self, data, all_mount_list, boot_type, version):
        logging.info("Geted host data successful.")
        logging.info("Checking host data.....")
        support_synchronization = 'Yes'
        support_increment = 'Yes'
        migration_proposal = ''
        # Judge version
        if self.version[0] == "CentOS" or self.version[0] == "RedHat":
            # Judge el version
            if int(self.version[1].split('.', 1)[0]) < 6:
                support_synchronization = 'No'
                support_increment = 'No'
                migration_proposal = ('Host version %s%s not support '
                                      'migration. ' % (self.version[0],
                                                       self.version[1]))
        elif self.version[0] == "SLES":
            if int(self.version[1].split('.', 1)[0]) < 11:
                support_synchronization = 'No'
                support_increment = 'No'
                migration_proposal = ('Host version %s%s not support '
                                      'migration. ' % (self.version[0],
                                                       self.version[1]))
        else:
            support_synchronization = 'No'
            support_increment = 'No'
            migration_proposal = ('Host verison %s not support '
                                  'migration. ' % self.version[0])
        # Judge vgs num
        if 'ansible_lvm' in (self.data[status].values()[0]
                             [host_facts].keys()):
            host_vgs = (self.data[status].values()[0][host_facts]
                        ['ansible_lvm']['vgs'].keys())
            if len(host_vgs) > 1:
                support_synchronization = 'No'
                support_increment = 'No'
                migration_proposal = ('Host is lvm and has %s vg, not '
                                      'support migration. ' % len(host_vgs))
        # Judge partition available
        for mount_list_num in range(len(self.all_mount_list)):
            if int(self.all_mount_list.values()[mount_list_num]
                   [5].split(':', 1)[1].strip("%")) < 13:
                support_synchronization = 'No'
                support_increment = 'No'
                migration_proposal = (migration_proposal +
                                      'Disk %s partition available '
                                      'space less than 13%%, migration '
                                      'is not supported, please clean '
                                      'some data. ' % (
                                          self.all_mount_list.values()
                                          [mount_list_num]
                                          [1].split(':', 1)[1]))
            # Judge file system
            if (self.all_mount_list.values()[mount_list_num]
                    [0].split(':', 1)[1]) == "btrfs":
                support_synchronization = 'No'
                support_increment = 'No'
                migration_proposal = (migration_proposal +
                                      'Host file system is btrfs, not '
                                      'support migration. ')
        # Judge boot type
        if 'efi' in self.boot_type:
            migration_proposal = (migration_proposal +
                                  'Boot type:EFI, cloud not supported, '
                                  'so migrate to the cloud start system '
                                  'failed, need fix boot type is BIOS.')
        if migration_proposal.strip() == '':
            migration_proposal = 'Check successful'
        logging.info("Host data check completed.")
        return (support_synchronization,
                support_increment,
                migration_proposal)
