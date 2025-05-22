"""
BNSW UI Widgets - Host Table
-------------------------
This module provides a table widget for displaying host scan results.
"""

from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QBrush

class HostTableWidget(QTableWidget):
    """Table widget for displaying host scan results."""
    
    host_selected = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        """Initialize host table widget."""
        super().__init__(parent)
        
        # Set up table
        self.setColumnCount(5)
        self.setHorizontalHeaderLabels(['IP Address', 'Hostname', 'Status', 'OS', 'MAC Address'])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        
        # Set selection behavior
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        
        # Connect signals
        self.itemSelectionChanged.connect(self._on_selection_changed)
        
        # Store host data
        self.host_data = []

    def get_hosts(self):
        hosts = []
        for row in range(self.rowCount()):
            # Safely retrieve item text or default to an empty string
            ip_item = self.item(row, 0)
            hostname_item = self.item(row, 1)
            status_item = self.item(row, 2)
            os_item = self.item(row, 3)
            mac_item = self.item(row, 4)

            host = {
                'ip': ip_item.text() if ip_item else '',
                'hostname': hostname_item.text() if hostname_item else '',
                'status': status_item.text() if status_item else '',
                'os': os_item.text() if os_item else '',
                'mac': mac_item.text() if mac_item else '',
                'ports': []  # Adjust as necessary
            }
            hosts.append(host)
        return hosts
    
    def set_hosts(self, hosts):
        """
        Set hosts to display.
        
        Args:
            hosts: List of host dictionaries
        """
        # Clear table
        self.clearContents()
        self.setRowCount(0)
        self.host_data = []
        
        # Add hosts
        for host in hosts:
            self.add_host(host)
    
    def add_host(self, host):
        """
        Add host to table.
        
        Args:
            host: Host dictionary
        """
        # Add row
        row = self.rowCount()
        self.insertRow(row)
        
        # Set host data
        ip = host.get('ip', '')
        hostname = host.get('hostname', '')
        status = host.get('status', '')
        os_name = host.get('os', {}).get('name', '')
        mac = host.get('mac', '')
        
        # Create items
        ip_item = QTableWidgetItem(ip)
        hostname_item = QTableWidgetItem(hostname)
        status_item = QTableWidgetItem(status)
        os_item = QTableWidgetItem(os_name)
        mac_item = QTableWidgetItem(mac)
        
        # Set alignment
        ip_item.setTextAlignment(Qt.AlignCenter)
        status_item.setTextAlignment(Qt.AlignCenter)
        mac_item.setTextAlignment(Qt.AlignCenter)
        
        # Set color based on status
        if status == 'up':
            status_item.setBackground(QBrush(QColor(200, 255, 200)))
        elif status == 'down':
            status_item.setBackground(QBrush(QColor(255, 200, 200)))
        
        # Set items
        self.setItem(row, 0, ip_item)
        self.setItem(row, 1, hostname_item)
        self.setItem(row, 2, status_item)
        self.setItem(row, 3, os_item)
        self.setItem(row, 4, mac_item)
        
        # Store host data
        self.host_data.append(host)
    
    def get_selected_host(self):
        """
        Get selected host.
        
        Returns:
            dict: Selected host dictionary, or None if no selection
        """
        # Get selected row
        selected_rows = self.selectionModel().selectedRows()
        if not selected_rows:
            return None
        
        # Get host data
        row = selected_rows[0].row()
        if row < 0 or row >= len(self.host_data):
            return None
        
        return self.host_data[row]
    
    def _on_selection_changed(self):
        """Handle selection changed."""
        host = self.get_selected_host()
        if host:
            self.host_selected.emit(host)
