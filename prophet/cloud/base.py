
# Copyright 2017 Prophet Tech (Shanghai) Ltd.
#
# Authors: Li Xipeng <lixipeng@prophetech.cn>
# Authors: Zheng Wei <zhengwei@prophetech.cn>
#
# Copyright (c) 2017. This file is confidential and proprietary.
# All Rights Reserved, Prophet Tech (Shanghai) Ltd(http://www.prophetech.cn).)
"""Cloud Base driver for HyperGate.

When adding a new cloud driver, finished follow driver method:

Step1: Authenticate and check cloud APIs, quotas:
    We should do authenticate and check whether all needed APIs,
    quotas are avaliable.

:Method: Do authenticate:

    - Detail: see `minitgt.cloud.base.CloudDriver.authenticate`_.

:Method: Do check register:

    - Detail: see `minitgt.cloud.base.CloudDriver.check_register`_.

:Method: Check cloud APIs:

    - Detail: see `minitgt.cloud.base.CloudDriver.check_cloud_apis`_.

:Method: Check cloud Quotas:

    - Detail: see `minitgt.cloud.base.CloudDriver.check_cloud_quota`_

:Method: Static method for authentication params schema:

    - Detail: see `minitgt.cloud.base.CloudDriver.cloud_auth_schema`_.


Step2: Volume management:
    Volume and related snapshots actions must be implemented to set
    hypergate as storage.

:Method: Get volume detail by id:

    - Detail: see `minitgt.cloud.base.CloudDriver.get_volume`_.

:Method: Create volume:

    - Detail: see `minitgt.cloud.base.CloudDriver.create_volume`_.

:Method: Delete volume:

    - Detail: see `minitgt.cloud.base.CloudDriver.delete_volume`_.

:Method: Get volume snapshot by id:

    - Detail: see `minitgt.cloud.base.CloudDriver.get_volume_snapshot`_.

:Method: Create volume snapshot:

    - Detail: see `minitgt.cloud.base.CloudDriver.create_volume_snapshot`_.

:Method: Delete volume snapshot:

    - Detail: see `minitgt.cloud.base.CloudDriver.delete_volume_snapshot`_.

:Method: Create volume from snapshot:

    - Detail:
        see `minitgt.cloud.base.CloudDriver.create_volume_from_snapshot`_.

:Method: Attach volume to local:

    - Detail: see `minitgt.cloud.base.CloudDriver.attach_volume_to_local`_.

:Method: Detach volume:

    - Detail: see `minitgt.cloud.base.CloudDriver.detach_volume`_.

:Method: Get volume path in local node:

    - Detail: see `minitgt.cloud.base.CloudDriver.get_volume_path_in_node`_.

:Method: Get volume types in cloud:

    - Detail: see `minitgt.cloud.base.CloudDriver.get_volume_types`_.


Step3: Migrate instance management:
    All related actions when boot instance with specified volumes.

:Method: Get cloud env detail info:

    - Detail: see `minitgt.cloud.base.CloudDriver.get_cloud_info`_.

:Method: Check params for booting instance:

    - Detail: see `minitgt.cloud.base.CloudDriver.check_cloud_env`_.

:Method: Check quota before creating instance:

    - Detail: see `minitgt.cloud.base.CloudDriver.check_quota`

:Method: Check specified ip addr:

    - Detail: see `minitgt.cloud.base.CloudDriver.check_ip_addr`_.

:Method: Get instance detail by id:

    - Detail: see `minitgt.cloud.base.CloudDriver.get_instance`_.

:Method: Create instance:

    - Detail: see `minitgt.cloud.base.CloudDriver.create_instance`_.

:Method: Delete instance:

    - Detail: see `minitgt.cloud.base.CloudDriver.delete_instance`_.

:Method: Static method to set instance creating params schema:

    - Detail: see `minitgt.cloud.base.CloudDriver.set_instance_schema`_.
"""

import abc
import six


