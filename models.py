from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')  # 'admin' or 'user'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    leads = db.relationship('Lead', backref='assigned_user', lazy=True, foreign_keys='Lead.assigned_to')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'

class Workspace(db.Model):
    __tablename__ = 'workspaces'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    creator = db.relationship('User', backref='created_workspaces')
    leads = db.relationship('Lead', backref='workspace', lazy=True)
    custom_headers = db.relationship('WorkspaceHeader', backref='workspace', lazy=True, cascade='all, delete-orphan')

class WorkspaceHeader(db.Model):
    __tablename__ = 'workspace_headers'
    
    id = db.Column(db.Integer, primary_key=True)
    workspace_id = db.Column(db.Integer, db.ForeignKey('workspaces.id'), nullable=False)
    header_name = db.Column(db.String(100), nullable=False)
    is_default = db.Column(db.Boolean, default=False)  # True for system default headers
    order = db.Column(db.Integer, nullable=False)  # To maintain header order

class Lead(db.Model):
    __tablename__ = 'leads'
    
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    status = db.Column(db.String(50), default='New')
    bank = db.Column(db.String(100))
    date = db.Column(db.Date)
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    workspace_id = db.Column(db.Integer, db.ForeignKey('workspaces.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # For custom fields
    custom_fields = db.relationship('LeadCustomField', backref='lead', lazy=True, cascade='all, delete-orphan')

class LeadCustomField(db.Model):
    __tablename__ = 'lead_custom_fields'
    
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'), nullable=False)
    header_id = db.Column(db.Integer, db.ForeignKey('workspace_headers.id'), nullable=False)
    value = db.Column(db.String(255))
    
    header = db.relationship('WorkspaceHeader')
