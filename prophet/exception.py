# -*- coding=utf8 -*-

# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2019 Prophet Tech (Shanghai) Ltd.
#
# Authors: Ray <sunqi@prophetech.cn>
#
# Copyright (c) 2019 This file is confidential and proprietary.
# All Rights Resrved, Prophet Tech (Shanghai) Ltd (http://www.prophetech.cn).

"""TODO(Ray): Global exception defined for prophet project"""

from flask_babel import gettext as _

from prophet import http_status_codes as status_codes


class ExceptionBase(Exception):
    """Base exception"""

    message = _("An unknown exception occurred.")
    code = "0000"
    http_code = status_codes.INTERNAL_SERVER_ERROR

    def __init__(self, message=None, **kwargs):
        Exception.__init__(self)
        self.message = message if message is not None else self.message
        self.code = kwargs.get("code", self.code)
        self.http_code = kwargs.get("http_code", self.http_code)
