# -*- coding=utf8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2019 Prophet Tech (Shanghai) Ltd.
#
# Authors: Ray <sunqi@prophetech.cn>
#
# Copyright (c) 2019 This file is confidential and proprietary.
# All Rights Resrved, Prophet Tech (Shanghai) Ltd (http://www.prophetech.cn).

"""Use yaml as config file"""

import logging
import yaml


class ConfigFile(object):

    def __init__(self, config_file):
        logging.info("Reading config file %s ..." % config_file)
        self.config_file = config_file

        self.cfg = {}
        with open(config_file, "r") as ymlfile:
            self.cfg = yaml.load(ymlfile)

    def list(self):
        return self.cfg

    def get(self, key):
        return self.cfg[key]

    def set(self, key, values):
        if key not in self.cfg:
            self.cfg[key] = {}
        self.cfg[key] = values
        with open(self.config_file, "w") as outfile:
            yaml.dump(self.cfg,
                      outfile,
                      default_flow_style=False)
