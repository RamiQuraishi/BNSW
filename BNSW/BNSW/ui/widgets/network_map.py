"""
BNSW UI Widgets - Network Map
-------------------------
This module provides a widget for displaying a network map visualization.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QGraphicsView, QGraphicsScene, 
                            QGraphicsEllipseItem, QGraphicsTextItem, QGraphicsLineItem)
from PyQt5.QtCore import Qt, pyqtSignal, QRectF, QPointF
from PyQt5.QtGui import QColor, QBrush, QPen, QFont, QPainter

import math
import random

class NetworkMapWidget(QWidget):
    """Widget for displaying a network map visualization."""
    
    host_selected = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        """Initialize network map widget."""
        super().__init__(parent)
        
        # Create layout
        main_layout = QVBoxLayout(self)
        
        # Create controls layout
        controls_layout = QHBoxLayout()
        
        # Create refresh button
        self.refresh_button = QPushButton("Refresh Map")
        self.refresh_button.clicked.connect(self.refresh)
        controls_layout.addWidget(self.refresh_button)
        
        # Add stretch
        controls_layout.addStretch()
        
        # Create zoom controls
        self.zoom_in_button = QPushButton("+")
        self.zoom_in_button.setMaximumWidth(30)
        self.zoom_in_button.clicked.connect(self._on_zoom_in)
        controls_layout.addWidget(self.zoom_in_button)
        
        self.zoom_out_button = QPushButton("-")
        self.zoom_out_button.setMaximumWidth(30)
        self.zoom_out_button.clicked.connect(self._on_zoom_out)
        controls_layout.addWidget(self.zoom_out_button)
        
        # Add controls layout
        main_layout.addLayout(controls_layout)
        
        # Create graphics view
        self.view = QGraphicsView()
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setDragMode(QGraphicsView.ScrollHandDrag)
        main_layout.addWidget(self.view)
        
        # Create scene
        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)
        
        # Store hosts
        self.hosts = []
        self.host_items = {}
        
        # Set zoom level
        self.zoom_level = 1.0
        
        # Set main layout
        self.setLayout(main_layout)
    
    def set_hosts(self, hosts):
        """
        Set hosts to display.
        
        Args:
            hosts: List of host dictionaries
        """
        # Store hosts
        self.hosts = hosts
        
        # Refresh map
        self.refresh()
    
    def refresh(self):
        """Refresh network map."""
        # Clear scene
        self.scene.clear()
        self.host_items = {}
        
        # Check if hosts exist
        if not self.hosts:
            # Add message
            text = self.scene.addText("No hosts to display")
            text.setDefaultTextColor(Qt.darkGray)
            font = QFont()
            font.setPointSize(14)
            text.setFont(font)
            return
        
        # Get up hosts
        up_hosts = [host for host in self.hosts if host.get('status') == 'up']
        
        # Check if up hosts exist
        if not up_hosts:
            # Add message
            text = self.scene.addText("No active hosts to display")
            text.setDefaultTextColor(Qt.darkGray)
            font = QFont()
            font.setPointSize(14)
            text.setFont(font)
            return
        
        # Calculate layout
        self._calculate_layout(up_hosts)
        
        # Draw connections
        self._draw_connections(up_hosts)
        
        # Draw hosts
        self._draw_hosts(up_hosts)
        
        # Fit scene in view
        self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
    
    def _calculate_layout(self, hosts):
        """
        Calculate layout for hosts.
        
        Args:
            hosts: List of host dictionaries
        """
        # Get number of hosts
        num_hosts = len(hosts)
        
        # Calculate radius
        radius = max(100, num_hosts * 20)
        
        # Calculate center
        center_x = 0
        center_y = 0
        
        # Calculate positions
        for i, host in enumerate(hosts):
            # Calculate angle
            angle = 2 * math.pi * i / num_hosts
            
            # Calculate position
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            
            # Store position
            host['_pos'] = (x, y)
        
        # Set scene rect
        margin = 100
        self.scene.setSceneRect(
            center_x - radius - margin,
            center_y - radius - margin,
            2 * (radius + margin),
            2 * (radius + margin)
        )
    
    def _draw_connections(self, hosts):
        """
        Draw connections between hosts.
        
        Args:
            hosts: List of host dictionaries
        """
        # Get gateway host (if any)
        gateway_host = None
        for host in hosts:
            if host.get('ip', '').endswith('.1'):
                gateway_host = host
                break
        
        # Draw connections
        if gateway_host:
            # Draw connections to gateway
            gateway_pos = gateway_host.get('_pos')
            
            for host in hosts:
                if host == gateway_host:
                    continue
                
                host_pos = host.get('_pos')
                
                # Create line
                line = QGraphicsLineItem(
                    gateway_pos[0], gateway_pos[1],
                    host_pos[0], host_pos[1]
                )
                
                # Set pen
                pen = QPen(QColor(200, 200, 200))
                pen.setWidth(1)
                line.setPen(pen)
                
                # Add to scene
                self.scene.addItem(line)
    
    def _draw_hosts(self, hosts):
        """
        Draw hosts.
        
        Args:
            hosts: List of host dictionaries
        """
        # Draw hosts
        for host in hosts:
            # Get position
            pos = host.get('_pos')
            
            # Get host info
            ip = host.get('ip', '')
            hostname = host.get('hostname', '')
            os_name = host.get('os', {}).get('name', '')
            
            # Determine color based on OS
            color = self._get_host_color(os_name)
            
            # Create ellipse
            ellipse = QGraphicsEllipseItem(
                pos[0] - 15, pos[1] - 15,
                30, 30
            )
            
            # Set brush and pen
            ellipse.setBrush(QBrush(color))
            ellipse.setPen(QPen(Qt.black))
            
            # Make clickable
            ellipse.setFlag(QGraphicsEllipseItem.ItemIsSelectable)
            ellipse.setFlag(QGraphicsEllipseItem.ItemIsMovable)
            ellipse.setAcceptHoverEvents(True)
            
            # Store host data
            ellipse.host_data = host
            
            # Connect to click event
            ellipse.mousePressEvent = lambda event, item=ellipse: self._on_host_clicked(event, item)
            
            # Add to scene
            self.scene.addItem(ellipse)
            
            # Store item
            self.host_items[ip] = ellipse
            
            # Create label
            label_text = ip
            if hostname:
                label_text += f"\n{hostname}"
            
            label = QGraphicsTextItem(label_text)
            label.setPos(pos[0] - label.boundingRect().width() / 2, pos[1] + 20)
            
            # Add to scene
            self.scene.addItem(label)
    
    def _get_host_color(self, os_name):
        """
        Get color for host based on OS.
        
        Args:
            os_name: OS name
            
        Returns:
            QColor: Host color
        """
        os_name = os_name.lower()
        
        if 'windows' in os_name:
            return QColor(100, 100, 255)
        elif 'linux' in os_name:
            return QColor(255, 100, 100)
        elif 'mac' in os_name or 'apple' in os_name:
            return QColor(100, 255, 100)
        else:
            return QColor(200, 200, 200)
    
    def _on_host_clicked(self, event, item):
        """
        Handle host clicked.
        
        Args:
            event: Mouse event
            item: Graphics item
        """
        # Get host data
        host = item.host_data
        
        # Emit signal
        self.host_selected.emit(host)
    
    def _on_zoom_in(self):
        """Handle zoom in."""
        # Increase zoom level
        self.zoom_level *= 1.2
        
        # Apply transform
        self.view.resetTransform()
        self.view.scale(self.zoom_level, self.zoom_level)
    
    def _on_zoom_out(self):
        """Handle zoom out."""
        # Decrease zoom level
        self.zoom_level /= 1.2
        
        # Apply transform
        self.view.resetTransform()
        self.view.scale(self.zoom_level, self.zoom_level)
