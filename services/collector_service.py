# Copyright (c) 2021 OnePro Cloud Ltd.
#
#   prophet is licensed under Mulan PubL v2.

"""Collector service to wrap HostCollector"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from prophet.collector.hosts.linux import LinuxCollector
from prophet.collector.hosts.windows import WindowsCollector
from prophet.collector.hosts.vmware import VMwareCollector
from models import (
    Host, HostCredential, HostDetail, CollectionTask, 
    db, SystemConfig
)
from datetime import datetime
import tempfile
import os

logger = logging.getLogger(__name__)


class CollectorService:
    """Service for host collection"""
    
    def __init__(self, collection_task_id: int):
        """Initialize collector service with task ID"""
        self.collection_task_id = collection_task_id
        self.collection_task = CollectionTask.query.get(collection_task_id)
        if not self.collection_task:
            raise ValueError(f"Collection task {collection_task_id} not found")
        # Cache host_ids to avoid repeated database access
        self._cached_host_ids = None
        self._cached_total = None
    
    def _commit_with_retry(self, max_retries: int = 3, retry_delay: float = 0.1):
        """Commit database changes with retry on lock errors"""
        import time
        from sqlalchemy.orm.exc import StaleDataError
        
        for attempt in range(max_retries):
            try:
                db.session.commit()
                return True
            except Exception as e:
                error_str = str(e)
                is_locked = 'database is locked' in error_str.lower() or 'locked' in error_str.lower()
                is_stale = isinstance(e, StaleDataError) or 'staledataerror' in error_str.lower() or 'expected to update' in error_str.lower()
                
                if (is_locked or is_stale) and attempt < max_retries - 1:
                    error_type = "locked" if is_locked else "stale data"
                    logger.warning(f"Database {error_type} in commit (attempt {attempt + 1}/{max_retries}), retrying after {retry_delay}s...")
                    db.session.rollback()
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                else:
                    logger.error(f"Failed to commit after {max_retries} attempts: {e}")
                    db.session.rollback()
                    raise
    
    def update_progress(self, completed: int = None, failed: int = None, running: int = None):
        """Update collection task progress"""
        import time
        import json
        from sqlalchemy.orm.exc import StaleDataError
        max_retries = 5
        retry_delay = 0.1
        
        for attempt in range(max_retries):
            try:
                # Rollback any previous failed transaction
                try:
                    db.session.rollback()
                except Exception:
                    pass
                
                # Always re-query the task to get the latest state from database
                # This avoids StaleDataError when multiple processes update the same task
                collection_task = CollectionTask.query.get(self.collection_task_id)
                if not collection_task:
                    logger.warning(f"Collection task {self.collection_task_id} not found, skipping progress update")
                    return
                
                # Use merge to ensure the object is in the session
                collection_task = db.session.merge(collection_task)
                
                # Update fields if provided
                if completed is not None:
                    collection_task.completed_count = completed
                if failed is not None:
                    collection_task.failed_count = failed
                if running is not None:
                    collection_task.current_running = running
                
                # Calculate progress based on actual task hosts
                # Use cached total or read directly from column to avoid triggering autoflush
                if self._cached_total is None:
                    # Read host_ids directly from column without triggering any lazy loading
                    host_ids_str = collection_task.host_ids
                    if host_ids_str:
                        try:
                            host_ids = json.loads(host_ids_str)
                            self._cached_total = len(host_ids)
                            self._cached_host_ids = host_ids
                        except (json.JSONDecodeError, TypeError):
                            self._cached_total = 0
                            self._cached_host_ids = []
                    else:
                        self._cached_total = 0
                        self._cached_host_ids = []
                
                total = self._cached_total
                if total > 0:
                    done = collection_task.completed_count + collection_task.failed_count
                    collection_task.progress = int(done / total * 100)
                else:
                    collection_task.progress = 0
                
                # Use no_autoflush to prevent premature flushes that might cause conflicts
                with db.session.no_autoflush:
                    db.session.commit()
                
                # Update cached reference
                self.collection_task = collection_task
                return  # Success, exit retry loop
                
            except StaleDataError as e:
                # Task was modified or deleted by another process
                if attempt < max_retries - 1:
                    logger.warning(f"StaleDataError in update_progress (attempt {attempt + 1}/{max_retries}), retrying after {retry_delay}s...")
                    db.session.rollback()
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                else:
                    logger.error(f"StaleDataError in update_progress after {max_retries} attempts: {e}")
                    db.session.rollback()
                    # Don't raise, just log - progress update is not critical
                    return
                    
            except Exception as e:
                error_str = str(e)
                is_locked = 'database is locked' in error_str.lower() or 'locked' in error_str.lower()
                is_stale = 'staledataerror' in error_str.lower() or 'expected to update' in error_str.lower()
                
                if (is_locked or is_stale) and attempt < max_retries - 1:
                    # Database locked or stale data, retry after delay
                    error_type = "locked" if is_locked else "stale data"
                    logger.warning(f"Database {error_type} in update_progress (attempt {attempt + 1}/{max_retries}), retrying after {retry_delay}s...")
                    db.session.rollback()
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                else:
                    # Other error or max retries reached
                    logger.error(f"Failed to update progress: {e}")
                    db.session.rollback()
                    # Don't raise for progress updates - they're not critical
                    return
    
    def collect_hosts(self, concurrent_limit: int = None):
        """Collect hosts with concurrent execution"""
        try:
            # Get concurrent limit
            if concurrent_limit is None:
                config = SystemConfig.query.filter_by(key='default_collect_concurrent').first()
                concurrent_limit = int(config.value) if config else 5
            
            self.collection_task.concurrent_limit = concurrent_limit
            self.collection_task.status = 'running'
            self.collection_task.started_at = datetime.utcnow()
            db.session.commit()
            
            # Get host IDs - use cached value if available, otherwise load and cache
            if self._cached_host_ids is None:
                import json
                host_ids_str = self.collection_task.host_ids
                if host_ids_str:
                    try:
                        self._cached_host_ids = json.loads(host_ids_str)
                        self._cached_total = len(self._cached_host_ids)
                    except (json.JSONDecodeError, TypeError):
                        self._cached_host_ids = []
                        self._cached_total = 0
                else:
                    self._cached_host_ids = []
                    self._cached_total = 0
            
            host_ids = self._cached_host_ids
            if not host_ids:
                logger.warning(f"Collection task {self.collection_task_id} has no hosts")
                self.collection_task.status = 'completed'
                self.collection_task.completed_at = datetime.utcnow()
                db.session.commit()
                return
            
            # Collect hosts with thread pool
            # Get app context to pass to threads
            from flask import current_app
            app = current_app._get_current_object() if hasattr(current_app, '_get_current_object') else current_app
            
            # Mark all hosts as collecting at task start for real-time updates
            try:
                for host_id in host_ids:
                    host = Host.query.get(host_id)
                    if host:
                        host.collection_status = 'collecting'
                db.session.commit()
            except Exception as status_error:
                logger.error(f"Failed to pre-mark hosts as collecting: {status_error}")
                db.session.rollback()
            
            with ThreadPoolExecutor(max_workers=concurrent_limit) as executor:
                futures = {}
                successful_hosts = set()
                failed_hosts = set()
                
                for host_id in host_ids:
                    host = Host.query.get(host_id)
                    if not host:
                        logger.warning(f"Host {host_id} not found")
                        continue
                    
                    # Submit with app context
                    future = executor.submit(self._collect_with_context, app, host)
                    futures[future] = host_id
                
                # Process completed tasks
                completed = 0
                failed = 0
                
                for future in as_completed(futures):
                    host_id = futures[future]
                    try:
                        result = future.result()
                        if result:
                            completed += 1
                            successful_hosts.add(host_id)
                            logger.debug(f"Host {host_id} collection completed successfully")
                        else:
                            failed += 1
                            failed_hosts.add(host_id)
                            logger.debug(f"Host {host_id} collection failed (returned False)")
                    except Exception as e:
                        logger.error(f"Error collecting host {host_id}: {e}")
                        import traceback
                        logger.error(traceback.format_exc())
                        failed += 1
                        failed_hosts.add(host_id)
                        # Ensure host status is set to failed even if exception occurred
                        try:
                            host = Host.query.get(host_id)
                            if host and host.collection_status != 'failed':
                                host.collection_status = 'failed'
                                # Check if error detail already exists
                                existing_detail = HostDetail.query.filter_by(
                                    host_id=host.id,
                                    status='failed'
                                ).order_by(HostDetail.collected_at.desc()).first()
                                if not existing_detail:
                                    host_detail = HostDetail(
                                        host_id=host.id,
                                        details='',
                                        status='failed',
                                        collection_method=host.os_type.lower() if host.os_type else 'unknown',
                                        error_message=f"Collection task exception: {str(e)[:500]}",
                                    )
                                    db.session.add(host_detail)
                                db.session.commit()
                        except Exception as status_update_error:
                            logger.error(f"Failed to update host {host_id} status after exception: {status_update_error}")
                            db.session.rollback()
                    
                    # Update progress
                    running = len([f for f in futures if not f.done()])
                    self.update_progress(completed=completed, failed=failed, running=running)
            
            # Ensure host statuses are synchronized with results
            # This is critical to ensure no hosts are left in 'collecting' or 'pending' state
            try:
                processed_hosts = successful_hosts | failed_hosts
                for host_id in host_ids:
                    host = Host.query.get(host_id)
                    if not host:
                        logger.warning(f"Host {host_id} not found during status synchronization")
                        continue
                    
                    # Check if host was processed
                    if host_id in successful_hosts:
                        # Host was successfully collected
                        if host.collection_status != 'completed':
                            logger.info(f"Updating host {host_id} ({host.ip}) status to 'completed'")
                            host.collection_status = 'completed'
                    elif host_id in failed_hosts:
                        # Host collection failed
                        if host.collection_status != 'failed':
                            logger.info(f"Updating host {host_id} ({host.ip}) status to 'failed'")
                            host.collection_status = 'failed'
                    elif host_id not in processed_hosts:
                        # Host was not processed at all (should not happen, but handle it)
                        logger.warning(f"Host {host_id} ({host.ip}) was not processed, marking as failed")
                        host.collection_status = 'failed'
                        # Create a failure record
                        host_detail = HostDetail(
                            host_id=host.id,
                            details='',
                            status='failed',
                            collection_method=host.os_type.lower() if host.os_type else 'unknown',
                            error_message='Host was not processed during collection task execution',
                        )
                        db.session.add(host_detail)
                    elif host.collection_status == 'collecting':
                        # Host was marked as collecting but didn't finish -> mark as failed
                        logger.warning(f"Host {host_id} ({host.ip}) was still in 'collecting' state, marking as failed")
                        host.collection_status = 'failed'
                        # Create a failure record if one doesn't exist
                        existing_detail = HostDetail.query.filter_by(
                            host_id=host.id,
                            status='failed'
                        ).order_by(HostDetail.collected_at.desc()).first()
                        if not existing_detail:
                            host_detail = HostDetail(
                                host_id=host.id,
                                details='',
                                status='failed',
                                collection_method=host.os_type.lower() if host.os_type else 'unknown',
                                error_message='Collection task did not complete for this host',
                            )
                            db.session.add(host_detail)
                
                db.session.commit()
                logger.info(f"Status synchronization completed. Successful: {len(successful_hosts)}, Failed: {len(failed_hosts)}, Total: {len(host_ids)}")
            except Exception as status_error:
                logger.error(f"Failed to synchronize host statuses after collection: {status_error}")
                import traceback
                logger.error(traceback.format_exc())
                db.session.rollback()
            
            # Update task status based on results
            total = len(host_ids)
            if failed == total and total > 0:
                # All hosts failed
                self.collection_task.status = 'failed'
                self.collection_task.error_message = f"All {total} hosts failed to collect. Check individual host details for more information."
            elif completed + failed == total:
                # All hosts processed
                self.collection_task.status = 'completed'
            else:
                # Should not happen, but set to completed anyway
                self.collection_task.status = 'completed'
            
            self.collection_task.completed_at = datetime.utcnow()
            self.collection_task.progress = 100
            db.session.commit()
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Collection task {self.collection_task_id} failed: {e}")
            import traceback
            traceback_str = traceback.format_exc()
            logger.error(traceback_str)
            
            # Save detailed error message
            self.collection_task.status = 'failed'
            # Include full error message and traceback for debugging
            self.collection_task.error_message = f"{error_msg}\n\n{traceback_str[:1000]}"  # Limit traceback length
            self.collection_task.completed_at = datetime.utcnow()
            db.session.commit()
            raise
    
    def _collect_with_context(self, app, host: Host) -> bool:
        """Collect a single host with app context"""
        with app.app_context():
            return self._collect_single_host(host)
    
    def _collect_single_host(self, host: Host) -> bool:
        """Collect a single host (implementation)"""
        try:
            # Get credentials
            credential = HostCredential.query.filter_by(host_id=host.id).first()
            if not credential:
                # Use hostname if available, otherwise use IP
                host_identifier = host.hostname or host.ip
                error_msg = f"No credentials found for host {host_identifier} (IP: {host.ip})"
                logger.warning(error_msg)
                
                # Update host collection status
                host.collection_status = 'failed'
                host.last_collected_at = datetime.utcnow()
                
                # Record failure with error message
                host_detail = HostDetail(
                    host_id=host.id,
                    details='',
                    status='failed',
                    collection_method=host.os_type.lower() if host.os_type else 'unknown',
                    error_message=error_msg,
                )
                db.session.add(host_detail)
                db.session.commit()
                
                return False
            
            # Create temp directory for collection
            temp_dir = tempfile.mkdtemp()
            
            try:
                # Prevent collection for ESXI hosts
                if host.os_type == 'VMware ESXi':
                    logger.warning(f"VMware ESXi hosts cannot be collected via standard methods. Skipping collection for host {host.id} ({host.ip})")
                    host.collection_status = 'collected'
                    host.last_collected_at = datetime.utcnow()
                    
                    # Record failure with error message
                    host_detail = HostDetail(
                        host_id=host.id,
                        details='',
                        status='collected',
                        collection_method='none',
                        error_message='VMware ESXi hosts cannot be collected via standard collection methods. VMware ESXi host information is synced from VMware platform.',
                    )
                    db.session.add(host_detail)
                    db.session.commit()
                    return False
                
                # Mark host as collecting before starting long-running operations
                host.collection_status = 'collecting'
                host.last_collected_at = datetime.utcnow()
                db.session.commit()
                
                # Determine collector based on OS type
                os_type = host.os_type.upper() if host.os_type else 'LINUX'
                
                collector_class = None
                if os_type == 'LINUX':
                    collector_class = LinuxCollector
                elif os_type == 'WINDOWS':
                    collector_class = WindowsCollector
                elif os_type == 'VMWARE':
                    collector_class = VMwareCollector
                else:
                    logger.warning(f"Unknown OS type: {os_type}")
                    return False
                
                # Create collector
                collector = collector_class(
                    ip=host.ip,
                    username=credential.username,
                    password=credential.password_encrypted and self._decrypt_password(credential.password_encrypted),
                    ssh_port=int(credential.ssh_port) if credential.ssh_port else 22,
                    key_path=credential.key_path or None,
                    output_path=temp_dir,
                    os_type=os_type,
                    tcp_ports="",  # Will be updated from scan results
                )
                
                # Collect - get data directly from collector (returns dict, no YAML file)
                collected_data = collector.collect()
                
                if collected_data:
                    # Parse and update host using parser service
                    from services.collection_parser_service import CollectionParserService
                    parser_service = CollectionParserService(os_type)
                    parsed_data = parser_service.parse_collection_data(collected_data)
                    parser_service.update_host_from_parsed_data(host, parsed_data)
                    
                    host_detail = HostDetail(
                        host_id=host.id,
                        details='',  # No longer storing raw data
                        status='success',
                        collection_method=os_type.lower(),
                    )
                    db.session.add(host_detail)
                    
                    db.session.commit()
                    return True
                else:
                    logger.error(f"Collection returned no data for host {host.ip}")
                    host.collection_status = 'failed'
                    # Record failure with error message
                    host_detail = HostDetail(
                        host_id=host.id,
                        details='',
                        status='failed',
                        collection_method=os_type.lower() if os_type else 'unknown',
                        error_message='Collection returned no data',
                    )
                    db.session.add(host_detail)
                    db.session.commit()
                    return False
                    
            finally:
                # Cleanup temp directory
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error collecting host {host.ip}: {e}")
            import traceback
            traceback_str = traceback.format_exc()
            logger.error(traceback_str)
            # Update collection status
            try:
                host.collection_status = 'failed'
                host_detail = HostDetail(
                    host_id=host.id,
                    details='',
                    status='failed',
                    collection_method=host.os_type.lower() if host.os_type else 'unknown',
                    error_message=f"{error_msg}\n\n{traceback_str[:500]}",  # Limit traceback length
                )
                db.session.add(host_detail)
                db.session.commit()
            except:
                db.session.rollback()
            return False
    
    
    def _decrypt_password(self, encrypted: str) -> str:
        """Decrypt password"""
        from utils.encryption import decrypt_password
        try:
            return decrypt_password(encrypted)
        except Exception as e:
            logger.error(f"Failed to decrypt password: {e}")
            return ""

