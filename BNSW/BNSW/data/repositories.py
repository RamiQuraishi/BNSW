"""
BNSW Data Repositories
--------------------
This module provides repository classes for database operations.
"""

import logging
import threading
import datetime
import traceback
from typing import Dict, List, Any, Optional, Tuple

from peewee import DatabaseError, IntegrityError, OperationalError, DoesNotExist

from BNSW.data.models import db, Scan, Host, Port, Script

# Set up logger
logger = logging.getLogger('BNSW.data.repositories')

class DatabaseManager:
    """Database manager for coordinating repository operations."""
    
    def __init__(self):
        """Initialize database manager."""
        self.lock = threading.RLock()
        self.scan_repo = ScanRepository(self.lock)
        self.host_repo = HostRepository(self.lock)
        self.port_repo = PortRepository(self.lock)
        self.script_repo = ScriptRepository(self.lock)
    
    def save_scan_result(self, scan_id: str, result: Dict[str, Any]) -> Tuple[bool, Optional[int], str]:
        """
        Save scan result to database.
        
        Args:
            scan_id: Scan ID
            result: Scan result dictionary
            
        Returns:
            Tuple[bool, Optional[int], str]: (success, database_id, error_message)
        """
        with self.lock:
            try:
                # Begin transaction
                with db.atomic():
                    # Create scan record
                    scan_info = result.get('scan_info', {})
                    hosts = result.get('hosts', [])
                    
                    # Create scan
                    scan = Scan.create(
                        target=scan_info.get('target', ''),
                        command=scan_info.get('args', ''),
                        start_time=datetime.datetime.now(),
                        end_time=datetime.datetime.now(),
                        status='completed'
                    )
                    scan.set_metadata(scan_info)
                    scan.save()
                    
                    # Create hosts
                    for host_data in hosts:
                        # Create host
                        host = Host.create(
                            scan=scan,
                            ip=host_data.get('ip', ''),
                            hostname=host_data.get('hostname', None),
                            status=host_data.get('status', 'up'),
                            mac=host_data.get('mac', None),
                            os=host_data.get('os', {}).get('name', None)
                        )
                        host.set_metadata(host_data)
                        host.save()
                        
                        # Create ports
                        for port_data in host_data.get('ports', []):
                            try:
                                port_number = int(port_data.get('portid', 0))
                                port = Port.create(
                                    host=host,
                                    port=port_number,
                                    protocol=port_data.get('protocol', ''),
                                    state=port_data.get('state', ''),
                                    service=port_data.get('service', ''),
                                    version=port_data.get('version', '')
                                )
                                port.set_metadata(port_data)
                                port.save()
                            except (ValueError, TypeError) as e:
                                # Log error but continue with other ports
                                logger.warning(f"Error creating port: {str(e)}")
                                continue
                    
                    return True, scan.id, ""
            
            except IntegrityError as e:
                logger.error(f"Database integrity error: {str(e)}")
                return False, None, f"Database integrity error: {str(e)}"
            
            except OperationalError as e:
                logger.error(f"Database operational error: {str(e)}")
                return False, None, f"Database operational error: {str(e)}"
            
            except DatabaseError as e:
                logger.error(f"Database error: {str(e)}")
                return False, None, f"Database error: {str(e)}"
            
            except Exception as e:
                logger.error(f"Unexpected error saving scan result: {str(e)}")
                logger.debug(traceback.format_exc())
                return False, None, f"Unexpected error: {str(e)}"
    
    def get_scan_with_details(self, scan_id: int) -> Tuple[bool, Dict[str, Any], str]:
        """
        Get scan with all details.
        
        Args:
            scan_id: Database ID of scan
            
        Returns:
            Tuple[bool, Dict[str, Any], str]: (success, scan_details, error_message)
        """
        with self.lock:
            try:
                # Get scan
                scan = Scan.get_by_id(scan_id)
                
                # Build result
                result = scan.to_dict()
                result['hosts'] = []
                
                # Get hosts
                for host in scan.hosts:
                    host_data = host.to_dict()
                    host_data['ports'] = []
                    
                    # Get ports
                    for port in host.ports:
                        port_data = port.to_dict()
                        port_data['scripts'] = []
                        
                        # Get scripts
                        for script in port.scripts:
                            script_data = script.to_dict()
                            port_data['scripts'].append(script_data)
                        
                        host_data['ports'].append(port_data)
                    
                    # Get host scripts
                    host_data['scripts'] = []
                    for script in host.scripts:
                        script_data = script.to_dict()
                        host_data['scripts'].append(script_data)
                    
                    result['hosts'].append(host_data)
                
                return True, result, ""
            
            except DoesNotExist:
                logger.warning(f"Scan with ID {scan_id} does not exist")
                return False, {}, f"Scan with ID {scan_id} does not exist"
            
            except DatabaseError as e:
                logger.error(f"Database error retrieving scan: {str(e)}")
                return False, {}, f"Database error: {str(e)}"
            
            except Exception as e:
                logger.error(f"Unexpected error retrieving scan: {str(e)}")
                logger.debug(traceback.format_exc())
                return False, {}, f"Unexpected error: {str(e)}"

