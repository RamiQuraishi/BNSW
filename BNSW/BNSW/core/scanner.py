"""
BNSW Core Scanner Module
--------------------
This module provides the core scanning functionality for the BNSW application.
It handles Nmap scanning operations with thread safety and progress monitoring.

Classes:
    Scanner: Main class for Nmap scanning operations
"""

import os
import re
import sys
import time
import uuid
import shlex
import tempfile
import threading
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List, Any, Callable, Optional, Tuple

class Scanner:
    """Thread-safe Nmap scanner with progress updates."""
    
    def __init__(self, max_concurrent_scans=3):
        """
        Initialize scanner with concurrency limit.
        
        Args:
            max_concurrent_scans: Maximum number of concurrent scans
        """
        self.scan_semaphore = threading.Semaphore(max_concurrent_scans)
        self.running_scans = {}
        self.scan_lock = threading.Lock()
    
    def scan(self, target: str, arguments: str = "-sV", callback: Callable = None) -> str:
        """
        Perform Nmap scan with progress updates.
        
        Args:
            target: Target to scan
            arguments: Nmap arguments
            callback: Progress callback function
            
        Returns:
            str: Scan ID
        """
        # Validate target
        if not self._validate_target(target):
            raise ValueError(f"Invalid target: {target}")
        
        # Sanitize arguments
        safe_args = self._sanitize_arguments(arguments)
        
        # Generate scan ID
        scan_id = str(uuid.uuid4())
        
        # Start scan thread
        scan_thread = threading.Thread(
            target=self._scan_thread,
            args=(scan_id, target, safe_args, callback)
        )
        scan_thread.daemon = True
        scan_thread.start()
        
        return scan_id
    
    def get_scan_status(self, scan_id: str) -> Dict[str, Any]:
        """
        Get scan status.
        
        Args:
            scan_id: Scan ID
            
        Returns:
            Dict[str, Any]: Scan status dictionary
        """
        with self.scan_lock:
            return self.running_scans.get(scan_id, {}).copy()
    
    def get_all_scans(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all scans.
        
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of scan ID to scan status
        """
        with self.scan_lock:
            return self.running_scans.copy()
    
    def cancel_scan(self, scan_id: str) -> bool:
        """
        Cancel scan.
        
        Args:
            scan_id: Scan ID
            
        Returns:
            bool: True if scan was cancelled, False otherwise
        """
        with self.scan_lock:
            if scan_id not in self.running_scans:
                return False
            
            scan_info = self.running_scans[scan_id]
            if scan_info.get('process') and scan_info.get('status') == 'running':
                try:
                    scan_info['process'].terminate()
                    scan_info['status'] = 'cancelled'
                    return True
                except:
                    return False
            
            return False
    
    def _scan_thread(self, scan_id: str, target: str, arguments: str, callback: Callable):
        """
        Scan thread function.
        
        Args:
            scan_id: Scan ID
            target: Target to scan
            arguments: Nmap arguments
            callback: Progress callback function
        """
        # Acquire semaphore
        self.scan_semaphore.acquire()
        
        try:
            # Register scan
            with self.scan_lock:
                self.running_scans[scan_id] = {
                    'target': target,
                    'arguments': arguments,
                    'start_time': datetime.now(),
                    'progress': 0,
                    'status': 'running',
                    'process': None,
                    'output': None,
                    'result': None,
                    'error_message': None
                }
            
            # Create temporary files
            output_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xml')
            output_file.close()
            
            # Check if admin privileges are needed
            needs_admin = self._needs_admin_privileges(arguments)
            
            # Update scan info with privilege requirement
            with self.scan_lock:
                self.running_scans[scan_id]['needs_admin'] = needs_admin
            
            # Build command
            cmd = f"nmap {arguments} -oX {output_file.name} {target}"
            
            # Start process
            process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Update process in scan info
            with self.scan_lock:
                self.running_scans[scan_id]['process'] = process
            
            # Monitor progress
            while process.poll() is None:
                # Read output
                line = process.stdout.readline()
                
                # Update progress
                progress = self._parse_progress(line)
                if progress is not None:
                    with self.scan_lock:
                        self.running_scans[scan_id]['progress'] = progress
                    
                    # Call callback
                    if callback:
                        callback(scan_id, progress)
                
                # Sleep to reduce CPU usage
                time.sleep(0.1)
            
            # Process completed
            return_code = process.wait()
            stderr_output = process.stderr.read()
            
            # Check for permission errors
            permission_error = False
            error_message = None
            if return_code != 0:
                if "requires root privileges" in stderr_output or "requires privileged access" in stderr_output:
                    permission_error = True
                    error_message = "This scan type requires administrator privileges. Please run the application as administrator."
                else:
                    error_message = f"Scan failed with error code {return_code}: {stderr_output}"
            
            # Read output file
            try:
                with open(output_file.name, 'r') as f:
                    output = f.read()
                
                # Parse XML output
                if return_code == 0:
                    try:
                        # Parse XML directly
                        result = self._parse_nmap_xml(output)
                    except Exception as e:
                        print(f"Error parsing XML: {str(e)}")
                        result = None
                        error_message = f"Error parsing scan results: {str(e)}"
                else:
                    result = None
            except Exception as e:
                print(f"Error reading output file: {str(e)}")
                output = None
                result = None
                error_message = f"Error reading scan results: {str(e)}"
            
            # Update scan status
            with self.scan_lock:
                self.running_scans[scan_id]['end_time'] = datetime.now()
                if permission_error:
                    self.running_scans[scan_id]['status'] = 'permission_denied'
                else:
                    self.running_scans[scan_id]['status'] = 'completed' if return_code == 0 else 'failed'
                self.running_scans[scan_id]['output'] = output
                self.running_scans[scan_id]['result'] = result
                self.running_scans[scan_id]['return_code'] = return_code
                self.running_scans[scan_id]['error_message'] = error_message
            
            # Call callback with final progress
            if callback:
                if permission_error:
                    callback(scan_id, -2)  # Special code for permission denied
                else:
                    callback(scan_id, 100 if return_code == 0 else -1)
            
            # Clean up
            try:
                os.unlink(output_file.name)
            except:
                pass
        
        finally:
            # Release semaphore
            self.scan_semaphore.release()
    
    def _parse_nmap_xml(self, xml_content):
        """
        Parse Nmap XML output directly.
        
        Args:
            xml_content: XML content to parse
            
        Returns:
            Dict: Parsed data
        """
        try:
            # Parse XML
            root = ET.fromstring(xml_content)
            
            # Extract scan info
            scan_info = {}
            for attr, value in root.attrib.items():
                scan_info[attr] = value
            
            # Extract hosts
            hosts = []
            host_nodes = root.findall('.//host')
            
            for host_node in host_nodes:
                host = {}
                
                # Extract status
                status_node = host_node.find('status')
                if status_node is not None:
                    host['status'] = status_node.get('state', '')
                
                # Extract addresses
                host['addresses'] = []
                address_nodes = host_node.findall('address')
                for address_node in address_nodes:
                    addr_type = address_node.get('addrtype', '')
                    addr = address_node.get('addr', '')
                    
                    if addr_type == 'ipv4':
                        host['ip'] = addr
                    elif addr_type == 'mac':
                        host['mac'] = addr
                    
                    host['addresses'].append({
                        'type': addr_type,
                        'addr': addr
                    })
                
                # Extract hostnames
                host['hostnames'] = []
                hostnames_node = host_node.find('hostnames')
                if hostnames_node is not None:
                    hostname_nodes = hostnames_node.findall('hostname')
                    for hostname_node in hostname_nodes:
                        hostname = hostname_node.get('name', '')
                        hostname_type = hostname_node.get('type', '')
                        
                        if hostname_type == 'user':
                            host['hostname'] = hostname
                        
                        host['hostnames'].append({
                            'name': hostname,
                            'type': hostname_type
                        })
                
                # Extract ports
                host['ports'] = []
                ports_node = host_node.find('ports')
                if ports_node is not None:
                    port_nodes = ports_node.findall('port')
                    for port_node in port_nodes:
                        port = {}
                        port['protocol'] = port_node.get('protocol', '')
                        port['portid'] = port_node.get('portid', '')
                        
                        # Extract state
                        state_node = port_node.find('state')
                        if state_node is not None:
                            port['state'] = state_node.get('state', '')
                            port['reason'] = state_node.get('reason', '')
                        
                        # Extract service
                        service_node = port_node.find('service')
                        if service_node is not None:
                            port['service'] = service_node.get('name', '')
                            port['product'] = service_node.get('product', '')
                            port['version'] = service_node.get('version', '')
                            
                            # Create a combined version string for display
                            version_info = []
                            if port['product']:
                                version_info.append(port['product'])
                            if port['version']:
                                version_info.append(port['version'])
                            
                            port['version_info'] = ' '.join(version_info)
                            
                            # Extract additional service info
                            for attr in ['extrainfo', 'ostype', 'devicetype', 'servicefp']:
                                value = service_node.get(attr, '')
                                if value:
                                    port[attr] = value
                        
                        # Extract scripts
                        script_nodes = port_node.findall('script')
                        if script_nodes:
                            port['scripts'] = []
                            for script_node in script_nodes:
                                script = {
                                    'id': script_node.get('id', ''),
                                    'output': script_node.get('output', '')
                                }
                                port['scripts'].append(script)
                        
                        host['ports'].append(port)
                
                # Extract OS
                host['os'] = {}
                os_node = host_node.find('os')
                if os_node is not None:
                    # Extract OS matches
                    osmatch_nodes = os_node.findall('osmatch')
                    if osmatch_nodes:
                        host['os_matches'] = []
                        for osmatch_node in osmatch_nodes:
                            osmatch = {
                                'name': osmatch_node.get('name', ''),
                                'accuracy': osmatch_node.get('accuracy', ''),
                                'line': osmatch_node.get('line', '')
                            }
                            
                            # Extract OS class
                            osclass_nodes = osmatch_node.findall('osclass')
                            if osclass_nodes:
                                osmatch['classes'] = []
                                for osclass_node in osclass_nodes:
                                    osclass = {
                                        'type': osclass_node.get('type', ''),
                                        'vendor': osclass_node.get('vendor', ''),
                                        'osfamily': osclass_node.get('osfamily', ''),
                                        'osgen': osclass_node.get('osgen', ''),
                                        'accuracy': osclass_node.get('accuracy', '')
                                    }
                                    osmatch['classes'].append(osclass)
                            
                            host['os_matches'].append(osmatch)
                        
                        # Use the best match for the main OS info
                        best_match = osmatch_nodes[0]
                        host['os'] = {
                            'name': best_match.get('name', ''),
                            'accuracy': best_match.get('accuracy', '')
                        }
                
                # Extract uptime
                uptime_node = host_node.find('uptime')
                if uptime_node is not None:
                    host['uptime'] = {
                        'seconds': uptime_node.get('seconds', ''),
                        'lastboot': uptime_node.get('lastboot', '')
                    }
                
                # Extract distance
                distance_node = host_node.find('distance')
                if distance_node is not None:
                    host['distance'] = {
                        'value': distance_node.get('value', '')
                    }
                
                # Extract trace
                trace_node = host_node.find('trace')
                if trace_node is not None:
                    host['trace'] = {
                        'proto': trace_node.get('proto', ''),
                        'port': trace_node.get('port', ''),
                        'hops': []
                    }
                    
                    hop_nodes = trace_node.findall('hop')
                    for hop_node in hop_nodes:
                        hop = {
                            'ttl': hop_node.get('ttl', ''),
                            'ipaddr': hop_node.get('ipaddr', ''),
                            'host': hop_node.get('host', ''),
                            'rtt': hop_node.get('rtt', '')
                        }
                        host['trace']['hops'].append(hop)
                
                hosts.append(host)
            
            # Extract runstats
            runstats_node = root.find('runstats')
            if runstats_node is not None:
                scan_info['runstats'] = {}
                
                # Extract finished info
                finished_node = runstats_node.find('finished')
                if finished_node is not None:
                    scan_info['runstats']['finished'] = {
                        'time': finished_node.get('time', ''),
                        'timestr': finished_node.get('timestr', ''),
                        'elapsed': finished_node.get('elapsed', ''),
                        'summary': finished_node.get('summary', '')
                    }
                
                # Extract hosts info
                hosts_node = runstats_node.find('hosts')
                if hosts_node is not None:
                    scan_info['runstats']['hosts'] = {
                        'up': hosts_node.get('up', ''),
                        'down': hosts_node.get('down', ''),
                        'total': hosts_node.get('total', '')
                    }
            
            return {
                'scan_info': scan_info,
                'hosts': hosts
            }
        
        except Exception as e:
            print(f"Error parsing XML: {str(e)}")
            return {
                'error': str(e),
                'scan_info': {},
                'hosts': []
            }
    
    def _validate_target(self, target: str) -> bool:
        """
        Validate target.
        
        Args:
            target: Target to validate
            
        Returns:
            bool: True if target is valid, False otherwise
        """
        # IP address
        ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if re.match(ip_pattern, target):
            # Check each octet is in range 0-255
            octets = target.split('.')
            if all(0 <= int(octet) <= 255 for octet in octets):
                return True
            return False
        
        # CIDR notation
        cidr_pattern = r'^(\d{1,3}\.){3}\d{1,3}/\d{1,2}$'
        if re.match(cidr_pattern, target):
            # Split into IP and prefix
            ip, prefix = target.split('/')
            
            # Validate IP
            octets = ip.split('.')
            if not all(0 <= int(octet) <= 255 for octet in octets):
                return False
            
            # Validate prefix
            try:
                prefix_int = int(prefix)
                if 0 <= prefix_int <= 32:
                    return True
            except ValueError:
                pass
            
            return False
        
        # IP range
        ip_range_pattern = r'^(\d{1,3}\.){3}\d{1,3}-(\d{1,3}\.){3}\d{1,3}$'
        if re.match(ip_range_pattern, target):
            # Split into start and end IPs
            start_ip, end_ip = target.split('-')
            
            # Validate start IP
            start_octets = start_ip.split('.')
            if not all(0 <= int(octet) <= 255 for octet in start_octets):
                return False
            
            # Validate end IP
            end_octets = end_ip.split('.')
            if not all(0 <= int(octet) <= 255 for octet in end_octets):
                return False
            
            return True
        
        # Hostname
        hostname_pattern = r'^[a-zA-Z0-9][-a-zA-Z0-9.]*[a-zA-Z0-9]$'
        if re.match(hostname_pattern, target):
            return True
        
        return False
    
    def _sanitize_arguments(self, arguments: str) -> str:
        """
        Sanitize Nmap arguments.
        
        Args:
            arguments: Nmap arguments
            
        Returns:
            str: Sanitized arguments
        """
        # Split arguments
        args = shlex.split(arguments)
        
        # Sanitize each argument
        sanitized = [shlex.quote(arg) for arg in args]
        
        # Join arguments
        return ' '.join(sanitized)
    
    def _parse_progress(self, line: str) -> Optional[float]:
        """
        Parse progress from Nmap output.
        
        Args:
            line: Nmap output line
            
        Returns:
            Optional[float]: Progress percentage, or None if not found
        """
        # Match progress line
        match = re.search(r'About (\d+\.\d+)% done', line)
        if match:
            return float(match.group(1))
        
        return None
    
    def _needs_admin_privileges(self, arguments: str) -> bool:
        """
        Check if scan needs admin privileges.
        
        Args:
            arguments: Nmap arguments
            
        Returns:
            bool: True if admin privileges are needed, False otherwise
        """
        # Check for OS detection
        if '-O' in arguments or '--osscan-guess' in arguments:
            return True
        
        # Check for SYN scan
        if '-sS' in arguments:
            return True
        
        # Check for comprehensive scan (which typically includes OS detection)
        if '-A' in arguments:
            return True
        
        return False
    
    def get_scan_profiles(self) -> Dict[str, str]:
        """
        Get predefined scan profiles.
        
        Returns:
            Dict[str, str]: Dictionary of profile name to Nmap arguments
        """
        return {
            "Quick": "-T4 -F",
            "Full": "-T4 -p-",
            "Ping": "-sn",
            "Service": "-sV",
            "OS Detection": "-O",
            "Comprehensive": "-T4 -A -v -PE -PP -PS80,443 -PA3389 -PU40125 -PY -g 53"
        }
    
    def check_nmap_installation(self) -> Tuple[bool, str]:
        """
        Check if Nmap is installed.
        
        Returns:
            Tuple[bool, str]: (is_installed, version_string)
        """
        try:
            # Run nmap version command
            process = subprocess.Popen(
                ["nmap", "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Get output
            stdout, stderr = process.communicate()
            
            # Check if successful
            if process.returncode == 0 and stdout:
                # Extract version
                match = re.search(r'Nmap version (\S+)', stdout)
                if match:
                    return True, match.group(1)
                return True, "Unknown version"
            
            return False, ""
        
        except:
            return False, ""
