# Copyright (c) 2021 OnePro Cloud Ltd.
#
#   prophet is licensed under Mulan PubL v2.

"""Scanner service to wrap NetworkController"""

import logging
from typing import List, Dict
from prophet.scanner.network import NetworkController
from models import Host, ScanTask, db
from datetime import datetime

logger = logging.getLogger(__name__)


class ScannerService:
    """Service for network scanning"""
    
    def __init__(self, scan_task_id: int):
        """Initialize scanner service with task ID"""
        self.scan_task_id = scan_task_id
        self.scan_task = ScanTask.query.get(scan_task_id)
        if not self.scan_task:
            raise ValueError(f"Scan task {scan_task_id} not found")
    
    def update_progress(self, progress: int, current_host: str = None, result_count: int = None):
        """Update scan task progress"""
        self.scan_task.progress = progress
        if current_host:
            self.scan_task.current_host = current_host
        if result_count is not None:
            self.scan_task.result_count = result_count
        db.session.commit()
    
    def scan_and_save(self, host: str, nmap_args: str = None) -> List[Dict]:
        """Scan network and save results to database in real-time"""
        try:
            # Update status to running
            self.scan_task.status = 'running'
            self.scan_task.started_at = datetime.utcnow()
            db.session.commit()
            
            # Initialize scanner
            scanner = NetworkController(host, nmap_args)
            
            # Perform initial scan to get host list (for progress calculation)
            scanner._scan()  # This performs the nmap scan
            all_hosts = scanner.nm.all_hosts()
            total_hosts = len(all_hosts)
            
            if total_hosts == 0:
                logger.warning(f"No hosts found in scan target: {host}")
                self.scan_task.status = 'completed'
                self.scan_task.completed_at = datetime.utcnow()
                self.scan_task.result_count = 0
                self.scan_task.progress = 100
                db.session.commit()
                return []
            
            logger.info(f"Found {total_hosts} hosts to scan")
            
            # Track progress
            saved_hosts = []
            errors = []
            total_scanned = 0
            
            # Process each host and save immediately
            # Note: scanner.scan() will analyze hosts from the already-scanned nmap results
            for scan_result in scanner.scan():
                total_scanned += 1
                host_ip = scan_result.get('ip', 'unknown')
                
                try:
                    # Check if host already exists
                    existing_host = Host.query.filter_by(ip=host_ip, deleted_at=None).first()
                    
                    if existing_host:
                        # Update existing host
                        self._update_host_from_scan(existing_host, scan_result)
                        host_obj = existing_host
                    else:
                        # Create new host
                        host_obj = self._create_host_from_scan(scan_result)
                        db.session.add(host_obj)
                    
                    # Commit immediately for this host
                    db.session.commit()
                    saved_hosts.append(host_obj)
                    
                    # Update progress
                    progress = int((total_scanned / total_hosts) * 100)
                    self.update_progress(
                        progress=min(99, progress),  # Cap at 99% until all done
                        current_host=host_ip,
                        result_count=len(saved_hosts)
                    )
                    
                    logger.info(f"Saved host {host_ip} ({len(saved_hosts)}/{total_scanned}/{total_hosts})")
                    
                except Exception as e:
                    # Handle IntegrityError (UNIQUE constraint failed)
                    from sqlalchemy.exc import IntegrityError
                    db.session.rollback()
                    
                    if isinstance(e, IntegrityError) and 'UNIQUE constraint failed: hosts.ip' in str(e):
                        # Try to find and update existing host
                        try:
                            existing_host = Host.query.filter_by(ip=host_ip, deleted_at=None).first()
                            if existing_host:
                                self._update_host_from_scan(existing_host, scan_result)
                                db.session.commit()
                                saved_hosts.append(existing_host)
                                logger.info(f"Updated existing host {host_ip} after UNIQUE constraint error")
                            else:
                                errors.append(f"Host {host_ip}: UNIQUE constraint failed but host not found")
                        except Exception as e2:
                            errors.append(f"Host {host_ip}: Error updating after UNIQUE constraint: {e2}")
                            db.session.rollback()
                    else:
                        # Other errors
                        errors.append(f"Host {host_ip}: {str(e)}")
                        logger.error(f"Error saving host {host_ip}: {e}")
                    continue
            
            # Log error summary
            if errors:
                error_summary = f"Scan task {self.scan_task_id} completed with {len(errors)} errors: {', '.join(errors[:10])}"
                if len(errors) > 10:
                    error_summary += f" ... and {len(errors) - 10} more"
                logger.warning(error_summary)
            
            # Update task status to completed
            self.scan_task.status = 'completed'
            self.scan_task.completed_at = datetime.utcnow()
            self.scan_task.result_count = len(saved_hosts)
            self.scan_task.progress = 100
            db.session.commit()
            
            logger.info(f"Scan task {self.scan_task_id} completed: {len(saved_hosts)} hosts saved")
            return [h.to_dict() for h in saved_hosts]
                
        except Exception as e:
            logger.error(f"Scan task {self.scan_task_id} failed: {e}")
            self.scan_task.status = 'failed'
            self.scan_task.error_message = str(e)
            self.scan_task.completed_at = datetime.utcnow()
            db.session.commit()
            raise
    
    def _create_host_from_scan(self, scan_result: Dict) -> Host:
        """Create Host object from scan result"""
        host = Host(
            hostname=scan_result.get('hostname'),
            ip=scan_result.get('ip', ''),
            mac=scan_result.get('mac'),
            vendor=scan_result.get('vendor'),
            os_type=scan_result.get('os'),
            os_version=scan_result.get('os_version'),
            device_type='host' if scan_result.get('os') else 'network_device',
            is_physical=True,  # Default to physical, will be updated during collection
            source='scan',
            source_scan_task_id=self.scan_task_id,
            created_by=self.scan_task.created_by,
        )
        
        # Set scan ports
        ports_info = scan_result.get('ports', {})
        if ports_info:
            host.set_scan_ports(ports_info)
        
        return host
    
    def _update_host_from_scan(self, host: Host, scan_result: Dict):
        """Update existing Host from scan result"""
        if not host.hostname and scan_result.get('hostname'):
            host.hostname = scan_result['hostname']
        if not host.mac and scan_result.get('mac'):
            host.mac = scan_result['mac']
        if not host.vendor and scan_result.get('vendor'):
            host.vendor = scan_result['vendor']
        if not host.os_type and scan_result.get('os'):
            host.os_type = scan_result['os']
        if not host.os_version and scan_result.get('os_version'):
            host.os_version = scan_result['os_version']
        
        # Update scan ports (always update from latest scan)
        ports_info = scan_result.get('ports', {})
        if ports_info:
            host.set_scan_ports(ports_info)
        
        # Update source if not set
        if not host.source:
            host.source = 'scan'
            host.source_scan_task_id = self.scan_task_id

