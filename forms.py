from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, PasswordField, BooleanField, HiddenField, SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Length, Optional, Email

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

class UserForm(FlaskForm):
    user_id = HiddenField('User ID')
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    password = PasswordField('Password', validators=[
        Length(min=6, max=64, message="Password must be at least 6 characters long"),
        Optional()  # Make password optional for editing existing users
    ])
    sheet_filter = StringField('Sheet Filter', validators=[Optional()], 
                              description="Column name or value to filter lead data (leave blank for full access)")
    is_admin = BooleanField('Admin Access')
    submit = SubmitField('Save User')

class WorkspaceForm(FlaskForm):
    workspace_id = HiddenField('Workspace ID')
    name = StringField('Workspace Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Optional()])
    active = BooleanField('Active', default=True)
    default_header_mapping_id = SelectField('Default Header Mapping', coerce=int, validators=[Optional()],
                           description="Select the default header mapping for this workspace")
    submit = SubmitField('Save Workspace')

class LeadForm(FlaskForm):
    lead_id = HiddenField('Lead ID')
    
    # Contact Information
    first_name = StringField('First Name', validators=[Optional(), Length(max=50)])
    last_name = StringField('Last Name', validators=[Optional(), Length(max=50)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=100)])
    phone = StringField('Phone Number', validators=[Optional(), Length(max=20)])
    
    # Address Information
    city = StringField('City', validators=[Optional(), Length(max=50)])
    state = StringField('State', validators=[Optional(), Length(max=50)])
    zipcode = StringField('Zip Code', validators=[Optional(), Length(max=20)])
    
    # Additional Information
    bank_name = StringField('Bank Name', validators=[Optional(), Length(max=100)])
    date_captured = StringField('Date Captured', validators=[Optional(), Length(max=20)])
    time_captured = StringField('Time Captured', validators=[Optional(), Length(max=20)])
    
    # Legacy fields (for backward compatibility)
    name = StringField('Full Name (Legacy)', validators=[Optional(), Length(max=100)])
    company = StringField('Company', validators=[Optional(), Length(max=100)])
    
    # Lead Status and Notes
    status = SelectField('Status', choices=[
        ('New', 'New'),
        ('Contacted', 'Contacted'),
        ('Qualified', 'Qualified'),
        ('Lost', 'Lost'),
        ('Converted', 'Converted')
    ])
    source = StringField('Source', validators=[Optional(), Length(max=50)])
    notes = TextAreaField('Notes', validators=[Optional()])
    
    # Workspace
    workspace_id = SelectField('Workspace', coerce=int, validators=[Optional()])
    
    submit = SubmitField('Save Lead')

class AssignLeadForm(FlaskForm):
    user_id = SelectField('Assign To User', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Assign Lead')

class CSVUploadForm(FlaskForm):
    file = FileField('CSV File', validators=[
        FileRequired(),
        FileAllowed(['csv'], 'CSV files only!')
    ])
    has_headers = BooleanField('File includes header row', default=True)
    workspace_id = SelectField('Workspace', coerce=int, validators=[Optional()],
                          description="Select a workspace to assign these leads to")
    header_mapping_id = SelectField('Header Mapping', coerce=int, validators=[Optional()],
                               description="Select a header mapping or use workspace default if available")
    submit = SubmitField('Upload CSV')

class ImportSheetForm(FlaskForm):
    spreadsheet_id = StringField('Google Spreadsheet ID', validators=[DataRequired()])
    sheet_name = StringField('Sheet Name (leave blank for first sheet)', validators=[Optional()])
    has_headers = BooleanField('Spreadsheet includes header row', default=True)
    workspace_id = SelectField('Workspace', coerce=int, validators=[Optional()],
                          description="Select a workspace to assign these leads to")
    header_mapping_id = SelectField('Header Mapping', coerce=int, validators=[Optional()],
                               description="Select a header mapping or use workspace default if available")
    submit = SubmitField('Import from Google Sheet')

class CustomFieldForm(FlaskForm):
    field_id = HiddenField('Field ID')
    name = StringField('Field Name', validators=[
        DataRequired(), 
        Length(max=50),
    ], description="Internal field name (letters, numbers, underscore)")
    label = StringField('Display Label', validators=[
        DataRequired(),
        Length(max=100)
    ], description="Label shown to users")
    field_type = SelectField('Field Type', choices=[
        ('text', 'Text'),
        ('number', 'Number'),
        ('date', 'Date'),
        ('select', 'Dropdown'),
        ('checkbox', 'Checkbox'),
        ('textarea', 'Text Area')
    ], validators=[DataRequired()])
    required = BooleanField('Required Field')
    options = TextAreaField('Options', validators=[Optional()], 
                           description="For dropdown fields, enter options one per line")
    order = StringField('Display Order', validators=[Optional()],
                       description="Numeric order for display (lower numbers shown first)")
    active = BooleanField('Active', default=True)
    submit = SubmitField('Save Field')

class CSVExportForm(FlaskForm):
    include_all_fields = BooleanField('Include all custom fields', default=True)
    submit = SubmitField('Export to CSV')

class HeaderMappingForm(FlaskForm):
    mapping_id = HiddenField('Mapping ID')
    name = StringField('Mapping Name', validators=[DataRequired(), Length(max=50)],
                     description="A name for this header mapping (e.g., 'Marketing CSV Format')")
    description = TextAreaField('Description', validators=[Optional()],
                              description="Optional description of this mapping")
    
    workspace_id = SelectField('Associated Workspace', coerce=int, validators=[Optional()],
                             description="Assign this mapping to a specific workspace")
    
    # Field mappings
    first_name_header = StringField('First Name', validators=[Optional()], 
                                   description="Header for first name column (e.g., 'First Name', 'Given Name')")
    last_name_header = StringField('Last Name', validators=[Optional()], 
                                  description="Header for last name column")
    email_header = StringField('Email', validators=[Optional()], 
                              description="Header for email column")
    phone_header = StringField('Phone', validators=[Optional()], 
                              description="Header for phone column")
    company_header = StringField('Company', validators=[Optional()], 
                                description="Header for company column")
    city_header = StringField('City', validators=[Optional()], 
                             description="Header for city column")
    state_header = StringField('State', validators=[Optional()], 
                              description="Header for state column")
    zipcode_header = StringField('Zip Code', validators=[Optional()], 
                                description="Header for zip code column")
    bank_name_header = StringField('Bank Name', validators=[Optional()], 
                                  description="Header for bank name column")
    date_captured_header = StringField('Date Captured', validators=[Optional()], 
                                      description="Header for date captured column")
    time_captured_header = StringField('Time Captured', validators=[Optional()], 
                                      description="Header for time captured column")
    status_header = StringField('Status', validators=[Optional()], 
                               description="Header for status column")
    source_header = StringField('Source', validators=[Optional()], 
                               description="Header for source column")
    notes_header = StringField('Notes', validators=[Optional()], 
                              description="Header for notes column")
    
    is_default = BooleanField('Set as Default Mapping', default=False,
                            description="Use this mapping by default for CSV imports")
    submit = SubmitField('Save Header Mapping')
