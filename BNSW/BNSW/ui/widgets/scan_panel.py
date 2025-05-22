from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QComboBox, QPushButton, QCheckBox, QGroupBox, QFormLayout,
                             QToolTip)
from PyQt5.QtCore import Qt, pyqtSignal

class ScanPanelWidget(QWidget):
    """Panel widget for configuring and starting network scans."""

    scan_requested = pyqtSignal(str, str, bool)
    schedule_requested = pyqtSignal(str, str)

    def __init__(self, parent=None):
        """Initialize scan panel widget."""
        super().__init__(parent)

        # Create layout
        main_layout = QVBoxLayout(self)

        # Create target group
        target_group = QGroupBox("Target")
        target_layout = QFormLayout()

        # Create target input
        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("Enter IP, hostname, or CIDR range")
        target_layout.addRow("Target:", self.target_input)

        # Create profile selector
        self.profile_selector = QComboBox()
        self.profile_selector.addItems(["Quick", "Full", "Ping", "Service", "OS Detection", "Comprehensive"])
        self.profile_selector.setToolTip(self._get_profile_tooltip("Quick"))
        self.profile_selector.currentTextChanged.connect(self._on_profile_changed)
        target_layout.addRow("Profile:", self.profile_selector)

        # Set target group layout
        target_group.setLayout(target_layout)
        main_layout.addWidget(target_group)

        # Create options group
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout()

        # Create save option
        self.save_option = QCheckBox("Save results to database")
        self.save_option.setChecked(True)
        options_layout.addWidget(self.save_option)

        # Create aggressive option
        self.aggressive_option = QCheckBox("Aggressive scan (may trigger IDS/IPS)")
        self.aggressive_option.setToolTip("Enables more aggressive scanning techniques that may be detected by security systems")
        options_layout.addWidget(self.aggressive_option)

        # Set options group layout
        options_group.setLayout(options_layout)
        main_layout.addWidget(options_group)

        # Create button layout
        button_layout = QHBoxLayout()

        # Create scan button
        self.scan_button = QPushButton("Scanning...")
        self.scan_button.setEnabled(False)
        self.scan_button.clicked.connect(self._on_scan_clicked)
        button_layout.addWidget(self.scan_button)

        # Create schedule button
        self.schedule_button = QPushButton("Schedule Scan")
        self.schedule_button.setToolTip("Schedule this scan to run at a later time")
        self.schedule_button.clicked.connect(self._on_schedule_clicked)  # <-- Connect the signal
        button_layout.addWidget(self.schedule_button)

        # Add button layout
        main_layout.addLayout(button_layout)

        # Set main layout
        self.setLayout(main_layout)

        # Set scan state
        self.set_scan_state(False)

    def set_scan_state(self, is_scanning):
        """Set scan state."""
        if is_scanning:
            self.scan_button.setText("Scanning...")
            self.scan_button.setEnabled(False)
            self.target_input.setEnabled(False)
            self.profile_selector.setEnabled(False)
            self.save_option.setEnabled(False)
            self.aggressive_option.setEnabled(False)
            self.schedule_button.setEnabled(False)
        else:
            self.scan_button.setText("Start Scan")
            self.scan_button.setEnabled(True)
            self.target_input.setEnabled(True)
            self.profile_selector.setEnabled(True)
            self.save_option.setEnabled(True)
            self.aggressive_option.setEnabled(True)
            self.schedule_button.setEnabled(True)

    def get_target(self):
        """Get target."""
        return self.target_input.text().strip()

    def get_profile(self):
        """Get profile."""
        return self.profile_selector.currentText()

    def get_save_option(self):
        """Get save option."""
        return self.save_option.isChecked()

    def get_aggressive_option(self):
        """Get aggressive option."""
        return self.aggressive_option.isChecked()

    def _on_scan_clicked(self):
        """Handle scan button clicked."""
        target = self.get_target()
        profile = self.get_profile()
        save = self.get_save_option()

        if target:
            self.scan_requested.emit(target, profile, save)

    def _on_schedule_clicked(self):
        """Handle schedule button clicked."""
        target = self.get_target()
        profile = self.get_profile()
        if target:
            self.schedule_requested.emit(target, profile)

    def _on_profile_changed(self, profile):
        """Handle profile changed."""
        self.profile_selector.setToolTip(self._get_profile_tooltip(profile))

        if profile in ["OS Detection", "Comprehensive"]:
            self.aggressive_option.setChecked(True)

            QToolTip.showText(
                self.profile_selector.mapToGlobal(self.profile_selector.rect().bottomRight()),
                "This scan type requires administrator privileges",
                self.profile_selector,
                self.profile_selector.rect(),
                2000
            )

    def _get_profile_tooltip(self, profile):
        """Get tooltip for profile."""
        tooltips = {
            "Quick": "Fast scan of the most common 100 ports (-T4 -F)",
            "Full": "Scan all 65535 ports (-T4 -p-)",
            "Ping": "Only check if hosts are online, no port scanning (-sn)",
            "Service": "Detect service versions on open ports (-sV)",
            "OS Detection": "Attempt to identify the operating system (requires admin privileges) (-O)",
            "Comprehensive": "Full scan with service detection, OS detection, and traceroute (requires admin privileges) (-T4 -A -v)"
        }

        return tooltips.get(profile, "")