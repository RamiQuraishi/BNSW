"""
BNSW Application Entry Point
-------------------------
This module provides the entry point for the BNSW application.
"""

import sys
import logging
import os
from PyQt5.QtWidgets import QApplication

from BNSW.ui.windows.main_window import MainWindow
from BNSW.data.models import initialize_database

# Configure logging
def configure_logging():
    """Configure logging."""
    # Create logs directory
    logs_dir = os.path.expanduser("~/.bnsw/logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(logs_dir, 'bnsw.log')),
            logging.StreamHandler()
        ]
    )

def main():
    """Application entry point."""
    # Configure logging
    configure_logging()
    
    # Initialize database
    initialize_database()
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("BNSW Network Scanner")
    
    # Create main window
    window = MainWindow()
    window.show()
    
    # Run application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
