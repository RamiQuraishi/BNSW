"""
BNSW Core Scanner Manager
---------------------
This module provides a high-level interface for managing scanning operations.
It integrates the scanner and parser components.
"""

import os
import threading
import logging
import ctypes
import sys
from typing import Dict, List, Any, Callable, Optional, Tuple

from BNSW.core.scanner import Scanner

logger = logging.getLogger('BNSW.core.scanner_manager')

class ScannerManager:
    """High-level manager for scanning operations."""
    
    def __init__(self, max_concurrent_scans=3):
        """
        Initialize scanner manager.
        
        Args:
            max_concurrent_scans: Maximum number of concurrent scans
        """
        self.scanner = Scanner(max_concurrent_scans=max_concurrent_scans)
        self.scan_callbacks = {}
        self.scan_results = {}
        self.lock = threading.Lock()

    def check_admin_privileges(self):
        """
        Check if the script is running with administrative privileges (Windows).
        """
        if sys.platform == 'win32':
            try:
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            except Exception:
                return False
        else:
            # On Unix-like systems, check for root
            return os.geteuid() == 0
    
    def start_scan(self, target: str, profile: str = "Quick", callback: Callable = None) -> str:
        """
        Start a scan with a predefined profile.
        
        Args:
            target: Target to scan
            profile: Scan profile name
            callback: Callback function for scan completion
            
        Returns:
            str: Scan ID
        """
        # Get profile arguments
        profiles = self.scanner.get_scan_profiles()
        arguments = profiles.get(profile, "-T4 -F")
        
        # Register callback
        def on_scan_complete(scan_id, progress):
            if progress == 100:
                # Scan completed successfully
                self._process_scan_result(scan_id)
                
                # Call user callback
                if callback:
                    callback(scan_id, 100)
            elif progress == -1:
                # Scan failed
                if callback:
                    callback(scan_id, -1)
            elif progress == -2:
                # Permission denied
                if callback:
                    callback(scan_id, -2)
        
        # Start scan
        scan_id = self.scanner.scan(target, arguments, on_scan_complete)
        
        # Store callback
        with self.lock:
            self.scan_callbacks[scan_id] = callback
        
        return scan_id
    
    def get_scan_status(self, scan_id: str) -> Dict[str, Any]:
        """
        Get scan status.
        
        Args:
            scan_id: Scan ID
            
        Returns:
            Dict[str, Any]: Scan status
        """
        return self.scanner.get_scan_status(scan_id)
    
    def get_scan_result(self, scan_id: str) -> Dict[str, Any]:
        """
        Get scan result.
        
        Args:
            scan_id: Scan ID
            
        Returns:
            Dict[str, Any]: Scan result
        """
        with self.lock:
            return self.scan_results.get(scan_id, {})
    
    def cancel_scan(self, scan_id: str) -> bool:
        """
        Cancel scan.
        
        Args:
            scan_id: Scan ID
            
        Returns:
            bool: True if scan was cancelled, False otherwise
        """
        return self.scanner.cancel_scan(scan_id)
    
    def get_all_scans(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all scans.
        
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of scan ID to scan status
        """
        return self.scanner.get_all_scans()
    
    def check_nmap_installation(self) -> Tuple[bool, str]:
        """
        Check if Nmap is installed.
        
        Returns:
            Tuple[bool, str]: (is_installed, version_string)
        """
        return self.scanner.check_nmap_installation()
    
    def get_scan_profiles(self) -> Dict[str, str]:
        """
        Get predefined scan profiles.
        
        Returns:
            Dict[str, str]: Dictionary of profile name to Nmap arguments
        """
        return self.scanner.get_scan_profiles()
    
    def _process_scan_result(self, scan_id: str) -> None:
        """
        Process scan result.
        
        Args:
            scan_id: Scan ID
        """
        try:
            # Get scan status
            scan_status = self.scanner.get_scan_status(scan_id)
            
            # Check if scan completed successfully
            if scan_status.get('status') != 'completed':
                return
            
            # Get result directly from scan status
            result = scan_status.get('result')
            
            # Store result
            with self.lock:
                self.scan_results[scan_id] = result
        
        except Exception as e:
            logger.exception(f"Error processing scan result: {str(e)}")
