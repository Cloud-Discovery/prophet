# Copyright (c) 2021 OnePro Cloud Ltd.
#
#   prophet is licensed under Mulan PubL v2.

"""Service for syncing VMware platform resources to database"""

import logging
from typing import Dict, List
from datetime import datetime

from models import Host, HostDetail, VirtualizationPlatform, db
from utils.jwt import get_current_user_id

logger = logging.getLogger(__name__)


class VMwareSyncService:
    """Service for syncing VMware resources to database"""
    
    def __init__(self, platform: VirtualizationPlatform, user_id: int = None):
        """Initialize sync service"""
        self.platform = platform
        self.user_id = user_id or get_current_user_id()
        self.synced_count = 0
        self.updated_count = 0
        self.failed_count = 0
        self.failed_items = []  # Track failed items with details
    
    def sync_from_collector(self, collector, collected_data=None) -> Dict:
        """Sync resources from VMwareCollector to database
        
        Args:
            collector: VMwareCollector instance (already called collect())
            collected_data: Optional collected data dict (if None, will get from collector.collect() return value)
        """
        try:
            # Get collected data from collector if not provided
            if collected_data is None:
                # Call collect() to get data (returns dict, no YAML file)
                collected_data = collector.collect()
            
            if not collected_data:
                logger.error("No collected data available from collector")
                return {
                    'synced': 0,
                    'updated': 0,
                    'failed': 0,
                    'total': 0
                }
            
            # Extract data from collected_data structure
            # Structure: {root_key: {results: {server_info: ..., vms: ...}, os_type: ..., tcp_ports: ...}}
            root_key = list(collected_data.keys())[0] if collected_data else None
            if not root_key:
                logger.error("Invalid collected data structure")
                logger.error(f"Collected data keys: {list(collected_data.keys()) if collected_data else 'None'}")
                return {
                    'synced': 0,
                    'updated': 0,
                    'failed': 0,
                    'total': 0
                }
            
            logger.info(f"Extracting data from root_key: {root_key}")
            results = collected_data[root_key].get('results', {})
            server_info = results.get('server_info', {})
            vms_info = results.get('vms', {})
            logger.info(f"Extracted server_info type: {type(server_info)}, keys: {list(server_info.keys()) if isinstance(server_info, dict) else 'N/A'}")
            logger.info(f"Extracted vms_info type: {type(vms_info)}, count: {len(vms_info) if isinstance(vms_info, dict) else 'N/A'}")
            
            # Get ESXi hosts from server_info
            esxi_hosts = []
            if isinstance(server_info, dict):
                # If vCenter, server_info contains vCenter info with esxi nested
                if 'esxi' in server_info:
                    # vCenter case
                    esxis = server_info['esxi']
                    logger.info(f"Found vCenter with {len(esxis) if isinstance(esxis, dict) else 0} ESXi hosts")
                    for esxi_name, esxi_info in esxis.items():
                        esxi_hosts.append({
                            'name': esxi_name,
                            'info': esxi_info
                        })
                else:
                    # ESXi case - server_info is the ESXi info itself
                    logger.info(f"Found ESXi server with {len(server_info)} ESXi hosts")
                    for esxi_name, esxi_info in server_info.items():
                        esxi_hosts.append({
                            'name': esxi_name,
                            'info': esxi_info
                        })
            
            logger.info(f"Total ESXi hosts to sync: {len(esxi_hosts)}")
            
            # If no ESXi hosts found, try alternative data extraction
            if len(esxi_hosts) == 0 and len(vms_info) == 0:
                logger.warning("No ESXi hosts or VMs found in collected_data, trying alternative extraction from collector")
                # Try to get data from collector's internal state
                alt_data = self._get_data_from_collector(collector)
                if alt_data:
                    logger.info("Found data using alternative extraction method")
                    root_key = list(alt_data.keys())[0] if alt_data else None
                    if root_key:
                        results = alt_data[root_key].get('results', {})
                        server_info = results.get('server_info', {})
                        vms_info = results.get('vms', {})
                        # Re-extract ESXi hosts
                        esxi_hosts = []
                        if isinstance(server_info, dict):
                            if 'esxi' in server_info:
                                esxis = server_info['esxi']
                                logger.info(f"Found vCenter with {len(esxis) if isinstance(esxis, dict) else 0} ESXi hosts (alternative)")
                                for esxi_name, esxi_info in esxis.items():
                                    esxi_hosts.append({
                                        'name': esxi_name,
                                        'info': esxi_info
                                    })
                            else:
                                logger.info(f"Found ESXi server with {len(server_info)} ESXi hosts (alternative)")
                                for esxi_name, esxi_info in server_info.items():
                                    esxi_hosts.append({
                                        'name': esxi_name,
                                        'info': esxi_info
                                    })
                        logger.info(f"After alternative extraction: {len(esxi_hosts)} ESXi hosts, {len(vms_info) if isinstance(vms_info, dict) else 0} VMs")
            
            # Get VMs from vms_info
            vms = []
            if isinstance(vms_info, dict):
                for vmid, vm_data in vms_info.items():
                    if isinstance(vm_data, dict):
                        vms.append(vm_data)
            
            logger.info(f"Total VMs to sync: {len(vms)}")
            
            # Sync ESXi hosts (each commit immediately in _sync_esxi_host)
            logger.info(f"Starting to sync {len(esxi_hosts)} ESXi hosts...")
            for esxi in esxi_hosts:
                logger.info(f"Syncing ESXi host: {esxi.get('name', 'unknown')}")
                self._sync_esxi_host(esxi)
            
            logger.info(f"Completed syncing ESXi hosts. Synced: {self.synced_count}, Updated: {self.updated_count}, Failed: {self.failed_count}")
            
            # Sync VMs (each commit immediately in _sync_vm)
            logger.info(f"Starting to sync {len(vms)} VMs...")
            for vm_data in vms:
                vm_name = vm_data.get('name', 'unknown')
                logger.info(f"Syncing VM: {vm_name}")
                self._sync_vm(vm_data)
            
            logger.info(f"Completed syncing VMs. Total synced: {self.synced_count}, Updated: {self.updated_count}, Failed: {self.failed_count}")
            
            # All hosts are already committed individually, no need for final commit
            # But we keep this for safety in case of any remaining uncommitted changes
            try:
                db.session.commit()
            except Exception:
                # If nothing to commit, that's fine
                pass
            
            return {
                'synced': self.synced_count,
                'updated': self.updated_count,
                'failed': self.failed_count,
                'total': self.synced_count + self.updated_count,
                'failed_items': self.failed_items
            }
        except Exception as e:
            logger.error(f"VMware sync failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            db.session.rollback()
            raise
    
    def _get_data_from_collector(self, collector) -> Dict:
        """Get collected data from collector's internal state"""
        # Try to get from collector's internal attributes
        data = {}
        root_key = collector.root_key if hasattr(collector, 'root_key') else None
        
        if hasattr(collector, '_vc_info') and collector._vc_info:
            # vCenter case
            data[root_key] = {
                'results': {
                    'server_info': collector._vc_info,
                    'vms': collector._vms_info if hasattr(collector, '_vms_info') else {}
                },
                'os_type': collector.os_type if hasattr(collector, 'os_type') else 'VMWARE',
                'tcp_ports': None
            }
        elif hasattr(collector, '_esxis_info') and collector._esxis_info:
            # ESXi case
            data[root_key] = {
                'results': {
                    'server_info': collector._esxis_info,
                    'vms': collector._vms_info if hasattr(collector, '_vms_info') else {}
                },
                'os_type': collector.os_type if hasattr(collector, 'os_type') else 'VMWARE',
                'tcp_ports': None
            }
        
        return data
    
    
    def _sync_esxi_host(self, esxi: Dict):
        """Sync ESXi host to database"""
        try:
            esxi_name = esxi['name']
            esxi_info = esxi['info']
            logger.info(f"Processing ESXi host: {esxi_name}")
            
            # Extract ESXi summary info
            esxi_summary = esxi_info.get('esxi_info', {}) if isinstance(esxi_info, dict) else esxi_info
            
            # Extract IP and hardware info
            ip = (esxi_summary.get('ip') or 
                  esxi_summary.get('managementIp') or 
                  esxi_summary.get('hostname') or 
                  esxi_name)
            
            # Try to find existing host by name or IP
            host = Host.query.filter(
                ((Host.hostname == esxi_name) | (Host.ip == ip)) &
                (Host.deleted_at == None)
            ).first()
            
            # Extract hardware info
            cpu_cores = (esxi_summary.get('numCpu') or 
                        esxi_summary.get('cpuCores') or 
                        esxi_summary.get('numCpuThreads'))
            memory_bytes = (esxi_summary.get('memorySize') or 
                           esxi_summary.get('totalMemory'))
            memory_gb = memory_bytes / (1024 * 1024 * 1024) if memory_bytes else None
            
            # Extract ESXI version for distribution field
            esxi_version = (esxi_summary.get('fullName') or 
                           esxi_summary.get('version') or 
                           esxi_summary.get('productLineId'))
            
            exsi_product_name = (esxi_summary.get('licenseProductName') or 
                               esxi_summary.get('productLineId'))
            
            if host:
                # Update existing host
                host.hostname = esxi_name
                if ip and ip != host.ip:
                    host.ip = ip
                host.os_type = "VMware ESXi"
                host.distribution = esxi_version
                host.device_type = exsi_product_name
                host.is_physical = False
                host.virtualization_platform_id = self.platform.id
                host.cpu_cores = cpu_cores
                host.memory_total = memory_gb
                host.updated_at = datetime.utcnow()
                self.updated_count += 1
            else:
                # Extract ESXI version for distribution field
                esxi_version = (esxi_summary.get('fullName') or 
                               esxi_summary.get('version') or 
                               esxi_summary.get('productLineId'))
                
                # Create new host
                host = Host(
                    hostname=esxi_name,
                    ip=ip,
                    os_type='VMware ESXi',
                    distribution=esxi_version,
                    device_type=exsi_product_name,
                    is_physical=False,
                    virtualization_platform_id=self.platform.id,
                    cpu_cores=cpu_cores,
                    memory_total=memory_gb,
                    created_by=self.user_id,
                )
                db.session.add(host)
                db.session.flush()  # Get host.id
                self.synced_count += 1
            
            # Set source information
            host.source = 'platform'
            host.source_platform_id = self.platform.id
            
            # Record collection history (no longer storing raw JSON)
            detail = HostDetail(
                host_id=host.id,
                details='',  # No longer storing raw data
                status='success',
                collection_method='vmware_esxi',
                collected_at=datetime.utcnow(),
            )
            db.session.add(detail)
            
            # Commit immediately for real-time database updates
            db.session.commit()
            logger.info(f"Successfully synced ESXi host {esxi_name} to database (host.id={host.id}, ip={host.ip})")
            
            # Return host ID for task tracking
            return host.id
            
        except Exception as e:
            esxi_name = esxi.get('name', 'unknown')
            error_msg = str(e)
            logger.error(f"Failed to sync ESXi host {esxi_name}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self.failed_count += 1
            self.failed_items.append({
                'type': 'esxi',
                'name': esxi_name,
                'ip': esxi.get('info', {}).get('ip') or esxi.get('info', {}).get('managementIp') or esxi_name,
                'error': error_msg
            })
            return None  # Return None on failure
    
    def _sync_vm(self, vm_info: Dict):
        """Sync VM to database using Parser"""
        try:
            vm_name = vm_info.get('name', '')
            vm_uuid = vm_info.get('uuid', '')
            logger.info(f"Processing VM: {vm_name} (UUID: {vm_uuid})")
            
            if not vm_name:
                logger.warning("VM info missing name, skipping")
                self.failed_count += 1
                return
            
            # Extract ESXi host name from vm_info
            # vm_info contains: {"esxi_host": {esxi_name: {...}}, ...}
            esxi_host_name = None
            esxi_host_info = vm_info.get('esxi_host', {})
            if esxi_host_info and isinstance(esxi_host_info, dict):
                # Get the first (and only) key which is the ESXi host name
                esxi_host_name = list(esxi_host_info.keys())[0] if esxi_host_info else None
                logger.info(f"VM {vm_name} is on ESXi host: {esxi_host_name}")
            
            # Prepare VM data in format expected by CollectionParserService
            # CollectionParserService expects: {root_key: {results: {...}, os_type: ...}}
            # VMwareParser expects: {vm_name: {esxi_host: {...}, name, memoryMB, numCpu, ...}}
            # So we wrap vm_info in the expected format
            vm_data_for_parser = {
                vm_name: vm_info
            }
            collector_data_format = {
                f"VMWARE_{vm_name}": {
                    "results": vm_data_for_parser,
                    "os_type": "VMWARE",
                    "tcp_ports": None
                }
            }
            
            # Use Parser to parse VM data
            from services.collection_parser_service import CollectionParserService
            parser_service = CollectionParserService('VMWARE')
            parsed_data = parser_service.parse_collection_data(collector_data_format)
            
            # Get IP from parsed data or vm_info
            vm_ip = parsed_data.get('basic', {}).get('conn_ip') or vm_info.get('ipAddress', '')
            if not vm_ip:
                # Try to get from network info
                network_info = vm_info.get('network', {})
                for net in network_info.values():
                    if net.get('ipAddress'):
                        vm_ip = net['ipAddress']
                        break
            
            # Try to find existing host by multiple criteria
            host = None
            
            # First, try to find by IP (most reliable)
            if vm_ip and vm_ip != vm_uuid and not vm_ip.startswith('vm-'):
                host = Host.query.filter_by(ip=vm_ip, deleted_at=None).first()
            
            # If not found, try by hostname
            if not host and vm_name:
                host = Host.query.filter_by(hostname=vm_name, deleted_at=None).first()
            
            # If not found, try by UUID (stored in mac field)
            if not host and vm_uuid:
                host = Host.query.filter_by(mac=vm_uuid, deleted_at=None).first()
            
            # If still not found, check if IP is a valid format (not UUID or vm- prefix)
            # and if it already exists (might be from scan)
            if not host and vm_ip:
                # Check if IP already exists (even if deleted_at is set, we might want to restore it)
                existing_by_ip = Host.query.filter_by(ip=vm_ip).first()
                if existing_by_ip:
                    # If exists but deleted, restore it
                    if existing_by_ip.deleted_at:
                        existing_by_ip.deleted_at = None
                    host = existing_by_ip
            
            if not host:
                # Use VM UUID or name as identifier if no valid IP
                if not vm_ip or vm_ip == vm_uuid or vm_ip.startswith('vm-'):
                    # Generate a unique IP-like identifier
                    vm_ip = f"vm-{vm_uuid[:8]}" if vm_uuid else f"vm-{vm_name}"
                
                # Double-check the IP doesn't exist before creating
                existing = Host.query.filter_by(ip=vm_ip, deleted_at=None).first()
                if existing:
                    host = existing
                else:
                    # Create new host
                    host = Host(
                        hostname=vm_name,
                        ip=vm_ip,
                        mac=vm_uuid,  # Use UUID as MAC for unique identification
                        source='platform',
                        source_platform_id=self.platform.id,
                        virtualization_platform_id=self.platform.id,
                        created_by=self.user_id,
                    )
                    db.session.add(host)
                    try:
                        db.session.flush()  # Get host.id
                        self.synced_count += 1
                    except Exception as e:
                        # If flush fails due to unique constraint, try to find existing
                        db.session.rollback()
                        existing = Host.query.filter_by(ip=vm_ip, deleted_at=None).first()
                        if existing:
                            host = existing
                            self.updated_count += 1
                        else:
                            raise
            else:
                # Update existing host
                self.updated_count += 1
            
            # Ensure host is committed before calling update_host_from_parsed_data
            # Because update_host_from_parsed_data does a rollback at the start, we need to commit first
            # to ensure the host exists in the database, otherwise the rollback will undo our new host creation
            if not host.id:
                # This shouldn't happen, but if host doesn't have an ID, flush to get it
                db.session.flush()
            
            # Commit host to database before calling update_host_from_parsed_data
            # This ensures the host exists even if update_host_from_parsed_data does a rollback
            db.session.commit()
            
            # Refresh host to ensure it's in the current session after commit
            db.session.refresh(host)
            
            # Update host from parsed data (this will update all fields including disks, partitions, networks)
            # Note: update_host_from_parsed_data will rollback and re-query, but host is now committed
            parser_service.update_host_from_parsed_data(host, parsed_data)
            
            # Ensure source is set and device_type is set for VM
            host.source = 'platform'
            host.source_platform_id = self.platform.id
            host.virtualization_platform_id = self.platform.id
            # Set device_type to 'vm' to distinguish from ESXi hosts
            if not host.device_type or host.device_type == 'host':
                host.device_type = 'vm'
            host.is_physical = False  # Ensure VM is marked as virtual
            
            # Store ESXi host name in vendor field for tree view grouping
            # Format: "ESXi: <host_name>" so get_hosts_tree can extract it
            if esxi_host_name:
                host.vendor = f"ESXi: {esxi_host_name}"
                logger.debug(f"Set VM {vm_name} vendor to: {host.vendor}")
            
            # Record collection history (no longer storing raw JSON)
            detail = HostDetail(
                host_id=host.id,
                details='',  # No longer storing raw data
                status='success',
                collection_method='vmware_vm',
                collected_at=datetime.utcnow(),
            )
            db.session.add(detail)
            
            # Commit immediately for real-time database updates
            db.session.commit()
            logger.info(f"Successfully synced VM {vm_name} to database (host.id={host.id})")
            
            # Return host ID for task tracking
            return host.id
            
        except Exception as e:
            vm_name = vm_info.get('name', 'unknown')
            vm_ip = vm_info.get('ipAddress', '')
            error_msg = str(e)
            logger.error(f"Failed to sync VM {vm_name}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self.failed_count += 1
            self.failed_items.append({
                'type': 'vm',
                'name': vm_name,
                'ip': vm_ip,
                'error': error_msg
            })
            return None  # Return None on failure

