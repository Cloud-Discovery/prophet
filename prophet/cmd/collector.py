#!/usr/bin/python
# -*- coding: utf-8 -*-

# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2019 Prophet Tech (Shanghai) Ltd.
#
# Authors: Ray <sunqi@prophetech.cn>
#
# Copyright (c) 2019 This file is confidential and proprietary.
# All Rights Resrved, Prophet Tech (Shanghai) Ltd (http://www.prophetech.cn).

"""Entry points for colletor"""

from gevent import monkey, pywsgi
import logging
import optparse
import os
import sys

from prophet import app, utils
from prophet.api import register_api

VER = "2019.03.01"
DEFAULT_PORT = 15000


def parse_args(argv):
    """Parses commaond-line arguments"""
    parser = optparse.OptionParser(version=VER)
    parser.add_option("--port", action="store",
                      dest="port", default=DEFAULT_PORT,
                      help="Data and log dir")
    parser.add_option("--data-path", action="store",
                      dest="data_path", default=None,
                      help="Data and log path")
    parser.add_option("-d", "--debug", action="store_true",
                      dest="debug", default=False,
                      help="Run revenue  in debug model.")
    parser.add_option("-v", "--verbose", action="store_true",
                      dest="verbose", default=False,
                      help="Print standard output in current console.")
    return parser.parse_args(argv[1:])[0]


def main():
    argv = sys.argv
    # Read options argv
    options = parse_args(argv)
    # utils.load_configs(options.config)

    # setup logging
    debug = options.debug
    verbose = options.verbose
    data_path = options.data_path
    port = int(options.port)

    if not data_path:
        print "Data path must be specified!"
        sys.exit(1)

    log_path = os.path.join(data_path, "logs")
    if not os.path.exists(log_path):
        utils.mkdir_p(log_path)

    utils.setup_logging(
            log_path=log_path,
            log_name="colletor.log",
            debug=debug,
            verbose=verbose)

    # register api
    register_api(app)

    # Start server
    monkey.patch_all()
    logging.info("Collctor target started at http://0.0.0.0:%s" % port)
    gevent_server = pywsgi.WSGIServer(("0.0.0.0", port), app)
    gevent_server.serve_forever()


if __name__ == "__main__":
    main()
