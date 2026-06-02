# Copyright (c) 2021 OnePro Cloud Ltd.
#
#   prophet is licensed under Mulan PubL v2.
#   You can use this software according to the terms and conditions of the Mulan PubL v2.
#   You may obtain a copy of Mulan PubL v2 at:
#
#            http://license.coscl.org.cn/MulanPubL-2.0
#
#   THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
#   EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
#   MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
#   See the Mulan PubL v2 for more details.

"""Network scanner based on nmap

Scan network based on ip address, then analysis and return results
for direct database storage

"""

import logging
import nmap

DEFAULT_ARGS = "-sS -O"
DEFAULT_LINUX_USER = "root"
DEFAULT_WINDOWS_USER = "Administrator"
DEFAULT_USER = "enter_your_username"
DEFAULT_LINUX_PORT = "22"
DEFAULT_VMWARE_PORT = "443"
CHECKSTATUS_CHECK = "check"


class NetworkController(object):

    def __init__(self, host, arg):
        """Initialize network scanner
        
        Args:
            host: IP address, IP range, or CIDR notation to scan
            arg: nmap arguments (default: "-sS -O")
        """
        self.host = host
        self.arg = arg if arg else DEFAULT_ARGS
        self.nm = nmap.PortScanner()

    def scan(self):
        """Scan network and return results as a generator
        
        Note: _scan() must be called first to perform the actual nmap scan.
        This method processes the already-scanned results.
        
        Yields:
            dict: Host scan result with keys:
                - ip: IP address
                - hostname: Hostname
                - mac: MAC address
                - vendor: Vendor information
                - os: Operating system family
                - os_version: OS version
                - ports: Dict with 'tcp' and 'udp' keys containing port lists
                - ssh_port: Suggested SSH port
                - username: Suggested username
        """
        # Get hosts from already-performed scan
        hosts = self.nm.all_hosts()
        if not hosts:
            # If no hosts, perform scan now
            hosts = self._scan()
        total = len(hosts)
        
        for idx, host_ip in enumerate(hosts):
            try:
                logging.info(f"Analyzing {host_ip} ({idx + 1}/{total})...")
                host_info = self.nm[host_ip]
                logging.debug(f"Host info: {host_info}")
                
                hostname = host_info.hostname()
                mac = self._get_mac(host_info.get("addresses"))
                osfamily, version = self._get_os(host_info.get("osmatch"))
                vendor = self._get_vendor(host_info.get("vendor"), mac)
                ssh_port = self._get_ssh_port(osfamily)
                username = self._get_username(osfamily)
                
                # Get TCP and UDP ports
                tcp_ports = list(self.nm[host_ip].all_tcp())
                udp_ports = list(self.nm[host_ip].all_udp())
                
                # Get detailed port information
                ports_info = {
                    'tcp': tcp_ports,
                    'udp': udp_ports,
                }
                
                result = {
                    "ip": host_ip,
                    "hostname": hostname or None,
                    "mac": mac or None,
                    "vendor": vendor or None,
                    "os": osfamily or None,
                    "os_version": version or None,
                    "ports": ports_info,
                    "tcp_ports": tcp_ports,  # Keep for backward compatibility
                    "ssh_port": ssh_port,
                    "username": username,
                }
                
                logging.debug(f"Scan result for {host_ip}: {result}")
                yield result
                
            except Exception as e:
                logging.exception(f"Analysis of host {host_ip} failed: {e}")
                logging.warning(f"Skipping host {host_ip} due to error")
                continue

    def _scan(self):
        logging.info("Begin scaning %s..." % self.host)
        self.nm.scan(hosts=self.host, arguments=self.arg)
        return self.nm.all_hosts()

    def _get_mac(self, addresses):
        if addresses:
            mac = addresses.get("mac")
            if mac:
                mac = mac.lower()
            return mac

    def _get_vendor(self, vendor, mac):
        if vendor and mac:
            return vendor.get(mac)
        return None

    def _get_username(self, osfamily):
        if not osfamily:
            return DEFAULT_USER
        if "linux" in osfamily.lower():
            return DEFAULT_LINUX_USER
        if "windows" in osfamily.lower():
            return DEFAULT_WINDOWS_USER
        return DEFAULT_USER

    def _get_ssh_port(self, osfamily):
        if not osfamily:
            return None
        if "linux" in osfamily.lower():
            return int(DEFAULT_LINUX_PORT)
        if "vmware" in osfamily.lower():
            return int(DEFAULT_VMWARE_PORT)
        return None

    def _get_check_status(self, vendor, osfamily):
        """Get check status (not used in new implementation, kept for compatibility)"""
        if not osfamily:
            return ""
        if vendor and vendor.lower() != "vmware":
            if osfamily.lower() == "linux" \
               or osfamily.lower() == "windows" \
               or osfamily.lower() == "vmware":
                return CHECKSTATUS_CHECK
        return ""

    def _get_os(self, osmatch):
        osfamily = ""
        version = ""

        # If only one match return osfamily and name
        if len(osmatch) == 1:
            first_osclass = osmatch[0]["osclass"][0]
            osfamily = first_osclass.get("osfamily")
            version = osmatch[0].get("name")

        # If the first two osfamily are embedded, maybe the device is
        # switch or router, return the first one, otherwise it's a
        # phhsical machine
        if len(osmatch) > 1:
            first_osclass = osmatch[0]["osclass"][0]
            second_osclass = osmatch[1]["osclass"][0]
            logging.debug("First osclass is %s" % first_osclass)
            logging.debug("Second osclass is %s" % second_osclass)

            first_osfamily = first_osclass.get("osfamily")
            second_osfamily = second_osclass.get("osfamily")
            logging.debug("Compre osfamily first is %s, second is %s."
                          % (first_osfamily, second_osfamily))
            if first_osfamily == "embedded" \
               and second_osfamily == "embedded":
                osfamily = first_osfamily
                version = osmatch[0].get("name")
            elif first_osfamily != "embedded":
                osfamily = first_osfamily
                version = osmatch[0].get("name")
            else:
                osfamily = second_osfamily
                version = osmatch[1].get("name")

        logging.debug("osfamily is %s, version is %s."
                      % (osfamily, version))
        if osfamily == "ESX Server":
            osfamily = "VMware"

        return osfamily, version
