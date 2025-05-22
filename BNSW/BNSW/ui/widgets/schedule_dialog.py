"""
BNSW UI Widgets - Schedule Dialog
-------------------------
This module provides a dialog for scheduling scans.
"""

import logging
from datetime import datetime, timedelta

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QDateTimeEdit, QComboBox, QFormLayout,
                            QDialogButtonBox, QCheckBox, QSpinBox, QGroupBox)
from PyQt5.QtCore import Qt, pyqtSignal, QDateTime

# Set up logger
logger = logging.getLogger('BNSW.ui.widgets.schedule_dialog')

class ScheduleDialog(QDialog):
    """Dialog for scheduling scans."""
    
    def __init__(self, target, profile, parent=None):
        """
        Initialize schedule dialog.
        
        Args:
            target: Target to scan
            profile: Scan profile
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Store parameters
        self.target = target
        self.profile = profile
        
        # Set window properties
        self.setWindowTitle("Schedule Scan")
        self.setMinimumWidth(400)
        
        # Create layout
        main_layout = QVBoxLayout(self)
        
        # Create form layout
        form_layout = QFormLayout()
        
        # Create target label
        target_label = QLabel(f"<b>Target:</b> {target}")
        form_layout.addRow(target_label)
        
        # Create profile label
        profile_label = QLabel(f"<b>Profile:</b> {profile}")
        form_layout.addRow(profile_label)
        
        # Create schedule type group
        schedule_group = QGroupBox("Schedule Type")
        schedule_layout = QVBoxLayout()
        
        # Create one-time radio
        self.one_time_radio = QCheckBox("One-time")
        self.one_time_radio.setChecked(True)
        self.one_time_radio.toggled.connect(self._on_schedule_type_changed)
        schedule_layout.addWidget(self.one_time_radio)
        
        # Create recurring radio
        self.recurring_radio = QCheckBox("Recurring")
        self.recurring_radio.toggled.connect(self._on_schedule_type_changed)
        schedule_layout.addWidget(self.recurring_radio)
        
        # Set schedule group layout
        schedule_group.setLayout(schedule_layout)
        form_layout.addRow(schedule_group)
        
        # Create one-time group
        self.one_time_group = QGroupBox("One-time Schedule")
        one_time_layout = QFormLayout()
        
        # Create date time edit
        self.date_time_edit = QDateTimeEdit()
        self.date_time_edit.setDateTime(QDateTime.currentDateTime().addSecs(3600))  # Default to 1 hour from now
        self.date_time_edit.setCalendarPopup(True)
        self.date_time_edit.setMinimumDateTime(QDateTime.currentDateTime())
        one_time_layout.addRow("Date and Time:", self.date_time_edit)
        
        # Set one-time group layout
        self.one_time_group.setLayout(one_time_layout)
        form_layout.addRow(self.one_time_group)
        
        # Create recurring group
        self.recurring_group = QGroupBox("Recurring Schedule")
        recurring_layout = QFormLayout()
        
        # Create interval type combo
        self.interval_type_combo = QComboBox()
        self.interval_type_combo.addItems(["Hours", "Days", "Weeks"])
        recurring_layout.addRow("Repeat every:", self.interval_type_combo)
        
        # Create interval value spin
        self.interval_value_spin = QSpinBox()
        self.interval_value_spin.setMinimum(1)
        self.interval_value_spin.setMaximum(999)
        self.interval_value_spin.setValue(24)  # Default to 24 hours
        recurring_layout.addRow("", self.interval_value_spin)
        
        # Create start date time edit
        self.start_date_time_edit = QDateTimeEdit()
        self.start_date_time_edit.setDateTime(QDateTime.currentDateTime().addSecs(3600))  # Default to 1 hour from now
        self.start_date_time_edit.setCalendarPopup(True)
        self.start_date_time_edit.setMinimumDateTime(QDateTime.currentDateTime())
        recurring_layout.addRow("Start Date and Time:", self.start_date_time_edit)
        
        # Create end date time edit
        self.end_date_time_edit = QDateTimeEdit()
        self.end_date_time_edit.setDateTime(QDateTime.currentDateTime().addDays(30))  # Default to 30 days from now
        self.end_date_time_edit.setCalendarPopup(True)
        self.end_date_time_edit.setMinimumDateTime(QDateTime.currentDateTime())
        recurring_layout.addRow("End Date and Time:", self.end_date_time_edit)
        
        # Set recurring group layout
        self.recurring_group.setLayout(recurring_layout)
        form_layout.addRow(self.recurring_group)
        
        # Add form layout
        main_layout.addLayout(form_layout)
        
        # Create button box
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)
        
        # Set main layout
        self.setLayout(main_layout)
        
        # Initialize UI
        self._on_schedule_type_changed()
    
    def _on_schedule_type_changed(self):
        """Handle schedule type changed."""
        # Update group visibility
        self.one_time_group.setVisible(self.one_time_radio.isChecked())
        self.recurring_group.setVisible(self.recurring_radio.isChecked())
    
    def get_schedule_data(self):
        """
        Get schedule data.
        
        Returns:
            dict: Schedule data
        """
        # Create schedule data
        schedule_data = {
            'target': self.target,
            'profile': self.profile,
            'type': 'one_time' if self.one_time_radio.isChecked() else 'recurring',
            'created_at': datetime.now().isoformat()
        }
        
        # Add type-specific data
        if self.one_time_radio.isChecked():
            # One-time schedule
            schedule_data['scheduled_time'] = self.date_time_edit.dateTime().toPyDateTime().isoformat()
        else:
            # Recurring schedule
            schedule_data['interval_type'] = self.interval_type_combo.currentText().lower()
            schedule_data['interval_value'] = self.interval_value_spin.value()
            schedule_data['start_time'] = self.start_date_time_edit.dateTime().toPyDateTime().isoformat()
            schedule_data['end_time'] = self.end_date_time_edit.dateTime().toPyDateTime().isoformat()
        
        return schedule_data
