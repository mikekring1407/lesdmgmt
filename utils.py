import logging
import csv
import io
import os
import json
import gspread
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from models import User, Lead, LeadAssignment, CustomField, db

logger = logging.getLogger(__name__)

def get_gspread_client():
    """Create and return an authorized Google Sheets client"""
    try:
        # Use credentials from environment variables
        creds_json = os.environ.get("GOOGLE_CREDENTIALS", None)
        
        if not creds_json:
            logger.error("Google credentials not found in environment variables")
            return None
            
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_dict(eval(creds_json), scope)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        logger.error(f"Error initializing Google Sheets client: {str(e)}")
        return None

def get_user_data(user):
    """Retrieve and filter lead data for a specific user"""
    try:
        # Get all lead fields for column headers
        column_headers = ["ID", "Name", "Email", "Phone", "Company", "Status", "Source", "Created"]
        
        # Get appropriate leads based on user filter and assignments
        if user.is_admin and (not user.sheet_filter or user.sheet_filter.strip() == ""):
            # Admin with no filter sees all leads
            leads = Lead.query.all()
        elif user.is_admin:
            # Admin with filter - custom filtering
            leads = filter_leads_by_criteria(user.sheet_filter)
        else:
            # Regular user sees only assigned leads
            assigned_leads = LeadAssignment.query.filter_by(
                user_id=user.id, 
                active=True
            ).all()
            lead_ids = [assignment.lead_id for assignment in assigned_leads]
            leads = Lead.query.filter(Lead.id.in_(lead_ids)).all()
            
        # Format data for display
        data = []
        for lead in leads:
            # Basic lead data
            lead_data = [
                lead.id,
                lead.name or "",
                lead.email or "",
                lead.phone or "",
                lead.company or "",
                lead.status or "New",
                lead.source or "",
                lead.created_at.strftime("%Y-%m-%d %H:%M") if lead.created_at else ""
            ]
            data.append(lead_data)
            
        if not data:
            return {"headers": column_headers, "data": []}
            
        return {"headers": column_headers, "data": data}
            
    except Exception as e:
        logger.error(f"Error fetching lead data: {str(e)}")
        raise

def filter_leads_by_criteria(filter_criteria):
    """Filter leads based on criteria string"""
    try:
        # Parse the filter - can be in format "column_name:value" or just "value"
        filter_parts = filter_criteria.split(":")
        
        if len(filter_parts) == 2:
            # Format is "column_name:value"
            column_name, filter_value = filter_parts
            
            # Map column name to model field
            if column_name.lower() == 'name':
                return Lead.query.filter(Lead.name.ilike(f'%{filter_value}%')).all()
            elif column_name.lower() == 'email':
                return Lead.query.filter(Lead.email.ilike(f'%{filter_value}%')).all()
            elif column_name.lower() == 'phone':
                return Lead.query.filter(Lead.phone.ilike(f'%{filter_value}%')).all()
            elif column_name.lower() == 'company':
                return Lead.query.filter(Lead.company.ilike(f'%{filter_value}%')).all()
            elif column_name.lower() == 'status':
                return Lead.query.filter(Lead.status.ilike(f'%{filter_value}%')).all()
            elif column_name.lower() == 'source':
                return Lead.query.filter(Lead.source.ilike(f'%{filter_value}%')).all()
            else:
                # For other columns, try to search in the extra_data JSON field
                return Lead.query.filter(
                    Lead.extra_data.cast(db.String).ilike(f'%"{column_name}": "%{filter_value}%"%')
                ).all()
        else:
            # Format is just "value" - search across multiple fields
            filter_value = filter_parts[0]
            return Lead.query.filter(
                db.or_(
                    Lead.name.ilike(f'%{filter_value}%'),
                    Lead.email.ilike(f'%{filter_value}%'),
                    Lead.phone.ilike(f'%{filter_value}%'),
                    Lead.company.ilike(f'%{filter_value}%'),
                    Lead.source.ilike(f'%{filter_value}%'),
                    Lead.notes.ilike(f'%{filter_value}%')
                )
            ).all()
            
    except Exception as e:
        logger.error(f"Error filtering leads: {str(e)}")
        return []

def get_all_users():
    """Get all users from the database"""
    return User.query.all()

def save_user(form):
    """Create or update a user from form data"""
    try:
        if form.user_id.data:
            # Update existing user
            user = User.query.get(int(form.user_id.data))
            user.username = form.username.data
            user.sheet_filter = form.sheet_filter.data
            user.is_admin = form.is_admin.data
            
            # Only update password if provided
            if form.password.data:
                user.set_password(form.password.data)
        else:
            # Create new user
            user = User(
                username=form.username.data,
                sheet_filter=form.sheet_filter.data,
                is_admin=form.is_admin.data
            )
            user.set_password(form.password.data)
            db.session.add(user)
            
        db.session.commit()
        return user
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving user: {str(e)}")
        raise

