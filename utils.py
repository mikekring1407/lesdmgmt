import pandas as pd
from datetime import datetime
from io import StringIO
import csv
from flask import g
from app import db
from models import Lead, LeadCustomField, WorkspaceHeader, User, Workspace

def get_workspace_headers(workspace_id):
    """Get all headers for a workspace"""
    headers = WorkspaceHeader.query.filter_by(workspace_id=workspace_id).order_by(WorkspaceHeader.order).all()
    return headers

def process_csv_upload(file_data, workspace_id, header_mapping):
    """Process CSV upload with custom header mapping
    
    Args:
        file_data: The CSV file data
        workspace_id: The workspace ID to associate leads with
        header_mapping: Dictionary mapping CSV headers to database fields
    
    Returns:
        tuple: (success_count, error_count, errors)
    """
    success_count = 0
    error_count = 0
    errors = []
    
    try:
        # Read CSV data - handle file paths, file objects, and bytes
        if isinstance(file_data, str):
            # It's a file path
            df = pd.read_csv(file_data)
        elif hasattr(file_data, 'read'):
            # It's a file-like object
            df = pd.read_csv(file_data)
        else:
            # It's already read bytes
            csv_data = file_data.decode('utf-8') if isinstance(file_data, bytes) else file_data
            df = pd.read_csv(StringIO(csv_data))
        
        # Get workspace headers
        workspace_headers = {h.header_name: h for h in get_workspace_headers(workspace_id)}
        
        # Process each row as a separate transaction
        for index, row in df.iterrows():
            # Start a new transaction for each lead
            db.session.begin_nested()
            
            try:
                # Create new lead with default fields
                lead = Lead(
                    workspace_id=workspace_id,
                    created_at=datetime.utcnow()
                )
                
                # Map CSV columns to lead fields based on header_mapping
                for csv_header, db_field in header_mapping.items():
                    if csv_header in row and db_field in ['first_name', 'last_name', 'email', 'phone', 'city', 'state', 'status', 'bank']:
                        # Handle NaN values
                        if pd.isna(row[csv_header]):
                            setattr(lead, db_field, None)
                        else:
                            setattr(lead, db_field, row[csv_header])
                    elif csv_header in row and db_field == 'date':
                        try:
                            # Try to parse the date
                            date_str = str(row[csv_header])
                            if pd.isna(row[csv_header]) or date_str.lower() in ['nat', 'nan', '', 'none', 'null']:
                                lead.date = None
                            else:
                                date_val = pd.to_datetime(row[csv_header]).date()
                                lead.date = date_val
                        except:
                            # If date parsing fails, set to None
                            lead.date = None
                
                # Add to session
                db.session.add(lead)
                db.session.flush()  # Get the lead ID without committing transaction
                
                # Process custom fields
                for csv_header, header_name in header_mapping.items():
                    if csv_header in row and header_name in workspace_headers and header_name not in ['first_name', 'last_name', 'email', 'phone', 'city', 'state', 'status', 'bank', 'date']:
                        # Create custom field
                        custom_field = LeadCustomField(
                            lead_id=lead.id,
                            header_id=workspace_headers[header_name].id,
                            value=str(row[csv_header]) if not pd.isna(row[csv_header]) else None
                        )
                        db.session.add(custom_field)
                
                success_count += 1
                
            except Exception as e:
                error_count += 1
                import traceback
                error_detail = traceback.format_exc()
                print(f"Error on row {index+1}: {str(e)}\n{error_detail}")
                errors.append(f"Error processing row {index+1}: {str(e)}")
                # Rollback this record but continue with others
                db.session.rollback()
        
        if success_count > 0:
            try:
                # Commit all successful leads
                db.session.commit()
            except Exception as e:
                # If commit fails, rollback and report error
                db.session.rollback()
                import traceback
                error_detail = traceback.format_exc()
                print(f"Error committing batch: {str(e)}\n{error_detail}")
                return 0, error_count + success_count, [f"Database error: {str(e)}"] + errors
        
        return success_count, error_count, errors
        
    except Exception as e:
        # Rollback on any error
        db.session.rollback()
        import traceback
        error_msg = f"Error processing CSV: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)  # Log to console for debugging
        return 0, 1, [f"Error processing CSV: {str(e)}"]

