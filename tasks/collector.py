# Copyright (c) 2021 OnePro Cloud Ltd.
#
#   prophet is licensed under Mulan PubL v2.

"""Collector Celery tasks"""

import logging
from celery_app import celery
from services.collector_service import CollectorService
from services.platform_collector_service import PlatformCollectorService
from db import db

logger = logging.getLogger(__name__)


@celery.task(bind=True, name='tasks.collect_hosts')
def collect_hosts_task(self, collection_task_id: int, concurrent_limit: int = None):
    """Celery task for host collection"""
    try:
        logger.info(f"Starting collection task {collection_task_id}")
        service = CollectorService(collection_task_id)
        service.collect_hosts(concurrent_limit)
        logger.info(f"Collection task {collection_task_id} completed")
        return {'status': 'success'}
    except Exception as e:
        logger.error(f"Collection task {collection_task_id} failed: {e}")
        raise


@celery.task(bind=True, name='tasks.collect_platform_hosts')
def collect_platform_hosts_task(self, collection_task_id: int, platform_id: int):
    """Celery task for platform host collection"""
    try:
        logger.info(f"Starting platform collection task {collection_task_id} for platform {platform_id}")
        service = PlatformCollectorService(collection_task_id, platform_id)
        service.collect_platform_hosts()
        logger.info(f"Platform collection task {collection_task_id} completed")
        return {'status': 'success'}
    except Exception as e:
        logger.error(f"Platform collection task {collection_task_id} failed: {e}")
        raise


