# Copyright (c) 2021 OnePro Cloud Ltd.
#
#   prophet is licensed under Mulan PubL v2.

"""Scanner Celery tasks"""

import logging
from celery.exceptions import SoftTimeLimitExceeded
from celery_app import celery
from services.scanner_service import ScannerService

logger = logging.getLogger(__name__)


@celery.task(
    bind=True, 
    name='tasks.scan_network',
    time_limit=28800,  # 8 hours (hard limit)
    soft_time_limit=28200  # 7 hours 50 minutes (soft limit, allows 10 min for cleanup)
)
def scan_network_task(self, scan_task_id: int, host: str, nmap_args: str = None):
    """Celery task for network scanning"""
    try:
        logger.info(f"Starting scan task {scan_task_id} for {host}")
        service = ScannerService(scan_task_id)
        results = service.scan_and_save(host, nmap_args)
        logger.info(f"Scan task {scan_task_id} completed with {len(results)} hosts")
        return {'status': 'success', 'results_count': len(results)}
    except SoftTimeLimitExceeded:
        logger.warning(f"Scan task {scan_task_id} exceeded soft time limit, performing cleanup...")
        # Task can perform cleanup here if needed
        # The task will be terminated after soft_time_limit + cleanup time
        raise
    except Exception as e:
        logger.error(f"Scan task {scan_task_id} failed: {e}")
        raise