def export_leads_to_csv(leads, workspace_id):
    """Export leads to CSV based on workspace headers
    
    Args:
        leads: List of Lead objects to export
        workspace_id: Workspace ID to get headers from
    
    Returns:
        StringIO object with CSV data
    """
    headers = get_workspace_headers(workspace_id)
    header_names = [h.header_name for h in headers]
    
    # Create CSV output
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header row
    writer.writerow(header_names)
    
    # Write data rows
    for lead in leads:
        row = []
        for header in headers:
            if header.header_name == 'first_name':
                row.append(lead.first_name or '')
            elif header.header_name == 'last_name':
                row.append(lead.last_name or '')
            elif header.header_name == 'email':
                row.append(lead.email or '')
            elif header.header_name == 'phone':
                row.append(lead.phone or '')
            elif header.header_name == 'city':
                row.append(lead.city or '')
            elif header.header_name == 'state':
                row.append(lead.state or '')
            elif header.header_name == 'status':
                row.append(lead.status or '')
            elif header.header_name == 'bank':
                row.append(lead.bank or '')
            elif header.header_name == 'date':
                row.append(lead.date.strftime('%m/%d/%Y') if lead.date else '')
            elif header.header_name == 'assigned_to':
                user = User.query.get(lead.assigned_to) if lead.assigned_to else None
                row.append(user.username if user else '')
            elif header.header_name == 'workspace':
                workspace = Workspace.query.get(lead.workspace_id)
                row.append(workspace.name if workspace else '')
            else:
                # Look for custom field
                custom_field = next((cf for cf in lead.custom_fields if cf.header.header_name == header.header_name), None)
                row.append(custom_field.value if custom_field else '')
        
        writer.writerow(row)
    
    output.seek(0)
    return output

def get_lead_stats(start_date=None, end_date=None, workspace_id=None):
    """Get lead statistics
    
    Args:
        start_date: Optional start date filter
        end_date: Optional end date filter
        workspace_id: Optional workspace filter
    
    Returns:
        Dictionary with lead statistics
    """
    query = Lead.query
    
    # Apply filters
    if start_date:
        query = query.filter(Lead.created_at >= start_date)
    if end_date:
        query = query.filter(Lead.created_at <= end_date)
    if workspace_id:
        query = query.filter(Lead.workspace_id == workspace_id)
    
    # Total leads
    total_leads = query.count()
    
    # Assigned/unassigned counts
    assigned_count = query.filter(Lead.assigned_to.isnot(None)).count()
    unassigned_count = total_leads - assigned_count
    
    # Status breakdown
    status_breakdown = {}
    for status in ['New', 'Contacted', 'Qualified', 'Proposal', 'Negotiation', 'Won', 'Lost']:
        status_breakdown[status] = query.filter(Lead.status == status).count()
    
    # Workspace breakdown (if not filtered by workspace)
    workspace_breakdown = {}
    if not workspace_id:
        workspaces = Workspace.query.all()
        for workspace in workspaces:
            workspace_breakdown[workspace.name] = query.filter(Lead.workspace_id == workspace.id).count()
    
    # Leads by user
    user_breakdown = {}
    users = User.query.all()
    for user in users:
        user_breakdown[user.username] = query.filter(Lead.assigned_to == user.id).count()
    
    return {
        'total': total_leads,
        'assigned': assigned_count,
        'unassigned': unassigned_count,
        'status_breakdown': status_breakdown,
        'workspace_breakdown': workspace_breakdown,
        'user_breakdown': user_breakdown
    }
