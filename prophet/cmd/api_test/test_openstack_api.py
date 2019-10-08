#!/usr/bin/env python
# -*- coding: utf-8 -*-

# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2017 Prophet Tech (Shanghai) Ltd.
#
# Authors: Ray <sunqi@prophetech.cn>
#
# Copyright (c) 2018. This file is confidential and proprietary.
# All Rights Reserved, Prophet Tech (Shanghai) Ltd(http://www.prophetech.cn).)

import logging
import optparse
import sys
import time

from cloud.openstack import OpenStackDriver

VER = "1.0.0"


class TestOpenStackDriver(object):

    def __init__(self, options):
        self.auth_info = options.__dict__
        self.openstack = OpenStackDriver(self.auth_info)
        self.instance_create_info = self._generate_create_info()
        self.volume_type = self.auth_info.get("volume_type")

    def _generate_create_info(self):
        cloud_info = self.openstack.get_cloud_info()

        az = self.auth_info["volume_availability_zone"]
        if az is None:
            az = cloud_info["availability_zones"][0]["id"]

        flavor_id = self.auth_info["flavor_id"]
        if flavor_id is None:
            flavor_id = cloud_info["flavors"][0]["id"]

        network_id = self.auth_info["network_id"]
        if network_id is None:
            # if network is not given, found the first fixed network
            networks = cloud_info["networks"]
            for network in networks:
                network_id = network["id"]
                break

        instance_create_info = {
            "availability_zone": az,
            "flavor": flavor_id,
            "network": {"id": network_id},
            "instance_name": "boot_from_volume-test",
            "security_groups": [],
        }
        return instance_create_info

    def run(self):
        """Run all test cases"""
        try:
            self.openstack.authenticate(self.auth_info)
        except Exception as e:
            logging.error("Authentication failed, detailed:")
            logging.exception(e)
            sys.exit(1)

        try:
            self.test_volume_api()
        except Exception as e:
            logging.error("Volume API Test failed, detailed:")
            logging.exception(e)
        else:
            logging.error("Volume API Test success.")

        try:
            self.test_instance_api()
        except Exception as e:
            logging.error("Instance API Test failed, detailed:")
            logging.exception(e)
        else:
            logging.error("Instance API Test success.")

    def test_volume_api(self):
        logging.info("Creating volume ...")
        volume = self.openstack.create_volume(
            1, "api-test", volume_type=self.volume_type)

        logging.info("Creating volume snapshot ...")
        snapshot = self.openstack.create_volume_snapshot(
            volume["id"], "api-test-snapshot")

        logging.info("Creating volume from snapshot ...")
        snap_volume = self.openstack.create_volume_from_snapshot(
            snapshot["id"])

        logging.info("Deleting snapshot volume ...")
        self.openstack.delete_volume(snap_volume["id"])

        logging.info("Deleting volume snapshot ...")
        self.openstack.delete_volume_snapshot(
            volume["id"], snapshot["id"])

        # wait 30 seconds to delete volume snapshot
        time.sleep(30)
        logging.info("Deleting volume ...")
        self.openstack.delete_volume(volume["id"])

    def test_instance_api(self):
        volume = self.openstack.create_volume(1, "boot_from_volume-test")
        instance = self.openstack.create_instance(
            volume, [], **self.instance_create_info)
        self.openstack.delete_instance(instance["id"])


log_format = "%(asctime)s %(process)s %(levelname)s [-] %(message)s"
logging.basicConfig(format=log_format, level=logging.DEBUG)


def parse_args(argv):
    """Parses commaond-line arguments"""

    parser = optparse.OptionParser(version=VER)
    parser.add_option(
        "--os-username", action="store",
        dest="os_username", default=None,
        help="OpenStack auth username.")
    parser.add_option(
        "--os-password", action="store",
        dest="os_password", default=None,
        help="OpenStack auth password.")
    parser.add_option(
        "--os-project-name", action="store",
        dest="os_project_name", default=None,
        help="OpenStack project.")
    parser.add_option(
        "--os-auth-url", action="store",
        dest="os_auth_url", default=None,
        help="OpenStack auth url, example: "
        "http://10.10.10.1:5000/v3.")
    parser.add_option(
        "--os-region-name", action="store",
        dest="os_region_name", default="RegionOne",
        help="OpenStack region name")
    parser.add_option(
        "--os-domain-name", action="store",
        dest="os_domain_name", default=None,
        help="OpenStack Domain, default is default.")
    parser.add_option(
        "--volume-type", action="store",
        dest="volume_type", default=None,
        help="Volume type")
    parser.add_option(
        "--volume-availability-zone", action="store",
        dest="volume_availability_zone", default=None,
        help="Volume avalibility zone")
    parser.add_option(
        "--flavor-id", action="store",
        dest="flavor_id", default=None,
        help="Instance flavor id")
    parser.add_option(
        "--network-id", action="store",
        dest="network_id", default=None,
        help="Instance network id")
    parser.add_option(
        "-d", "--debug", action="store_true",
        dest="debug", default=False,
        help="Enable debug message.")
    parser.add_option(
        "-v", "--verbose", action="store_true",
        dest="verbose", default=False,
        help="Show message in standard output.")

    options = parser.parse_args(argv[1:])[0]
    check_args(options, parser)
    return options


def check_args(options, parser):
    none_args = ["os_username", "os_password", "os_auth_url",
                 "os_project_name"]
    options_dict = options.__dict__
    for arg in none_args:
        if options_dict[arg] is None:
            parser.error("--%s not given" % arg)


def main(argv):
    options = parse_args(argv)
    test_openstack = TestOpenStackDriver(options)
    test_openstack.run()


# python test_openstack_api.py --os-username=zhaojiangbo --os-password=Abc999 --os-project-name=zhaojiangbo --os-auth-url=http://192.168.10.201:5000/v3 --os-region-name=RegionOne --os-domain-name=default
if __name__ == "__main__":
    main(sys.argv)
