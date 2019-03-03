# -*- coding: utf-8 -*-

# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2019 Prophet Tech (Shanghai) Ltd.
#
# Authors: Ray <sunqi@prophetech.cn>
#
# Copyright (c) 2019 This file is confidential and proprietary.
# All Rights Resrved, Prophet Tech (Shanghai) Ltd (http://www.prophetech.cn).

from flask import Flask
from flask_babel import Babel


app = Flask("prophet")

# Set default language
app.config["BABEL_DEFAULT_LOCALE"] = "zh_Hans_CN"

babel = Babel(app)
