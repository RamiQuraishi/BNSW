"""
BNSW UI Widgets - Scheduled Scans Tab
-------------------------
This module provides a widget for displaying and managing scheduled scans.
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QTableWidget, QTableWidgetItem,
                            QHeaderView, QMessageBox, QMenu, QAction)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QIcon, QCursor

from BNSW.core.scheduler import Scheduler

# Set up logger
logger = logging.getLogger('BNSW.ui.widgets.scheduled_scans_tab')

class ScheduledScansTabWidget(QWidget):
    """Widget for displaying and managing scheduled scans."""
    
    def __init__(self, parent=None):
        """Initialize scheduled scans tab widget."""
        super().__init__(parent)
        
        # Create scheduler
        self.scheduler = Scheduler()
        
        # Create layout
        main_layout = QVBoxLayout(self)
        
        # Create controls layout
        controls_layout = QHBoxLayout()
        
        # Create refresh button
        self.refresh_button = QPushButton("Refresh Scheduled Scans")
        self.refresh_button.clicked.connect(self.refresh)
        controls_layout.addWidget(self.refresh_button)
        
        # Add stretch
        controls_layout.addStretch()
        
        # Add controls layout
        main_layout.addLayout(controls_layout)
        
        # Create table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Target", "Profile", "Type", "Next Run", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        main_layout.addWidget(self.table)
        
        # Store scheduled scans
        self.scheduled_scans = []
        
        # Set main layout
        self.setLayout(main_layout)
        
        # Start scheduler
        self.scheduler.start()
        
        # Refresh on init
        self.refresh()
    
    def refresh(self):
        """Refresh scheduled scans."""
        try:
            # Get all scheduled scans
            success, scheduled_scans, error = self.scheduler.get_scheduled_scans()
            
            if not success:
                logger.error(f"Error retrieving scheduled scans: {error}")
                QMessageBox.warning(
                    self,
                    "Scheduled Scans Error",
                    f"Error retrieving scheduled scans: {error}"
                )
                return
            
            # Store scheduled scans
            self.scheduled_scans = scheduled_scans
            
            # Clear table
            self.table.setRowCount(0)
            
            # Add scheduled scans to table
            for i, scan in enumerate(scheduled_scans):
                # Insert row
                self.table.insertRow(i)
                
                # Set ID
                id_item = QTableWidgetItem(str(scan.get('id', '')))
                self.table.setItem(i, 0, id_item)
                
                # Set target
                target_item = QTableWidgetItem(scan.get('target', ''))
                self.table.setItem(i, 1, target_item)
                
                # Set profile
                profile_item = QTableWidgetItem(scan.get('profile', ''))
                self.table.setItem(i, 2, profile_item)
                
                # Set type
                schedule_type = scan.get('schedule_type', '')
                if schedule_type == 'one_time':
                    type_text = "One-time"
                elif schedule_type == 'recurring':
                    interval_type = scan.get('interval_type', '')
                    interval_value = scan.get('interval_value', '')
                    type_text = f"Every {interval_value} {interval_type}"
                else:
                    type_text = schedule_type
                type_item = QTableWidgetItem(type_text)
                self.table.setItem(i, 3, type_item)
                
                # Set next run
                next_run = scan.get('next_run', '')
                if next_run:
                    try:
                        next_run_dt = datetime.fromisoformat(next_run)
                        next_run_str = next_run_dt.strftime("%Y-%m-%d %H:%M:%S")
                    except (ValueError, TypeError):
                        next_run_str = next_run
                else:
                    next_run_str = "N/A"
                next_run_item = QTableWidgetItem(next_run_str)
                self.table.setItem(i, 4, next_run_item)
                
                # Set status
                status_item = QTableWidgetItem(scan.get('status', ''))
                self.table.setItem(i, 5, status_item)
        
        except Exception as e:
            logger.exception(f"Unexpected error refreshing scheduled scans: {str(e)}")
            QMessageBox.warning(
                self,
                "Scheduled Scans Error",
                f"Unexpected error refreshing scheduled scans: {str(e)}"
            )
    
    def _show_context_menu(self, position):
        """
        Show context menu.
        
        Args:
            position: Menu position
        """
        # Get selected row
        indexes = self.table.selectedIndexes()
        if not indexes:
            return
        
        # Get row
        row = indexes[0].row()
        
        # Get scheduled scan ID
        scheduled_scan_id = int(self.table.item(row, 0).text())
        
        # Get status
        status = self.table.item(row, 5).text()
        
        # Create menu
        menu = QMenu()
        
        # Create cancel action if pending or running
        if status in ['pending', 'running']:
            cancel_action = QAction("Cancel Scan", self)
            cancel_action.triggered.connect(lambda: self._cancel_scheduled_scan(scheduled_scan_id))
            menu.addAction(cancel_action)
        
        # Create delete action
        delete_action = QAction("Delete Scan", self)
        delete_action.triggered.connect(lambda: self._delete_scheduled_scan(scheduled_scan_id))
        menu.addAction(delete_action)
        
        # Show menu
        menu.exec_(QCursor.pos())
    
    def _cancel_scheduled_scan(self, scheduled_scan_id):
        """
        Cancel scheduled scan.
        
        Args:
            scheduled_scan_id: Scheduled scan ID
        """
        try:
            # Confirm cancellation
            reply = QMessageBox.question(
                self,
                "Confirm Cancellation",
                f"Are you sure you want to cancel scheduled scan {scheduled_scan_id}?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
            
            # Cancel scheduled scan
            success, error = self.scheduler.cancel_scheduled_scan(scheduled_scan_id)
            
            if not success:
                logger.error(f"Error cancelling scheduled scan: {error}")
                QMessageBox.warning(
                    self,
                    "Cancel Error",
                    f"Error cancelling scheduled scan: {error}"
                )
                return
            
            # Refresh
            self.refresh()
            
            # Show success message
            QMessageBox.information(
                self,
                "Cancel Successful",
                f"Scheduled scan {scheduled_scan_id} cancelled successfully"
            )
        
        except Exception as e:
            logger.exception(f"Unexpected error cancelling scheduled scan: {str(e)}")
            QMessageBox.warning(
                self,
                "Cancel Error",
                f"Unexpected error cancelling scheduled scan: {str(e)}"
            )
    
    def _delete_scheduled_scan(self, scheduled_scan_id):
        """
        Delete scheduled scan.
        
        Args:
            scheduled_scan_id: Scheduled scan ID
        """
        try:
            # Confirm deletion
            reply = QMessageBox.question(
                self,
                "Confirm Deletion",
                f"Are you sure you want to delete scheduled scan {scheduled_scan_id}?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
            
            # Delete scheduled scan
            success, error = self.scheduler.delete_scheduled_scan(scheduled_scan_id)
            
            if not success:
                logger.error(f"Error deleting scheduled scan: {error}")
                QMessageBox.warning(
                    self,
                    "Delete Error",
                    f"Error deleting scheduled scan: {error}"
                )
                return
            
            # Refresh
            self.refresh()
            
            # Show success message
            QMessageBox.information(
                self,
                "Delete Successful",
                f"Scheduled scan {scheduled_scan_id} deleted successfully"
            )
        
        except Exception as e:
            logger.exception(f"Unexpected error deleting scheduled scan: {str(e)}")
            QMessageBox.warning(
                self,
                "Delete Error",
                f"Unexpected error deleting scheduled scan: {str(e)}"
            )
