#!/usr/bin/env python
# -*- coding=utf8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2019 Prophet Tech (Shanghai) Ltd.
#
# Authors: Li ZengYuan <lizengyuan@prophetech.cn>
#
# Copyright (c) 2019 This file is confidential and proprietary.
# All Rights Resrved, Prophet Tech (Shanghai) Ltd (http://www.prophetech.cn).
#
# AnsibleApi Class get host info
#
# Steps:
#
#     1. Definition Callback
#     2. Dnsibles object
#     3. Run ansibles
#

import json
import logging
import os
import shutil
import yaml

from ansible import constants
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.inventory.manager import InventoryManager
from ansible.parsing.dataloader import DataLoader
from ansible.playbook.play import Play
from ansible.plugins.callback import CallbackBase
from ansible.vars.manager import VariableManager
from collections import namedtuple

constants.HOST_KEY_CHECKING = False


class ResultCallback(CallbackBase):

    def __init__(self, *args, **kwargs):
        self.host_ok = {}
        self.host_failed = {}
        self.host_unreachable = {}

    def v2_runner_on_ok(self, result, *args, **kwargs):
        self.host_ok[result._host.get_name()] = result

    def v2_runner_on_failed(self, result, *args, **kwargs):
        self.host_failed[result._host.get_name()] = result

    def v2_runner_on_unreachable(self, result):
        self.host_unreachable[result._host.get_name()] = result


class AnsibleApi(object):

    def __init__(self):
        self.options = namedtuple(
            "Options", [
                "ack_pass",
                "ask_sudo_pass",
                "become",
                "become_method",
                "become_user",
                "check",
                "connection",
                "diff",
                "forks",
                "listhosts",
                "listtags",
                "listtasks",
                "module_path",
                "remote_user",
                "sudo",
                "sudo_user",
                "syntax",
                "verbosity"
                ]
        )(
            ack_pass=None,
            ask_sudo_pass=False,
            become=None,
            become_method=None,
            become_user=None,
            check=False,
            connection="smart",
            diff=False,
            forks=5,
            listhosts=None,
            listtags=None,
            listtasks=None,
            module_path=None,
            remote_user=None,
            sudo=None,
            sudo_user=None,
            syntax=None,
            verbosity=5
        )
        self.passwords = {}
        self.hosts_file = None
        self.exec_host = None
        self.tasks = None

    def set_options(self, hosts_file=None,
                    exec_hosts=None, tasks=None):
        if hosts_file:
            self.hosts_file = hosts_file
        if exec_hosts:
            self.exec_hosts = exec_hosts
        if tasks:
            self.tasks = tasks

    def run_task(self):
        loader = DataLoader()
        inventory = InventoryManager(
            loader=loader, sources=[self.hosts_file])
        variable_manager = VariableManager(
            loader=loader, inventory=inventory)
        results_callback = ResultCallback()
        play_source = {
            "name": "Ansible Play",
            "hosts": self.exec_hosts,
            "tasks": self.tasks,
            "gather_facts": "no"
        }
        play = Play().load(
            play_source,
            variable_manager=variable_manager,
            loader=loader
        )
        tqm = None
        tqm = TaskQueueManager(
            inventory=inventory,
            variable_manager=variable_manager,
            loader=loader,
            options=self.options,
            passwords=self.passwords,
            stdout_callback=results_callback,
            run_additional_callbacks=constants.DEFAULT_LOAD_CALLBACK_PLUGINS,  # noqa
            run_tree=False
        )
        tqm.run(play)
        if tqm is not None:
            tqm.cleanup()
        shutil.rmtree(constants.DEFAULT_LOCAL_TMP, True)

        results = {
            "success": {},
            "failed": {},
            "unreachable": {}
        }
        for host, result in results_callback.host_ok.items():
            results["success"][host] = result._result
        for host, result in results_callback.host_failed.items():
            results["failed"][host] = result._result
        for host, result in results_callback.host_unreachable.items():
            results["unreachable"][host] = result._result

        return results