def save_lead(form):
    """Create or update a lead from form data"""
    try:
        if form.lead_id.data:
            # Update existing lead
            lead = Lead.query.get(int(form.lead_id.data))
            lead.name = form.name.data
            lead.email = form.email.data
            lead.phone = form.phone.data
            lead.company = form.company.data
            lead.status = form.status.data
            lead.source = form.source.data
            lead.notes = form.notes.data
            lead.updated_at = datetime.utcnow()
        else:
            # Create new lead
            lead = Lead(
                name=form.name.data,
                email=form.email.data,
                phone=form.phone.data,
                company=form.company.data,
                status=form.status.data,
                source=form.source.data,
                notes=form.notes.data
            )
            db.session.add(lead)
            
        db.session.commit()
        return lead
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving lead: {str(e)}")
        raise

def assign_lead(lead_id, user_id):
    """Assign a lead to a user"""
    try:
        # Deactivate any existing assignments for this lead
        existing_assignments = LeadAssignment.query.filter_by(
            lead_id=lead_id, 
            active=True
        ).all()
        
        for assignment in existing_assignments:
            assignment.active = False
            
        # Create new assignment
        new_assignment = LeadAssignment(
            lead_id=lead_id,
            user_id=user_id,
            active=True
        )
        
        db.session.add(new_assignment)
        db.session.commit()
        return new_assignment
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error assigning lead: {str(e)}")
        raise

def import_from_csv(file_stream, has_headers=True):
    """Import leads from a CSV file"""
    try:
        # Read the CSV file
        content = file_stream.read().decode('utf-8')
        csv_data = list(csv.reader(io.StringIO(content)))
        
        if not csv_data:
            return 0
            
        # Get headers if present, otherwise use column indices
        headers = csv_data[0] if has_headers else None
        data_rows = csv_data[1:] if has_headers else csv_data
        
        leads_imported = 0
        
        for row in data_rows:
            # Skip empty rows
            if not any(row):
                continue
                
            # Create a lead object with basic fields
            lead = Lead()
            
            # Map CSV columns to lead fields if headers are present
            if headers:
                extra_data = {}
                
                for i, value in enumerate(row):
                    # Skip empty values
                    if not value.strip():
                        continue
                        
                    header = headers[i].lower() if i < len(headers) else f"column_{i}"
                    
                    # Map known fields directly to model attributes
                    if header == 'name':
                        lead.name = value
                    elif header == 'email':
                        lead.email = value
                    elif header == 'phone':
                        lead.phone = value
                    elif header == 'company':
                        lead.company = value
                    elif header == 'status':
                        lead.status = value
                    elif header == 'source':
                        lead.source = value
                    elif header == 'notes':
                        lead.notes = value
                    else:
                        # Store other columns in extra_data
                        extra_data[header] = value
                
                # Set extra_data if we have any unmapped columns
                if extra_data:
                    lead.extra_data = extra_data
            else:
                # No headers, map by position with reasonable defaults
                if len(row) > 0: lead.name = row[0]
                if len(row) > 1: lead.email = row[1]
                if len(row) > 2: lead.phone = row[2]
                if len(row) > 3: lead.company = row[3]
                if len(row) > 4: lead.status = row[4]
                if len(row) > 5: lead.source = row[5]
                if len(row) > 6: lead.notes = row[6]
                
                # Store any remaining columns in extra_data
                if len(row) > 7:
                    extra_data = {}
                    for i in range(7, len(row)):
                        extra_data[f"column_{i}"] = row[i]
                    lead.extra_data = extra_data
            
            # Set status to "New" if not provided
            if not lead.status:
                lead.status = "New"
                
            # Add and commit the lead
            db.session.add(lead)
            leads_imported += 1
            
        # Commit all changes
        db.session.commit()
        return leads_imported
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error importing from CSV: {str(e)}")
        raise

def import_from_google_sheet(client, spreadsheet_id, sheet_name=None, has_headers=True):
    """Import leads from a Google Sheet"""
    try:
        # Open the spreadsheet
        spreadsheet = client.open_by_key(spreadsheet_id)
        
        # Get the specified sheet or the first sheet
        worksheet = spreadsheet.worksheet(sheet_name) if sheet_name else spreadsheet.sheet1
        
        # Get all data
        sheet_data = worksheet.get_all_values()
        
        if not sheet_data:
            return 0
            
        # Get headers if present, otherwise use column indices
        headers = sheet_data[0] if has_headers else None
        data_rows = sheet_data[1:] if has_headers else sheet_data
        
        # Use the CSV import function with the sheet data
        csv_file = io.StringIO()
        csv_writer = csv.writer(csv_file)
        
        if headers:
            csv_writer.writerow(headers)
            
        csv_writer.writerows(data_rows)
        
        # Reset the StringIO position
        csv_file.seek(0)
        
        # Import using the CSV function
        return import_from_csv(csv_file, has_headers)
    except Exception as e:
        logger.error(f"Error importing from Google Sheet: {str(e)}")
        raise

