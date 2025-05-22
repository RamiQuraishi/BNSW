"""
BNSW Data Models
---------------
This module defines the database models for the BNSW application.
"""

import os
import json
import datetime
from peewee import *

# Database file path
DB_PATH = os.path.expanduser("~/.bnsw/bnsw.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# Database instance
db = SqliteDatabase(DB_PATH, pragmas={
    'journal_mode': 'wal',
    'cache_size': -1 * 64000,  # 64MB
    'foreign_keys': 1,
    'ignore_check_constraints': 0,
    'synchronous': 0
})

class BaseModel(Model):
    """Base model class for all models."""
    
    class Meta:
        database = db
    
    def to_dict(self):
        """Convert model to dictionary."""
        data = {}
        for field in self._meta.fields:
            field_name = field.name
            field_value = getattr(self, field_name)
            
            # Handle special field types
            if isinstance(field_value, datetime.datetime):
                field_value = field_value.isoformat()
            
            data[field_name] = field_value
        return data

class Scan(BaseModel):
    """Scan model."""
    scan_id = AutoField()  # <- explicitly define this primary key

    target = CharField()
    command = CharField()
    start_time = DateTimeField(default=datetime.datetime.now)
    end_time = DateTimeField(null=True)
    status = CharField(default='running')
    metadata = TextField(null=True)
    
    def set_metadata(self, data):
        """Set metadata as JSON."""
        self.metadata = json.dumps(data)
    
    def get_metadata(self):
        """Get metadata as dictionary."""
        if not self.metadata:
            return {}
        return json.loads(self.metadata)

class Host(BaseModel):
    """Host model."""
    
    scan = ForeignKeyField(Scan, backref='hosts', on_delete='CASCADE')
    ip = CharField()
    hostname = CharField(null=True)
    status = CharField()
    mac = CharField(null=True)
    os = CharField(null=True)
    metadata = TextField(null=True)
    
    def set_metadata(self, data):
        """Set metadata as JSON."""
        self.metadata = json.dumps(data)
    
    def get_metadata(self):
        """Get metadata as dictionary."""
        if not self.metadata:
            return {}
        return json.loads(self.metadata)

class Port(BaseModel):
    """Port model."""
    
    host = ForeignKeyField(Host, backref='ports', on_delete='CASCADE')
    port = IntegerField()
    protocol = CharField()
    state = CharField()
    service = CharField(null=True)
    version = CharField(null=True)
    metadata = TextField(null=True)
    
    def set_metadata(self, data):
        """Set metadata as JSON."""
        self.metadata = json.dumps(data)
    
    def get_metadata(self):
        """Get metadata as dictionary."""
        if not self.metadata:
            return {}
        return json.loads(self.metadata)

class Script(BaseModel):
    """Script model."""
    
    port = ForeignKeyField(Port, backref='scripts', on_delete='CASCADE', null=True)
    host = ForeignKeyField(Host, backref='scripts', on_delete='CASCADE', null=True)
    name = CharField()
    output = TextField()
    metadata = TextField(null=True)
    
    def set_metadata(self, data):
        """Set metadata as JSON."""
        self.metadata = json.dumps(data)
    
    def get_metadata(self):
        """Get metadata as dictionary."""
        if not self.metadata:
            return {}
        return json.loads(self.metadata)

class ScheduledScan(BaseModel):
    """Scheduled scan model."""
    
    target = CharField()
    profile = CharField()
    schedule_type = CharField()  # 'one_time' or 'recurring'
    created_at = DateTimeField(default=datetime.datetime.now)
    scheduled_time = DateTimeField(null=True)  # For one-time scans
    interval_type = CharField(null=True)  # 'hours', 'days', 'weeks' for recurring scans
    interval_value = IntegerField(null=True)  # Value for interval
    start_time = DateTimeField(null=True)  # For recurring scans
    end_time = DateTimeField(null=True)  # For recurring scans
    last_run = DateTimeField(null=True)
    next_run = DateTimeField(null=True)
    status = CharField(default='pending')  # 'pending', 'running', 'completed', 'cancelled', 'error'
    metadata = TextField(null=True)
    
    def set_metadata(self, data):
        """Set metadata as JSON."""
        self.metadata = json.dumps(data)
    
    def get_metadata(self):
        """Get metadata as dictionary."""
        if not self.metadata:
            return {}
        return json.loads(self.metadata)
    
    def calculate_next_run(self):
        """
        Calculate next run time based on schedule type and parameters.
        
        Returns:
            datetime.datetime: Next run time
        """
        if self.schedule_type == 'one_time':
            # One-time schedule has no next run after scheduled_time
            if self.last_run and self.last_run >= self.scheduled_time:
                return None
            return self.scheduled_time
        
        elif self.schedule_type == 'recurring':
            # Get current time
            now = datetime.datetime.now()
            
            # If we haven't started yet, return start_time
            if not self.last_run and self.start_time > now:
                return self.start_time
            
            # If we've passed the end time, no more runs
            if self.end_time and now > self.end_time:
                return None
            
            # Calculate next run based on last run or now
            base_time = self.last_run if self.last_run else now
            
            # Calculate interval
            if self.interval_type == 'hours':
                delta = datetime.timedelta(hours=self.interval_value)
            elif self.interval_type == 'days':
                delta = datetime.timedelta(days=self.interval_value)
            elif self.interval_type == 'weeks':
                delta = datetime.timedelta(weeks=self.interval_value)
            else:
                # Default to daily
                delta = datetime.timedelta(days=1)
            
            # Calculate next run
            next_run = base_time + delta
            
            # If next run is past end time, no more runs
            if self.end_time and next_run > self.end_time:
                return None
            
            return next_run
        
        return None

def initialize_database():
    """Initialize database."""
    db.connect()
    db.create_tables([Scan, Host, Port, Script, ScheduledScan])
    db.close()
