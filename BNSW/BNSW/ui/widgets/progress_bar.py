"""
BNSW UI Widgets - Progress Bar
-------------------------
This module provides a progress bar widget for displaying scan progress.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QProgressBar, QPushButton)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor

class ScanProgressBarWidget(QWidget):
    """Progress bar widget for displaying scan progress."""
    
    cancel_requested = pyqtSignal(str)
    
    def __init__(self, parent=None):
        """Initialize progress bar widget."""
        super().__init__(parent)
        
        # Create layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create info layout
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create title label
        self.title_label = QLabel("Scan")
        info_layout.addWidget(self.title_label)
        
        # Create progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        info_layout.addWidget(self.progress_bar)
        
        # Add info layout
        main_layout.addLayout(info_layout, 1)
        
        # Create cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self._on_cancel_clicked)
        main_layout.addWidget(self.cancel_button)
        
        # Set main layout
        self.setLayout(main_layout)
        
        # Initialize variables
        self.scan_id = None
    
    def set_scan(self, scan_id, target):
        """
        Set scan.
        
        Args:
            scan_id: Scan ID
            target: Target
        """
        # Store scan ID
        self.scan_id = scan_id
        
        # Update title
        self.title_label.setText(f"Scanning {target}")
        
        # Reset progress
        self.progress_bar.setValue(0)
        
        # Set stylesheet for normal progress
        self.progress_bar.setStyleSheet("")
    
    def update_progress(self, progress):
        """
        Update progress.
        
        Args:
            progress: Progress percentage (0-100), or -1 for error, -2 for permission denied
        """
        if progress >= 0:
            # Normal progress
            self.progress_bar.setValue(int(progress))
            self.progress_bar.setStyleSheet("")
        elif progress == -1:
            # Error
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("Error")
            self.progress_bar.setStyleSheet("QProgressBar { color: white; background-color: #ffaaaa; }")
            self.cancel_button.setText("Close")
        elif progress == -2:
            # Permission denied
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("Permission Denied")
            self.progress_bar.setStyleSheet("QProgressBar { color: white; background-color: #ffcc88; }")
            self.cancel_button.setText("Close")
    
    def _on_cancel_clicked(self):
        """Handle cancel button clicked."""
        if self.scan_id:
            self.cancel_requested.emit(self.scan_id)