@celery.task(bind=True, name='tasks.sync_platform_resources')
def sync_platform_resources_task(self, collection_task_id: int, platform_id: int):
    """Celery task for syncing platform resources (ESXi hosts and VMs)"""
    try:
        logger.info(f"Starting platform sync task {collection_task_id} for platform {platform_id}")
        from models import CollectionTask, VirtualizationPlatform
        from datetime import datetime
        import tempfile
        import shutil
        from prophet.collector.hosts.vmware import VMwareCollector
        from services.vmware_sync_service import VMwareSyncService
        
        # Get task and platform
        task = CollectionTask.query.get(collection_task_id)
        if not task:
            raise ValueError(f"Collection task {collection_task_id} not found")
        
        platform = VirtualizationPlatform.query.filter_by(id=platform_id, deleted_at=None).first()
        if not platform:
            raise ValueError(f"Platform {platform_id} not found")
        
        user_id = task.created_by
        
        # Update task status to running
        task.status = 'running'
        task.started_at = datetime.utcnow()
        task.progress = 0
        db.session.commit()
        
        # Sync based on platform type
        if platform.type == 'vmware':
            # Create temp directory for collection
            temp_dir = tempfile.mkdtemp(prefix='vmware_sync_')
            
            try:
                password = platform.get_password()
                if not password:
                    raise ValueError("Platform password is not set or cannot be decrypted")
                
                collector = VMwareCollector(
                    ip=platform.host,
                    username=platform.username,
                    password=password,
                    ssh_port=platform.port,
                    key_path=None,
                    output_path=temp_dir,
                    os_type='VMWARE',
                )
                
                # Connect to platform
                collector.connect()
                
                # First, get VM count quickly without detailed collection
                # This allows us to show progress during collection
                from pyVmomi import vim
                content = collector._content
                container = content.rootFolder
                viewType = [vim.VirtualMachine]
                recursive = True
                containerView = content.viewManager.CreateContainerView(
                    container, viewType, recursive
                )
                vm_objects = containerView.view
                vm_count = len(vm_objects)
                
                # Get ESXi count
                esxi_obj = collector._get_content_obj(content, [vim.HostSystem])
                esxi_count = len(esxi_obj) if esxi_obj else 0
                
                # Total items = ESXi hosts + VMs
                # We'll collect ESXi info first, then VMs
                total_items = esxi_count + vm_count
                
                # Update task with total count
                task.completed_count = 0
                task.failed_count = 0
                task.progress = 0
                db.session.commit()
                
                # Update progress: 10% for connection and counting
                if total_items > 0:
                    task.progress = 10
                    db.session.commit()
                
                containerView.Destroy()
                
                # Create sync service first (needed for callback)
                sync_service = VMwareSyncService(platform, user_id)
                
                # Track progress during sync
                original_sync_esxi = sync_service._sync_esxi_host
                original_sync_vm = sync_service._sync_vm
                
                # Step 1: Get ESXi information first (needed before syncing)
                collector._get_esxi_info()
                
                # Step 2: Get vCenter info if applicable (this also populates _vc_info)
                if collector._content.about.name == "VMware vCenter Server":
                    collector._get_vcenter_info()
                    collector._vc_info[collector.ip]["esxi"] = collector._esxis_info
                
                # Step 3: Sync ESXi hosts immediately (before collecting VMs)
                esxi_hosts_data = {}
                if hasattr(collector, '_vc_info') and collector._vc_info:
                    # vCenter case
                    for vc_ip, vc_data in collector._vc_info.items():
                        if 'esxi' in vc_data:
                            esxi_hosts_data = vc_data['esxi']
                            break
                elif hasattr(collector, '_esxis_info') and collector._esxis_info:
                    # ESXi case
                    esxi_hosts_data = collector._esxis_info
                
                esxi_count = len(esxi_hosts_data)
                logger.info(f"Syncing {esxi_count} ESXi hosts...")
                
                # Define tracked_sync_esxi with esxi_count available
                esxi_synced_count = [0]  # Use list to allow modification in nested function
                def tracked_sync_esxi(esxi):
                    try:
                        host_id = original_sync_esxi(esxi)
                        if host_id:
                            # Add host ID to task's host_ids
                            # Keep first element as -platform_id to identify platform sync task
                            import json
                            host_ids = task.get_host_ids()
                            if not host_ids or host_ids[0] >= 0:
                                # Initialize with platform_id marker if not set
                                host_ids = [-platform_id]
                            if host_id not in host_ids:
                                host_ids.append(host_id)
                                task.set_host_ids(host_ids)
                        
                        task.completed_count += 1
                        esxi_synced_count[0] += 1
                        if total_items > 0 and esxi_count > 0:
                            # Progress: 10% (connection) + 20% (ESXi sync) 
                            # ESXi hosts are synced first, so progress from 10% to 30%
                            esxi_progress = 10 + int(20 * esxi_synced_count[0] / esxi_count)
                            task.progress = min(esxi_progress, 30)
                        db.session.commit()
                    except Exception as e:
                        task.failed_count += 1
                        db.session.commit()
                        logger.error(f"Failed to sync ESXi host: {e}")
                        # Don't raise - continue with other ESXi hosts
                
                # Update tracked_sync_vm to use esxi_count with thread safety
                import threading
                sync_lock = threading.Lock()  # Lock for thread-safe database operations
                
                def tracked_sync_vm_with_esxi_count(vm_data):
                    """Sync VM immediately after collection (real-time sync, thread-safe)"""
                    try:
                        # Sync VM to database (this is thread-safe as each call uses its own session)
                        host_id = original_sync_vm(vm_data)
                        
                        # Thread-safe update of task progress and host_ids
                        with sync_lock:
                            # Refresh task from database to get latest state
                            db.session.refresh(task)
                            
                            # Add host ID to task's host_ids
                            if host_id:
                                import json
                                host_ids = task.get_host_ids()
                                if not host_ids or host_ids[0] >= 0:
                                    # Initialize with platform_id marker if not set
                                    host_ids = [-platform_id]
                                if host_id not in host_ids:
                                    host_ids.append(host_id)
                                    task.set_host_ids(host_ids)
                            
                            task.completed_count += 1
                            if total_items > 0:
                                # Progress: 30% (after ESXi) + 70% * (completed/total)
                                # This gives us progress from 30% to 100% as VMs are collected and synced
                                vm_completed = task.completed_count - esxi_count
                                vm_total = max(total_items - esxi_count, 1)
                                sync_progress = int(30 + 70 * vm_completed / vm_total)
                                task.progress = min(sync_progress, 100)  # Cap at 100%
                            db.session.commit()
                    except Exception as e:
                        # Thread-safe update of failed count
                        with sync_lock:
                            db.session.refresh(task)
                            task.failed_count += 1
                            if total_items > 0:
                                vm_completed = task.completed_count + task.failed_count - esxi_count
                                vm_total = max(total_items - esxi_count, 1)
                                sync_progress = int(30 + 70 * vm_completed / vm_total)
                                task.progress = min(sync_progress, 100)
                            db.session.commit()
                        # Don't raise - continue collecting other VMs even if one fails
                        logger.error(f"Failed to sync VM during collection: {e}")
                
                sync_service._sync_esxi_host = tracked_sync_esxi
                sync_service._sync_vm = tracked_sync_vm_with_esxi_count
                
                # Sync ESXi hosts
                for esxi_name, esxi_info in esxi_hosts_data.items():
                    esxi_data = {
                        'name': esxi_name,
                        'info': esxi_info
                    }
                    tracked_sync_esxi(esxi_data)
                
                # Update progress: 30% after ESXi hosts are synced
                if total_items > 0:
                    task.progress = 30
                    db.session.commit()
                
                # Step 4: Now collect VMs with real-time sync callback (concurrent)
                # Each VM will be synced immediately after collection
                # Use concurrent collection to speed up the process
                max_workers = getattr(task, 'concurrent_limit', 5) or 5
                logger.info(f"🚀 Starting CONCURRENT VM collection with {max_workers} worker threads and real-time sync...")
                logger.info(f"   This will use thread-level concurrency within the Celery worker process")
                logger.info(f"   (Celery worker process name will remain the same, but multiple threads will run concurrently)")
                # We need to collect VMs, but ESXi info is already collected
                # So we'll call _get_vms_info directly with callback
                vms_info = collector._get_vms_info(callback=tracked_sync_vm_with_esxi_count, max_workers=max_workers)
                
                # Build collected_data structure for compatibility
                vmware_info = {}
                if hasattr(collector, '_vc_info') and collector._vc_info:
                    vmware_info = collector._vc_info
                else:
                    vmware_info = collector._esxis_info
                
                collected_data = {
                    collector.root_key: {
                        "results": {
                            "server_info": vmware_info,
                            "vms": vms_info
                        },
                        "os_type": collector.os_type,
                        "tcp_ports": None
                    }
                }
                collector._vms_info = vms_info
                collector.collected_data = collected_data
                
                # All VMs have been synced during collection, so we just need to get the result
                # Calculate final statistics
                result = {
                    'synced': sync_service.synced_count,
                    'updated': sync_service.updated_count,
                    'failed': sync_service.failed_count,
                    'total': sync_service.synced_count + sync_service.updated_count,
                    'failed_items': sync_service.failed_items
                }
                
                # Update task status
                if result['failed'] > 0 and result['synced'] + result['updated'] == 0:
                    task.status = 'failed'
                    task.error_message = f"Sync failed: {result['failed']} items failed"
                else:
                    task.status = 'completed'
                task.progress = 100
                task.completed_at = datetime.utcnow()
                db.session.commit()
                
                logger.info(f"Platform sync task {collection_task_id} completed: {result['synced']} created, {result['updated']} updated, {result['failed']} failed")
                return {'status': 'success', 'result': result}
                
            finally:
                # Cleanup temp directory
                shutil.rmtree(temp_dir, ignore_errors=True)
        else:
            raise ValueError(f'Platform type {platform.type} sync not implemented yet')
            
    except Exception as e:
        logger.error(f"Platform sync task {collection_task_id} failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Update task status to failed
        try:
            # Re-import in case we're in exception handler
            from models import CollectionTask
            task = CollectionTask.query.get(collection_task_id)
            if task:
                task.status = 'failed'
                task.error_message = str(e)
                task.completed_at = datetime.utcnow()
                db.session.commit()
        except Exception as update_error:
            logger.error(f"Failed to update task status: {update_error}")
        
        raise

