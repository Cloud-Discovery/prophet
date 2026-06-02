# Copyright (c) 2021 OnePro Cloud Ltd.
#
#   prophet is licensed under Mulan PubL v2.

"""Service for collecting platform hosts (VMware VMs, etc.)"""

import logging
from typing import List, Dict
from datetime import datetime
import tempfile
import shutil

from models import Host, HostDetail, VirtualizationPlatform, CollectionTask, db
from services.collection_parser_service import CollectionParserService

logger = logging.getLogger(__name__)


class PlatformCollectorService:
    """Service for collecting platform hosts"""
    
    def __init__(self, collection_task_id: int, platform_id: int):
        """Initialize platform collector service"""
        self.collection_task_id = collection_task_id
        self.collection_task = CollectionTask.query.get(collection_task_id)
        if not self.collection_task:
            raise ValueError(f"Collection task {collection_task_id} not found")
        
        self.platform_id = platform_id
        # Query platform with explicit column selection to ensure password_encrypted is loaded
        self.platform = VirtualizationPlatform.query.filter_by(
            id=platform_id,
            deleted_at=None
        ).first()
        if not self.platform:
            raise ValueError(f"Platform {platform_id} not found or deleted")
        
        # Log platform info for debugging
        logger.info(f"Initialized PlatformCollectorService for platform {self.platform.name} (ID: {platform_id})")
        logger.debug(f"Platform password_encrypted loaded: {self.platform.password_encrypted is not None}")
    
    def update_progress(self, completed: int = None, failed: int = None):
        """Update collection task progress"""
        if completed is not None:
            self.collection_task.completed_count = completed
        if failed is not None:
            self.collection_task.failed_count = failed
        
        # Calculate progress based on actual task hosts
        host_ids = self.collection_task.get_host_ids()
        total = len(host_ids)
        if total > 0:
            done = self.collection_task.completed_count + self.collection_task.failed_count
            self.collection_task.progress = int(done / total * 100)
        else:
            self.collection_task.progress = 0
        
        db.session.commit()
    
    def collect_platform_hosts(self):
        """Collect hosts from platform"""
        try:
            hosts: List[Host] = []
            # Update status to running
            self.collection_task.status = 'running'
            self.collection_task.started_at = datetime.utcnow()
            db.session.commit()
            
            # Get host IDs to collect
            host_ids = self.collection_task.get_host_ids()
            if not host_ids:
                logger.warning(f"No hosts to collect for task {self.collection_task_id}")
                self.collection_task.status = 'completed'
                self.collection_task.completed_at = datetime.utcnow()
                db.session.commit()
                return
            
            # Get hosts
            hosts = Host.query.filter(
                Host.id.in_(host_ids),
                Host.deleted_at == None
            ).all()
            
            if not hosts:
                logger.warning(f"No valid hosts found for task {self.collection_task_id}")
                self.collection_task.status = 'completed'
                self.collection_task.completed_at = datetime.utcnow()
                db.session.commit()
                return
            # Mark hosts as collecting at the start of task
            for host in hosts:
                host.collection_status = 'collecting'
            db.session.commit()
            self.update_progress()
            
            # Collect based on platform type
            if self.platform.type == 'vmware':
                self._collect_vmware_hosts(hosts)
            else:
                logger.error(f"Platform type {self.platform.type} not supported for collection")
                self.collection_task.status = 'failed'
                self.collection_task.error_message = f"Platform type {self.platform.type} not supported"
                self.collection_task.completed_at = datetime.utcnow()
                db.session.commit()
                return
            
            # Update task status
            total = len(hosts)
            completed = self.collection_task.completed_count
            failed = self.collection_task.failed_count
            
            if failed == total:
                self.collection_task.status = 'failed'
            elif completed + failed == total:
                self.collection_task.status = 'completed'
            
            self.collection_task.completed_at = datetime.utcnow()
            self.collection_task.progress = 100
            db.session.commit()
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Platform collection task {self.collection_task_id} failed: {e}")
            import traceback
            traceback_str = traceback.format_exc()
            logger.error(traceback_str)
            
            # Mark any hosts still collecting as failed
            try:
                from models import HostDetail
                failed_hosts = 0
                completed_hosts = 0
                for host in hosts:
                    if host.collection_status == 'collecting':
                        host.collection_status = 'failed'
                        host.last_collected_at = datetime.utcnow()
                        detail = HostDetail(
                            host_id=host.id,
                            details='',
                            status='failed',
                            collection_method='vmware_platform',
                            error_message=str(e),
                            collected_at=datetime.utcnow(),
                        )
                        db.session.add(detail)
                    if host.collection_status == 'failed':
                        failed_hosts += 1
                    elif host.collection_status == 'completed':
                        completed_hosts += 1
                db.session.commit()
                self.update_progress(completed=completed_hosts, failed=failed_hosts)
            except Exception as update_hosts_error:
                logger.error(f"Failed to update host statuses after error: {update_hosts_error}")
            
            # Save detailed error message
            self.collection_task.status = 'failed'
            # Include full error message and traceback for debugging
            self.collection_task.error_message = f"{error_msg}\n\n{traceback_str[:1000]}"  # Limit traceback length
            self.collection_task.completed_at = datetime.utcnow()
            db.session.commit()
            raise
    
    def _collect_vmware_hosts(self, hosts: List[Host]):
        """Collect VMware hosts using platform API"""
        try:
            # Filter out ESXi hosts - they cannot be collected via standard methods
            vm_hosts = [h for h in hosts if h.os_type != 'VMware ESXi']
            esxi_hosts = [h for h in hosts if h.os_type == 'VMware ESXi']
            
            if esxi_hosts:
                logger.info(f"Filtered out {len(esxi_hosts)} ESXi hosts from collection (ESXi hosts are synced from platform, not collected)")
                for esxi_host in esxi_hosts:
                    logger.info(f"  - ESXi host ID: {esxi_host.id}, IP: {esxi_host.ip}, Hostname: {esxi_host.hostname}")
                    # Mark ESXi hosts as collected (they are already synced from platform)
                    esxi_host.collection_status = 'collected'
                    esxi_host.last_collected_at = datetime.utcnow()
            
            if not vm_hosts:
                logger.warning("No VM hosts to collect after filtering ESXi hosts")
                if esxi_hosts:
                    db.session.commit()
                return
            
            # Use filtered VM hosts for collection
            hosts = vm_hosts
            
            from prophet.collector.hosts.vmware import VMwareCollector
            
            # Create temp directory for collection
            temp_dir = tempfile.mkdtemp(prefix='vmware_collect_')
            
            try:
                # Refresh platform object to ensure we have latest data
                db.session.refresh(self.platform)
                
                # Get platform password - ensure it's loaded from database
                logger.info(f"Getting password for platform {self.platform.name} (ID: {self.platform.id})")
                logger.debug(f"Platform password_encrypted field exists: {self.platform.password_encrypted is not None}")
                
                password = self.platform.get_password()
                
                if password is None or password == '':
                    error_msg = (
                        f"Platform {self.platform.name} (ID: {self.platform.id}) password is not set or cannot be decrypted. "
                        f"password_encrypted field: {'exists' if self.platform.password_encrypted else 'missing'}. "
                        f"Please update the platform credentials in the platform management page."
                    )
                    logger.error(error_msg)
                    raise ValueError(error_msg)
                
                logger.info(f"Password retrieved successfully for platform {self.platform.name}")
                
                # Connect to platform
                collector = VMwareCollector(
                    ip=self.platform.host,
                    username=self.platform.username,
                    password=password,  # Ensure password is a non-empty string
                    ssh_port=self.platform.port or 443,
                    key_path=None,
                    output_path=temp_dir,
                    os_type='VMWARE',
                )
                
                collector.connect()
                
                # Only collect data for selected hosts, not all VMs
                logger.info(f"Collecting data from platform {self.platform.name} for {len(hosts)} selected hosts only")
                
                # Get VM objects from platform to query specific VMs
                # We need to access the collector's content to query VMs
                content = collector._content
                if not content:
                    raise ValueError("Failed to connect to platform")
                
                # Get container view for VMs
                from pyVmomi import vim
                container = content.rootFolder
                viewType = [vim.VirtualMachine]
                recursive = True
                containerView = content.viewManager.CreateContainerView(
                    container, viewType, recursive
                )
                
                # Get ESXi and cluster info once (needed for _get_vm_info)
                esxi_obj = collector._get_content_obj(content, [vim.HostSystem])
                cluster_obj = collector._get_content_obj(content, [vim.ClusterComputeResource])
                
                # Initialize ESXi info dictionary (required by _get_vm_info)
                # This populates collector._esxis_info which is needed when _get_vm_info accesses it
                logger.info("Initializing ESXi host information...")
                collector._get_esxi_info()
                collector._get_vcenter_info()  # Also initialize vCenter info if needed
                logger.info(f"Initialized ESXi info for {len(collector._esxis_info)} ESXi hosts")
                
                # Only collect VM info for selected hosts
                # First pass: identify matching VMs (quick check without detailed collection)
                matching_vms = []
                vm_objects = containerView.view
                
                # Log selected hosts for debugging
                logger.info(f"Selected hosts to match: {len(hosts)}")
                for host in hosts:
                    logger.info(f"  - Host ID: {host.id}, IP: {host.ip}, Hostname: {host.hostname}, MAC: {host.mac}")
                
                total_vms = len(vm_objects)
                logger.info(f"Total VMs on platform: {total_vms}")
                
                for vm in vm_objects:
                    # Quick check: get basic info to match
                    try:
                        # Try to get VM info - handle cases where VM is not accessible
                        vm_ip = ''
                        vm_name = ''
                        vm_uuid = ''
                        
                        try:
                            vm_name = getattr(vm.config, 'name', '') or ''
                        except Exception:
                            pass
                        
                        try:
                            vm_uuid = getattr(vm.config, 'uuid', '') or ''
                            # Also try instanceUuid
                            if not vm_uuid:
                                vm_uuid = getattr(vm.config, 'instanceUuid', '') or ''
                        except Exception:
                            pass
                        
                        try:
                            vm_ip = getattr(vm.summary.guest, 'ipAddress', '') or ''
                            # Also try to get IP from network info if available
                            if not vm_ip and hasattr(vm.summary, 'guest') and hasattr(vm.summary.guest, 'net'):
                                for net in vm.summary.guest.net or []:
                                    if hasattr(net, 'ipAddress') and net.ipAddress:
                                        vm_ip = net.ipAddress
                                        break
                        except Exception:
                            pass
                    except Exception as e:
                        # Skip VMs that can't be accessed
                        logger.debug(f"Skip VM due to access error: {e}")
                        continue
                    
                    # Check if this VM matches any selected host
                    matches = False
                    matched_host = None
                    match_reason = None
                    
                    for host in hosts:
                        # Match by UUID (most reliable)
                        if vm_uuid and host.mac and vm_uuid.lower() == host.mac.lower():
                            matches = True
                            matched_host = host
                            match_reason = f"UUID match: {vm_uuid}"
                            break
                        
                        # Match by hostname (case-insensitive)
                        if vm_name and host.hostname and vm_name.lower() == host.hostname.lower():
                            matches = True
                            matched_host = host
                            match_reason = f"Hostname match: {vm_name}"
                            break
                        
                        # Match by IP (case-insensitive, handle multiple IPs)
                        if vm_ip and host.ip:
                            # Check if VM IP matches host IP (exact match)
                            if vm_ip.lower() == host.ip.lower():
                                matches = True
                                matched_host = host
                                match_reason = f"IP match: {vm_ip}"
                                break
                            
                            # Also check if host IP is in VM's IP list (for VMs with multiple IPs)
                            # This is handled above with the network check
                        
                        # Match by hostname containing or being contained (loose match)
                        if vm_name and host.hostname:
                            vm_name_lower = vm_name.lower()
                            hostname_lower = host.hostname.lower()
                            if vm_name_lower in hostname_lower or hostname_lower in vm_name_lower:
                                matches = True
                                matched_host = host
                                match_reason = f"Hostname partial match: {vm_name} <-> {host.hostname}"
                                break
                    
                    # Only collect detailed info for matching VMs
                    if matches:
                        logger.info(f"Found matching VM: {vm_name} (IP: {vm_ip}, UUID: {vm_uuid}) - {match_reason}")
                        matching_vms.append((vm, matched_host))
                    else:
                        logger.debug(f"VM {vm_name} (IP: {vm_ip}, UUID: {vm_uuid}) does not match any selected host")
                
                logger.info(f"Found {len(matching_vms)} matching VMs out of {total_vms} total VMs")
                
                if not matching_vms:
                    # Log detailed info about why no matches were found
                    logger.error("No matching VMs found. Details:")
                    logger.error(f"  Selected hosts: {len(hosts)}")
                    for host in hosts:
                        logger.error(f"    - Host {host.id}: IP={host.ip}, Hostname={host.hostname}, MAC={host.mac}")
                    logger.error(f"  Total VMs on platform: {total_vms}")
                    # Log first few VMs for comparison
                    sample_count = min(5, total_vms)
                    logger.error(f"  Sample VMs on platform (first {sample_count}):")
                    for i, vm in enumerate(list(vm_objects)[:sample_count]):
                        try:
                            vm_name = getattr(vm.config, 'name', 'unknown')
                            vm_uuid = getattr(vm.config, 'uuid', 'unknown')
                            vm_ip = ''
                            try:
                                vm_ip = getattr(vm.summary.guest, 'ipAddress', '') or 'N/A'
                            except:
                                vm_ip = 'N/A'
                            logger.error(f"    - VM: {vm_name}, IP: {vm_ip}, UUID: {vm_uuid}")
                        except:
                            logger.error(f"    - VM: (unable to read)")
                
                # Second pass: collect detailed info only for matching VMs
                vms_info = {}
                vm_to_host_map = {}  # Map VM ID to host for later processing
                
                for vm, matched_host in matching_vms:
                    try:
                        vm_name = getattr(vm.config, 'name', '') or 'unknown'
                        vmid = getattr(vm.config, "instanceUuid", getattr(
                            vm.config, "summary.instanceUuid", vm.config.uuid))
                        
                        logger.info(f"Collecting detailed data for selected VM: {vm_name} (matched with host ID: {matched_host.id})")
                        vm_info = collector._get_vm_info(esxi_obj, cluster_obj, vm)
                        vms_info[vmid] = vm_info
                        vm_to_host_map[vmid] = matched_host  # Store mapping
                        logger.info(f"Successfully collected data for VM: {vm_name}")
                    except Exception as e:
                        vm_name = getattr(vm.config, 'name', 'unknown')
                        logger.error(f"Failed to collect data for VM {vm_name}: {e}")
                        import traceback
                        logger.error(traceback.format_exc())
                        continue
                
                containerView.Destroy()
                
                if not vms_info:
                    raise ValueError("No matching VMs found for selected hosts")
                
                # Process each selected host using the VM-to-host mapping we created
                completed = 0
                failed = 0
                processed_host_ids = set()
                
                # Process VMs that were matched
                for vmid, vm_data in vms_info.items():
                    if vmid not in vm_to_host_map:
                        logger.warning(f"VM {vmid} not in host mapping, skipping")
                        continue
                    
                    host = vm_to_host_map[vmid]
                    processed_host_ids.add(host.id)
                    
                    try:
                        logger.info(f"Processing host {host.id} (IP: {host.ip}, Hostname: {host.hostname}) with matched VM data")
                        
                        # Extract ESXi host name from vm_data
                        # vm_data contains: {"esxi_host": {esxi_name: {...}}, ...}
                        esxi_host_name = None
                        esxi_host_info = vm_data.get('esxi_host', {})
                        if esxi_host_info and isinstance(esxi_host_info, dict):
                            # Get the first (and only) key which is the ESXi host name
                            esxi_host_name = list(esxi_host_info.keys())[0] if esxi_host_info else None
                            logger.info(f"VM {vm_data.get('name', 'unknown')} is on ESXi host: {esxi_host_name}")
                        
                        # Parse and update host data
                        vm_data_for_parser = {
                            vm_data.get('name', host.hostname or host.ip): vm_data
                        }
                        collector_data_format = {
                            f"VMWARE_{host.ip}": {
                                "results": vm_data_for_parser,
                                "os_type": "VMWARE",
                                "tcp_ports": None
                            }
                        }
                        
                        parser_service = CollectionParserService('VMWARE')
                        parsed_data = parser_service.parse_collection_data(collector_data_format)
                        parser_service.update_host_from_parsed_data(host, parsed_data)
                        
                        # Update host metadata
                        host.source = 'platform'
                        host.source_platform_id = self.platform.id
                        host.virtualization_platform_id = self.platform.id
                        # Set status to collecting first, then completed
                        host.collection_status = 'collecting'
                        
                        # Store ESXi host name in vendor field for tree view grouping
                        # Format: "ESXi: <host_name>" so get_hosts_tree can extract it
                        if esxi_host_name:
                            host.vendor = f"ESXi: {esxi_host_name}"
                            logger.debug(f"Set VM {vm_data.get('name', 'unknown')} vendor to: {host.vendor}")
                        
                        db.session.commit()  # Commit immediately for real-time updates
                        
                        # Update to completed
                        host.collection_status = 'completed'
                        host.last_collected_at = datetime.utcnow()
                        
                        # Record collection history
                        detail = HostDetail(
                            host_id=host.id,
                            details='',
                            status='success',
                            collection_method='vmware_platform',
                            collected_at=datetime.utcnow(),
                        )
                        db.session.add(detail)
                        
                        db.session.commit()
                        completed += 1
                        self.update_progress(completed=completed)
                        
                    except Exception as e:
                        logger.error(f"Error collecting host {host.ip}: {e}")
                        import traceback
                        logger.error(traceback.format_exc())
                        
                        host.collection_status = 'failed'
                        host.last_collected_at = datetime.utcnow()
                        
                        # Record failure with detailed error message
                        error_msg = str(e)
                        traceback_str = traceback.format_exc()
                        detail = HostDetail(
                            host_id=host.id,
                            details='',
                            status='failed',
                            collection_method='vmware_platform',
                            error_message=f"{error_msg}\n\n{traceback_str[:500]}",  # Limit traceback length
                            collected_at=datetime.utcnow(),
                        )
                        db.session.add(detail)
                        db.session.commit()
                        
                        failed += 1
                        self.update_progress(failed=failed)
                
                # Check for hosts that were selected but didn't match any VM
                for host in hosts:
                    if host.id not in processed_host_ids:
                        logger.warning(f"Host {host.id} (IP: {host.ip}, Hostname: {host.hostname}, MAC: {host.mac}) was selected but no matching VM was found on platform")
                        failed += 1
                        host.collection_status = 'failed'
                        self.update_progress(failed=failed)
                        db.session.commit()
                
            finally:
                # Cleanup temp directory
                shutil.rmtree(temp_dir, ignore_errors=True)
                
        except Exception as e:
            logger.error(f"VMware collection failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise

