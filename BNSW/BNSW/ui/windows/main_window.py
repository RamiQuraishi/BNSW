"""
BNSW UI Windows - Main Window
-------------------------
This module provides the main window for the BNSW application.
"""

import os
import json
import logging
import datetime
from typing import Dict, List, Any, Optional

from PyQt5.QtWidgets import (QMainWindow, QTabWidget, QVBoxLayout, QHBoxLayout, QWidget,
                            QAction, QMenu, QToolBar, QStatusBar, QFileDialog, QMessageBox,
                            QLabel, QSplitter, QDialog)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QTimer, QMetaObject, Q_ARG, Qt
from PyQt5.QtGui import QIcon, QPixmap

from BNSW.core.scanner_manager import ScannerManager
from BNSW.core.scheduler import Scheduler
from BNSW.data.repositories import DatabaseManager
from BNSW.data.models import initialize_database
from BNSW.ui.widgets.scan_panel import ScanPanelWidget
from BNSW.ui.widgets.host_table import HostTableWidget
from BNSW.ui.widgets.port_table import PortTableWidget
from BNSW.ui.widgets.progress_bar import ScanProgressBarWidget
from BNSW.ui.widgets.network_map import NetworkMapWidget
from BNSW.ui.widgets.history_tab import HistoryTabWidget
from BNSW.ui.widgets.scheduled_scans_tab import ScheduledScansTabWidget
from BNSW.ui.widgets.schedule_dialog import ScheduleDialog
from BNSW.utils.themes import set_dark_theme, set_light_theme

# Set up logger
logger = logging.getLogger('BNSW.ui.windows.main_window')

class MainWindow(QMainWindow):
    """Main window for the BNSW application."""
    
    # Define signals for thread-safe operations
    scan_complete_signal = pyqtSignal(str, int)
    update_progress_signal = pyqtSignal(str, int)
    
    def __init__(self):
        """Initialize main window."""
        super().__init__()
        
        # Initialize database
        initialize_database()
        
        # Create managers
        self.scanner_manager = ScannerManager()
        self.db_manager = DatabaseManager()
        self.scheduler = Scheduler()
        
        # Initialize variables
        self.active_scans = {}
        self.current_theme = 'light'
        self.scan_results_tabs = {}
        self.next_tab_id = 1
        
        # Initialize UI
        self._init_ui()
        
        # Connect signals
        self.scan_complete_signal.connect(self._on_scan_complete_main_thread)
        self.update_progress_signal.connect(self._on_update_progress_main_thread)
        
        # Check Nmap installation
        self._check_nmap_installation()
        
        # Start scheduler
        self.scheduler.start()
    
    def _init_ui(self):
        """Initialize UI."""
        # Set window properties
        self.setWindowTitle("BNSW Network Scanner")
        self.setMinimumSize(1000, 700)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Create scan panel
        self.scan_panel = ScanPanelWidget()
        self.scan_panel.scan_requested.connect(self._on_scan_requested)
        self.scan_panel.schedule_requested.connect(self._on_schedule_requested)
        main_layout.addWidget(self.scan_panel)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Create scan results tab container
        self.scan_results_container = QTabWidget()
        self.scan_results_container.setTabsClosable(True)
        self.scan_results_container.tabCloseRequested.connect(self._on_scan_tab_close_requested)
        
        # Create initial scan results tab
        self._create_scan_results_tab("Current Scan")
        
        # Create network map tab
        network_map_tab = QWidget()
        network_map_layout = QVBoxLayout(network_map_tab)
        
        # Create network map
        self.network_map = NetworkMapWidget()
        self.network_map.host_selected.connect(self._on_map_host_selected)
        network_map_layout.addWidget(self.network_map)
        
        # Create history tab
        self.history_tab = HistoryTabWidget()
        self.history_tab.scan_selected.connect(self._on_history_scan_selected)
        
        # Create scheduled scans tab
        self.scheduled_scans_tab = ScheduledScansTabWidget()
        
        # Add tabs to main tab widget
        self.tab_widget.addTab(self.scan_results_container, "Scan Results")
        self.tab_widget.addTab(network_map_tab, "Network Map")
        self.tab_widget.addTab(self.history_tab, "History")
        self.tab_widget.addTab(self.scheduled_scans_tab, "Scheduled Scans")
        
        # Add tab widget to main layout
        main_layout.addWidget(self.tab_widget)
        
        # Create progress layout
        self.progress_layout = QVBoxLayout()
        main_layout.addLayout(self.progress_layout)
        
        # Create menu bar
        self._create_menu_bar()
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Create admin indicator
        self.admin_indicator = QLabel()
        self.admin_indicator.setPixmap(QPixmap())  # Empty pixmap
        self.admin_indicator.setToolTip("Administrator privileges required for some scan types")
        self.status_bar.addPermanentWidget(self.admin_indicator)
        
        # Check admin status
        self._check_admin_status()
    
    def _create_menu_bar(self):
        """Create menu bar."""
        # Create menu bar
        menu_bar = self.menuBar()
        
        # Create file menu
        file_menu = menu_bar.addMenu("File")
        
        # Create save action
        save_action = QAction("Save Results", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._on_save_results)
        file_menu.addAction(save_action)
        
        # Create export menu
        export_menu = file_menu.addMenu("Export")
        
        # Create export to JSON action
        export_json_action = QAction("Export to JSON", self)
        export_json_action.triggered.connect(self._on_export_json)
        export_menu.addAction(export_json_action)
        
        # Create export to CSV action
        export_csv_action = QAction("Export to CSV", self)
        export_csv_action.triggered.connect(self._on_export_csv)
        export_menu.addAction(export_csv_action)
        
        # Create exit action
        exit_action = QAction("Exit", self)
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Create view menu
        view_menu = menu_bar.addMenu("View")
        
        # Create theme menu
        theme_menu = view_menu.addMenu("Theme")
        
        # Create light theme action
        light_theme_action = QAction("Light", self)
        light_theme_action.triggered.connect(lambda: self._set_theme('light'))
        theme_menu.addAction(light_theme_action)
        
        # Create dark theme action
        dark_theme_action = QAction("Dark", self)
        dark_theme_action.triggered.connect(lambda: self._set_theme('dark'))
        theme_menu.addAction(dark_theme_action)
        
        # Create help menu
        help_menu = menu_bar.addMenu("Help")
        
        # Create about action
        about_action = QAction("About", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)
    
    def _check_nmap_installation(self):
        """Check Nmap installation."""
        # Check if Nmap is installed
        is_installed, version = self.scanner_manager.check_nmap_installation()
        
        if not is_installed:
            # Show error message
            QMessageBox.critical(
                self,
                "Nmap Not Found",
                "Nmap is not installed or not in PATH. Please install Nmap and try again."
            )
            
            # Disable scan panel
            self.scan_panel.set_scan_state(True)
            
            # Update status bar
            self.status_bar.showMessage("Nmap not found")
        else:
            # Update status bar
            self.status_bar.showMessage(f"Nmap {version} detected")
    
    def _check_admin_status(self):
        """Check administrator status."""
        # This is a simplified check - in a real implementation, 
        # you would use platform-specific methods to check admin status
        try:
            # Try to run a privileged Nmap command
            is_admin = self.scanner_manager.check_admin_privileges()
            
            if is_admin:
                # Set admin indicator
                self.admin_indicator.setText("Admin: Yes")
                self.admin_indicator.setStyleSheet("color: green;")
                self.admin_indicator.setToolTip("Administrator privileges detected - all scan types available")
            else:
                # Set non-admin indicator
                self.admin_indicator.setText("Admin: No")
                self.admin_indicator.setStyleSheet("color: red;")
                self.admin_indicator.setToolTip(
                    "Administrator privileges not detected\n"
                    "OS Detection and Comprehensive scan types require administrator privileges\n"
                    "Please restart the application with administrator privileges to use these scan types"
                )
        except Exception as e:
            logger.exception(f"Error checking admin status: {str(e)}")
            # Set unknown indicator
            self.admin_indicator.setText("Admin: Unknown")
            self.admin_indicator.setStyleSheet("color: orange;")
            self.admin_indicator.setToolTip("Could not determine administrator status")

    def _set_theme(self, theme):
        """
        Set theme.

        Args:
            theme: Theme name
        """
        from PyQt5.QtWidgets import QApplication
        app = QApplication.instance()

        if theme == 'dark' and self.current_theme != 'dark':
            set_dark_theme(app)
            self.current_theme = 'dark'
        elif theme == 'light' and self.current_theme != 'light':
            set_light_theme(app)
            self.current_theme = 'light'
    
    def _create_scan_results_tab(self, title):
        """
        Create a new scan results tab.
        
        Args:
            title: Tab title
            
        Returns:
            tuple: (tab_id, host_table, port_table)
        """
        # Create tab ID
        tab_id = self.next_tab_id
        self.next_tab_id += 1
        
        # Create tab
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)
        
        # Create splitter
        splitter = QSplitter(Qt.Vertical)
        
        # Create host table
        host_table = HostTableWidget()
        host_table.host_selected.connect(lambda host: self._on_host_selected(host, tab_id))
        splitter.addWidget(host_table)
        
        # Create port table
        port_table = PortTableWidget()
        splitter.addWidget(port_table)
        
        # Add splitter to layout
        tab_layout.addWidget(splitter)
        
        # Add tab to container
        self.scan_results_container.addTab(tab, title)
        
        # Store tab info
        self.scan_results_tabs[tab_id] = {
            'tab': tab,
            'host_table': host_table,
            'port_table': port_table
        }
        
        # Select the new tab
        self.scan_results_container.setCurrentWidget(tab)
        
        return tab_id, host_table, port_table
    
    def _on_scan_requested(self, target, profile, save):
        """
        Handle scan requested.
        
        Args:
            target: Target
            profile: Profile
            save: Whether to save results
        """
        # Check if there are unsaved results
        if self._check_unsaved_results():
            # Create new tab for this scan
            tab_id, _, _ = self._create_scan_results_tab(f"Scan: {target}")
        else:
            # Use current tab
            tab_id = 1  # Default tab ID
        
        # Update scan panel
        self.scan_panel.set_scan_state(True)
        
        # Update status bar
        self.status_bar.showMessage(f"Scanning {target}...")
        
        # Create progress bar
        progress_bar = ScanProgressBarWidget()
        progress_bar.cancel_requested.connect(self._on_cancel_scan)
        self.progress_layout.addWidget(progress_bar)
        
        # Start scan
        scan_id = self.scanner_manager.start_scan(
            target,
            profile,
            self._on_scan_progress
        )
        
        # Store scan info
        self.active_scans[scan_id] = {
            'target': target,
            'profile': profile,
            'save': save,
            'progress_bar': progress_bar,
            'tab_id': tab_id
        }
        
        # Update progress bar
        progress_bar.set_scan(scan_id, target)
    
    def _on_schedule_requested(self, target, profile):
        """
        Handle schedule requested.
        
        Args:
            target: Target
            profile: Profile
        """
        # Create schedule dialog
        dialog = ScheduleDialog(target, profile, self)
        
        # Show dialog
        if dialog.exec_() == QDialog.Accepted:
            # Get schedule data
            schedule_data = dialog.get_schedule_data()
            
            # Schedule scan
            success, scheduled_scan_id, error = self.scheduler.schedule_scan(schedule_data)
            
            if not success:
                logger.error(f"Error scheduling scan: {error}")
                QMessageBox.warning(
                    self,
                    "Schedule Error",
                    f"Error scheduling scan: {error}"
                )
                return
            
            # Show success message
            QMessageBox.information(
                self,
                "Schedule Successful",
                f"Scan scheduled successfully with ID {scheduled_scan_id}"
            )
            
            # Refresh scheduled scans tab
            self.scheduled_scans_tab.refresh()
            
            # Switch to scheduled scans tab
            self.tab_widget.setCurrentWidget(self.scheduled_scans_tab)
    
    def _on_scan_progress(self, scan_id, progress):
        """
        Handle scan progress.
        
        Args:
            scan_id: Scan ID
            progress: Progress percentage (0-100), or -1 for error, -2 for permission denied
        """
        # Emit signal to update progress in main thread
        self.update_progress_signal.emit(scan_id, progress)
        
        # Check if scan is complete
        if progress == 100 or progress < 0:
            # Emit signal to handle completion in main thread
            self.scan_complete_signal.emit(scan_id, progress)
    
    @pyqtSlot(str, int)
    def _on_update_progress_main_thread(self, scan_id, progress):
        """
        Handle scan progress update in main thread.
        
        Args:
            scan_id: Scan ID
            progress: Progress percentage (0-100), or -1 for error, -2 for permission denied
        """
        # Get scan info
        scan_info = self.active_scans.get(scan_id)
        if not scan_info:
            return
        
        # Get progress bar
        progress_bar = scan_info.get('progress_bar')
        
        # Update progress bar
        if progress_bar:
            progress_bar.update_progress(progress)
    
    @pyqtSlot(str, int)
    def _on_scan_complete_main_thread(self, scan_id, status_code):
        """
        Handle scan complete in main thread.
        
        Args:
            scan_id: Scan ID
            status_code: Status code (100 for success, -1 for failure, -2 for permission denied)
        """
        # Get scan info
        scan_info = self.active_scans.get(scan_id)
        if not scan_info:
            return
        
        # Get tab ID
        tab_id = scan_info.get('tab_id', 1)
        
        # Get scan status
        scan_status = self.scanner_manager.get_scan_status(scan_id)
        
        # Check for permission error
        permission_error = scan_status.get('status') == 'permission_denied'
        
        # Get error message
        error_message = scan_status.get('error_message')
        
        # Get scan result
        result = self.scanner_manager.get_scan_result(scan_id)
        
        # Save result
        if scan_info.get('save', False) and status_code == 100 and result:
            try:
                success, db_id, error = self.db_manager.save_scan_result(scan_id, result)
                if not success:
                    logger.error(f"Error saving scan result: {error}")
                    QMessageBox.warning(
                        self,
                        "Save Error",
                        f"Error saving scan result: {error}"
                    )
            except Exception as e:
                logger.exception(f"Unexpected error saving scan result: {str(e)}")
                QMessageBox.warning(
                    self,
                    "Save Error",
                    f"Unexpected error saving scan result: {str(e)}"
                )
        
        # Update UI with result
        if status_code == 100 and result:
            self._update_ui_with_result(result, tab_id)
            
            # Refresh network map tab
            self.network_map.set_hosts(result.get('hosts', []))
            
            # Update tab title
            tab_info = self.scan_results_tabs.get(tab_id)
            if tab_info:
                tab_index = self.scan_results_container.indexOf(tab_info['tab'])
                if tab_index >= 0:
                    target = scan_info.get('target', '')
                    self.scan_results_container.setTabText(tab_index, f"Scan: {target}")
        
        # Update scan panel
        self.scan_panel.set_scan_state(False)
        
        # Update status bar
        target = scan_info.get('target', '')
        profile = scan_info.get('profile', '')
        
        if status_code == 100:
            self.status_bar.showMessage(f"Scan of {target} completed successfully")
        elif permission_error:
            self.status_bar.showMessage(f"Scan of {target} failed: Insufficient privileges")
            
            # Show error message
            QMessageBox.warning(
                self,
                "Insufficient Privileges",
                f"The '{profile}' scan type requires administrator privileges.\n\n"
                "Please run the application as administrator to use this scan type."
            )
        else:
            self.status_bar.showMessage(f"Scan of {target} failed")
            
            # Show error message if available
            if error_message:
                QMessageBox.warning(
                    self,
                    "Scan Failed",
                    f"Scan of {target} failed:\n\n{error_message}"
                )
        
        # Schedule removal of progress bar
        QTimer.singleShot(5000, lambda: self._remove_progress_bar(scan_id))
    
    def _remove_progress_bar(self, scan_id):
        """
        Remove progress bar.
        
        Args:
            scan_id: Scan ID
        """
        # Get scan info
        scan_info = self.active_scans.get(scan_id)
        if not scan_info:
            return
        
        # Get progress bar
        progress_bar = scan_info.get('progress_bar')
        
        # Remove progress bar
        if progress_bar:
            self.progress_layout.removeWidget(progress_bar)
            progress_bar.deleteLater()
        
        # Remove scan info
        self.active_scans.pop(scan_id, None)
    
    def _on_cancel_scan(self, scan_id):
        """
        Handle cancel scan.
        
        Args:
            scan_id: Scan ID
        """
        # Cancel scan
        self.scanner_manager.cancel_scan(scan_id)
        
        # Remove progress bar
        self._remove_progress_bar(scan_id)
        
        # Update scan panel
        self.scan_panel.set_scan_state(False)
        
        # Update status bar
        scan_info = self.active_scans.get(scan_id, {})
        target = scan_info.get('target', '')
        self.status_bar.showMessage(f"Scan of {target} cancelled")
    
    def _update_ui_with_result(self, result, tab_id=1):
        """
        Update UI with result.
        
        Args:
            result: Scan result
            tab_id: Tab ID
        """
        # Get hosts
        hosts = result.get('hosts', [])
        
        # Get tab info
        tab_info = self.scan_results_tabs.get(tab_id)
        if not tab_info:
            return
        
        # Update host table
        tab_info['host_table'].set_hosts(hosts)
        
        # Switch to scan results tab
        self.tab_widget.setCurrentIndex(0)
        
        # Switch to specific scan tab
        self.scan_results_container.setCurrentWidget(tab_info['tab'])
    
    def _on_host_selected(self, host, tab_id=1):
        """
        Handle host selected.
        
        Args:
            host: Host dictionary
            tab_id: Tab ID
        """
        # Get tab info
        tab_info = self.scan_results_tabs.get(tab_id)
        if not tab_info:
            return
        
        # Update port table
        tab_info['port_table'].set_ports(host.get('ports', []))
    
    def _on_map_host_selected(self, host):
        """
        Handle host selected from map.
        
        Args:
            host: Host dictionary
        """
        # Get current tab ID
        current_tab_id = 1  # Default to first tab
        
        # Find first tab with hosts
        for tab_id, tab_info in self.scan_results_tabs.items():
            if tab_info['host_table'].get_hosts():
                current_tab_id = tab_id
                break
        
        # Select host in table
        tab_info = self.scan_results_tabs.get(current_tab_id)
        if tab_info:
            tab_info['host_table'].select_host(host.get('ip', ''))
            tab_info['port_table'].set_ports(host.get('ports', []))
        
        # Switch to scan tab
        self.tab_widget.setCurrentIndex(0)
        
        # Switch to specific scan tab
        if tab_info:
            self.scan_results_container.setCurrentWidget(tab_info['tab'])
    
    def _on_history_scan_selected(self, result):
        """
        Handle history scan selected.
        
        Args:
            result: Scan result
        """
        # Check if there are unsaved results
        if self._check_unsaved_results():
            # Create new tab for this scan
            tab_id, _, _ = self._create_scan_results_tab("History Scan")
        else:
            # Use current tab
            tab_id = 1  # Default tab ID
        
        # Update UI with result
        self._update_ui_with_result(result, tab_id)
    
    def _on_scan_tab_close_requested(self, index):
        """
        Handle scan tab close requested.
        
        Args:
            index: Tab index
        """
        # Get tab
        tab = self.scan_results_container.widget(index)
        
        # Find tab ID
        tab_id = None
        for tid, tab_info in self.scan_results_tabs.items():
            if tab_info['tab'] == tab:
                tab_id = tid
                break
        
        if tab_id is None:
            return
        
        # Check if this is the last tab
        if len(self.scan_results_tabs) <= 1:
            # Don't close the last tab, just clear it
            tab_info = self.scan_results_tabs.get(tab_id)
            if tab_info:
                tab_info['host_table'].clear()
                tab_info['port_table'].clear()
                self.scan_results_container.setTabText(index, "Current Scan")
            return
        
        # Remove tab
        self.scan_results_container.removeTab(index)
        
        # Remove tab info
        if tab_id in self.scan_results_tabs:
            del self.scan_results_tabs[tab_id]
    
    def _check_unsaved_results(self):
        """
        Check if there are unsaved results in the current tab.
        
        Returns:
            bool: True if a new tab should be created, False otherwise
        """
        # Get current tab index
        current_index = self.scan_results_container.currentIndex()
        
        # Get current tab
        current_tab = self.scan_results_container.widget(current_index)
        
        # Find current tab ID
        current_tab_id = None
        for tab_id, tab_info in self.scan_results_tabs.items():
            if tab_info['tab'] == current_tab:
                current_tab_id = tab_id
                break
        
        if current_tab_id is None:
            return True
        
        # Get current tab info
        tab_info = self.scan_results_tabs.get(current_tab_id)
        if not tab_info:
            return True
        
        # Check if there are hosts in the table
        if tab_info['host_table'].get_hosts():
            # Ask user if they want to keep the results
            reply = QMessageBox.question(
                self,
                "Unsaved Results",
                "There are unsaved scan results in the current tab. Do you want to keep them?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                # Create a new tab
                return True
        
        # Use current tab
        return False
    
    def _on_save_results(self):
        """Handle save results."""
        # Get current tab ID
        current_index = self.scan_results_container.currentIndex()
        current_tab = self.scan_results_container.widget(current_index)
        
        # Find current tab ID
        current_tab_id = None
        for tab_id, tab_info in self.scan_results_tabs.items():
            if tab_info['tab'] == current_tab:
                current_tab_id = tab_id
                break
        
        if current_tab_id is None:
            return
        
        # Get current tab info
        tab_info = self.scan_results_tabs.get(current_tab_id)
        if not tab_info:
            return
        
        # Get current hosts
        hosts = tab_info['host_table'].get_hosts()
        
        # Check if hosts exist
        if not hosts:
            QMessageBox.information(
                self,
                "No Results",
                "No scan results to save."
            )
            return
        
        # Get save path
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Results",
            os.path.expanduser("~/scan_results.json"),
            "JSON Files (*.json)"
        )
        
        # Check if file path is valid
        if not file_path:
            return
        
        # Create result dictionary
        result = {
            'scan_info': {
                'timestamp': datetime.datetime.now().isoformat(),
                'hosts_count': len(hosts)
            },
            'hosts': hosts
        }
        
        try:
            # Save to file
            with open(file_path, 'w') as f:
                json.dump(result, f, indent=2)
            
            # Show success message
            QMessageBox.information(
                self,
                "Save Successful",
                f"Results saved to {file_path}"
            )
        
        except Exception as e:
            # Show error message
            QMessageBox.critical(
                self,
                "Save Error",
                f"Error saving results: {str(e)}"
            )
    
    def _on_export_json(self):
        """Handle export to JSON."""
        # Get current tab ID
        current_index = self.scan_results_container.currentIndex()
        current_tab = self.scan_results_container.widget(current_index)
        
        # Find current tab ID
        current_tab_id = None
        for tab_id, tab_info in self.scan_results_tabs.items():
            if tab_info['tab'] == current_tab:
                current_tab_id = tab_id
                break
        
        if current_tab_id is None:
            return
        
        # Get current tab info
        tab_info = self.scan_results_tabs.get(current_tab_id)
        if not tab_info:
            return
        
        # Get current hosts
        hosts = tab_info['host_table'].get_hosts()
        
        # Check if hosts exist
        if not hosts:
            QMessageBox.information(
                self,
                "No Results",
                "No scan results to export."
            )
            return
        
        # Get export path
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export to JSON",
            os.path.expanduser("~/scan_results.json"),
            "JSON Files (*.json)"
        )
        
        # Check if file path is valid
        if not file_path:
            return
        
        # Create result dictionary with enhanced metadata
        result = {
            'scan_info': {
                'timestamp': datetime.datetime.now().isoformat(),
                'hosts_count': len(hosts),
                'export_type': 'json',
                'application': 'BNSW Network Scanner'
            },
            'hosts': hosts
        }
        
        try:
            # Save to file
            with open(file_path, 'w') as f:
                json.dump(result, f, indent=2)
            
            # Show success message
            QMessageBox.information(
                self,
                "Export Successful",
                f"Results exported to {file_path}"
            )
        
        except Exception as e:
            # Show error message
            QMessageBox.critical(
                self,
                "Export Error",
                f"Error exporting results: {str(e)}"
            )
    
    def _on_export_csv(self):
        """Handle export to CSV."""
        # Get current tab ID
        current_index = self.scan_results_container.currentIndex()
        current_tab = self.scan_results_container.widget(current_index)
        
        # Find current tab ID
        current_tab_id = None
        for tab_id, tab_info in self.scan_results_tabs.items():
            if tab_info['tab'] == current_tab:
                current_tab_id = tab_id
                break
        
        if current_tab_id is None:
            return
        
        # Get current tab info
        tab_info = self.scan_results_tabs.get(current_tab_id)
        if not tab_info:
            return
        
        # Get current hosts
        hosts = tab_info['host_table'].get_hosts()
        
        # Check if hosts exist
        if not hosts:
            QMessageBox.information(
                self,
                "No Results",
                "No scan results to export."
            )
            return
        
        # Get export path
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export to CSV",
            os.path.expanduser("~/scan_results.csv"),
            "CSV Files (*.csv)"
        )
        
        # Check if file path is valid
        if not file_path:
            return
        
        try:
            # Create CSV content
            csv_content = "IP,Hostname,Status,MAC,OS,Ports\n"
            
            for host in hosts:
                # Get host info
                ip = host.get('ip', '')
                hostname = host.get('hostname', '')
                status = host.get('status', '')
                mac = host.get('mac', '')
                os_name = host.get('os', {}).get('name', '')
                
                # Get ports
                ports = host.get('ports', [])
                ports_str = "|".join([
                    f"{p.get('port', '')}/{p.get('protocol', '')}/{p.get('state', '')}/{p.get('service', '')}"
                    for p in ports
                ])
                
                # Add row
                csv_content += f'"{ip}","{hostname}","{status}","{mac}","{os_name}","{ports_str}"\n'
            
            # Save to file
            with open(file_path, 'w') as f:
                f.write(csv_content)
            
            # Show success message
            QMessageBox.information(
                self,
                "Export Successful",
                f"Results exported to {file_path}"
            )
        
        except Exception as e:
            # Show error message
            QMessageBox.critical(
                self,
                "Export Error",
                f"Error exporting results: {str(e)}"
            )
    
    def _on_about(self):
        """Handle about."""
        # Show about dialog
        QMessageBox.about(
            self,
            "About BNSW Network Scanner",
            "BNSW Network Scanner\n\n"
            "A Python-based desktop network scanning application similar to Zenmap.\n\n"
            "Features:\n"
            "- Multiple scan types\n"
            "- Real-time progress monitoring\n"
            "- Network visualization\n"
            "- Result management\n"
            "- Scan history\n"
            "- Scan scheduling\n"
            "- Dark/Light theme\n\n"
            "This software is provided for educational and ethical use only."
        )
    
    def closeEvent(self, event):
        """
        Handle close event.
        
        Args:
            event: Close event
        """
        # Stop scheduler
        self.scheduler.stop()
        
        # Accept event
        event.accept()
