"""
BNSW Core Scheduler
---------------------
This module provides a scheduler for running scans at specified times.
"""

import os
import time
import json
import logging
import threading
import datetime
from typing import Dict, List, Any, Optional

from BNSW.core.scanner_manager import ScannerManager
from BNSW.data.repositories import DatabaseManager
from BNSW.data.models import ScheduledScan

# Set up logger
logger = logging.getLogger('BNSW.core.scheduler')

class Scheduler:
    """Scheduler for running scans at specified times."""
    
    def __init__(self, check_interval=60):
        """
        Initialize scheduler.
        
        Args:
            check_interval: Interval in seconds to check for scheduled scans
        """
        self.check_interval = check_interval
        self.scanner_manager = ScannerManager()
        self.db_manager = DatabaseManager()
        self.running = False
        self.thread = None
        self.lock = threading.RLock()
        self.active_scans = {}
    
    def start(self):
        """Start scheduler."""
        with self.lock:
            if self.running:
                return
            
            self.running = True
            self.thread = threading.Thread(target=self._scheduler_loop, daemon=True)
            self.thread.start()
            logger.info("Scheduler started")
    
    def stop(self):
        """Stop scheduler."""
        with self.lock:
            if not self.running:
                return
            
            self.running = False
            if self.thread:
                self.thread.join(timeout=5)
                self.thread = None
            logger.info("Scheduler stopped")
    
    def _scheduler_loop(self):
        """Scheduler loop."""
        while self.running:
            try:
                # Check for scheduled scans
                self._check_scheduled_scans()
                
                # Sleep for check interval
                time.sleep(self.check_interval)
            
            except Exception as e:
                logger.exception(f"Error in scheduler loop: {str(e)}")
                # Sleep for a bit to avoid tight loop in case of persistent error
                time.sleep(5)
    
    def _check_scheduled_scans(self):
        """Check for scheduled scans."""
        try:
            # Get current time
            now = datetime.datetime.now()
            
            # Get all scheduled scans
            scheduled_scans = self._get_scheduled_scans()
            
            # Check each scheduled scan
            for scan in scheduled_scans:
                # Skip if already running
                if scan.status == 'running':
                    continue
                
                # Calculate next run if not set
                if not scan.next_run:
                    next_run = scan.calculate_next_run()
                    if next_run:
                        scan.next_run = next_run
                        scan.save()
                    continue
                
                # Check if it's time to run
                if scan.next_run and scan.next_run <= now:
                    # Run scan
                    self._run_scheduled_scan(scan)
                    
                    # Update last run and next run
                    scan.last_run = now
                    scan.next_run = scan.calculate_next_run()
                    scan.save()
        
        except Exception as e:
            logger.exception(f"Error checking scheduled scans: {str(e)}")
    
    def _get_scheduled_scans(self):
        """
        Get all scheduled scans.
        
        Returns:
            List[ScheduledScan]: List of scheduled scans
        """
        try:
            # Get all scheduled scans
            return list(ScheduledScan.select().where(
                (ScheduledScan.status == 'pending') | 
                (ScheduledScan.status == 'running')
            ))
        
        except Exception as e:
            logger.exception(f"Error getting scheduled scans: {str(e)}")
            return []
    
    def _run_scheduled_scan(self, scheduled_scan):
        """
        Run scheduled scan.
        
        Args:
            scheduled_scan: Scheduled scan
        """
        try:
            # Update status
            scheduled_scan.status = 'running'
            scheduled_scan.save()
            
            # Get scan parameters
            target = scheduled_scan.target
            profile = scheduled_scan.profile
            
            # Start scan
            scan_id = self.scanner_manager.start_scan(
                target,
                profile,
                lambda sid, progress: self._on_scan_progress(scheduled_scan.id, sid, progress)
            )
            
            # Store scan ID
            with self.lock:
                self.active_scans[scheduled_scan.id] = scan_id
            
            logger.info(f"Started scheduled scan {scheduled_scan.id} with scan ID {scan_id}")
        
        except Exception as e:
            logger.exception(f"Error running scheduled scan {scheduled_scan.id}: {str(e)}")
            
            # Update status
            scheduled_scan.status = 'error'
            scheduled_scan.save()
    
    def _on_scan_progress(self, scheduled_scan_id, scan_id, progress):
        """
        Handle scan progress.
        
        Args:
            scheduled_scan_id: Scheduled scan ID
            scan_id: Scan ID
            progress: Progress percentage (0-100), or -1 for error, -2 for permission denied
        """
        try:
            # Check if scan is complete
            if progress == 100 or progress < 0:
                # Get scheduled scan
                try:
                    scheduled_scan = ScheduledScan.get_by_id(scheduled_scan_id)
                except Exception:
                    logger.warning(f"Scheduled scan {scheduled_scan_id} not found")
                    return
                
                # Get scan result
                result = self.scanner_manager.get_scan_result(scan_id)
                
                # Save result
                if progress == 100 and result:
                    try:
                        success, db_id, error = self.db_manager.save_scan_result(scan_id, result)
                        if not success:
                            logger.error(f"Error saving scan result: {error}")
                    except Exception as e:
                        logger.exception(f"Error saving scan result: {str(e)}")
                
                # Update status
                if progress == 100:
                    scheduled_scan.status = 'completed'
                else:
                    scheduled_scan.status = 'error'
                
                scheduled_scan.save()
                
                # Remove from active scans
                with self.lock:
                    self.active_scans.pop(scheduled_scan_id, None)
                
                logger.info(f"Scheduled scan {scheduled_scan_id} completed with status {scheduled_scan.status}")
        
        except Exception as e:
            logger.exception(f"Error handling scan progress: {str(e)}")
    
    def schedule_scan(self, schedule_data):
        """
        Schedule a scan.
        
        Args:
            schedule_data: Schedule data dictionary
            
        Returns:
            Tuple[bool, Optional[int], str]: (success, scheduled_scan_id, error_message)
        """
        try:
            # Create scheduled scan
            scheduled_scan = ScheduledScan.create(
                target=schedule_data.get('target', ''),
                profile=schedule_data.get('profile', ''),
                schedule_type=schedule_data.get('type', 'one_time')
            )
            
            # Set type-specific fields
            if schedule_data.get('type') == 'one_time':
                # One-time schedule
                scheduled_time = datetime.datetime.fromisoformat(schedule_data.get('scheduled_time'))
                scheduled_scan.scheduled_time = scheduled_time
                scheduled_scan.next_run = scheduled_time
            else:
                # Recurring schedule
                scheduled_scan.interval_type = schedule_data.get('interval_type')
                scheduled_scan.interval_value = schedule_data.get('interval_value')
                scheduled_scan.start_time = datetime.datetime.fromisoformat(schedule_data.get('start_time'))
                scheduled_scan.end_time = datetime.datetime.fromisoformat(schedule_data.get('end_time'))
                scheduled_scan.next_run = scheduled_scan.calculate_next_run()
            
            # Save metadata
            scheduled_scan.set_metadata(schedule_data)
            
            # Save scheduled scan
            scheduled_scan.save()
            
            # Ensure scheduler is running
            self.start()
            
            return True, scheduled_scan.id, ""
        
        except Exception as e:
            logger.exception(f"Error scheduling scan: {str(e)}")
            return False, None, f"Error scheduling scan: {str(e)}"
    
    def get_scheduled_scans(self):
        """
        Get all scheduled scans.
        
        Returns:
            Tuple[bool, List[Dict], str]: (success, scheduled_scans, error_message)
        """
        try:
            # Get all scheduled scans
            scheduled_scans = list(ScheduledScan.select().order_by(ScheduledScan.created_at.desc()))
            
            # Convert to dictionaries
            result = []
            for scan in scheduled_scans:
                scan_dict = scan.to_dict()
                scan_dict['metadata'] = scan.get_metadata()
                result.append(scan_dict)
            
            return True, result, ""
        
        except Exception as e:
            logger.exception(f"Error getting scheduled scans: {str(e)}")
            return False, [], f"Error getting scheduled scans: {str(e)}"
    
    def cancel_scheduled_scan(self, scheduled_scan_id):
        """
        Cancel scheduled scan.
        
        Args:
            scheduled_scan_id: Scheduled scan ID
            
        Returns:
            Tuple[bool, str]: (success, error_message)
        """
        try:
            # Get scheduled scan
            scheduled_scan = ScheduledScan.get_by_id(scheduled_scan_id)
            
            # Check if already completed or cancelled
            if scheduled_scan.status in ['completed', 'cancelled', 'error']:
                return False, f"Scheduled scan already {scheduled_scan.status}"
            
            # Cancel active scan if running
            with self.lock:
                scan_id = self.active_scans.get(scheduled_scan_id)
                if scan_id:
                    self.scanner_manager.cancel_scan(scan_id)
                    self.active_scans.pop(scheduled_scan_id, None)
            
            # Update status
            scheduled_scan.status = 'cancelled'
            scheduled_scan.save()
            
            return True, ""
        
        except ScheduledScan.DoesNotExist:
            logger.warning(f"Scheduled scan {scheduled_scan_id} not found")
            return False, f"Scheduled scan {scheduled_scan_id} not found"
        
        except Exception as e:
            logger.exception(f"Error cancelling scheduled scan: {str(e)}")
            return False, f"Error cancelling scheduled scan: {str(e)}"
    
    def delete_scheduled_scan(self, scheduled_scan_id):
        """
        Delete scheduled scan.
        
        Args:
            scheduled_scan_id: Scheduled scan ID
            
        Returns:
            Tuple[bool, str]: (success, error_message)
        """
        try:
            # Get scheduled scan
            scheduled_scan = ScheduledScan.get_by_id(scheduled_scan_id)
            
            # Cancel if running
            if scheduled_scan.status == 'running':
                self.cancel_scheduled_scan(scheduled_scan_id)
            
            # Delete scheduled scan
            scheduled_scan.delete_instance()
            
            return True, ""
        
        except ScheduledScan.DoesNotExist:
            logger.warning(f"Scheduled scan {scheduled_scan_id} not found")
            return False, f"Scheduled scan {scheduled_scan_id} not found"
        
        except Exception as e:
            logger.exception(f"Error deleting scheduled scan: {str(e)}")
            return False, f"Error deleting scheduled scan: {str(e)}"
