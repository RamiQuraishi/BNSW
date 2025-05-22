"""
BNSW UI Widgets - History Tab
-------------------------
This module provides a widget for displaying scan history.
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QTableWidget, QTableWidgetItem,
                            QHeaderView, QMessageBox, QMenu, QAction)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QIcon, QCursor

from BNSW.data.repositories import DatabaseManager

# Set up logger
logger = logging.getLogger('BNSW.ui.widgets.history_tab')

class HistoryTabWidget(QWidget):
    """Widget for displaying scan history."""
    
    scan_selected = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        """Initialize history tab widget."""
        super().__init__(parent)
        
        # Create database manager
        self.db_manager = DatabaseManager()
        
        # Create layout
        main_layout = QVBoxLayout(self)
        
        # Create controls layout
        controls_layout = QHBoxLayout()
        
        # Create refresh button
        self.refresh_button = QPushButton("Refresh History")
        self.refresh_button.clicked.connect(self.refresh)
        controls_layout.addWidget(self.refresh_button)
        
        # Add stretch
        controls_layout.addStretch()
        
        # Add controls layout
        main_layout.addLayout(controls_layout)
        
        # Create table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Target", "Profile", "Date", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.table.itemDoubleClicked.connect(self._on_item_double_clicked)
        main_layout.addWidget(self.table)
        
        # Store scans
        self.scans = []
        
        # Set main layout
        self.setLayout(main_layout)
        
        # Refresh on init
        self.refresh()
    
    def refresh(self):
        """Refresh history."""
        try:
            # Get all scans
            success, scans, error = self.db_manager.scan_repo.get_all()
            
            if not success:
                logger.error(f"Error retrieving scan history: {error}")
                QMessageBox.warning(
                    self,
                    "History Error",
                    f"Error retrieving scan history: {error}"
                )
                return
            
            # Store scans
            self.scans = scans
            
            # Clear table
            self.table.setRowCount(0)
            
            # Add scans to table
            for i, scan in enumerate(scans):
                # Insert row
                self.table.insertRow(i)
                
                # Set ID
                id_item = QTableWidgetItem(str(scan.id))
                self.table.setItem(i, 0, id_item)
                
                # Set target
                target_item = QTableWidgetItem(scan.target)
                self.table.setItem(i, 1, target_item)
                
                # Set profile
                profile = self._get_profile_from_command(scan.command)
                profile_item = QTableWidgetItem(profile)
                self.table.setItem(i, 2, profile_item)
                
                # Set date
                date_str = scan.start_time.strftime("%Y-%m-%d %H:%M:%S")
                date_item = QTableWidgetItem(date_str)
                self.table.setItem(i, 3, date_item)
                
                # Set status
                status_item = QTableWidgetItem(scan.status)
                self.table.setItem(i, 4, status_item)
        
        except Exception as e:
            logger.exception(f"Unexpected error refreshing history: {str(e)}")
            QMessageBox.warning(
                self,
                "History Error",
                f"Unexpected error refreshing history: {str(e)}"
            )
    
    def _get_profile_from_command(self, command):
        """
        Get profile name from command.
        
        Args:
            command: Command string
            
        Returns:
            str: Profile name
        """
        if "-T4 -F" in command:
            return "Quick"
        elif "-T4 -p-" in command:
            return "Full"
        elif "-sn" in command:
            return "Ping"
        elif "-sV" in command and "-O" not in command:
            return "Service"
        elif "-O" in command and "-A" not in command:
            return "OS Detection"
        elif "-A" in command:
            return "Comprehensive"
        else:
            return "Custom"

    def _on_item_double_clicked(self, item):
        row = item.row()
        id_item = self.table.item(row, 0)
        if id_item is None or not id_item.text().isdigit():
            return
        scan_id = int(id_item.text())
        self._load_scan(scan_id)

    def _show_context_menu(self, position):
        indexes = self.table.selectedIndexes()
        if not indexes:
            return

        row = indexes[0].row()
        id_item = self.table.item(row, 0)

        if id_item is None or not id_item.text().isdigit():
            logger.warning("Invalid scan ID in selected row.")
            return

        scan_id = int(id_item.text())

        menu = QMenu()
        load_action = QAction("Load Scan", self)
        load_action.triggered.connect(lambda: self._load_scan(scan_id))
        menu.addAction(load_action)

        delete_action = QAction("Delete Scan", self)
        delete_action.triggered.connect(lambda: self._delete_scan(scan_id))
        menu.addAction(delete_action)

        menu.exec_(QCursor.pos())
    
    def _load_scan(self, scan_id):
        """
        Load scan.
        
        Args:
            scan_id: Scan ID
        """
        try:
            # Get scan with details
            success, scan_data, error = self.db_manager.get_scan_with_details(scan_id)
            
            if not success:
                logger.error(f"Error loading scan: {error}")
                QMessageBox.warning(
                    self,
                    "Load Error",
                    f"Error loading scan: {error}"
                )
                return
            
            # Check if scan data exists
            if not scan_data:
                QMessageBox.warning(
                    self,
                    "Load Error",
                    f"No data found for scan ID {scan_id}"
                )
                return
            
            # Convert to scan result format
            result = {
                'scan_info': {
                    'target': scan_data.get('target', ''),
                    'args': scan_data.get('command', ''),
                    'start_time': scan_data.get('start_time', ''),
                    'end_time': scan_data.get('end_time', ''),
                    'status': scan_data.get('status', '')
                },
                'hosts': scan_data.get('hosts', [])
            }
            
            # Emit signal
            self.scan_selected.emit(result)
        
        except Exception as e:
            logger.exception(f"Unexpected error loading scan: {str(e)}")
            QMessageBox.warning(
                self,
                "Load Error",
                f"Unexpected error loading scan: {str(e)}"
            )
    
    def _delete_scan(self, scan_id):
        """
        Delete scan.
        
        Args:
            scan_id: Scan ID
        """
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete scan {scan_id}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        try:
            # Delete scan
            success, error = self.db_manager.scan_repo.delete(scan_id)
            
            if not success:
                logger.error(f"Error deleting scan: {error}")
                QMessageBox.warning(
                    self,
                    "Delete Error",
                    f"Error deleting scan: {error}"
                )
                return
            
            # Refresh
            self.refresh()
            
            # Show success message
            QMessageBox.information(
                self,
                "Delete Successful",
                f"Scan {scan_id} deleted successfully"
            )
        
        except Exception as e:
            logger.exception(f"Unexpected error deleting scan: {str(e)}")
            QMessageBox.warning(
                self,
                "Delete Error",
                f"Unexpected error deleting scan: {str(e)}"
            )
