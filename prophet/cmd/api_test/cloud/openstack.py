# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2019 Prophet Tech (Shanghai) Ltd.
#
# Authors: Li Xipeng <lixipeng@prophetech.cn>
# Authors: Zheng Wei <zhengwei@prophetech.cn>
#
# Copyright (c) 2019. This file is confidential and proprietary.
# All Rights Reserved, Prophet Tech (Shanghai) Ltd(http://www.prophetech.cn).)
"""OPENSTACK class for aws clouds driver"""

import logging
import json
import os
import six
import time
from multiprocessing.dummy import Pool as ThreadPool
import uuid
import base
from errors import ItemNotFound, HttpServerError
from openstack_client import OpenStackClient

NAME_MAX_LEN = 127
TIMEOUT_WAIT = 3600
ATTACH_TIMEOUT = 30
WAIT_INTERVAL = 5
ATTACH_TRY_TIMES = 4


def get_my_mac():
    node = uuid.getnode()
    mac_str = uuid.UUID(int=node).hex[-12:]
    mac = "%s:%s:%s:%s:%s:%s" % (mac_str[0:2], mac_str[2:4],
                                 mac_str[4:6], mac_str[6:8],
                                 mac_str[8:10], mac_str[10:12])
    return mac


class OpenStackDriver(base.CloudDriver):

    def __init__(self, auth_info, **kwargs):
        # node_id is the uuid of HyperGate
        self._node_id = auth_info.get("node_id")
        self._client = None
        super(OpenStackDriver, self).__init__(auth_info)
        self.authenticate(self._auth_info)

        # Handle volume availability zone
        self.volume_availability_zone = auth_info.get(
            "volume_availability_zone", None)

    @property
    def client(self):
        if not self._client:
            self._client = self.authenticate(self._auth_info)
        return self._client

    def authenticate(self, auth_info, **kwargs):
        logging.info("Authenticate auth_info is: %s" % auth_info)
        try:
            _client = OpenStackClient(**auth_info)
            return _client
        except Exception as err:
            logging.error("Failed start openstack client. "
                          "Error: %s" % six.text_type(err))
            raise err

    def get_node_info(self, my_mac, find_return=True, **kwargs):
        nodes = self.client.list_instances()["body"]["servers"]
        node_port_info = {}
        for node in nodes:
            if "addresses" in node.keys():
                for net, net_info in node["addresses"].iteritems():
                    for port in net_info:
                        if my_mac == port["OS-EXT-IPS-MAC:mac_addr"]:
                            if node["id"] not in node_port_info.keys():
                                node_port_info[node["id"]] = []
                            node_port_info[node["id"]].append(port)
            if node_port_info and find_return:
                break

        num = len(node_port_info.keys())
        if num == 0:
            return None
        elif num >= 1:
            logging.info("Find %s node(node_port_info: %s),"
                         " find_return is %s."
                         % (num, node_port_info, find_return))
            for node_id, port_info in node_port_info.items():
                node_info = {
                    "node_id": node_id,
                    "node_mac_addr":
                        port_info[0].get("OS-EXT-IPS-MAC:mac_addr"),
                    "external_ip": port_info[0].get("addr")
                }
                return node_info

    # FIXME(Ray): This function name is not siutable,
    # need change it to get_instance_info()
    # FIXME(Zhao Jiangbo): Now only node_id is need,
    # but need to check this host is in the cloud or not
    # The constraint is the mac can't be repeated.
    # Every time to register a new hypergate need to
    # clean last auth token cache
    def check_register(self, find_return=True, **kwargs):
        """Check current node is a instance in cloud or not

        :param find_return: <bool>, Find a node and return immediatly
        """
        try:
            self.client.cache_clean()
            my_mac = get_my_mac()
            node_info = self.get_node_info(my_mac)
            if node_info:
                return node_info
            else:
                pass
            raise Exception("Can not find this node in your account,"
                            " Please check your hypergate host.")
        except Exception as err:
            logging.error("Failed get current node info."
                          "Error: %s." % six.text_type(err))
            # raise err

    def check_cloud_apis(self, **kwargs):
        pass

    def check_cloud_quota(self, **kwargs):
        pass

    def _get_availability_zones(self):
        azs = []
        zones = self.client.list_availability_zones()["body"]
        for az in zones["availabilityZoneInfo"]:
            if not az["zoneState"]["available"]:
                continue
            azs.append({
                "id": az["zoneName"],
                "name": az["zoneName"]})
        return {"azs": azs}

    def _get_flavors(self):
        flavors = []
        flvs = self.client.list_flavors()["body"]
        for flv in flvs['flavors']:
            flavors.append({
                "id": flv["id"],
                "name": flv["name"],
                "ram": flv["ram"],
                "vcpus": flv["vcpus"]})
        return {"flavors": flavors}

    def _get_keypairs(self):
        keypairs = [{
            "name": "",
            "id": ""
        }]
        pairs = self.client.list_keypairs()["body"]
        for keypair in pairs['keypairs']:
            keypairs.append({
                "name": keypair["keypair"]["name"],
                "id": keypair["keypair"]["name"]})
        return {"keypairs": keypairs}

    def _get_networks(self):
        networks = self.client.list_networks()["body"]
        return {"networks": networks}

    def _get_subnets(self):
        subnets = self.client.list_subnets()["body"]
        return {"subnets": subnets['subnets']}

    def _get_compute_quota(self):
        try:
            usage = self.client.get_compute_quota()["body"]["quota_set"]
            cores = usage["cores"]
            cores_total = cores["limit"] - cores["reserved"]
            if cores["limit"] == -1:
                cores_total = -1
            ram = usage["ram"]
            ram_total = ram["limit"] - ram["reserved"]
            if ram["limit"] == -1:
                ram_total = -1
            instances = usage["instances"]
            instances_total = instances["limit"] - instances["reserved"]
            if instances["limit"] == -1:
                instances_total = -1
            ports = usage["cores"]
            ports_total = ports["limit"] - ports["reserved"]
            if ports["limit"] == -1:
                ports_total = -1
            return {
                "compute_quota": {
                    "cores": {
                        "used": usage["cores"]["in_use"],
                        "total": cores_total},
                    "ram": {
                        "used": usage["ram"]["in_use"],
                        "total": ram_total},
                    "instances": {
                        "used": usage["instances"]["in_use"],
                        "total": instances_total},
                    "ports": {
                        "used": usage["fixed_ips"]["in_use"],
                        "total": ports_total}
                }
            }
        except Exception as err:
            logging.warn("Failed get compute quota and return no limit. "
                         "Please check compute quota manually. "
                         "Error: %s" % six.text_type(err))
            return {
                "compute_quota": {
                    "cores": {
                        "used": 0,
                        "total": -1},
                    "ram": {
                        "used": 0,
                        "total": -1},
                    "instances": {
                        "used": 0,
                        "total": -1},
                    "ports": {
                        "used": 0,
                        "total": -1}
                }
            }

    def _get_volume_quota(self):
        try:
            usage = self.client.get_volume_quota()["body"]["quota_set"]
            volumes = usage["volumes"]
            gigabytes = usage["gigabytes"]
            snapshots = usage["snapshots"]
            volumes_total = volumes["limit"] - volumes["reserved"]
            if volumes["limit"] == -1:
                volumes_total = -1
            gigabytes_total = gigabytes["limit"] - gigabytes["reserved"]
            if gigabytes["limit"] == -1:
                gigabytes_total = -1
            snapshots_total = snapshots["limit"] - snapshots["reserved"]
            if snapshots["limit"] == -1:
                snapshots_total = -1
            return {
                "volume_quota": {
                    "volumes": {
                        "used": volumes["in_use"],
                        "total": volumes_total},
                    "gigabytes": {
                        "used": gigabytes["in_use"],
                        "total": gigabytes_total},
                    "snapshots": {
                        "used": snapshots["in_use"],
                        "total": snapshots_total},
                }
            }
        except Exception as err:
            logging.warn("Failed get volume quota and return no limit. "
                         "Please check volume quota manually. "
                         "Error: %s" % six.text_type(err))
            return {
                "volume_quota": {
                    "volumes": {
                        "used": 0,
                        "total": -1},
                    "gigabytes": {
                        "used": 0,
                        "total": -1},
                    "snapshots": {
                        "used": 0,
                        "total": -1},
                }
            }

    def _get_network_quota(self):
        try:
            usage = self.client.get_network_quota()["body"]["quota"]
            return {"port_total": usage['port']}
        except Exception as err:
            logging.warn("Failed get network quota and return no limit. "
                         "Please check network quota manually. "
                         "Error: %s" % six.text_type(err))
            return {"port_total": -1}

    def _get_ports(self):
        try:
            ports = self.client.list_ports()["body"]["ports"]
            return {"port_used": len(ports)}
        except Exception as err:
            logging.warn("Failed get port quota and return no limit. "
                         "Please check port quota manually. "
                         "Error: %s" % six.text_type(err))
            return {"port_used": 0}

    def _get_security_groups(self):
        groups = self.client.list_security_groups()["body"]
        sgs = []
        for sg in groups['security_groups']:
            sgs.append({
                "id": sg["id"],
                "name": sg["name"]})
        return {"sgroups": sgs}

    def _build_quota(self, compute_quota, volume_quota, network_quota):
        quota = {}
        if self.client.neutron_enabled:
            compute_quota["ports"] = network_quota["ports"]
        quota.update(compute_quota)
        quota.update(volume_quota)
        return quota

    def _build_networks(self, networks, subnets):
        if not self.client.neutron_enabled:
            return networks
        nets = {}
        for net in networks:
            nets[net["id"]] = net
        available_nets = {}
        for sub in subnets:
            if sub["network_id"] not in nets:
                continue
            if sub["network_id"] not in available_nets:
                net = nets[sub["network_id"]]
                if net["status"] != "ACTIVE":
                    continue
                _type = "floating" if net["router:external"] else "fixed"
                available_nets[sub["network_id"]] = {
                    "id": nets[sub["network_id"]]["id"],
                    "name": nets[sub["network_id"]]["name"],
                    "type": _type,
                    "subnets": []}
            available_nets[sub["network_id"]]["subnets"].append({
                "name": sub["name"],
                "cidr": sub["cidr"],
                "gateway": sub["gateway_ip"],
                "allocation_pool": json.dumps(sub["allocation_pools"])})
        return available_nets.values()

    def _parallel_run(self):
        pool = ThreadPool(10)

        def add_wrap(args):
            func = args[0]
            try:
                result = func(*args[1:])
            except Exception as err:
                return False, err, func.__name__
            return True, result, func.__name__

        result = pool.map(add_wrap, [
            (self._get_availability_zones,),
            (self._get_flavors,),
            (self._get_keypairs,),
            (self._get_networks,),
            (self._get_subnets,),
            (self._get_volume_quota,),
            (self._get_compute_quota,),
            (self._get_network_quota,),
            (self._get_ports,),
            (self._get_security_groups,)
        ])
        pool.close()
        return result

    def get_cloud_info(self, **kwargs):
        result = self._parallel_run()
        info = {}
        for success, data, name in result:
            if not success:
                message = ("Failed to execute %(func)s: "
                           "%(err)s" % {"func": name,
                                        "err": six.text_type(data)})
                raise Exception(message)
            info.update(data)
        network_quota = {
            "ports": {
                "used": info["port_used"],
                "total": info["port_total"]
            }
        }
        return {
            "availability_zones": info["azs"],
            "flavors": info["flavors"],
            "keypairs": info["keypairs"],
            "networks": self._build_networks(info["networks"],
                                             info["subnets"]),
            "quota": self._build_quota(info["compute_quota"],
                                       info["volume_quota"],
                                       network_quota),
            "security_groups": info["sgroups"]
        }

    def get_cloud_quota(self):
        """Show total volume size can be used

        This is equal to the gigabytes in quota response
        """
        volume_quota = self._get_volume_quota()
        volume_gigabytes = volume_quota["volume_quota"]["gigabytes"]
        total_capacity = volume_gigabytes["total"]
        return {
            "total_capacity": total_capacity,
            "volumes_max_num": 20
        }

    # NOTE(Zhao Jiangbo): Compare status use capitalized words
    def _wait_snapshot_state(self, snap_id, state, allowed_state):
        timeout = TIMEOUT_WAIT
        interval = 2
        while timeout > 0:
            try:
                snap = self._get_snapshot_by_id(snap_id)
            except Exception:
                interval = min(timeout, interval)
                time.sleep(interval)
                timeout -= interval
                continue
            if not snap and not state:
                return True, None
            elif not snap and state:
                raise Exception("Could not find snapshot %s" % snap_id)
            if snap["status"].upper() == state:
                return True, snap
            elif snap["status"].upper() in allowed_state:
                return False, snap
            interval = min(timeout, interval)
            time.sleep(interval)
            timeout -= interval

    def _get_snapshot_by_id(self, snap_id):
        try:
            return self.client.get_snapshot_by_id(snap_id)["body"]["snapshot"]
        except ItemNotFound as err:
            logging.warn("Failed to get snapshot(id:%s). And return None. "
                         "Error: %s" % (snap_id, six.text_type(err)))
            return None
        except Exception as err:
            logging.error("Failed to get snapshot(id:%s). Error: %s"
                          % (snap_id, six.text_type(err)))
            raise err

    @property
    def volume_attached_status(self):
        return "IN-USE"

    # NOTE(Zhao Jiangbo): Compare status use capitalized words
    def _wait_volume_state(self, vol_id, state, allowed_state):
        timeout = TIMEOUT_WAIT
        interval = 2
        while timeout > 0:
            try:
                vol = self._get_volume(vol_id)
            except Exception:
                interval = min(timeout, interval)
                time.sleep(interval)
                timeout -= interval
                continue
            if not vol and not state:
                return True, None
            elif not vol and state:
                raise Exception("Could not find volume %s" % vol_id)
            if vol["status"].upper() == state:
                return True, vol
            elif vol["status"].upper() in allowed_state:
                return False, vol
            interval = min(timeout, interval)
            time.sleep(interval)
            timeout -= interval

    def _get_volume(self, volume_id):
        try:
            return self.client.get_volume(volume_id)["body"]["volume"]
        except ItemNotFound as err:
            logging.warn("Failed to get volume(id:%s). And return None. "
                         "Error: %s" % (volume_id, six.text_type(err)))
            return None
        except Exception as err:
            logging.error("Failed to get volume(id:%s). Error: %s"
                          % (volume_id, six.text_type(err)))
            raise err

    def get_volume(self, volume_id):
        try:
            vol = self._get_volume(volume_id)
            if vol:
                return {
                    "id": vol["id"],
                    "name": vol["name"],
                    "status": vol["status"],
                    "size": vol["size"],
                    "extra": ""
                }
        except Exception:
            logging.warn("Failed to get volume_id(id:%s). And return None."
                         % (volume_id))
            return None

    def create_volume(self, size, name, volume_type=None, **kwargs):
        try:
            # NOTE(Ray): To avoid long name, we just keep 128 chars of
            # volume name
            name = name[0:NAME_MAX_LEN]

            volume_az = self.volume_availability_zone
            logging.info("Creating volume with: "
                         "name[%s] size[%s] type[%s] AZ[%s]" % (
                             name, size, volume_type, volume_az))
            volume = self.client.create_volume(
                size, name, volume_type, volume_az)["body"]["volume"]
            success, new_vol = self._wait_volume_state(volume["id"],
                                                       "AVAILABLE",
                                                       allowed_state=["ERROR"])
            logging.debug("Volume info is %s." % new_vol)
            if not success:
                message = ("Create volume %s failed, error %s."
                           % (volume["id"], new_vol))
                raise Exception(message)
            return {
                "id": new_vol["id"],
                "name": new_vol["name"],
                "status": new_vol["status"],
                "size": new_vol["size"],
                "extra": ""
            }
        except Exception as err:
            logging.error("Failed to get create volume. Error: %s"
                          % (six.text_type(err)))
            raise err

    def delete_volume(self, volume_id,
                      openstack_allowed_state=["AVAILABLE", "ERROR_DELETING"],
                      **kwargs):
        try:
            logging.info("Deleteing volume(id: %s)" % volume_id)
            if not self._get_volume(volume_id):
                return
            self.client.delete_volume(volume_id)
            # NOTE(Zhao Jiangbo): Cann't delete the volume
            # because of chain relationship. So when deleteing add
            # "AVAILABLE" in allowed_state.
            succ, vol = self._wait_volume_state(
                volume_id, None, allowed_state=openstack_allowed_state)
            if not succ:
                message = ("Failed to delete volume(id: %s), error %s"
                           % (volume_id, vol))
                logging.error(message)
                raise Exception(message)
            else:
                logging.info("Success to delete volume %s" % volume_id)
        except Exception as err:
            logging.error("Failed to get delete volume. Error: %s"
                          % (six.text_type(err)))
            raise err

    def get_volume_snapshot(self, volume_id, snapshot_id):
        snap = self._get_snapshot_by_id(snapshot_id)
        snap_info = {
            "id": snap["id"],
            "name": "",
            "status": snap["status"],
            "size": snap["size"],
            "extra": ""
        }
        if "name" in snap.keys():
            snap_info["name"] = snap["name"]
        elif "displayName" in snap.keys():
            snap_info["name"] = snap["displayName"]
        return snap_info

    def create_volume_snapshot(self, volume_id, snap_name, **kwargs):
        try:
            # NOTE(Ray): keep 127 chars for snap name
            snap_name = snap_name[0:NAME_MAX_LEN]
            logging.info("Creating volume snapshot with: "
                         "snapshot name[%s] volume id[%s]"
                         % (snap_name, volume_id))
            snapshot = self.client.create_volume_snapshot(
                volume_id, snap_name)["body"]["snapshot"]

            success, snap = self._wait_snapshot_state(snapshot["id"],
                                                      "AVAILABLE",
                                                      ["ERROR"])
            if not success:
                message = ("Create snapshot %s failed, error %s."
                           % (snapshot["id"], snap))
                raise Exception(message)
            snap_info = {
                "id": snap["id"],
                "name": "",
                "status": snap["status"],
                "size": snap["size"],
                "extra": ""
            }
            if "name" in snap.keys():
                snap_info["name"] = snap["name"]
            elif "displayName" in snap.keys():
                snap_info["name"] = snap["displayName"]
            return snap_info
        except Exception as err:
            logging.error("Failed to create volume. Error: %s"
                          % six.text_type(err))
            raise err

    # FIXME(Ray): volume id should be removed
    def delete_volume_snapshot(self, volume_id, snapshot_id, **kwargs):
        try:
            logging.info("Delete snapshot %s" % snapshot_id)
            snapshot = self._get_snapshot_by_id(snapshot_id)
            if snapshot:
                self.client.delete_volume_snapshot(snapshot_id)
                # NOTE(Zhao Jiangbo): Cann't delete the snapshot which
                # used to create a volume. So when deleteing add
                # "AVAILABLE" in allowed_state.
                succ, snap = self._wait_snapshot_state(
                    snapshot_id, None, allowed_state=["AVAILABLE",
                                                      "ERROR_DELETING"])
                if not succ:
                    message = ("Failed to delete snapshot %s, "
                               "error %s."
                               % (snapshot_id, snap))
                    logging.error(message)
                    raise Exception(message)
                else:
                    logging.info("Success to delete snapshot %s" % snapshot_id)
        except Exception as err:
            logging.error("Failed to delete volume snapshot(id: %s). Error: %s"
                          % (snapshot_id, six.text_type(err)))
            raise err

    def create_volume_from_snapshot(self, snap_id, name=None, **kwargs):
        try:
            snap = self._get_snapshot_by_id(snap_id)
            vol = self._get_volume(snap["volumeId"])

            if "name" in snap.keys():
                snap_name = snap["name"]
            elif "displayName" in snap.keys():
                snap_name = snap["displayName"]
            else:
                snap_name = snap["id"]
            if "name" in vol.keys():
                vol_name = vol["name"]
            else:
                vol_name = vol["id"]
            # name length should shorter than 255 before sending to cloud
            # here we keep 40 chars for each part and if name is given keep
            # NAME_MAX_LENGTH
            if not name:
                name = '%s:%s:%s' % (vol_name[:40],
                                     snap_name[:40],
                                     time.time())
            else:
                name = name[:NAME_MAX_LEN]
            logging.info("Creating volume %s from snapshot, "
                         "volume size is %s ..." % (name, vol["size"]))
            new_vol = self.client.create_volume(
                vol["size"], name, volume_type=vol["volume_type"],
                volume_az=vol["availability_zone"],
                snapshot_id=snap["id"])["body"]["volume"]
            success, vol = self._wait_volume_state(new_vol["id"],
                                                   "AVAILABLE",
                                                   ["ERROR"])
            if not success:
                message = ("Create volume %s failed, error %s."
                           % (new_vol["id"], vol))
                raise Exception(message)
            return {
                "id": vol["id"],
                "name": vol["name"],
                "status": vol["status"],
                "size": vol["size"],
                "extra": ""
            }
        except Exception as err:
            logging.error("Failed to create volume from snapshot(id: %s)."
                          " Error: %s" % (snap_id, six.text_type(err)))
            raise err

    # TODO(Zhao Jiangbo): Need to optimize. Function _attach_volume_to_local
    # need to to split it into two functions. One is attach volume to local,
    # another one is check whether the disk symbol is generated in OS.
    def _attach_volume_to_local(self, vol_id, **kwargs):
        try:
            self.client.attach_volume(
                volume_id=vol_id, instance_id=self._node_id)["body"]
            succ, vol = self._wait_volume_state(vol_id, "IN-USE",
                                                allowed_state=["AVAILABLE",
                                                               "ERROR"])
            if not succ:
                message = ("Attach volume(id: %s) to local(id: %s) failed,"
                           " error %s." % (vol_id, self._node_id, vol))
                raise Exception(message)
            logging.info("Success attach volume(id: %s) to instance(id: %s)"
                         % (vol_id, self._node_id))
            path_info = self.get_volume_path_in_node(vol_id)
            # Note(Zhao Jiangbo): After attach we need wait for
            # kernel processing, then check the disk path
            timeout = ATTACH_TIMEOUT
            interval = WAIT_INTERVAL
            is_existed = False
            path = "/dev/disk/by-id/"
            logging.info("Begin check disk path in os, "
                         "path is %s, timeout is %ss"
                         % (path_info, timeout))
            while timeout > 0:
                interval = min(timeout, interval)
                time.sleep(interval)
                timeout -= interval
                for file in os.listdir(path):
                    file_path = path + file
                    if path_info.get("path") == file_path:
                        is_existed = True
                        break
                if is_existed:
                    break
            if not is_existed:
                logging.warn("Check disk path(%s) in os failed."
                             " And will attach again."
                             % path_info.get("path"))
                return None
            logging.info("Check disk path(%s) in os success"
                         % path_info.get("path"))
            return {
                "id": vol["id"],
                "name": vol["name"],
                "status": vol["status"],
                "size": vol["size"],
                "path": path_info.get("path"),
                "extra": ""
            }
        except HttpServerError as err:
            message = ("Access API error when attach volume(id: %s) to "
                       "instance(id: %s). If cloud platform is running "
                       "normally, maybe maximum disk count attach to "
                       "HyperGate VM exceed. Check how many disks attach"
                       " to HyperGate. If there are rubbish volumes, try"
                       " to clean them mannully and try again. Error: %s."
                       % (vol_id, self._node_id, six.text_type(err)))
            raise Exception(message)
        except Exception as err:
            logging.error("Failed to attach volume(id: %s) to local(id: %s)."
                          " Error: %s" % (vol_id, self._node_id,
                                          six.text_type(err)))
            raise err

    def attach_volume_to_local(self, vol_id, **kwargs):
        try:
            logging.info("Start attach volume(id: %s) to instance(id: %s)"
                         % (vol_id, self._node_id))
            try_times = ATTACH_TRY_TIMES
            i = 0
            while i < try_times:
                logging.info("Try attach times is %s, now is %s."
                             % (try_times, i))
                vol_info = self._attach_volume_to_local(vol_id, **kwargs)
                if vol_info:
                    return vol_info
                self.detach_volume(vol_id, allowed_state=["ERROR"])
                i += 1
            message = ("Failed to find disk path in os, when "
                       "attach volume(id: %s) to local(id: %s)."
                       % (vol_id, self._node_id))
            raise Exception(message)
        except Exception as err:
            logging.error("Failed to attach volume(id: %s) to local(id: %s)."
                          " Error: %s" % (vol_id, self._node_id,
                                          six.text_type(err)))
            raise err

    def detach_volume(self, vol_id, allowed_state=None, **kwargs):
        try:
            logging.info("Start detach volume(id: %s) to instance(id: %s)"
                         % (vol_id, self._node_id))
            self.client.detach_volume(
                volume_id=vol_id, instance_id=self._node_id)["body"]
            if allowed_state is None:
                allowed_state = ["IN-USE", "ERROR"]
            succ, vol = self._wait_volume_state(vol_id, "AVAILABLE",
                                                allowed_state=allowed_state)
            if not succ:
                message = ("Detach volume(id: %s) from local(id: %s) failed,"
                           " error %s." % (vol_id, self._node_id, vol))
                raise Exception(message)
            logging.info("Success detach volume(id: %s) from instance(id: %s)"
                         % (vol_id, self._node_id))
            return {
                "id": vol["id"],
                "name": vol["name"],
                "status": vol["status"],
                "size": vol["size"],
                "extra": ""
            }
        except Exception as err:
            logging.error("Failed to detach volume(id: %s) from local(id: %s)."
                          " Error: %s" % (vol_id, self._node_id,
                                          six.text_type(err)))
            raise err

    def get_volume_types(self):
        """Return volume types"""

        try:
            volume_types = self.client.list_volume_types()["body"]
            logging.debug("Volume type list: %s" % volume_types)
            vol_types_info = []
            if len(volume_types["volume_types"]) > 0:
                for vol in volume_types["volume_types"]:
                    vol_types_info.append({
                        "id": vol["id"],
                        "name": vol["name"],
                        "description": vol["description"]
                    })
            return vol_types_info
        except Exception as err:
            logging.error("Failed to get volume types."
                          " Error: %s" % (six.text_type(err)))
            return None

    def _get_instance(self, inst_id):
        try:
            server = self.client.get_instance(inst_id)["body"]["server"]
            # NOTE(lixipeng): To fix soft delete condition
            # FIXME(Zhao Jiangbo): Did instance has status "SOFT_DELETED"?
            if server['status'] == 'SOFT_DELETED':
                return None
            return server
        except ItemNotFound as err:
            logging.warn("Failed to get instance(id:%s). And return None. "
                         "Error: %s" % (inst_id, six.text_type(err)))
            return None
        except Exception as err:
            logging.error("Failed to get instance(id: %s)."
                          " Error: %s" % (inst_id, six.text_type(err)))
            raise err

    # NOTE(Zhao Jiangbo): Compare status use capitalized words
    def _wait_instance_state(self, inst_id, state, allowed_state):
        timeout = TIMEOUT_WAIT
        interval = 2
        while timeout > 0:
            try:
                ins = self._get_instance(inst_id)
            except Exception as err:
                logging.warn("Failed to get instance by id %(id)s as "
                             "error %(err)s" % {"id": inst_id,
                                                "err": six.text_type(err)})
                interval = min(timeout, interval)
                time.sleep(interval)
                timeout -= interval
                continue
            if not ins and not state:
                return True, None
            elif not ins and state:
                raise Exception("Could not find instance %s" % inst_id)
            logging.info("Instance state %s" % ins["status"])
            if ins["status"].upper() == state:
                return True, ins
            elif ins["status"].upper() in allowed_state:
                return False, ins

            interval = min(timeout, interval)
            time.sleep(interval)
            timeout -= interval

    def _nets_args(self, net):
        if net.get('fixed_ip'):
            return [{"uuid": net["id"],
                     "fixed_ip": net.get("addr")}]
        return [{"uuid": net["id"]}]

    def _bdm_args(self, boot_volume, data_volume, del_on_termin=True):
        bdms = [{
            "source_type": "volume",
            "boot_index": 0,
            "uuid": boot_volume["id"],
            "volume_size": boot_volume["size"],
            "destination_type": "volume",
            "delete_on_termination": del_on_termin
        }]
        count = 1
        for vol in (data_volume or []):
            bdms.append({
                "source_type": "volume",
                "boot_index": count,
                "uuid": vol["id"],
                "volume_size": vol["size"],
                "destination_type": "volume",
                "delete_on_termination": del_on_termin})
            count += 1
        return bdms

    def _ensure_boot_volume_bootable(self, boot_volume):
        try:
            data = {
                "os-set_bootable": {
                    "bootable": True
                }
            }
            self.client.update_volume_metedata(boot_volume["id"], data)["body"]
        except Exception as err:
            logging.error("Failed to ensure volume(id: %s) bootable."
                          " Error: %s" % (boot_volume["id"],
                                          six.text_type(err)))
            raise err

    def _sg_args(self, sgs):
        sgs_info = self._get_security_groups()
        sgroups = []
        for sg in sgs:
            for sgroup in sgs_info["sgroups"]:
                if sg == sgroup["id"]:
                    sgroups.append({"name": sgroup["name"]})
                    break
        return sgroups

    def _metadata_args(self, **create_info):
        source_extra = create_info.get("source_extra", {})
        os_type = source_extra.get("os_type", "")
        os_version = source_extra.get("os_version", "")
        return {"os_type": os_type,
                "os_version": os_version}

    def _build_instance_args(self, boot_volume, data_volumes, **create_info):
        # Ensure boot volume bootable.
        self._ensure_boot_volume_bootable(boot_volume)
        default_name = "RECOVER:%s" % time.time()
        del_on_termin = create_info.get("delete_on_termination", True)

        sgs = self._sg_args(create_info.get("security_groups"))
        data = {
            "server": {
                "name": create_info.get("instance_name", default_name),
                "security_groups": sgs,
                "networks": self._nets_args(create_info.get("network")),
                "flavorRef": create_info.get("flavor"),
                "block_device_mapping_v2": self._bdm_args(boot_volume,
                                                          data_volumes,
                                                          del_on_termin),
                "metadata": self._metadata_args(**create_info)
            }
        }
        if create_info.get("availability_zone"):
            az = create_info.get("availability_zone")
            data["server"]["availability_zone"] = az
        if create_info.get("keypair"):
            data["server"]["key_name"] = create_info["keypair"]
        return data

    def _do_create_instance(self, data):
        return self.client.create_instance(data=data)["body"]

    def _create_instance(self, data):
        logging.info("Create instance with params: %s" % data)
        res = self._do_create_instance(data=data)
        # NOTE(Ray): During T2Cloud testing, we found this interface is
        # changed, the return value changed from dict to list due to
        # mutliple boot from volume requirements, we just handle here
        # and output a warning message instead of error output
        ret_server = res["server"]
        server_id = None
        if type(ret_server) is list and len(ret_server) == 1:
            logging.warn("Boot from volume API should return an dict, "
                         "but list return here, default API is changed, "
                         "double check with cloud provider.")
            server_id = ret_server[0]["id"]
        else:
            server_id = ret_server["id"]
        success, ser = self._wait_instance_state(
            server_id, "ACTIVE", allowed_state=["ERROR"])
        if not success:
            logging.error("Failed to clear instance %s, error: %s"
                          % (server_id, ser))
            # If create instance failed, try to clear failed instance
            try:
                instance = self._get_instance(server_id)
                if instance:
                    self.client.delete_instance(server_id)
            except Exception:
                logging.warn("Failed to clear instance %s" % server_id)
            message = ("Create server %s failed, error: %s"
                       % (server_id, ser))
            raise Exception(message)
        return {
            "id": ser["id"],
            "name": ser["name"],
            "state": ser["status"],
            "public_ips": self._get_instance_ip(ser),
            "private_ips": "",
            "extra": ""
        }

    def create_instance(self, boot_volume, data_volumes, **create_info):
        data = self._build_instance_args(
            boot_volume, data_volumes, **create_info)
        return self._create_instance(data)

    def _get_instance_ip(self, inst_info):
        ips = []
        if "addresses" in inst_info.keys():
            for net, net_info in inst_info["addresses"].iteritems():
                for port in net_info:
                    if "addr" in port.keys():
                        ips.append(port["addr"])
        return ips

    # NOTE:(Zhao Jiangbo): Now, get_instance is not called
    # ip need parse from instance["server"]["addresses"]
    def get_instance(self, instance_id):
        instance = self._get_instance(instance_id)
        return {
            "id": instance["id"],
            "name": instance["name"],
            "state": instance["status"],
            "public_ips": self._get_instance_ip(instance),
            "private_ips": "",
            "networks": instance["addresses"],
            "security_groups": instance["security_groups"],
            "extra": ""
        }

    def delete_instance(self, instance_id, **kwargs):
        try:
            instance = self._get_instance(instance_id)
            if not instance:
                return
            self.client.delete_instance(instance_id)
            success, inst = self._wait_instance_state(instance_id,
                                                      None,
                                                      ["ERROR"])
            if not success:
                message = ("Delete instance(id: %s) failed, "
                           "error %s." % (instance_id, inst))
                raise Exception(message)
            return inst
        except Exception as err:
            logging.error("Failed to delete instance(id: %s)."
                          " Error: %s" % (instance_id,
                                          six.text_type(err)))
            raise err

    def check_instance_params(self, instance, **kwargs):
        info = self.get_cloud_info()
        create_info = instance["info"]
        result = {}
        # Check availability_zone
        if 'availability_zone' in create_info:
            for az in info["availability_zones"]:
                if az["name"] == create_info["availability_zone"]:
                    result['availability_zone'] = az
                    break
            else:
                raise Exception("Could not find availablity zone "
                                "%s" % create_info["availability_zone"])
        # Check keypair
        if 'keypair' in create_info:
            for keypair in info["keypairs"]:
                if keypair["name"] == create_info["keypair"]:
                    result['keypair'] = keypair
                    break
            else:
                raise Exception("Could not find keypair "
                                "%s" % create_info["keypair"])
        # Check flavor
        if 'flavor' in create_info:
            for flavor in info["flavors"]:
                if flavor["id"] == create_info["flavor"]:
                    result["flavor"] = flavor
                    break
            else:
                raise Exception("Could not find flavor "
                                "%s" % create_info["flavor"])
        # Check network
        if 'network' in create_info:
            for net in info["networks"]:
                if net["id"] == create_info["network"]["id"]:
                    result["network"] = create_info["network"]
                    break
            else:
                raise Exception("Could not find network "
                                "%s" % create_info["network"])
        # Check security_groups
        result["security_groups"] = []
        if 'security_groups' in create_info:
            for sg in create_info["security_groups"]:
                for sgroup in info["security_groups"]:
                    if sg == sgroup["id"]:
                        result["security_groups"].append(sgroup)
                        break
                else:
                    raise Exception("Could not find security "
                                    "group %s" % sg)
        return result

    def _check_flavor(self, quota, flavor):
        if quota["cores"]["total"] != -1:
            need = flavor["vcpus"] + quota["cores"]["used"]
            if need > quota["cores"]["total"]:
                kw = {"need": flavor["vcpus"]}
                kw.update(quota["cores"])
                raise Exception("Quota vCPUs is not enough: "
                                "used %(used)s, total %(total)s, "
                                "but %(need)s needed." % kw)
        if quota["ram"]["total"] != -1:
            need = flavor["ram"] + quota["ram"]["used"]
            if need > quota["ram"]["total"]:
                kw = {"need": flavor["ram"]}
                kw.update(quota["ram"])
                raise Exception("Quota RAM is not enough: "
                                "used %(used)s, total %(total)s, "
                                "but %(need)s needed." % kw)
        if quota["instances"]["total"] != -1:
            need = 1 + quota["instances"]["used"]
            if need > quota["instances"]["total"]:
                kw = {"need": 1}
                kw.update(quota["ram"])
                raise Exception("Quota instances is not enough: "
                                "used %(used)s, total %(total)s, "
                                "but %(need)s needed." % kw)

    def _check_volume_quota(self, snapshots, quota):
        if quota["volumes"]["total"] != -1:
            need = len(snapshots) + quota["volumes"]["used"]
            if need > quota["volumes"]["total"]:
                kw = {"need": len(snapshots)}
                kw.update(quota["volumes"])
                raise Exception("Quota volumes is not enough: "
                                "used %(used)s, total %(total)s, "
                                "but %(need)s needed." % kw)
        needed = 0
        for snap in snapshots:
            snap = self._get_snapshot_by_id(snap["cloud_snap_id"])
            if not snap:
                continue
            needed += float(snap["size"])
        if quota["gigabytes"]["total"] != -1:
            need = needed + quota["gigabytes"]["used"]
            if need > quota["gigabytes"]["total"]:
                kw = {"need": needed}
                kw.update(quota["gigabytes"])
                raise Exception("Quota volumes is not enough: "
                                "used %(used)s, total %(total)s, "
                                "but %(need)s needed." % kw)

    def check_quota(self, instance, info, **kwargs):
        compute_quota = self._get_compute_quota()["compute_quota"]
        volume_quota = self._get_volume_quota()["volume_quota"]
        port_total = self._get_network_quota()["port_total"]
        port_used = self._get_ports()["port_used"]
        # Check vCPUs, RAM, instances
        self._check_flavor(compute_quota, info["flavor"])
        # Check ports
        if port_total != -1 and port_total <= port_used:
            raise Exception("Fixed ip not enough: none ip available.")
        # Check volumes
        self._check_volume_quota(instance["snapshots"],
                                 volume_quota)

    def check_ip_addr(self, instance, **kwargs):
        try:
            network = instance["info"]["network"]
            ports = self.client.list_ports(
                network_id=network["id"])["body"]["ports"]
            for port in ports:
                if port["network_id"] != network["id"]:
                    continue
                for fixed in port["fixed_ips"]:
                    if fixed["ip_address"] == network["addr"]:
                        raise Exception("IP address %s is in "
                                        "used." % network["addr"])
        except Exception as err:
            logging.error("Failed to check ip addr."
                          " Error: %s" % (six.text_type(err)))
            # NOTE(Zhao Jiangbo): For exception just pass

    def get_volume_path_in_node(self, vol_id, **kwargs):
        # For openstack, when volume attached to server,
        # we can find new device in /dev/disk/by-id/,
        # adn new disk is named with 'virtio-<vol_id[:20]>'
        path = "/dev/disk/by-id/virtio-{0}".format(vol_id[:20])
        return {"id": vol_id,
                "path": path}

    @staticmethod
    def cloud_auth_schema():
        return {
            "type": "object",
            "properties": {
                "cloud_type": {
                    "type": "string",
                    "enum": ["OpenStack"]
                },
                "external_ip": {
                    "type": "string"
                },
                "os_auth_url": {
                    "type": "string",
                },
                "node_id": {
                    "type": "string"
                },
                "os_region_name": {
                    "type": "string",
                },
                "os_username": {
                    "type": "string"
                },
                "os_password": {
                    "type": "string"
                },
                "os_project": {
                    "type": "string"
                },
                "os_domain": {
                    "type": "string"
                }
            },
            'required': ["cloud_type", "external_ip", "os_project",
                         "os_auth_url", "os_region_name",
                         "os_username", "os_username", "os_password"]
        }

    @staticmethod
    def volume_create_schema():
        return {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string"
                },
                "size": {
                    "type": "integer"
                },
                "uuid": {
                    "type": "string"
                },
                "volume_type": {
                    "type": "string"
                },
                'required': ["name", "size", "uuid"]
            }
        }

    @staticmethod
    def instance_create_schema():
        return {
            "type": "object",
            "properties": {
                "snapshots": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "index": {"type": "integer"}
                        }
                    },
                    "required": ["id"]
                },
                "create_info": {
                    "type": "object",
                    "properties": {
                        "availability_zone": {
                            "type": "string"
                        },
                        "network": {
                            "type": "object",
                            "properties": {
                                "id": {
                                    "type": "string"
                                },
                                "addr": {
                                    "type": "string"
                                }
                            },
                            "required": ["id"]
                        },
                        "security_groups": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "keypair": {"type": "string"},
                        "instance_name": {"type": "string"},
                        "flavor": {"type": "string"},
                        "delete_on_termination": {
                            "type": "string"
                        }
                    },
                    'required': ["network", "flavor"]
                },
                "source_extra": {
                    "type": "object",
                    "properties": {
                        "boot_type": {
                            "type": "string"
                        },
                        "os_type": {
                            "type": "string"
                        },
                        "os_version": {
                            "type": "string"
                        },
                        "os_bit": {
                            "type": "string"
                        },
                        "protect_type": {
                            "type": "string"
                        },
                        "boot_disk_identifier": {
                            "type": "string"
                        }
                    },
                    'required': ["os_version", "os_bit"]
                },
                'required': ["snapshots", "create_info", "source_extra"]
            }
        }

    def check_cloud_env(self, **kwargs):
        logging.info("Start to check APIs ...")
        self.check_cloud_apis()
        logging.info("Check APIs success")
        logging.info("Start to check cloud quota ...")
        self.check_cloud_quota()
        logging.info("Check cloud quota success.")
