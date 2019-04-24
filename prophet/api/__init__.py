# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2019 Prophet Tech (Shanghai) Ltd.
#
# Authors: Ray <sunqi@prophetech.cn>
#
# Copyright (c) 2019. This file is confidential and proprietary.
# All Rights Reserved, Prophet Tech (Shanghai) Ltd(http://www.prophetech.cn).

import inspect
import logging
import sys
import traceback

from flask import jsonify, request
from flask_babel import gettext as _
from werkzeug.exceptions import NotFound

from prophet import app, babel
from prophet import exception


@babel.localeselector
def get_locale():
    """Override the language based on the headers in the request"""
    override = "zh_Hans_CN"
    lang = request.headers.get("LANG")
    if lang:
        if lang == 'zh_hk':
            override = "zh_Hant_HK"
        elif lang == 'en':
            override = "en"
    return override


def register_api(app):
    """Register function all routes"""
    pass
    # app.register_blueprint(user.user_bp)
    # app.register_blueprint(setup_step.setup_step_bp,
    #                        url_prefix="/hypermotion/v1")


def _make_error(err):
    """Common method for http error response"""
    logging.exception(err)
    return jsonify(code=err.code,
                   message=_(err.message),
                   traceback=traceback.format_exc()), err.http_code


@app.errorhandler(Exception)
def handle_errors(e):
    """Common method for handle API response error"""

    # Handle url not found
    if isinstance(e, NotFound):
        e.message = exception.UrlNotFound.message
        e.code = exception.UrlNotFound.code
        e.http_code = exception.UrlNotFound.http_code
    else:

        # Handle all errors defined in exceptions, return unkown error
        # when not defined
        exception_classes = inspect.getmembers(
                sys.modules["prophet.exception"], inspect.isclass)
        for name, obj in exception_classes:
            if type(e) is obj:
                logging.info("Handle excpetion "
                             "%s" % obj.__class__.__name__)
                break
        else:
            logging.exception(e)
            e.code = exception.ExceptionBase.code
            e.http_code = exception.ExceptionBase.http_code

    return _make_error(e)