class BaseRepository:
    """Base repository class."""
    
    def __init__(self, lock):
        """
        Initialize repository.
        
        Args:
            lock: Thread lock
        """
        self.lock = lock

class ScanRepository(BaseRepository):
    """Repository for scan operations."""
    
    def create(self, target: str, command: str) -> Tuple[bool, Optional[Scan], str]:
        """
        Create scan.
        
        Args:
            target: Target
            command: Command
            
        Returns:
            Tuple[bool, Optional[Scan], str]: (success, scan, error_message)
        """
        with self.lock:
            try:
                scan = Scan.create(
                    target=target,
                    command=command,
                    start_time=datetime.datetime.now(),
                    status='running'
                )
                return True, scan, ""
            except IntegrityError as e:
                logger.error(f"Database integrity error creating scan: {str(e)}")
                return False, None, f"Database integrity error: {str(e)}"
            except DatabaseError as e:
                logger.error(f"Database error creating scan: {str(e)}")
                return False, None, f"Database error: {str(e)}"
            except Exception as e:
                logger.error(f"Unexpected error creating scan: {str(e)}")
                logger.debug(traceback.format_exc())
                return False, None, f"Unexpected error: {str(e)}"
    
    def update_status(self, scan_id: int, status: str) -> Tuple[bool, str]:
        """
        Update scan status.
        
        Args:
            scan_id: Scan ID
            status: Status
            
        Returns:
            Tuple[bool, str]: (success, error_message)
        """
        with self.lock:
            try:
                scan = Scan.get_by_id(scan_id)
                scan.status = status
                
                if status in ['completed', 'failed', 'cancelled']:
                    scan.end_time = datetime.datetime.now()
                
                scan.save()
                return True, ""
            
            except DoesNotExist:
                logger.warning(f"Scan with ID {scan_id} does not exist")
                return False, f"Scan with ID {scan_id} does not exist"
            
            except DatabaseError as e:
                logger.error(f"Database error updating scan status: {str(e)}")
                return False, f"Database error: {str(e)}"
            
            except Exception as e:
                logger.error(f"Unexpected error updating scan status: {str(e)}")
                logger.debug(traceback.format_exc())
                return False, f"Unexpected error: {str(e)}"
    
    def get_all(self) -> Tuple[bool, List[Scan], str]:
        """
        Get all scans.
        
        Returns:
            Tuple[bool, List[Scan], str]: (success, scans, error_message)
        """
        with self.lock:
            try:
                scans = list(Scan.select().order_by(Scan.start_time.desc()))
                return True, scans, ""
            except DatabaseError as e:
                logger.error(f"Database error retrieving scans: {str(e)}")
                return False, [], f"Database error: {str(e)}"
            except Exception as e:
                logger.error(f"Unexpected error retrieving scans: {str(e)}")
                logger.debug(traceback.format_exc())
                return False, [], f"Unexpected error: {str(e)}"
    
    def get_by_id(self, scan_id: int) -> Tuple[bool, Optional[Scan], str]:
        """
        Get scan by ID.
        
        Args:
            scan_id: Scan ID
            
        Returns:
            Tuple[bool, Optional[Scan], str]: (success, scan, error_message)
        """
        with self.lock:
            try:
                scan = Scan.get_by_id(scan_id)
                return True, scan, ""
            except DoesNotExist:
                logger.warning(f"Scan with ID {scan_id} does not exist")
                return False, None, f"Scan with ID {scan_id} does not exist"
            except DatabaseError as e:
                logger.error(f"Database error retrieving scan: {str(e)}")
                return False, None, f"Database error: {str(e)}"
            except Exception as e:
                logger.error(f"Unexpected error retrieving scan: {str(e)}")
                logger.debug(traceback.format_exc())
                return False, None, f"Unexpected error: {str(e)}"
    
    def delete(self, scan_id: int) -> Tuple[bool, str]:
        """
        Delete scan.
        
        Args:
            scan_id: Scan ID
            
        Returns:
            Tuple[bool, str]: (success, error_message)
        """
        with self.lock:
            try:
                scan = Scan.get_by_id(scan_id)
                scan.delete_instance(recursive=True)
                return True, ""
            
            except DoesNotExist:
                logger.warning(f"Scan with ID {scan_id} does not exist")
                return False, f"Scan with ID {scan_id} does not exist"
            
            except DatabaseError as e:
                logger.error(f"Database error deleting scan: {str(e)}")
                return False, f"Database error: {str(e)}"
            
            except Exception as e:
                logger.error(f"Unexpected error deleting scan: {str(e)}")
                logger.debug(traceback.format_exc())
                return False, f"Unexpected error: {str(e)}"

