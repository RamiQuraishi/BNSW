"""
BNSW UI Widgets - Port Table
-------------------------
This module provides a table widget for displaying port scan results.
"""

from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QBrush

class PortTableWidget(QTableWidget):
    """Table widget for displaying port scan results."""
    
    port_selected = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        """Initialize port table widget."""
        super().__init__(parent)
        
        # Set up table
        self.setColumnCount(5)
        self.setHorizontalHeaderLabels(['Port', 'Protocol', 'State', 'Service', 'Version'])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        
        # Set selection behavior
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        
        # Connect signals
        self.itemSelectionChanged.connect(self._on_selection_changed)
        
        # Store port data
        self.port_data = []
    
    def set_ports(self, ports):
        """
        Set ports to display.
        
        Args:
            ports: List of port dictionaries
        """
        # Clear table
        self.clearContents()
        self.setRowCount(0)
        self.port_data = []
        
        # Add ports
        for port in ports:
            self.add_port(port)
    
    def add_port(self, port):
        """
        Add port to table.
        
        Args:
            port: Port dictionary
        """
        # Add row
        row = self.rowCount()
        self.insertRow(row)
        
        # Set port data
        port_id = port.get('portid', '')
        protocol = port.get('protocol', '')
        state = port.get('state', '')
        service = port.get('service', '')
        version = port.get('version', '')
        
        # Create items
        port_item = QTableWidgetItem(port_id)
        protocol_item = QTableWidgetItem(protocol)
        state_item = QTableWidgetItem(state)
        service_item = QTableWidgetItem(service)
        version_item = QTableWidgetItem(version)
        
        # Set alignment
        port_item.setTextAlignment(Qt.AlignCenter)
        protocol_item.setTextAlignment(Qt.AlignCenter)
        state_item.setTextAlignment(Qt.AlignCenter)
        
        # Set color based on state
        if state == 'open':
            state_item.setBackground(QBrush(QColor(200, 255, 200)))
        elif state == 'closed':
            state_item.setBackground(QBrush(QColor(255, 200, 200)))
        elif state == 'filtered':
            state_item.setBackground(QBrush(QColor(255, 255, 200)))
        
        # Set items
        self.setItem(row, 0, port_item)
        self.setItem(row, 1, protocol_item)
        self.setItem(row, 2, state_item)
        self.setItem(row, 3, service_item)
        self.setItem(row, 4, version_item)
        
        # Store port data
        self.port_data.append(port)
    
    def get_selected_port(self):
        """
        Get selected port.
        
        Returns:
            dict: Selected port dictionary, or None if no selection
        """
        # Get selected row
        selected_rows = self.selectionModel().selectedRows()
        if not selected_rows:
            return None
        
        # Get port data
        row = selected_rows[0].row()
        if row < 0 or row >= len(self.port_data):
            return None
        
        return self.port_data[row]
    
    def _on_selection_changed(self):
        """Handle selection changed."""
        port = self.get_selected_port()
        if port:
            self.port_selected.emit(port)