@six.add_metaclass(abc.ABCMeta)
class CloudDriver(object):

    def __init__(self, auth_info):
        self._auth_info = auth_info

    @abc.abstractmethod
    def authenticate(self, auth_info, **kwargs):
        """Do authenticate for specified cloud.

        :param auth_info: <dict>, detail authentication info,
            See `minitgt.cloud.base.CloudDriver.cloud_auth_schema`_.
        :param kwargs: extra arguments.
        :return: an related libcloud cloud connection client.
        """
        pass

    @abc.abstractmethod
    def check_register(self, **kwargs):
        """Do check register for specified cloud.

        :param kwargs: extra arguments.
        :return: nodo info with node id in cloud.
        """
        pass

    @abc.abstractmethod
    def check_cloud_apis(self, **kwargs):
        """Check all used cloud apis.

        When authentication success, all related APIs
        such as volume related APIs, instance related APIs,
        should be tested.
        """
        pass

    @abc.abstractmethod
    def check_cloud_quota(self, **kwargs):
        """Check cloud volume avaliable quota.

        We would set a threshold, check volumes avaliable
        quota is larger then this threshold.
        """
        pass

    @abc.abstractmethod
    def check_instance_params(self, instance, **kwargs):
        pass

    @staticmethod
    def cloud_auth_schema():
        return {}

    @abc.abstractmethod
    def volume_attached_status(self, *args, **kwargs):
        """Get volume attached status.

        :return: <string>, volume attached status
        """
        pass

    @abc.abstractmethod
    def get_volume(self, volume_id):
        """Get volume with volume id.

        :param volume_id: <string>, volume id
        :return: <dict>, detail volume info,

            - id: <string>, volume id
            - name: <string>, volume name
            - status: <enum>, volume status
            - size: <integer>, volume size
            - extra: <dict>, volume extra info
        """
        pass

    @abc.abstractmethod
    def create_volume(self, size, name, **kwargs):
        """Create volume with volume_info.

        :param volume_id: <string>, volume id
        """
        pass

    @abc.abstractmethod
    def delete_volume(self, volume_id, **kwargs):
        """Delete volume with volume id.

        :param volume_id: <string>, volume id
        """
        pass

    @abc.abstractmethod
    def create_volume_snapshot(self, volume_id, snapshot_name, **kwargs):
        """Create volume with volume_info.

        :param volume_id: <string>, volume id
        :param snapshot_name: < string >, snapshot name
        """
        pass

    @abc.abstractmethod
    def delete_volume_snapshot(self, volume_id, snapshot_id, **kwargs):
        """Delete volume with volume id.

        :param volume_id: <string>, volume id
        :param snapshot_id: <string>, snapshot id
        """
        pass

    @abc.abstractmethod
    def create_volume_from_snapshot(self, snap_id, name=None, **kwargs):
        """Create volume from specified snapshot.

        :param snap_id: <string>, snapshot id
        :param name: <string, optional>, volume name
        :return: <dict>, detail volume info,

            - id: <string>, volume id
            - name: <string>, volume name
            - status: <enum>, volume status
            - size: <integer>, volume size
            - extra: <dict>, volume extra info
        """
        pass

    @abc.abstractmethod
    def detach_volume(self, volume_id, **kwargs):
        """Detach volume from local host.

        :param volume_id: <string>, volume id
        :return: <dict>, detail volume info,

            - id: <string>, volume id
            - name: <string>, volume name
            - status: <enum>, volume status
            - size: <integer>, volume size
            - extra: <dict>, volume extra info
        """
        pass

    @abc.abstractmethod
    def attach_volume_to_local(self, volume_id, **kwargs):
        """Attach volume to local host.

        :param volume_id: <string>, volume id
        :return: <dict>, detail volume info,

            - id: <string>, volume id
            - name: <string>, volume name
            - status: <enum>, volume status
            - size: <integer>, volume size
            - path: <string>, volume device path
            - extra: <dict>, volume extra info
        """
        pass

    @abc.abstractmethod
    def get_volume_path_in_node(self, vol_id, **kwargs):
        """Get attached disk local path info.

        :param vol_id: <dict>, volume id
            see `minitgt.cloud.base.CloudDriver.get_volume`_ return.
        :return: <dict>, local path info, see:

            - id: <string>, volume id
            - path: <string>, local path for this volume
        """
        pass

    @abc.abstractmethod
    def get_cloud_info(self, **kwargs):
        """Get cloud env detail info.

        :return: <dict>, detail cloud env info,

            - availability_zones: [<dict>] AZ list, OpenStack only
                - id: <string>, az id
                - name: <string>, az name
            - security_groups: [<dict>] security group list
                - id: <string>, sg id
                - name: <string>, sg name
            - keypairs: [<dict>], keypair list
                - id: <string>, keypair id
                - name: <string>, keypair name
            - flavors: [<dict>], flavor list
                - id: <string>, flavor id
                - name: <string>, flavor name
                - vcpus: <string>, vcpu number
                - ram: <integer>, ram size
            - networks: [<dict>], network list
                - id: <string>, network id
                - name: <string>, network name
                - type: <enum[fixed|floating]>, net type
                - subnets: [<dict>], subnets list for this network
                    - name: <string>, subnet name
                    - cidr: <CIDR>, net cidr
                    - gateway: <IP>, gateway ip
                    - allocation_pools: <string>, available ip pools
            - quota: <dict> quota detail info
                - cores: <dict>, cores usage
                    - used: <integer>, used cores
                    - total: <integer>, maximum cores
                - ram: <dict>, RAM usage
                    - used: <integer>, used RAM
                    - total: <integer>, maximum RAM
                - instances: <dict>, instances usage
                    - used: <integer>, used instances
                    - total: <integer>, maximum instances
                - volumes: <dict>, volumes usage
                    - used: <integer>, used volumes
                    - total: <integer>, maximum volumes
                - gigabytes: <dict>, volume capacity usage
                    - used: <integer>, used volume capacity
                    - total: <integer>, maximum volume capacity
                - ports: <dict>, ports usage
                    - used: <integer>, used ports
                    - total: <integer>, maximum ports
        """
        pass

    @abc.abstractmethod
    def check_cloud_env(self, instance, **kwargs):
        """Check instance params inf cloud env.

        :param instance: <dict>, detail instance info, see:

            - id: <string>, instance id
            - type: <string>, instance type
            - info: <dict>, detail instance,
                see info in `minitgt.api.instance.get`_.
            - source_extra: <dict>, would not be used
            - snapshots: [<dict>], would not be used
            - status: <enum>, instance status
        :return: <dict>, detail params info,

            - availability_zone: <dict> AZ info, OpenStack only
                - id: <string>, az id
                - name: <string>, az name
            - security_groups: [<dict>] security group list
                - id: <string>, sg id
                - name: <string>, sg name
            - keypair: <dict>, keypair info
                - id: <string>, keypair id
                - name: <string>, keypair name
            - flavor: <dict>, flavor info
                - id: <string>, flavor id
                - name: <string>, flavor name
                - vcpus: <string>, vcpu number
                - ram: <integer>, ram size
            - network: <dict>, network info
                - id: <string>, network id
                - addr: <IP>, specified ip addr
        """
        pass

    @abc.abstractmethod
    def check_quota(self, instance, info, **kwargs):
        """Check cloud quota before creating instance.

        :param instance: <dict>, detail instance info, see:

            - id: <string>, instance id
            - type: <string>, instance type
            - info: <dict>, detail instance,
                see info in `minitgt.api.instance.get`_.
            - source_extra: <dict>, would not be used
            - snapshots: [<dict>], would not be used
            - status: <enum>, instance status
        :param info: <dict>, detail instance creating params info,

            - availability_zone: <dict> AZ info, OpenStack only
                - id: <string>, az id
                - name: <string>, az name
            - security_groups: [<dict>] security group list
                - id: <string>, sg id
                - name: <string>, sg name
            - keypair: <dict>, keypair info
                - id: <string>, keypair id
                - name: <string>, keypair name
            - flavor: <dict>, flavor info
                - id: <string>, flavor id
                - name: <string>, flavor name
                - vcpus: <string>, vcpu number
                - ram: <integer>, ram size
            - network: <dict>, network info
                - id: <string>, network id
                - addr: <IP>, specified ip addr
        """
        pass

    @abc.abstractmethod
    def check_ip_addr(self, instance, **kwargs):
        """Check whether specified ip addr is in used.

        :param instance: <dict>, detail instance info, see:

            - id: <string>, instance id
            - type: <string>, instance type
            - info: <dict>, detail instance,
                see info in `minitgt.api.instance.get`_.
            - source_extra: <dict>, would not be used
            - snapshots: [<dict>], would not be used
            - status: <enum>, instance status
        """
        pass

    @abc.abstractmethod
    def get_instance(self, instance_id):
        """Get instance info with instance id.

        :param instance_id: <string>, instance id
        :return: <dict>, detail instance info, see:

            - id: <string>, instance id
            - name: <string>, instance name
            - state: <enum>, instance status
            - public_ips: <string>, instance public ips
            - private_ips: <string>, instance private ips
            - extra: <dict>, extra info
       """
        pass

    @abc.abstractmethod
    def create_instance(self, boot_volume, data_volumes, **create_info):
        """Boot instance from volumes.

        :param boot_volume: <dict>, detail boot volume info,
            see `minitgt.cloud.base.CloudDriver.get_volume`_ return.
        :param data_volumes: [<dict>], detail data volume info,
            see `minitgt.cloud.base.CloudDriver.get_volume`_ return.
        :param create_info: <dict>, detail creating params,
            see `minitgt.cloud.base.CloudDriver.create_instance_schema`_.
        :return: <dict>, detail instance info, see:

            - id: <string>, instance id
            - name: <string>, instance name
            - state: <enum>, instance status
            - public_ips: <string>, instance public ips
            - private_ips: <string>, instance private ips
            - extra: <dict>, extra info
        """
        pass

    @abc.abstractmethod
    def delete_instance(self, instance_id, **kwargs):
        """Get instance info with instance id.

        :param instance_id: <string>, instance id
        """
        pass

    @staticmethod
    def set_instance_schema():
        return {}

    def get_volume_types(self):
        """Get volume types

        :return: <dict>, volume types

            - id: <string>, volume type id
            - name: <string>, volume type name
            - description: <string>, description
        """
        return []

    def get_cloud_quota(self):
        """Get cloud quota information

        :return:
        {
            "total_capacity",  // <float>, total capacity, in GB, (-1 no limit)
            "volumes_max_num"  // <int>,  total volume number
        }
        """
        return {
            "total_capacity": -1,
            "volumes_max_num": 20
        }
