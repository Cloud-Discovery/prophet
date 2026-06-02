# Copyright (c) 2021 OnePro Cloud Ltd.
#
#   prophet is licensed under Mulan PubL v2.

"""Celery tasks"""

from celery_app import celery

# Import tasks to register them
from tasks.scanner import scan_network_task
from tasks.collector import collect_hosts_task, collect_platform_hosts_task

__all__ = ['scan_network_task', 'collect_hosts_task', 'collect_platform_hosts_task']