class HostRepository(BaseRepository):
    """Repository for host operations."""
    
    def create(self, scan_id: int, ip: str, hostname: str = None, status: str = 'up',
               mac: str = None, os: str = None) -> Tuple[bool, Optional[Host], str]:
        """
        Create host.
        
        Args:
            scan_id: Scan ID
            ip: IP address
            hostname: Hostname
            status: Status
            mac: MAC address
            os: Operating system
            
        Returns:
            Tuple[bool, Optional[Host], str]: (success, host, error_message)
        """
        with self.lock:
            try:
                host = Host.create(
                    scan_id=scan_id,
                    ip=ip,
                    hostname=hostname,
                    status=status,
                    mac=mac,
                    os=os
                )
                return True, host, ""
            except IntegrityError as e:
                logger.error(f"Database integrity error creating host: {str(e)}")
                return False, None, f"Database integrity error: {str(e)}"
            except DatabaseError as e:
                logger.error(f"Database error creating host: {str(e)}")
                return False, None, f"Database error: {str(e)}"
            except Exception as e:
                logger.error(f"Unexpected error creating host: {str(e)}")
                logger.debug(traceback.format_exc())
                return False, None, f"Unexpected error: {str(e)}"
    
    def get_by_scan(self, scan_id: int) -> Tuple[bool, List[Host], str]:
        """
        Get hosts by scan ID.
        
        Args:
            scan_id: Scan ID
            
        Returns:
            Tuple[bool, List[Host], str]: (success, hosts, error_message)
        """
        with self.lock:
            try:
                hosts = list(Host.select().where(Host.scan_id == scan_id))
                return True, hosts, ""
            except DatabaseError as e:
                logger.error(f"Database error retrieving hosts: {str(e)}")
                return False, [], f"Database error: {str(e)}"
            except Exception as e:
                logger.error(f"Unexpected error retrieving hosts: {str(e)}")
                logger.debug(traceback.format_exc())
                return False, [], f"Unexpected error: {str(e)}"
    
    def get_by_id(self, host_id: int) -> Tuple[bool, Optional[Host], str]:
        """
        Get host by ID.
        
        Args:
            host_id: Host ID
            
        Returns:
            Tuple[bool, Optional[Host], str]: (success, host, error_message)
        """
        with self.lock:
            try:
                host = Host.get_by_id(host_id)
                return True, host, ""
            except DoesNotExist:
                logger.warning(f"Host with ID {host_id} does not exist")
                return False, None, f"Host with ID {host_id} does not exist"
            except DatabaseError as e:
                logger.error(f"Database error retrieving host: {str(e)}")
                return False, None, f"Database error: {str(e)}"
            except Exception as e:
                logger.error(f"Unexpected error retrieving host: {str(e)}")
                logger.debug(traceback.format_exc())
                return False, None, f"Unexpected error: {str(e)}"

class PortRepository(BaseRepository):
    """Repository for port operations."""
    
    def create(self, host_id: int, port: int, protocol: str, state: str,
               service: str = None, version: str = None) -> Tuple[bool, Optional[Port], str]:
        """
        Create port.
        
        Args:
            host_id: Host ID
            port: Port number
            protocol: Protocol
            state: State
            service: Service
            version: Version
            
        Returns:
            Tuple[bool, Optional[Port], str]: (success, port, error_message)
        """
        with self.lock:
            try:
                port_obj = Port.create(
                    host_id=host_id,
                    port=port,
                    protocol=protocol,
                    state=state,
                    service=service,
                    version=version
                )
                return True, port_obj, ""
            except IntegrityError as e:
                logger.error(f"Database integrity error creating port: {str(e)}")
                return False, None, f"Database integrity error: {str(e)}"
            except DatabaseError as e:
                logger.error(f"Database error creating port: {str(e)}")
                return False, None, f"Database error: {str(e)}"
            except Exception as e:
                logger.error(f"Unexpected error creating port: {str(e)}")
                logger.debug(traceback.format_exc())
                return False, None, f"Unexpected error: {str(e)}"
    
    def get_by_host(self, host_id: int) -> Tuple[bool, List[Port], str]:
        """
        Get ports by host ID.
        
        Args:
            host_id: Host ID
            
        Returns:
            Tuple[bool, List[Port], str]: (success, ports, error_message)
        """
        with self.lock:
            try:
                ports = list(Port.select().where(Port.host_id == host_id))
                return True, ports, ""
            except DatabaseError as e:
                logger.error(f"Database error retrieving ports: {str(e)}")
                return False, [], f"Database error: {str(e)}"
            except Exception as e:
                logger.error(f"Unexpected error retrieving ports: {str(e)}")
                logger.debug(traceback.format_exc())
                return False, [], f"Unexpected error: {str(e)}"
    
    def get_by_id(self, port_id: int) -> Tuple[bool, Optional[Port], str]:
        """
        Get port by ID.
        
        Args:
            port_id: Port ID
            
        Returns:
            Tuple[bool, Optional[Port], str]: (success, port, error_message)
        """
        with self.lock:
            try:
                port = Port.get_by_id(port_id)
                return True, port, ""
            except DoesNotExist:
                logger.warning(f"Port with ID {port_id} does not exist")
                return False, None, f"Port with ID {port_id} does not exist"
            except DatabaseError as e:
                logger.error(f"Database error retrieving port: {str(e)}")
                return False, None, f"Database error: {str(e)}"
            except Exception as e:
                logger.error(f"Unexpected error retrieving port: {str(e)}")
                logger.debug(traceback.format_exc())
                return False, None, f"Unexpected error: {str(e)}"

