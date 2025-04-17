"""
One-time setup route to create admin user and workspace.
Only use this route for initial setup when shell access is not available.
"""
from flask import Blueprint, jsonify, request
import os
from app import db
from models import User, Workspace, WorkspaceHeader

# Create blueprint
setup_bp = Blueprint('setup', __name__)

@setup_bp.route('/create-admin', methods=['GET'])
def create_admin():
    """
    Create admin user and workspace.
    """
    # Use a secure setup key to prevent unauthorized access
    setup_key = os.environ.get('SETUP_KEY', 'CHANGE_THIS_TO_A_SECURE_VALUE')
    request_key = request.args.get('key')
    
    if not request_key or request_key != setup_key:
        return jsonify({"error": "Unauthorized. Invalid or missing setup key."}), 401
    
    try:
        # Check if admin already exists
        existing_admin = User.query.filter_by(username='admin').first()
        if existing_admin:
            return jsonify({"message": "Admin user already exists", "username": "admin", "password": "Use existing password"}), 200
        
        # Create admin user
        admin = User(
            username='admin',
            email='admin@example.com',
            role='admin'
        )
        admin.set_password('Admin@123')
        
        db.session.add(admin)
        db.session.flush()  # Get the admin ID
        
        # Check if workspace exists
        existing_workspace = Workspace.query.first()
        if existing_workspace:
            db.session.commit()
            return jsonify({
                "message": "Admin user created, workspace already exists", 
                "username": "admin", 
                "password": "Admin@123"
            }), 200
        
        # Create workspace
        workspace = Workspace(
            name="Default Workspace",
            created_by=admin.id
        )
        
        db.session.add(workspace)
        db.session.flush()
        
        # Add default headers
        default_headers = [
            "first_name", "last_name", "email", "phone", 
            "city", "state", "status", "bank", "date"
        ]
        
        for i, header in enumerate(default_headers):
            header_obj = WorkspaceHeader(
                workspace_id=workspace.id,
                header_name=header,
                is_default=True,
                order=i
            )
            db.session.add(header_obj)
        
        # Add custom headers
        custom_headers = ["source", "notes", "priority"]
        for i, header in enumerate(custom_headers):
            header_obj = WorkspaceHeader(
                workspace_id=workspace.id,
                header_name=header,
                is_default=False,
                order=len(default_headers) + i
            )
            db.session.add(header_obj)
        
        db.session.commit()
        
        return jsonify({
            "message": "Setup completed successfully", 
            "username": "admin", 
            "password": "Admin@123"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500