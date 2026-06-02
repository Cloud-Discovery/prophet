# Copyright (c) 2021 OnePro Cloud Ltd.
#
#   prophet is licensed under Mulan PubL v2.

"""Database models"""

from db import db
from models.user import User
from models.host import (
    Host, HostCredential, HostDetail, HostTag, HostTagRelation, HostRelationship,
    HostDisk, HostPartition, HostNetworkInterface
)
from models.platform import VirtualizationPlatform, PlatformTagRelation
from models.application import Application, ApplicationHost
from models.task import ScanTask, CollectionTask
from models.system import SystemConfig, AuditLog

__all__ = [
    'db',
    'User',
    'Host',
    'HostCredential',
    'HostDetail',
    'HostTag',
    'HostTagRelation',
    'HostRelationship',
    'HostDisk',
    'HostPartition',
    'HostNetworkInterface',
    'VirtualizationPlatform',
    'Application',
    'ApplicationHost',
    'ScanTask',
    'CollectionTask',
    'SystemConfig',
    'AuditLog',
]

