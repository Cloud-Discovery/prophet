# Copyright (c) 2021 OnePro Cloud Ltd.
#
#   prophet is licensed under Mulan PubL v2.

"""Collection data parser service

Parse collector returned data using Parser classes and update database models.
"""

import logging
from typing import Dict, Any
from models import Host, HostDisk, HostPartition, HostNetworkInterface, db
from datetime import datetime

logger = logging.getLogger(__name__)


class CollectionParserService:
    """Service for parsing collection data and updating database"""
    
    def __init__(self, os_type: str):
        """Initialize parser service
        
        Args:
            os_type: OS type (LINUX, WINDOWS, VMWARE)
        """
        self.os_type = os_type.upper()
        self.parser = None
        self._init_parser()
    
    def _init_parser(self):
        """Initialize appropriate parser based on OS type"""
        try:
            if self.os_type == 'LINUX':
                from prophet.parser.hosts.linux import LinuxParser
                self.parser_class = LinuxParser
            elif self.os_type == 'WINDOWS':
                from prophet.parser.hosts.windows import WindowsParser
                self.parser_class = WindowsParser
            elif self.os_type == 'VMWARE':
                from prophet.parser.hosts.vmware import VMwareParser
                self.parser_class = VMwareParser
            else:
                raise ValueError(f"Unsupported OS type: {self.os_type}")
        except ImportError as e:
            logger.error(f"Failed to import parser for {self.os_type}: {e}")
            raise
    
    def parse_collection_data(self, collector_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse collector returned data
        
        Args:
            collector_data: Data dictionary returned by collector.collect()
                Format: {
                    "ostype_ip": {
                        "results": {...},
                        "os_type": "LINUX",
                        "tcp_ports": "..."
                    }
                }
        
        Returns:
            Parsed structured data dictionary
        """
        try:
            # Extract the root key and data
            root_key = list(collector_data.keys())[0] if collector_data else None
            if not root_key:
                raise ValueError("Empty collector data")
            
            data = collector_data[root_key]
            results = data.get('results', {})
            
            # Initialize parser with results
            # For Linux/Windows, results structure is different from VMware
            if self.os_type == 'LINUX':
                # Linux collector returns: {"results": ansible_facts_dict}
                # But LinuxParser expects: {"success": {ip: {"ansible_facts": {...}}}, "failed": {}}
                # So we need to convert the format
                if isinstance(results, dict) and ('success' in results or 'failed' in results):
                    # Already in correct format (from ansible_api directly)
                    parser_input = results
                elif isinstance(results, dict):
                    # Results is ansible_facts dict directly
                    # Extract IP from ansible_facts to use as key
                    ansible_facts = results
                    ip = None
                    if isinstance(ansible_facts, dict):
                        if 'ansible_default_ipv4' in ansible_facts:
                            ip = ansible_facts['ansible_default_ipv4'].get('address')
                        elif 'ansible_all_ipv4_addresses' in ansible_facts and ansible_facts['ansible_all_ipv4_addresses']:
                            ip = ansible_facts['ansible_all_ipv4_addresses'][0]
                        # Also try to extract from root_key (format: LINUX_192.168.10.66)
                        if not ip and root_key:
                            parts = root_key.split('_')
                            if len(parts) >= 2:
                                potential_ip = parts[-1]
                                # Validate it's an IP
                                import re
                                if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', potential_ip):
                                    ip = potential_ip
                    
                    # Use root_key as fallback if IP not found
                    host_key = ip if ip else root_key.split('_')[-1] if root_key else 'unknown'
                    
                    # Convert to expected format
                    parser_input = {
                        "success": {
                            host_key: {
                                "ansible_facts": ansible_facts
                            }
                        },
                        "failed": {}
                    }
                else:
                    # Invalid format
                    raise ValueError(f"Invalid results format for Linux parser: {type(results)}")
                
                parser = self.parser_class(parser_input)
            elif self.os_type == 'WINDOWS':
                # Windows collector returns WMI data directly
                parser = self.parser_class(results)
            elif self.os_type == 'VMWARE':
                # VMware collector returns: {vm_name: {esxi_host: {...}, name, memoryMB, ...}}
                # Parser expects the same structure
                parser = self.parser_class(results)
            else:
                raise ValueError(f"Unsupported OS type: {self.os_type}")
            
            # Parse all information
            parsed_data = parser.parse()
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"Failed to parse collection data: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    def update_host_from_parsed_data(self, host: Host, parsed_data: Dict[str, Any]) -> None:
        """Update host and related models from parsed data
        
        Args:
            host: Host model instance to update
            parsed_data: Parsed data from parser.parse()
        """
        import time
        max_retries = 3
        retry_delay = 0.1  # 100ms
        
        host_id = host.id
        
        for attempt in range(max_retries):
            try:
                try:
                    host = db.session.merge(host)
                    logger.debug(f"Merged host {host_id} into session")
                except Exception as merge_error:
                    logger.warning(f"Failed to merge host {host_id} into session: {merge_error}")
                    try:
                        db.session.rollback()
                    except Exception:
                        pass
                    
                    host = Host.query.get(host_id)
                    if not host:
                        raise ValueError(f"Host {host_id} not found")
                    logger.warning(f"Had to re-query host {host_id} in update_host_from_parsed_data (attempt {attempt + 1})")
                
                basic = parsed_data.get('basic', {})
                os_info = parsed_data.get('os', {})
                cpu_info = parsed_data.get('cpu', {})
                memory_info = parsed_data.get('memory', {})
                disks_info = parsed_data.get('disks', {})
                networks_info = parsed_data.get('networks', {})
                vt_info = parsed_data.get('vt', {})
                
                # Update basic information
                if basic.get('hostname'):
                    host.hostname = basic.get('hostname')
                if basic.get('conn_ip'):
                    host.ip = basic.get('conn_ip')
                if basic.get('conn_mac'):
                    host.mac = basic.get('conn_mac')
                
                # Update OS information
                if os_info.get('os'):
                    host.os_type = os_info.get('os')
                if 'distribution' in os_info:
                    host.distribution = os_info.get('distribution')
                if os_info.get('os_version'):
                    host.os_version = os_info.get('os_version')
                if os_info.get('os_kernel'):
                    host.os_kernel = os_info.get('os_kernel')
                if os_info.get('os_bit'):
                    host.os_bit = os_info.get('os_bit')
                
                # Update CPU information
                if cpu_info.get('cpu_info'):
                    host.cpu_info = cpu_info.get('cpu_info')
                if cpu_info.get('cpu_cores') is not None:  # Allow 0 as valid value
                    host.cpu_cores = cpu_info.get('cpu_cores')
                else:
                    logger.warning(f"cpu_cores is None or missing in cpu_info: {cpu_info}")
                
                # Update memory information
                if memory_info.get('total_mem') is not None:  # Allow 0 as valid value
                    # Convert bytes to GB
                    total_mem_bytes = memory_info.get('total_mem')
                    host.memory_total = round(total_mem_bytes / (1024**3), 2) if total_mem_bytes else None
                else:
                    logger.warning(f"total_mem is None or missing in memory_info: {memory_info}")
                if memory_info.get('free_mem') is not None:  # Allow 0 as valid value
                    free_mem_bytes = memory_info.get('free_mem')
                    host.memory_free = round(free_mem_bytes / (1024**3), 2) if free_mem_bytes else None
                else:
                    logger.warning(f"free_mem is None or missing in memory_info: {memory_info}")
                if memory_info.get('memory_info'):
                    host.memory_info = memory_info.get('memory_info')
                
                # Update boot type
                if disks_info.get('boot_type'):
                    host.boot_type = disks_info.get('boot_type')
                
                # Update virtualization information
                if vt_info.get('vt_platform'):
                    host.vt_platform = vt_info.get('vt_platform')
                if vt_info.get('vt_platform_ver'):
                    host.vt_platform_ver = vt_info.get('vt_platform_ver')
                
                # Update device type based on host_type
                if basic.get('host_type'):
                    host_type = basic.get('host_type')
                    if 'VMware' in host_type or 'OpenStack' in host_type:
                        host.is_physical = False
                    else:
                        host.is_physical = True
                
                # Update disks
                self._update_disks(host, disks_info)
                
                # Update partitions
                self._update_partitions(host, disks_info)
                
                # Update network interfaces
                self._update_network_interfaces(host, networks_info)
                
                # Update summary fields - use counts from parsed data to avoid lazy loading
                disk_count = len(disks_info.get('disks', []))
                host.disk_count = disk_count
                if disks_info.get('total_size'):
                    total_size_bytes = disks_info.get('total_size')
                    host.disk_total_size = round(total_size_bytes / (1024**3), 2) if total_size_bytes else None
                network_count = len(networks_info.get('nics', []))
                host.network_count = network_count
                
                # Update collection status
                host.last_collected_at = datetime.utcnow()
                host.collection_status = 'completed'
                
                # Commit changes
                db.session.commit()
                return  # Success, exit retry loop
                
            except Exception as e:
                from sqlalchemy.orm.exc import StaleDataError
                error_str = str(e)
                is_locked = 'database is locked' in error_str.lower() or 'locked' in error_str.lower()
                is_stale = isinstance(e, StaleDataError) or 'staledataerror' in error_str.lower() or 'expected to update' in error_str.lower()
                
                if (is_locked or is_stale) and attempt < max_retries - 1:
                    error_type = "locked" if is_locked else "stale data"
                    logger.warning(f"Database {error_type} in update_host_from_parsed_data (attempt {attempt + 1}/{max_retries}), retrying after {retry_delay}s...")
                    db.session.rollback()
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                else:
                    # Other error or max retries reached
                    logger.error(f"Failed to update host from parsed data: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    try:
                        db.session.rollback()
                        # Re-query host to ensure we have the latest state
                        host = Host.query.get(host_id)
                        if host:
                            host.collection_status = 'failed'
                            db.session.commit()
                    except Exception as commit_error:
                        logger.error(f"Failed to update host status after error: {commit_error}")
                        db.session.rollback()
                    raise
    
    def _update_disks(self, host: Host, disks_info: Dict[str, Any]) -> None:
        """Update host disks"""
        # Delete existing disks
        HostDisk.query.filter_by(host_id=host.id).delete()
        
        disks = disks_info.get('disks', [])
        for idx, disk_data in enumerate(disks):
            disk = HostDisk(
                host_id=host.id,
                device=disk_data.get('device', ''),
                size=disk_data.get('size'),
                vendor=disk_data.get('vendor'),
                model=disk_data.get('model'),
                index=idx
            )
            db.session.add(disk)
    
    def _update_partitions(self, host: Host, disks_info: Dict[str, Any]) -> None:
        """Update host partitions"""
        # Delete existing partitions
        HostPartition.query.filter_by(host_id=host.id).delete()
        
        partitions = disks_info.get('partitions', [])
        for part_data in partitions:
            partition = HostPartition(
                host_id=host.id,
                device=part_data.get('device', ''),
                size_total=part_data.get('size_total'),
                size_available=part_data.get('size_available'),
                size_available_ratio=part_data.get('size_available_ratio'),
                fstype=part_data.get('fstype'),
                disk_index=part_data.get('disk_index')
            )
            db.session.add(partition)
    
    def _update_network_interfaces(self, host: Host, networks_info: Dict[str, Any]) -> None:
        """Update host network interfaces"""
        # Delete existing network interfaces
        HostNetworkInterface.query.filter_by(host_id=host.id).delete()
        
        nics = networks_info.get('nics', [])
        default_interface = networks_info.get('interface')
        
        for nic_data in nics:
            interface_name = nic_data.get('interface')
            is_default = (interface_name == default_interface)
            
            nic = HostNetworkInterface(
                host_id=host.id,
                interface=interface_name,
                macaddress=nic_data.get('macaddress'),
                active=nic_data.get('active', True),
                mtu=nic_data.get('mtu'),
                speed=nic_data.get('speed'),
                ipv4_address=nic_data.get('ipv4_address'),
                ipv4_netmask=nic_data.get('ipv4_netmask'),
                ipv4_network=nic_data.get('ipv4_network'),
                ipv4_broadcast=nic_data.get('ipv4_broadcast'),
                ipv6_address=nic_data.get('ipv6_address'),
                gateway=nic_data.get('gateway'),
                is_default=is_default
            )
            db.session.add(nic)

