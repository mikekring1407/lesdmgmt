import os
import logging
import io
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, Response
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from models import User, Lead, LeadAssignment, CustomField, db
from forms import LoginForm, UserForm, LeadForm, AssignLeadForm, CSVUploadForm, ImportSheetForm, CustomFieldForm, CSVExportForm
from utils import (get_user_data, get_all_users, save_user, save_lead, assign_lead, 
                  import_from_csv, import_from_google_sheet, get_gspread_client, 
                  save_custom_field, get_custom_fields, get_lead_data_for_export, generate_csv_file)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key-for-development")

# Configure PostgreSQL database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///users.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize SQLAlchemy with app
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Google Sheets API setup is now in utils.py

# Remove duplicated imports that are now at the top of the file

# Routes
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and user.check_password(form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        # Get user-specific data from database
        user_data = get_user_data(current_user)
        
        if user_data is None:
            flash("No data found for your account", "warning")
            return render_template('dashboard.html', user=current_user, data=[], headers=[])
            
        return render_template('dashboard.html', user=current_user, data=user_data['data'], headers=user_data['headers'])
        
    except Exception as e:
        logger.error(f"Error fetching user data: {str(e)}")
        flash("Error retrieving your data", "danger")
        return render_template('error.html', message=f"Error retrieving your data: {str(e)}")

# USER MANAGEMENT ROUTES
@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if not current_user.is_admin:
        flash("You don't have permission to access the admin panel", "danger")
        return redirect(url_for('dashboard'))
    
    # Default to user management tab
    return redirect(url_for('admin_users'))

@app.route('/admin/users', methods=['GET', 'POST'])
@login_required
def admin_users():
    if not current_user.is_admin:
        flash("You don't have permission to access the admin panel", "danger")
        return redirect(url_for('dashboard'))
    
    form = UserForm()
    
    if form.validate_on_submit():
        # Check if user already exists
        existing_user = User.query.filter_by(username=form.username.data).first()
        
        if existing_user and form.user_id.data == '':
            flash(f"User '{form.username.data}' already exists", "danger")
        else:
            # Create or update user
            save_user(form)
            flash("User saved successfully", "success")
            return redirect(url_for('admin_users'))
    
    users = User.query.all()
    return render_template('admin_users.html', users=users, form=form, edit_mode=False)

@app.route('/admin/users/edit/<int:user_id>', methods=['GET'])
@login_required
def edit_user(user_id):
    if not current_user.is_admin:
        flash("You don't have permission to access the admin panel", "danger")
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    form = UserForm(
        user_id=user.id,
        username=user.username,
        password="",  # Don't send password to the form
        sheet_filter=user.sheet_filter,
        is_admin=user.is_admin
    )
    
    users = User.query.all()
    return render_template('admin_users.html', users=users, form=form, edit_mode=True)

@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        flash("You don't have permission to access the admin panel", "danger")
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    # Don't allow deleting yourself
    if user.id == current_user.id:
        flash("You cannot delete your own account", "danger")
        return redirect(url_for('admin_users'))
    
    try:
        db.session.delete(user)
        db.session.commit()
        flash(f"User '{user.username}' deleted successfully", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting user: {str(e)}", "danger")
    
    return redirect(url_for('admin_users'))

# LEAD MANAGEMENT ROUTES
@app.route('/admin/leads', methods=['GET'])
@login_required
def admin_leads():
    if not current_user.is_admin:
        flash("You don't have permission to access the admin panel", "danger")
        return redirect(url_for('dashboard'))
    
    # Get all leads
    leads = Lead.query.order_by(Lead.created_at.desc()).all()
    
    return render_template('admin_leads.html', leads=leads)

@app.route('/admin/leads/add', methods=['GET', 'POST'])
@login_required
def add_lead():
    if not current_user.is_admin:
        flash("You don't have permission to access the admin panel", "danger")
        return redirect(url_for('dashboard'))
    
    form = LeadForm()
    
    if form.validate_on_submit():
        try:
            lead = save_lead(form)
            flash(f"Lead '{lead.name}' added successfully", "success")
            return redirect(url_for('admin_leads'))
        except Exception as e:
            logger.error(f"Error adding lead: {str(e)}")
            flash(f"Error adding lead: {str(e)}", "danger")
    
    return render_template('lead_form.html', form=form, title="Add New Lead")

@app.route('/admin/leads/edit/<int:lead_id>', methods=['GET', 'POST'])
@login_required
def edit_lead(lead_id):
    if not current_user.is_admin:
        flash("You don't have permission to access the admin panel", "danger")
        return redirect(url_for('dashboard'))
    
    lead = Lead.query.get_or_404(lead_id)
    
    form = LeadForm(
        lead_id=lead.id,
        name=lead.name,
        email=lead.email,
        phone=lead.phone,
        company=lead.company,
        status=lead.status,
        source=lead.source,
        notes=lead.notes
    )
    
    if form.validate_on_submit():
        try:
            lead = save_lead(form)
            flash(f"Lead '{lead.name}' updated successfully", "success")
            return redirect(url_for('admin_leads'))
        except Exception as e:
            logger.error(f"Error updating lead: {str(e)}")
            flash(f"Error updating lead: {str(e)}", "danger")
    
    return render_template('lead_form.html', form=form, lead=lead, title="Edit Lead")

@app.route('/admin/leads/delete/<int:lead_id>', methods=['POST'])
@login_required
def delete_lead(lead_id):
    if not current_user.is_admin:
        flash("You don't have permission to access the admin panel", "danger")
        return redirect(url_for('dashboard'))
    
    lead = Lead.query.get_or_404(lead_id)
    
    try:
        db.session.delete(lead)
        db.session.commit()
        flash(f"Lead deleted successfully", "success")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting lead: {str(e)}")
        flash(f"Error deleting lead: {str(e)}", "danger")
    
    return redirect(url_for('admin_leads'))

@app.route('/admin/leads/assign/<int:lead_id>', methods=['GET', 'POST'])
@login_required
def assign_lead_route(lead_id):
    if not current_user.is_admin:
        flash("You don't have permission to access the admin panel", "danger")
        return redirect(url_for('dashboard'))
    
    lead = Lead.query.get_or_404(lead_id)
    
    # Get all non-admin users for assignment
    users = User.query.filter_by(is_admin=False).all()
    # Also include admins
    admins = User.query.filter_by(is_admin=True).all()
    all_users = admins + users
    
    # Pre-select current assignment if it exists
    current_assignment = lead.current_assignment
    currently_assigned_to = current_assignment.assigned_user.id if current_assignment else None
    
    form = AssignLeadForm()
    form.user_id.choices = [(u.id, u.username) for u in all_users]
    
    if currently_assigned_to:
        form.user_id.default = currently_assigned_to
        form.process()
    
    if form.validate_on_submit():
        try:
            assign_lead(lead.id, form.user_id.data)
            assigned_user = User.query.get(form.user_id.data)
            flash(f"Lead assigned to {assigned_user.username} successfully", "success")
            return redirect(url_for('admin_leads'))
        except Exception as e:
            logger.error(f"Error assigning lead: {str(e)}")
            flash(f"Error assigning lead: {str(e)}", "danger")
    
    return render_template('assign_lead.html', form=form, lead=lead)

# DATA IMPORT ROUTES
@app.route('/admin/imports', methods=['GET'])
@login_required
def admin_imports():
    if not current_user.is_admin:
        flash("You don't have permission to access the admin panel", "danger")
        return redirect(url_for('dashboard'))
    
    csv_form = CSVUploadForm()
    sheet_form = ImportSheetForm()
    export_form = CSVExportForm()
    
    return render_template('admin_imports.html', csv_form=csv_form, sheet_form=sheet_form, export_form=export_form)

@app.route('/admin/imports/csv', methods=['POST'])
@login_required
def import_csv():
    if not current_user.is_admin:
        flash("You don't have permission to access the admin panel", "danger")
        return redirect(url_for('dashboard'))
    
    form = CSVUploadForm()
    
    if form.validate_on_submit():
        try:
            # Process uploaded file
            file = form.file.data
            has_headers = form.has_headers.data
            
            leads_imported = import_from_csv(file, has_headers)
            
            flash(f"Successfully imported {leads_imported} leads from CSV", "success")
        except Exception as e:
            logger.error(f"Error importing CSV: {str(e)}")
            flash(f"Error importing CSV: {str(e)}", "danger")
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{error}", "danger")
    
    return redirect(url_for('admin_imports'))

@app.route('/admin/imports/sheet', methods=['POST'])
@login_required
def import_sheet():
    if not current_user.is_admin:
        flash("You don't have permission to access the admin panel", "danger")
        return redirect(url_for('dashboard'))
    
    form = ImportSheetForm()
    
    if form.validate_on_submit():
        try:
            # Get Google Sheets client
            client = get_gspread_client()
            if not client:
                flash("Error connecting to Google Sheets", "danger")
                return redirect(url_for('admin_imports'))
            
            spreadsheet_id = form.spreadsheet_id.data
            sheet_name = form.sheet_name.data if form.sheet_name.data else None
            has_headers = form.has_headers.data
            
            leads_imported = import_from_google_sheet(
                client, 
                spreadsheet_id, 
                sheet_name,
                has_headers
            )
            
            flash(f"Successfully imported {leads_imported} leads from Google Sheet", "success")
        except Exception as e:
            logger.error(f"Error importing from Google Sheet: {str(e)}")
            flash(f"Error importing from Google Sheet: {str(e)}", "danger")
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{error}", "danger")
    
    return redirect(url_for('admin_imports'))

# CUSTOM FIELD MANAGEMENT ROUTES
@app.route('/admin/fields', methods=['GET', 'POST'])
@login_required
def admin_fields():
    if not current_user.is_admin:
        flash("You don't have permission to access the admin panel", "danger")
        return redirect(url_for('dashboard'))
    
    form = CustomFieldForm()
    
    if form.validate_on_submit():
        try:
            field = save_custom_field(form)
            flash(f"Custom field '{field.label}' saved successfully", "success")
            return redirect(url_for('admin_fields'))
        except Exception as e:
            logger.error(f"Error saving custom field: {str(e)}")
            flash(f"Error saving custom field: {str(e)}", "danger")
    
    # Get all fields
    fields = get_custom_fields(active_only=False)
    
    return render_template('admin_fields.html', fields=fields, form=form, edit_mode=False)

@app.route('/admin/fields/edit/<int:field_id>', methods=['GET'])
@login_required
def edit_field(field_id):
    if not current_user.is_admin:
        flash("You don't have permission to access the admin panel", "danger")
        return redirect(url_for('dashboard'))
    
    field = CustomField.query.get_or_404(field_id)
    
    # Prepare form with field data
    form = CustomFieldForm(
        field_id=field.id,
        name=field.name,
        label=field.label,
        field_type=field.field_type,
        required=field.required,
        order=field.order,
        active=field.active
    )
    
    # Load options for select fields
    if field.field_type == 'select' and field.options:
        try:
            options_list = json.loads(field.options)
            form.options.data = '\n'.join(options_list)
        except:
            pass
    
    # Get all fields
    fields = get_custom_fields(active_only=False)
    
    return render_template('admin_fields.html', fields=fields, form=form, edit_mode=True)

@app.route('/admin/fields/delete/<int:field_id>', methods=['POST'])
@login_required
def delete_field(field_id):
    if not current_user.is_admin:
        flash("You don't have permission to access the admin panel", "danger")
        return redirect(url_for('dashboard'))
    
    field = CustomField.query.get_or_404(field_id)
    
    try:
        db.session.delete(field)
        db.session.commit()
        flash(f"Custom field '{field.label}' deleted successfully", "success")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting custom field: {str(e)}")
        flash(f"Error deleting custom field: {str(e)}", "danger")
    
    return redirect(url_for('admin_fields'))

# CSV EXPORT ROUTES
@app.route('/export/csv', methods=['GET', 'POST'])
@login_required
def export_csv():
    try:
        # Default to exporting all fields
        include_custom_fields = True
        export_type = 'all'
        status_filter = None
        
        # Handle form submission if it exists
        if request.method == 'POST':
            form = CSVExportForm()
            if form.validate_on_submit():
                include_custom_fields = form.include_all_fields.data
                
                # Additional filters can be added here if needed
                if 'export_type' in request.form:
                    export_type = request.form['export_type']
                
                if 'status_filter' in request.form and request.form['status_filter']:
                    status_filter = request.form['status_filter']
        
        # Get data for export
        export_data = get_lead_data_for_export(
            user=current_user,
            include_custom_fields=include_custom_fields,
            status_filter=status_filter,
            export_type=export_type
        )
        
        if not export_data or not export_data.get('rows'):
            flash("No data available for export", "warning")
            return redirect(url_for('dashboard'))
        
        # Generate CSV file
        csv_file = generate_csv_file(export_data['headers'], export_data['rows'])
        
        # Generate a filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"leads_export_{timestamp}.csv"
        
        # Return the CSV file as a download
        return send_file(
            csv_file,
            as_attachment=True,
            download_name=filename,
            mimetype='text/csv'
        )
    except Exception as e:
        logger.error(f"Error exporting CSV: {str(e)}")
        flash(f"Error exporting CSV: {str(e)}", "danger")
        return redirect(url_for('dashboard'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', message="Page not found"), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', message="Internal server error"), 500

# Create database tables on application startup
def create_tables():
    with app.app_context():
        try:
            db.create_all()
            
            # Create admin user if no users exist
            if User.query.count() == 0:
                admin = User(
                    username="admin",
                    sheet_filter="",  # Admin sees all data
                    is_admin=True
                )
                admin.set_password("admin")  # Default password, should be changed immediately
                db.session.add(admin)
                db.session.commit()
                logger.info("Created default admin user")
        except Exception as e:
            logger.error(f"Error creating database tables: {str(e)}")

# Call create_tables on startup
create_tables()
