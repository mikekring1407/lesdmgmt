"""
One-time setup route to create admin user and workspace.
Only use this route for initial setup when shell access is not available.
"""
from flask import Blueprint, jsonify, request, render_template, flash, redirect, url_for
import os
import secrets
from app import db
from models import User, Workspace, WorkspaceHeader

# Create blueprint
setup_bp = Blueprint('setup', __name__)

DEFAULT_HEADERS = [
    "first_name", "last_name", "email", "phone", 
    "city", "state", "status", "bank", "date"
]

CUSTOM_HEADERS = ["source", "notes", "priority"]

@setup_bp.route('/setup', methods=['GET', 'POST'])
def setup():
    """
    Web interface for initial system setup
    """
    # Use a secure setup key to prevent unauthorized access
    setup_key = os.environ.get('SETUP_KEY', 'CHANGE_THIS_TO_A_SECURE_VALUE')
    request_key = request.args.get('key')
    
    if not request_key or request_key != setup_key:
        return render_template('setup/access.html')
    
    # Check if setup is already done
    admin_exists = User.query.filter_by(role='admin').first() is not None
    workspace_exists = Workspace.query.first() is not None
    
    if admin_exists and workspace_exists:
        return render_template('setup/complete.html')
    
    if request.method == 'POST':
        try:
            username = request.form.get('username', 'admin')
            email = request.form.get('email', 'admin@example.com')
            password = request.form.get('password')
            workspace_name = request.form.get('workspace_name', 'Default Workspace')
            
            if not password:
                flash('Password is required', 'danger')
                return render_template('setup/form.html', key=request_key)
                
            # Create admin if needed
            admin = User.query.filter_by(username=username).first()
            if not admin:
                admin = User(
                    username=username,
                    email=email,
                    role='admin'
                )
                admin.set_password(password)
                db.session.add(admin)
                db.session.flush()  # Get the admin ID
                admin_created = True
            else:
                admin_created = False
            
            # Create workspace if needed
            if not workspace_exists:
                workspace = Workspace(
                    name=workspace_name,
                    created_by=admin.id
                )
                
                db.session.add(workspace)
                db.session.flush()
                
                # Add headers
                for i, header in enumerate(DEFAULT_HEADERS):
                    header_obj = WorkspaceHeader(
                        workspace_id=workspace.id,
                        header_name=header,
                        is_default=True,
                        order=i
                    )
                    db.session.add(header_obj)
                
                for i, header in enumerate(CUSTOM_HEADERS):
                    header_obj = WorkspaceHeader(
                        workspace_id=workspace.id,
                        header_name=header,
                        is_default=False,
                        order=len(DEFAULT_HEADERS) + i
                    )
                    db.session.add(header_obj)
                
                workspace_created = True
            else:
                workspace_created = False
            
            db.session.commit()
            
            return render_template('setup/success.html', 
                                admin_created=admin_created,
                                workspace_created=workspace_created,
                                username=username,
                                password=password)
                
        except Exception as e:
            db.session.rollback()
            flash(f'Error during setup: {str(e)}', 'danger')
            return render_template('setup/form.html', key=request_key)
    
    return render_template('setup/form.html', key=request_key)

@setup_bp.route('/create-admin', methods=['GET'])
def create_admin():
    """
    API route to create admin user and workspace programmatically.
    """
    # Use a secure setup key to prevent unauthorized access
    setup_key = os.environ.get('SETUP_KEY', 'CHANGE_THIS_TO_A_SECURE_VALUE')
    request_key = request.args.get('key')
    
    if not request_key or request_key != setup_key:
        return jsonify({"error": "Unauthorized. Invalid or missing setup key."}), 401
    
    try:
        # Generate a secure password
        password = request.args.get('password', secrets.token_urlsafe(12))
        username = request.args.get('username', 'admin')
        email = request.args.get('email', 'admin@example.com')
        
        # Check if admin already exists
        existing_admin = User.query.filter_by(username=username).first()
        if existing_admin:
            return jsonify({"message": "Admin user already exists", "username": username, "password": "Use existing password"}), 200
        
        # Create admin user
        admin = User(
            username=username,
            email=email,
            role='admin'
        )
        admin.set_password(password)
        
        db.session.add(admin)
        db.session.flush()  # Get the admin ID
        
        # Check if workspace exists
        existing_workspace = Workspace.query.first()
        if existing_workspace:
            db.session.commit()
            return jsonify({
                "message": "Admin user created, workspace already exists", 
                "username": username, 
                "password": password
            }), 200
        
        # Create workspace
        workspace = Workspace(
            name="Default Workspace",
            created_by=admin.id
        )
        
        db.session.add(workspace)
        db.session.flush()
        
        # Add default headers
        for i, header in enumerate(DEFAULT_HEADERS):
            header_obj = WorkspaceHeader(
                workspace_id=workspace.id,
                header_name=header,
                is_default=True,
                order=i
            )
            db.session.add(header_obj)
        
        # Add custom headers
        for i, header in enumerate(CUSTOM_HEADERS):
            header_obj = WorkspaceHeader(
                workspace_id=workspace.id,
                header_name=header,
                is_default=False,
                order=len(DEFAULT_HEADERS) + i
            )
            db.session.add(header_obj)
        
        db.session.commit()
        
        return jsonify({
            "message": "Setup completed successfully", 
            "username": username, 
            "password": password
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500