# Copyright (c) 2021 OnePro Cloud Ltd.
#
#   prophet is licensed under Mulan PubL v2.

"""Host related models"""

from datetime import datetime
from db import db
import json


class Host(db.Model):
    """Host/Device model"""
    __tablename__ = 'hosts'
    
    id = db.Column(db.Integer, primary_key=True)
    hostname = db.Column(db.String(255), index=True)
    ip = db.Column(db.String(45), nullable=False, index=True)
    mac = db.Column(db.String(17), index=True)
    vendor = db.Column(db.String(100))
    
    # OS information
    os_type = db.Column(db.String(50), index=True)
    os_version = db.Column(db.String(255))
    os_kernel = db.Column(db.String(255))  # Kernel version
    os_bit = db.Column(db.String(20))  # 32-bit/64-bit
    distribution = db.Column(db.String(100))  # OS distribution (e.g., Ubuntu, CentOS)
    boot_type = db.Column(db.String(10))  # bios/efi
    
    # Hardware information
    cpu_info = db.Column(db.String(255))
    cpu_cores = db.Column(db.Integer)
    memory_total = db.Column(db.Float)  # GB
    memory_free = db.Column(db.Float)  # GB
    memory_info = db.Column(db.String(255))  # Memory model info
    disk_count = db.Column(db.Integer)
    disk_total_size = db.Column(db.Float)  # GB
    network_count = db.Column(db.Integer)
    
    # Virtualization information
    vt_platform = db.Column(db.String(50))  # VMware/OpenStack/etc
    vt_platform_ver = db.Column(db.String(255))  # Virtualization platform version
    
    # Device type
    device_type = db.Column(db.String(50), default='host', index=True)  # host/network_device
    is_physical = db.Column(db.Boolean, default=True, index=True)
    
    # Source information
    source = db.Column(db.String(20), default='manual', index=True)  # scan/platform/manual
    source_scan_task_id = db.Column(db.Integer, db.ForeignKey('scan_tasks.id'), nullable=True)
    source_platform_id = db.Column(db.Integer, db.ForeignKey('virtualization_platforms.id'), nullable=True)
    
    # Scan information
    scan_ports = db.Column(db.Text)  # JSON string of scanned ports: {"tcp": [22, 80, 443], "udp": [...]}
    
    # Collection status
    last_collected_at = db.Column(db.DateTime, nullable=True, index=True)
    collection_status = db.Column(db.String(20), default='not_collected', index=True)  # not_collected/collecting/completed/failed
    
    # Relationships
    virtualization_platform_id = db.Column(db.Integer, db.ForeignKey('virtualization_platforms.id'), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True, index=True)
    
    # Relationships
    credentials = db.relationship('HostCredential', backref='host', lazy=True, cascade='all, delete-orphan')
    details = db.relationship('HostDetail', backref='host', lazy=True, cascade='all, delete-orphan')
    tags = db.relationship('HostTag', secondary='host_tag_relations', lazy='subquery', backref=db.backref('hosts', lazy=True))
    platform = db.relationship('VirtualizationPlatform', foreign_keys=[virtualization_platform_id], backref='hosts', lazy=True)
    disks = db.relationship('HostDisk', backref='host', lazy=True, cascade='all, delete-orphan', order_by='HostDisk.index')
    partitions = db.relationship('HostPartition', backref='host', lazy=True, cascade='all, delete-orphan')
    network_interfaces = db.relationship('HostNetworkInterface', backref='host', lazy=True, cascade='all, delete-orphan', order_by='HostNetworkInterface.is_default.desc(), HostNetworkInterface.interface')
    
    def to_dict(self, include_details=False):
        """Convert to dictionary"""
        data = {
            'id': self.id,
            'hostname': self.hostname,
            'ip': self.ip,
            'mac': self.mac,
            'vendor': self.vendor,
            'os_type': self.os_type,
            'os_version': self.os_version,
            'os_kernel': self.os_kernel,
            'os_bit': self.os_bit,
            'distribution': self.distribution,
            'boot_type': self.boot_type,
            'cpu_info': self.cpu_info,
            'cpu_cores': self.cpu_cores,
            'memory_total': self.memory_total,
            'memory_free': self.memory_free,
            'memory_info': self.memory_info,
            'disk_count': self.disk_count,
            'disk_total_size': self.disk_total_size,
            'network_count': self.network_count,
            'device_type': self.device_type,
            'is_physical': self.is_physical,
            'vt_platform': self.vt_platform,
            'vt_platform_ver': self.vt_platform_ver,
            'source': self.source,
            'source_scan_task_id': self.source_scan_task_id,
            'source_platform_id': self.source_platform_id,
            'scan_ports': self.get_scan_ports(),
            'last_collected_at': self.last_collected_at.isoformat() if self.last_collected_at else None,
            'collection_status': self.collection_status,
            'virtualization_platform_id': self.virtualization_platform_id,
            'platform_name': self.platform.name if self.platform else None,
            'tags': [tag.to_dict() for tag in self.tags],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_details:
            data['disks'] = [disk.to_dict() for disk in self.disks]
            data['partitions'] = [part.to_dict() for part in self.partitions]
            data['network_interfaces'] = [nic.to_dict() for nic in self.network_interfaces]
        
        if include_details and self.details:
            latest_detail = max(self.details, key=lambda d: d.collected_at or datetime.min)
            if latest_detail:
                data['latest_detail'] = latest_detail.to_dict()
        
        return data
    
    def get_scan_ports(self):
        """Get scan ports as dict"""
        if self.scan_ports:
            try:
                return json.loads(self.scan_ports)
            except (json.JSONDecodeError, TypeError):
                return None
        return None
    
    def set_scan_ports(self, ports_dict):
        """Set scan ports from dict"""
        if ports_dict:
            self.scan_ports = json.dumps(ports_dict, ensure_ascii=False)
        else:
            self.scan_ports = None
    
    def __repr__(self):
        return f'<Host {self.ip}>'


class HostCredential(db.Model):
    """Host credential model"""
    __tablename__ = 'host_credentials'
    
    id = db.Column(db.Integer, primary_key=True)
    host_id = db.Column(db.Integer, db.ForeignKey('hosts.id'), nullable=False, index=True)
    username = db.Column(db.String(255), nullable=False)
    password_encrypted = db.Column(db.Text)  # Encrypted password
    ssh_port = db.Column(db.Integer, default=22)
    key_path = db.Column(db.String(500))  # Path to SSH key file
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self, decrypt_password=False):
        """Convert to dictionary"""
        data = {
            'id': self.id,
            'host_id': self.host_id,
            'username': self.username,
            'ssh_port': self.ssh_port,
            'key_path': self.key_path,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        
        if decrypt_password and self.password_encrypted:
            from utils.encryption import decrypt_password
            try:
                data['password'] = decrypt_password(self.password_encrypted)
            except Exception:
                data['password'] = None
        
        return data
    
    def __repr__(self):
        return f'<HostCredential {self.host_id}>'


class HostDetail(db.Model):
    """Host detail collection result"""
    __tablename__ = 'host_details'
    
    id = db.Column(db.Integer, primary_key=True)
    host_id = db.Column(db.Integer, db.ForeignKey('hosts.id'), nullable=False, index=True)
    details = db.Column(db.Text)  # JSON string of collection result
    collected_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    status = db.Column(db.String(50), default='success')  # success/failed
    collection_method = db.Column(db.String(50))  # ansible/wmi/vmware_api
    error_message = db.Column(db.Text)  # Error message if collection failed
    
    def get_details(self):
        """Get details as dict"""
        if self.details:
            return json.loads(self.details)
        return {}
    
    def set_details(self, details_dict):
        """Set details from dict"""
        self.details = json.dumps(details_dict, ensure_ascii=False)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'host_id': self.host_id,
            'details': self.get_details(),
            'collected_at': self.collected_at.isoformat() if self.collected_at else None,
            'status': self.status,
            'collection_method': self.collection_method,
            'error_message': self.error_message,
        }
    
    def __repr__(self):
        return f'<HostDetail {self.host_id}>'


