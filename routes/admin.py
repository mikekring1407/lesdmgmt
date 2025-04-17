import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, g, jsonify, Response
from datetime import datetime, timedelta
from app import db
from models import User, Workspace, WorkspaceHeader, Lead, LeadCustomField
from auth import admin_required
from config import DEFAULT_LEAD_FIELDS, LEAD_STATUSES
from utils import process_csv_upload, export_leads_to_csv, get_lead_stats
import pandas as pd

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Admin dashboard"""
    # Get lead statistics
    today = datetime.utcnow().date()
    start_of_week = today - timedelta(days=today.weekday())
    start_of_month = today.replace(day=1)
    
    # Get stats
    daily_stats = get_lead_stats(today, today + timedelta(days=1))
    weekly_stats = get_lead_stats(start_of_week, start_of_week + timedelta(days=7))
    monthly_stats = get_lead_stats(start_of_month, today + timedelta(days=1))
    all_time_stats = get_lead_stats()
    
    return render_template('admin/dashboard.html', 
                           daily_stats=daily_stats,
                           weekly_stats=weekly_stats,
                           monthly_stats=monthly_stats,
                           all_time_stats=all_time_stats)

@admin_bp.route('/users')
@admin_required
def users():
    """Manage users"""
    users_list = User.query.all()
    return render_template('admin/users.html', users=users_list)

@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    """Delete a user"""
    user = User.query.get_or_404(user_id)
    
    # Don't allow deleting yourself
    if user.id == g.user_id:
        flash('You cannot delete yourself', 'danger')
        return redirect(url_for('admin.users'))
    
    try:
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting user: {str(e)}', 'danger')
    
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    """Edit a user"""
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        role = request.form.get('role')
        password = request.form.get('password')
        
        # Check if username or email already exists
        username_exists = User.query.filter(User.username == username, User.id != user_id).first()
        email_exists = User.query.filter(User.email == email, User.id != user_id).first()
        
        if username_exists:
            flash('Username already exists', 'danger')
            return redirect(url_for('admin.edit_user', user_id=user_id))
        
        if email_exists:
            flash('Email already exists', 'danger')
            return redirect(url_for('admin.edit_user', user_id=user_id))
        
        # Update user
        user.username = username
        user.email = email
        user.role = role
        
        if password:
            user.set_password(password)
        
        try:
            db.session.commit()
            flash('User updated successfully', 'success')
            return redirect(url_for('admin.users'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating user: {str(e)}', 'danger')
    
    return render_template('admin/users.html', edit_user=user, users=User.query.all())

@admin_bp.route('/workspaces')
@admin_required
def workspaces():
    """Manage workspaces"""
    workspaces_list = Workspace.query.all()
    return render_template('admin/workspaces.html', workspaces=workspaces_list)

@admin_bp.route('/workspaces/create', methods=['GET', 'POST'])
@admin_required
def create_workspace():
    """Create a new workspace"""
    if request.method == 'POST':
        name = request.form.get('name')
        headers = request.form.getlist('headers[]')
        
        if not name:
            flash('Workspace name is required', 'danger')
            return redirect(url_for('admin.workspaces'))
        
        # Create workspace
        workspace = Workspace(
            name=name,
            created_by=g.user_id
        )
        
        try:
            db.session.add(workspace)
            db.session.flush()  # Get workspace ID without committing
            
            # Add all headers (both default and custom)
            order = 0
            for header_name in headers:
                if header_name:  # Make sure header name is not empty
                    is_default = header_name in DEFAULT_LEAD_FIELDS
                    header = WorkspaceHeader(
                        workspace_id=workspace.id,
                        header_name=header_name,
                        is_default=is_default,
                        order=order
                    )
                    db.session.add(header)
                    order += 1
            
            db.session.commit()
            flash('Workspace created successfully', 'success')
            return redirect(url_for('admin.workspaces'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating workspace: {str(e)}', 'danger')
    
    return render_template('admin/workspaces.html', workspaces=Workspace.query.all(), creating=True)

@admin_bp.route('/workspaces/edit/<int:workspace_id>', methods=['GET', 'POST'])
@admin_required
def edit_workspace(workspace_id):
    """Edit a workspace"""
    workspace = Workspace.query.get_or_404(workspace_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        headers = request.form.getlist('headers[]')
        
        if not name:
            flash('Workspace name is required', 'danger')
            return redirect(url_for('admin.workspaces'))
        
        # Update workspace
        workspace.name = name
        
        try:
            # Delete all existing headers (both default and custom)
            WorkspaceHeader.query.filter_by(workspace_id=workspace.id).delete()
            
            # Add all headers (both default and custom)
            order = 0
            for header_name in headers:
                if header_name:  # Make sure header name is not empty
                    is_default = header_name in DEFAULT_LEAD_FIELDS
                    header = WorkspaceHeader(
                        workspace_id=workspace.id,
                        header_name=header_name,
                        is_default=is_default,
                        order=order
                    )
                    db.session.add(header)
                    order += 1
            
            db.session.commit()
            flash('Workspace updated successfully', 'success')
            return redirect(url_for('admin.workspaces'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating workspace: {str(e)}', 'danger')
    
    # Get ALL headers for the workspace, both default and custom
    all_headers = WorkspaceHeader.query.filter_by(workspace_id=workspace.id).order_by(WorkspaceHeader.order).all()
    workspace_headers = [h.header_name for h in all_headers]
    
    # Add any missing default headers for display purposes
    for default_header in DEFAULT_LEAD_FIELDS:
        if default_header not in workspace_headers:
            workspace_headers.append(default_header)
    
    return render_template('admin/workspaces.html', 
                          workspaces=Workspace.query.all(), 
                          edit_workspace=workspace,
                          workspace_headers=workspace_headers,
                          default_headers=DEFAULT_LEAD_FIELDS)

@admin_bp.route('/workspaces/delete/<int:workspace_id>', methods=['POST'])
@admin_required
def delete_workspace(workspace_id):
    """Delete a workspace"""
    workspace = Workspace.query.get_or_404(workspace_id)
    
    try:
        # Check if workspace has leads
        leads_count = Lead.query.filter_by(workspace_id=workspace_id).count()
        if leads_count > 0:
            flash(f'Cannot delete workspace with {leads_count} leads', 'danger')
            return redirect(url_for('admin.workspaces'))
        
        # Delete workspace and headers
        db.session.delete(workspace)
        db.session.commit()
        flash('Workspace deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting workspace: {str(e)}', 'danger')
    
    return redirect(url_for('admin.workspaces'))

@admin_bp.route('/leads')
@admin_required
def leads():
    """View all leads"""
    workspace_id = request.args.get('workspace_id', type=int)
    status = request.args.get('status')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    assigned_to = request.args.get('assigned_to', type=int)
    
    # Build query
    query = Lead.query
    
    # Apply filters
    if workspace_id:
        query = query.filter_by(workspace_id=workspace_id)
    if status:
        query = query.filter_by(status=status)
    if assigned_to:
        query = query.filter_by(assigned_to=assigned_to)
    if start_date:
        try:
            # Try both MM/DD/YYYY and YYYY-MM-DD formats
            try:
                start_date_obj = datetime.strptime(start_date, '%m/%d/%Y')
            except ValueError:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Lead.created_at >= start_date_obj)
        except ValueError:
            pass
    if end_date:
        try:
            # Try both MM/DD/YYYY and YYYY-MM-DD formats
            try:
                end_date_obj = datetime.strptime(end_date, '%m/%d/%Y')
            except ValueError:
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            end_date_obj = end_date_obj.replace(hour=23, minute=59, second=59)
            query = query.filter(Lead.created_at <= end_date_obj)
        except ValueError:
            pass
    
    # Get leads
    leads_list = query.order_by(Lead.created_at.desc()).all()
    
    # Get workspaces and users for filters
    workspaces = Workspace.query.all()
    users = User.query.all()
    
    return render_template('admin/leads.html', 
                          leads=leads_list,
                          workspaces=workspaces,
                          users=users,
                          statuses=LEAD_STATUSES,
                          selected_workspace=workspace_id,
                          selected_status=status,
                          selected_start_date=start_date,
                          selected_end_date=end_date,
                          selected_assigned_to=assigned_to)

@admin_bp.route('/leads/upload', methods=['GET', 'POST'])
@admin_required
def upload_leads():
    """Upload leads from CSV"""
    if request.method == 'POST':
        # Check if mapping form is submitted
        if 'map_headers' in request.form:
            workspace_id = request.form.get('workspace_id', type=int)
            
            if not workspace_id:
                flash('Invalid workspace', 'danger')
                return redirect(url_for('admin.leads'))
            
            # Get workspace
            workspace = Workspace.query.get_or_404(workspace_id)
            
            try:
                # Process the mapping and import
                temp_file_path = '/tmp/temp_csv_file.csv'
                csv_data = pd.read_csv(temp_file_path)
                csv_headers = csv_data.columns.tolist()
                
                # Get header mapping
                header_mapping = {}
                for csv_header in csv_headers:
                    db_header = request.form.get(f'header_{csv_header}')
                    if db_header and db_header != 'ignore':
                        header_mapping[csv_header] = db_header
                
                # Process CSV using the temp file
                success_count, error_count, errors = process_csv_upload(temp_file_path, workspace_id, header_mapping)
                
                if success_count > 0:
                    flash(f'Successfully imported {success_count} leads. {error_count} errors.', 'success')
                else:
                    flash(f'Failed to import leads. {len(errors)} errors.', 'danger')
                    for error in errors:
                        flash(error, 'warning')
                
                return redirect(url_for('admin.leads', workspace_id=workspace_id))
                
            except Exception as e:
                import traceback
                print(f"Error in mapping: {str(e)}")
                print(traceback.format_exc())
                flash(f'Error processing CSV: {str(e)}', 'danger')
                return redirect(url_for('admin.leads'))
                
        # Initial file upload
        file = request.files.get('file')
        workspace_id = request.form.get('workspace_id', type=int)
        
        # Debug information to help troubleshoot
        print(f"File received: {file.filename if file else 'None'}")
        print(f"Workspace ID received: {workspace_id}")
        
        if not file or not workspace_id:
            flash('Please provide both a CSV file and select a workspace', 'danger')
            return redirect(url_for('admin.leads'))
        
        if not file.filename.endswith('.csv'):
            flash('Please upload a CSV file', 'danger')
            return redirect(url_for('admin.leads'))
        
        # Get workspace headers
        workspace = Workspace.query.get_or_404(workspace_id)
        
        # Process file headers
        try:
            # Make a copy of the file data to avoid reading it twice
            temp_file_path = '/tmp/temp_csv_file.csv'
            file.save(temp_file_path)  # Save to temp file
            csv_data = pd.read_csv(temp_file_path)
            csv_headers = csv_data.columns.tolist()
            
            # Render header mapping form - include all headers, both default and custom
            all_headers = WorkspaceHeader.query.filter_by(workspace_id=workspace_id).order_by(WorkspaceHeader.order).all()
            db_headers = [h.header_name for h in all_headers]
            default_headers = [h.header_name for h in all_headers if h.is_default]
            custom_headers = [h.header_name for h in all_headers if not h.is_default]
            
            print(f"Default headers: {default_headers}")
            print(f"Custom headers: {custom_headers}")
            print(f"All headers: {db_headers}")
            
            return render_template('admin/leads.html', 
                                  csv_headers=csv_headers,
                                  db_headers=db_headers,
                                  default_headers=default_headers,
                                  custom_headers=custom_headers,
                                  workspace=workspace,
                                  mapping=True)
        
        except Exception as e:
            import traceback
            print(f"Error in initial upload: {str(e)}")
            print(traceback.format_exc())
            flash(f'Error processing CSV: {str(e)}', 'danger')
            return redirect(url_for('admin.leads'))
    
    # GET request - show upload form
    workspaces = Workspace.query.all()
    return render_template('admin/leads.html', 
                          workspaces=workspaces,
                          upload=True)

@admin_bp.route('/leads/assign', methods=['POST'])
@admin_required
def assign_leads():
    """Assign leads to users"""
    lead_ids = request.form.getlist('lead_ids[]')
    user_id = request.form.get('user_id', type=int)
    
    if not lead_ids or user_id is None:
        flash('Please select leads and a user to assign them to', 'danger')
        return redirect(url_for('admin.leads'))
    
    # Check if user exists
    if user_id > 0 and not User.query.get(user_id):
        flash('Selected user does not exist', 'danger')
        return redirect(url_for('admin.leads'))
    
    try:
        # Update lead assignments
        for lead_id in lead_ids:
            lead = Lead.query.get(lead_id)
            if lead:
                lead.assigned_to = user_id if user_id > 0 else None
        
        db.session.commit()
        
        if user_id > 0:
            user = User.query.get(user_id)
            flash(f'Successfully assigned {len(lead_ids)} leads to {user.username}', 'success')
        else:
            flash(f'Successfully unassigned {len(lead_ids)} leads', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error assigning leads: {str(e)}', 'danger')
    
    return redirect(url_for('admin.leads'))

@admin_bp.route('/leads/export', methods=['POST'])
@admin_required
def export_leads():
    """Export leads to CSV"""
    lead_ids = request.form.getlist('lead_ids[]')
    
    if not lead_ids:
        flash('Please select leads to export', 'danger')
        return redirect(url_for('admin.leads'))
    
    try:
        # Get leads
        leads = Lead.query.filter(Lead.id.in_(lead_ids)).all()
        
        if not leads:
            flash('No leads found to export', 'danger')
            return redirect(url_for('admin.leads'))
        
        # Group leads by workspace
        workspace_leads = {}
        for lead in leads:
            if lead.workspace_id not in workspace_leads:
                workspace_leads[lead.workspace_id] = []
            
            workspace_leads[lead.workspace_id].append(lead)
        
        # If leads from multiple workspaces, export separately
        if len(workspace_leads) > 1:
            flash('Leads from multiple workspaces must be exported separately', 'danger')
            return redirect(url_for('admin.leads'))
        
        # Export CSV
        workspace_id = list(workspace_leads.keys())[0]
        csv_data = export_leads_to_csv(leads, workspace_id)
        
        workspace = Workspace.query.get(workspace_id)
        filename = f"{workspace.name}_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return Response(
            csv_data.getvalue(),
            mimetype='text/csv',
            headers={"Content-Disposition": f"attachment;filename={filename}"}
        )
    except Exception as e:
        flash(f'Error exporting leads: {str(e)}', 'danger')
        return redirect(url_for('admin.leads'))

@admin_bp.route('/leads/delete', methods=['POST'])
@admin_required
def delete_leads():
    """Delete leads"""
    lead_ids = request.form.getlist('lead_ids[]')
    
    if not lead_ids:
        flash('Please select leads to delete', 'danger')
        return redirect(url_for('admin.leads'))
    
    try:
        # Delete leads
        deleted_count = 0
        for lead_id in lead_ids:
            lead = Lead.query.get(lead_id)
            if lead:
                db.session.delete(lead)
                deleted_count += 1
        
        db.session.commit()
        flash(f'Successfully deleted {deleted_count} leads', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting leads: {str(e)}', 'danger')
    
    return redirect(url_for('admin.leads'))

@admin_bp.route('/reports')
@admin_required
def reports():
    """View reports and analytics"""
    # Date range filtering
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    workspace_id = request.args.get('workspace_id', type=int)
    
    try:
        if start_date:
            # Try both MM/DD/YYYY and YYYY-MM-DD formats
            try:
                start_date_obj = datetime.strptime(start_date, '%m/%d/%Y')
            except ValueError:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
        else:
            start_date_obj = None
            
        if end_date:
            # Try both MM/DD/YYYY and YYYY-MM-DD formats
            try:
                end_date_obj = datetime.strptime(end_date, '%m/%d/%Y')
            except ValueError:
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            end_date_obj = end_date_obj.replace(hour=23, minute=59, second=59)
        else:
            end_date_obj = None
    except ValueError:
        start_date_obj = None
        end_date_obj = None
    
    # Get statistics
    stats = get_lead_stats(start_date_obj, end_date_obj, workspace_id)
    
    # Get workspaces for filter
    workspaces = Workspace.query.all()
    
    return render_template('admin/reports.html',
                          stats=stats,
                          workspaces=workspaces,
                          selected_workspace=workspace_id,
                          selected_start_date=start_date,
                          selected_end_date=end_date)