class ScriptRepository(BaseRepository):
    """Repository for script operations."""
    
    def create(self, name: str, output: str, port_id: int = None, host_id: int = None) -> Tuple[bool, Optional[Script], str]:
        """
        Create script.
        
        Args:
            name: Script name
            output: Script output
            port_id: Port ID
            host_id: Host ID
            
        Returns:
            Tuple[bool, Optional[Script], str]: (success, script, error_message)
        """
        with self.lock:
            try:
                script = Script.create(
                    name=name,
                    output=output,
                    port_id=port_id,
                    host_id=host_id
                )
                return True, script, ""
            except IntegrityError as e:
                logger.error(f"Database integrity error creating script: {str(e)}")
                return False, None, f"Database integrity error: {str(e)}"
            except DatabaseError as e:
                logger.error(f"Database error creating script: {str(e)}")
                return False, None, f"Database error: {str(e)}"
            except Exception as e:
                logger.error(f"Unexpected error creating script: {str(e)}")
                logger.debug(traceback.format_exc())
                return False, None, f"Unexpected error: {str(e)}"
    
    def get_by_port(self, port_id: int) -> Tuple[bool, List[Script], str]:
        """
        Get scripts by port ID.
        
        Args:
            port_id: Port ID
            
        Returns:
            Tuple[bool, List[Script], str]: (success, scripts, error_message)
        """
        with self.lock:
            try:
                scripts = list(Script.select().where(Script.port_id == port_id))
                return True, scripts, ""
            except DatabaseError as e:
                logger.error(f"Database error retrieving scripts: {str(e)}")
                return False, [], f"Database error: {str(e)}"
            except Exception as e:
                logger.error(f"Unexpected error retrieving scripts: {str(e)}")
                logger.debug(traceback.format_exc())
                return False, [], f"Unexpected error: {str(e)}"
    
    def get_by_host(self, host_id: int) -> Tuple[bool, List[Script], str]:
        """
        Get scripts by host ID.
        
        Args:
            host_id: Host ID
            
        Returns:
            Tuple[bool, List[Script], str]: (success, scripts, error_message)
        """
        with self.lock:
            try:
                scripts = list(Script.select().where(Script.host_id == host_id))
                return True, scripts, ""
            except DatabaseError as e:
                logger.error(f"Database error retrieving scripts: {str(e)}")
                return False, [], f"Database error: {str(e)}"
            except Exception as e:
                logger.error(f"Unexpected error retrieving scripts: {str(e)}")
                logger.debug(traceback.format_exc())
                return False, [], f"Unexpected error: {str(e)}"
    
    def get_by_id(self, script_id: int) -> Tuple[bool, Optional[Script], str]:
        """
        Get script by ID.
        
        Args:
            script_id: Script ID
            
        Returns:
            Tuple[bool, Optional[Script], str]: (success, script, error_message)
        """
        with self.lock:
            try:
                script = Script.get_by_id(script_id)
                return True, script, ""
            except DoesNotExist:
                logger.warning(f"Script with ID {script_id} does not exist")
                return False, None, f"Script with ID {script_id} does not exist"
            except DatabaseError as e:
                logger.error(f"Database error retrieving script: {str(e)}")
                return False, None, f"Database error: {str(e)}"
            except Exception as e:
                logger.error(f"Unexpected error retrieving script: {str(e)}")
                logger.debug(traceback.format_exc())
                return False, None, f"Unexpected error: {str(e)}"
