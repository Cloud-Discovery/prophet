#!/usr/bin/env python
# -*- coding=utf8 -*-

# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2019 OnePro Cloud (Shanghai) Ltd.
#
# Authors: Ray <ray.sun@oneprocloud.com>
#
# Copyright (c) 2019 This file is confidential and proprietary.
# All Rights Resrved, OnePro Cloud (Shanghai) Ltd (http://www.oneprocloud.com).

import argparse
import logging
import sys

from prophet.controller.analysis.report_job import ReportJob
from prophet.utils import init_logging

VER = "v1.0.0"


def analysis_report(args):
    report_job = ReportJob(args.package_file,
                           args.output_path,
                           args.clean)
    report_job.analysis()


def parse_sys_args(argv):
    """Parses commaond-line arguments"""
    parser = argparse.ArgumentParser(
        description="HyperMotion Hosts Analysis Tool")
    parser.add_argument("-d", "--debug", action="store_true",
            dest="debug", default=False,
            help="Enable debug message.")
    parser.add_argument("-v", "--verbose", action="store_true",
            dest="verbose", default=False,
            help="Show message in standard output.")

    subparsers = parser.add_subparsers(title='Avaliable commands')

    parser_report = subparsers.add_parser("report")
    parser_report.add_argument("--package-file",
            dest="package_file", required=True,
            help="Investigate package file which is "
                 "genreated by prophet-collect")
    parser_report.add_argument("--output-path", dest="output_path",
            required=True, help="Generate report path")
    parser_report.add_argument("--clean", action="store_true",
            dest="clean", required=False, default=False,
            help="Generate report path")

    parser_report.set_defaults(func=analysis_report)

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    else:
        return parser.parse_args(argv[1:])


def main():
    args = parse_sys_args(sys.argv)
    init_logging(args.debug, args.verbose)
    args.func(args)


if __name__ == "__main__":
    main()
