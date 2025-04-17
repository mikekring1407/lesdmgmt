from flask import Blueprint, render_template, request, redirect, url_for, flash, g, Response
from datetime import datetime
from app import db
from models import Lead, User, Workspace, WorkspaceHeader
from auth import login_required
from utils import export_leads_to_csv

user_bp = Blueprint('user', __name__, url_prefix='/user')

@user_bp.route('/leads')
@login_required
def leads():
    """View user's assigned leads"""
    # Only show leads assigned to this user
    user_id = g.user_id
    
    # Get filter values
    date_filter = request.args.get('date')
    
    # Build query
    query = Lead.query.filter_by(assigned_to=user_id)
    
    # Apply date filter if provided
    if date_filter:
        try:
            # Try both MM/DD/YYYY and YYYY-MM-DD formats
            try:
                date_obj = datetime.strptime(date_filter, '%m/%d/%Y')
            except ValueError:
                date_obj = datetime.strptime(date_filter, '%Y-%m-%d')
            # Filter for a single day
            next_day = date_obj.replace(hour=23, minute=59, second=59)
            query = query.filter(Lead.created_at >= date_obj, Lead.created_at <= next_day)
        except ValueError:
            pass
    
    # Get leads
    leads_list = query.order_by(Lead.created_at.desc()).all()
    
    # No need to pass workspaces to the template since we removed the workspace column
    return render_template('user/leads.html', 
                          leads=leads_list,
                          selected_date=date_filter)

@user_bp.route('/leads/export', methods=['POST'])
@login_required
def export_leads():
    """Export user's assigned leads to CSV"""
    lead_ids = request.form.getlist('lead_ids[]')
    user_id = g.user_id
    
    if not lead_ids:
        flash('Please select leads to export', 'danger')
        return redirect(url_for('user.leads'))
    
    try:
        # Get leads that belong to this user
        leads = Lead.query.filter(Lead.id.in_(lead_ids), Lead.assigned_to == user_id).all()
        
        if not leads:
            flash('No leads found to export', 'danger')
            return redirect(url_for('user.leads'))
        
        # Group leads by workspace
        workspace_leads = {}
        for lead in leads:
            if lead.workspace_id not in workspace_leads:
                workspace_leads[lead.workspace_id] = []
            
            workspace_leads[lead.workspace_id].append(lead)
        
        # If leads from multiple workspaces, export separately
        if len(workspace_leads) > 1:
            flash('Leads from multiple workspaces must be exported separately', 'danger')
            return redirect(url_for('user.leads'))
        
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
        return redirect(url_for('user.leads'))
