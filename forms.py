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

class LeadForm(FlaskForm):
    lead_id = HiddenField('Lead ID')
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=100)])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    company = StringField('Company', validators=[Optional(), Length(max=100)])
    status = SelectField('Status', choices=[
        ('New', 'New'),
        ('Contacted', 'Contacted'),
        ('Qualified', 'Qualified'),
        ('Lost', 'Lost'),
        ('Converted', 'Converted')
    ])
    source = StringField('Source', validators=[Optional(), Length(max=50)])
    notes = TextAreaField('Notes', validators=[Optional()])
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
    submit = SubmitField('Upload CSV')

class ImportSheetForm(FlaskForm):
    spreadsheet_id = StringField('Google Spreadsheet ID', validators=[DataRequired()])
    sheet_name = StringField('Sheet Name (leave blank for first sheet)', validators=[Optional()])
    has_headers = BooleanField('Spreadsheet includes header row', default=True)
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