def save_custom_field(form):
    """Create or update a custom field definition"""
    try:
        if form.field_id.data:
            # Update existing field
            field = CustomField.query.get(int(form.field_id.data))
            field.name = form.name.data
            field.label = form.label.data
            field.field_type = form.field_type.data
            field.required = form.required.data
            field.active = form.active.data
            
            # Process options for select/dropdown fields
            if form.field_type.data == 'select' and form.options.data:
                options_list = [opt.strip() for opt in form.options.data.split('\n') if opt.strip()]
                field.options = json.dumps(options_list)
            else:
                field.options = None
                
            # Set order if provided
            if form.order.data:
                try:
                    field.order = int(form.order.data)
                except ValueError:
                    field.order = 0
        else:
            # Create new field
            # Process options for select/dropdown fields
            options_json = None
            if form.field_type.data == 'select' and form.options.data:
                options_list = [opt.strip() for opt in form.options.data.split('\n') if opt.strip()]
                options_json = json.dumps(options_list)
                
            # Set order if provided
            order = 0
            if form.order.data:
                try:
                    order = int(form.order.data)
                except ValueError:
                    order = 0
                    
            field = CustomField(
                name=form.name.data,
                label=form.label.data,
                field_type=form.field_type.data,
                required=form.required.data,
                options=options_json,
                order=order,
                active=form.active.data
            )
            db.session.add(field)
            
        db.session.commit()
        return field
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving custom field: {str(e)}")
        raise

def get_custom_fields(active_only=True):
    """Get all custom field definitions, optionally filtered by active status"""
    if active_only:
        return CustomField.query.filter_by(active=True).order_by(CustomField.order).all()
    return CustomField.query.order_by(CustomField.order).all()

def get_lead_data_for_export(user=None, include_custom_fields=True, status_filter=None, export_type='all'):
    """Get lead data formatted for CSV export, optionally filtered by user assignment"""
    try:
        # Start with basic fields as headers
        headers = ['ID', 'Name', 'Email', 'Phone', 'Company', 'Status', 'Source', 'Notes', 'Created', 'Updated', 'Assigned To']
        
        # Add custom field headers if requested
        custom_field_headers = []
        if include_custom_fields:
            custom_fields = get_custom_fields(active_only=True)
            custom_field_headers = [cf.label for cf in custom_fields]
            headers.extend(custom_field_headers)
            
        # Build query with filters
        query = Lead.query
        
        # Apply status filter if provided
        if status_filter:
            query = query.filter(Lead.status == status_filter)
        
        # Filter by assignment if requested
        if export_type == 'assigned' and user:
            if user.is_admin:
                # Admin exporting assigned leads only - all assigned leads
                assigned_lead_ids = db.session.query(LeadAssignment.lead_id).filter(
                    LeadAssignment.active == True
                ).subquery()
                query = query.filter(Lead.id.in_(assigned_lead_ids))
            else:
                # Regular user exporting their assigned leads only
                assigned_lead_ids = db.session.query(LeadAssignment.lead_id).filter(
                    LeadAssignment.user_id == user.id,
                    LeadAssignment.active == True
                ).subquery()
                query = query.filter(Lead.id.in_(assigned_lead_ids))
        elif export_type == 'unassigned':
            # Only unassigned leads
            assigned_lead_ids = db.session.query(LeadAssignment.lead_id).filter(
                LeadAssignment.active == True
            ).subquery()
            query = query.filter(~Lead.id.in_(assigned_lead_ids))
        elif not user.is_admin and user:
            # Regular user can only export their assigned leads regardless of type
            assigned_lead_ids = db.session.query(LeadAssignment.lead_id).filter(
                LeadAssignment.user_id == user.id,
                LeadAssignment.active == True
            ).subquery()
            query = query.filter(Lead.id.in_(assigned_lead_ids))
        
        # Get leads with custom filters applied
        leads = query.order_by(Lead.created_at.desc()).all()
        
        # Format data for CSV export
        rows = []
        for lead in leads:
            # Get assignment info
            current_assignment = lead.current_assignment()
            assigned_to = current_assignment.assigned_user.username if current_assignment else "Unassigned"
            
            # Format dates
            created_at = lead.created_at.strftime("%Y-%m-%d %H:%M:%S") if lead.created_at else ""
            updated_at = lead.updated_at.strftime("%Y-%m-%d %H:%M:%S") if lead.updated_at else ""
            
            # Add basic lead data
            row = [
                lead.id,
                lead.name or "",
                lead.email or "",
                lead.phone or "",
                lead.company or "",
                lead.status or "New",
                lead.source or "",
                lead.notes or "",
                created_at,
                updated_at,
                assigned_to
            ]
            
            # Add custom field data if requested
            if include_custom_fields and custom_fields:
                for field in custom_fields:
                    value = lead.get_custom_field_value(field.name) or ""
                    row.append(value)
            
            rows.append(row)
        
        return {
            "headers": headers,
            "rows": rows
        }
    except Exception as e:
        logger.error(f"Error preparing data for export: {str(e)}")
        raise

def generate_csv_file(headers, rows):
    """Generate a CSV file from headers and rows"""
    try:
        csv_file = io.StringIO()
        writer = csv.writer(csv_file)
        
        # Write headers
        writer.writerow(headers)
        
        # Write data rows
        writer.writerows(rows)
        
        # Reset to start of file
        csv_file.seek(0)
        return csv_file
    except Exception as e:
        logger.error(f"Error generating CSV file: {str(e)}")
        raise
