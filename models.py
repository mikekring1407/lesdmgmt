from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    sheet_filter = db.Column(db.String(255), nullable=True)  # Used to filter lead data
    is_admin = db.Column(db.Boolean, default=False)
    
    # Add relationship to assigned leads
    assigned_leads = db.relationship('LeadAssignment', back_populates='assigned_user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class CustomField(db.Model):
    """Model to store custom field definitions for leads"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)  # Name of the field
    label = db.Column(db.String(100), nullable=False)  # Display label
    field_type = db.Column(db.String(20), nullable=False)  # text, number, date, select, etc.
    required = db.Column(db.Boolean, default=False)  # Is this field required?
    options = db.Column(db.Text, nullable=True)  # JSON string for select options
    order = db.Column(db.Integer, default=0)  # Display order
    active = db.Column(db.Boolean, default=True)  # Is this field currently active?
    
    def __repr__(self):
        return f'<CustomField {self.name}: {self.label}>'
    
    @property
    def options_list(self):
        """Return the options as a list if they exist"""
        if not self.options:
            return []
        try:
            return json.loads(self.options)
        except:
            return []

class Lead(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # Basic contact information
    name = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    company = db.Column(db.String(100), nullable=True)
    
    # Additional information - can be customized as needed
    status = db.Column(db.String(20), default='New')  # New, Contacted, Qualified, Lost, Converted
    source = db.Column(db.String(50), nullable=True)  # Where the lead came from
    notes = db.Column(db.Text, nullable=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Denormalized JSON data to store extra columns from Google Sheets, CSV or custom fields
    extra_data = db.Column(db.JSON, nullable=True)
    
    # Relationships
    assignments = db.relationship('LeadAssignment', back_populates='lead', lazy='dynamic')
    
    def __repr__(self):
        return f'<Lead {self.id}: {self.name or "Unnamed"}>'
    
    @property
    def current_assignment(self):
        """Get the current active assignment for this lead"""
        return self.assignments.filter_by(active=True).first()
    
    @property
    def assigned_user(self):
        """Get the currently assigned user for this lead"""
        assignment = self.current_assignment
        return assignment.assigned_user if assignment else None
    
    def get_custom_field_value(self, field_name):
        """Get a custom field value from extra_data"""
        if not self.extra_data:
            return None
        return self.extra_data.get(field_name)
    
    def set_custom_field_value(self, field_name, value):
        """Set a custom field value in extra_data"""
        if not self.extra_data:
            self.extra_data = {}
        self.extra_data[field_name] = value

class LeadAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('lead.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    active = db.Column(db.Boolean, default=True)
    
    # Relationships
    lead = db.relationship('Lead', back_populates='assignments')
    assigned_user = db.relationship('User', back_populates='assigned_leads')
    
    def __repr__(self):
        return f'<LeadAssignment {self.id}: Lead {self.lead_id} to User {self.user_id}>'