class HostTag(db.Model):
    """Host tag model"""
    __tablename__ = 'host_tags'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    color = db.Column(db.String(7), default='#3B82F6')  # Hex color
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
    
    def __repr__(self):
        return f'<HostTag {self.name}>'


class HostTagRelation(db.Model):
    """Host-Tag relation table"""
    __tablename__ = 'host_tag_relations'
    
    host_id = db.Column(db.Integer, db.ForeignKey('hosts.id'), primary_key=True)
    tag_id = db.Column(db.Integer, db.ForeignKey('host_tags.id'), primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class HostRelationship(db.Model):
    """Host dependency relationship (graph structure)"""
    __tablename__ = 'host_relationships'
    
    id = db.Column(db.Integer, primary_key=True)
    from_host_id = db.Column(db.Integer, db.ForeignKey('hosts.id'), nullable=False, index=True)
    to_host_id = db.Column(db.Integer, db.ForeignKey('hosts.id'), nullable=False, index=True)
    relationship_type = db.Column(db.String(50), nullable=False)  # depends_on/communicates_with/backup_of
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    from_host = db.relationship('Host', foreign_keys=[from_host_id], backref='outgoing_relationships')
    to_host = db.relationship('Host', foreign_keys=[to_host_id], backref='incoming_relationships')
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'from_host_id': self.from_host_id,
            'to_host_id': self.to_host_id,
            'relationship_type': self.relationship_type,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
    
    def __repr__(self):
        return f'<HostRelationship {self.from_host_id} -> {self.to_host_id}>'


class HostDisk(db.Model):
    """Host disk model"""
    __tablename__ = 'host_disks'
    
    id = db.Column(db.Integer, primary_key=True)
    host_id = db.Column(db.Integer, db.ForeignKey('hosts.id'), nullable=False, index=True)
    device = db.Column(db.String(100), nullable=False)  # Device name (e.g., sda, /dev/sda)
    size = db.Column(db.BigInteger)  # Size in bytes
    vendor = db.Column(db.String(100))  # Disk vendor
    model = db.Column(db.String(255))  # Disk model
    index = db.Column(db.Integer, default=0)  # Disk index/order
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'host_id': self.host_id,
            'device': self.device,
            'size': self.size,
            'size_gb': round(self.size / (1024**3), 2) if self.size else None,
            'vendor': self.vendor,
            'model': self.model,
            'index': self.index,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
    
    def __repr__(self):
        return f'<HostDisk {self.device} on host {self.host_id}>'


class HostPartition(db.Model):
    """Host partition model"""
    __tablename__ = 'host_partitions'
    
    id = db.Column(db.Integer, primary_key=True)
    host_id = db.Column(db.Integer, db.ForeignKey('hosts.id'), nullable=False, index=True)
    device = db.Column(db.String(255), nullable=False)  # Partition device (e.g., /dev/sda1, C:)
    size_total = db.Column(db.BigInteger)  # Total size in bytes
    size_available = db.Column(db.BigInteger)  # Available size in bytes
    size_available_ratio = db.Column(db.Float)  # Available ratio (0.0-1.0)
    fstype = db.Column(db.String(50))  # Filesystem type (xfs, ext4, NTFS, etc.)
    disk_index = db.Column(db.Integer, nullable=True)  # Associated disk index
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'host_id': self.host_id,
            'device': self.device,
            'size_total': self.size_total,
            'size_total_gb': round(self.size_total / (1024**3), 2) if self.size_total else None,
            'size_available': self.size_available,
            'size_available_gb': round(self.size_available / (1024**3), 2) if self.size_available else None,
            'size_used_gb': round((self.size_total - self.size_available) / (1024**3), 2) if (self.size_total and self.size_available) else None,
            'size_available_ratio': self.size_available_ratio,
            'fstype': self.fstype,
            'disk_index': self.disk_index,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
    
    def __repr__(self):
        return f'<HostPartition {self.device} on host {self.host_id}>'


class HostNetworkInterface(db.Model):
    """Host network interface model"""
    __tablename__ = 'host_network_interfaces'
    
    id = db.Column(db.Integer, primary_key=True)
    host_id = db.Column(db.Integer, db.ForeignKey('hosts.id'), nullable=False, index=True)
    interface = db.Column(db.String(100), nullable=False)  # Interface name (e.g., eth0, ens2f0)
    macaddress = db.Column(db.String(17))  # MAC address
    active = db.Column(db.Boolean, default=True)  # Is interface active
    mtu = db.Column(db.Integer)  # MTU value
    speed = db.Column(db.Integer)  # Speed in Mbps
    ipv4_address = db.Column(db.String(45))  # IPv4 address
    ipv4_netmask = db.Column(db.String(45))  # IPv4 netmask
    ipv4_network = db.Column(db.String(45))  # IPv4 network
    ipv4_broadcast = db.Column(db.String(45))  # IPv4 broadcast
    ipv6_address = db.Column(db.String(45))  # IPv6 address
    gateway = db.Column(db.String(45))  # Gateway address
    is_default = db.Column(db.Boolean, default=False)  # Is default interface
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'host_id': self.host_id,
            'interface': self.interface,
            'macaddress': self.macaddress,
            'active': self.active,
            'mtu': self.mtu,
            'speed': self.speed,
            'ipv4_address': self.ipv4_address,
            'ipv4_netmask': self.ipv4_netmask,
            'ipv4_network': self.ipv4_network,
            'ipv4_broadcast': self.ipv4_broadcast,
            'ipv6_address': self.ipv6_address,
            'gateway': self.gateway,
            'is_default': self.is_default,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
    
    def __repr__(self):
        return f'<HostNetworkInterface {self.interface} on host {self.host_id}>'

