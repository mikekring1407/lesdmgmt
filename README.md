# Next US Lead Management System

A secure web application for displaying and managing leads from a PostgreSQL database with user-specific access controls.

## Features

- User authentication with role-based access control
- Admin dashboard for user management
- Lead assignment and management
- Custom field creation and management
- CSV import and export capabilities
- Google Sheets integration (optional)
- Comprehensive filtering and search
- Mobile-responsive interface

## Tech Stack

- **Backend**: Flask
- **Database**: PostgreSQL
- **Authentication**: Flask-Login
- **Forms**: Flask-WTF
- **ORM**: SQLAlchemy
- **Frontend**: Bootstrap, DataTables.js
- **External APIs**: Google Sheets (optional)

## Setup and Installation

### Local Development

1. Clone the repository
2. Install the required dependencies
3. Set up environment variables (see `.env.sample`)
4. Run database migrations:
   ```
   python migrations.py
   ```
5. Run the application:
   ```
   gunicorn --bind 0.0.0.0:5000 main:app
   ```

### Production Deployment

For detailed deployment instructions, see the [Deployment Guide](DEPLOYMENT_GUIDE.md).

### Database Migrations

When updating an existing installation, run the migrations script to add the new fields:

```
python migrations.py
```

This will add the following fields to the lead table:
- first_name
- last_name
- city
- state
- zipcode
- bank_name
- date_captured
- time_captured
- workspace_id (with foreign key constraint)

## Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `SESSION_SECRET`: Secret key for session management
- `GOOGLE_CREDENTIALS`: (Optional) Google API credentials
- `SPREADSHEET_ID`: (Optional) ID of Google Spreadsheet for imports

## Project Structure

- `/app.py`: Main application file
- `/models.py`: Database models
- `/forms.py`: Form definitions
- `/utils.py`: Utility functions
- `/templates/`: HTML templates
- `/static/`: Static assets (CSS, JS, images)
- `/instance/`: Instance-specific data (database files)

## Usage

### Default Admin Credentials

Username: `admin`  
Password: `admin`

**Important**: Change these credentials immediately after the first login.

### User Management

1. Log in as admin
2. Navigate to Admin Dashboard > Users
3. Create or manage users

### Lead Management

1. Import leads via CSV or Google Sheets
2. Assign leads to users
3. Filter and export lead data

## Custom Fields

The system supports custom fields for leads:
- Text fields
- Number fields
- Date fields
- Dropdown/select fields
- Checkboxes
- Text areas

## License

[MIT License](LICENSE)