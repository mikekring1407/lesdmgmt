# Next US - Lead Management System Deployment Guide

This guide provides instructions for deploying the Next US lead management application on a third-party hosting service, particularly for cPanel environments.

## Required Dependencies

Ensure your hosting environment has Python 3.8+ and the following packages installed:

```
email-validator==2.0.0
Flask==2.3.3
Flask-Login==0.6.2
Flask-SQLAlchemy==3.1.1
Flask-WTF==1.1.1
gspread==5.10.0
gunicorn==23.0.0
oauth2client==4.1.3
psycopg2-binary==2.9.7
SQLAlchemy==2.0.23
Werkzeug==2.3.7
WTForms==3.0.1
```

## Database Setup

1. Create a PostgreSQL database on your hosting provider
2. Note the database credentials (hostname, username, password, database name)
3. You'll need these for environment configuration

## Environment Variables

Set up the following environment variables in your hosting environment:

- `DATABASE_URL`: Your PostgreSQL connection string (format: `postgresql://username:password@hostname:port/database`)
- `SESSION_SECRET`: A strong random string for Flask session encryption
- `GOOGLE_CREDENTIALS`: (Optional) JSON credentials for Google Sheets API if you plan to use the import from Google Sheets feature

## Deployment Steps for cPanel

1. **Upload Files**:
   - Upload all application files to your hosting account via FTP or cPanel File Manager
   - Keep the directory structure intact

2. **Setup Python Application**:
   - In cPanel, locate the "Setup Python App" or similar section
   - Create a new Python application pointing to your uploaded directory
   - Set the application entry point to `main.py`
   - Configure the application to use Python 3.8 or newer

3. **Configure Environment Variables**:
   - In the Python application settings, add the required environment variables
   - Alternatively, create a `.env` file in the application root directory

4. **Set Up Virtual Environment**:
   - Most cPanel setups automatically create a virtual environment
   - If needed, install the required packages using pip:
     ```
     pip install -r requirements.txt
     ```

5. **Database Migration**:
   - Ensure the application can access your PostgreSQL database
   - The application will automatically create necessary tables on first run

6. **Configure Web Server**:
   - Set up the application to run with a WSGI server like gunicorn
   - Configure your domain/subdomain to point to the application

## Passenger Configuration (if using)

If your hosting provider uses Passenger for Python applications, create a `passenger_wsgi.py` file:

```python
import sys
import os
INTERP = os.path.expanduser("/path/to/your/venv/bin/python")
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

from main import app as application
```

Replace `/path/to/your/venv/bin/python` with the actual path to your Python interpreter.

## Apache Configuration (if needed)

If you need to configure Apache manually, create a `.htaccess` file:

```
<IfModule mod_rewrite.c>
    RewriteEngine On
    RewriteCond %{REQUEST_FILENAME} !-f
    RewriteRule ^(.*)$ /app.py/$1 [QSA,L]
</IfModule>
```

## Troubleshooting

- **Database Connection Issues**: Verify your DATABASE_URL is correct and the database user has proper permissions
- **File Permissions**: Ensure all files have the correct permissions (typically 644 for files, 755 for directories)
- **Google Sheets API**: If using Google Sheets import, ensure the GOOGLE_CREDENTIALS environment variable is properly set
- **Logs**: Check application logs for error messages (typically in the logs directory of your hosting account)

## Security Notes

- Change the default admin password immediately after first login
- Keep your SESSION_SECRET secure and unique
- Consider setting up HTTPS for your domain
- Restrict file permissions to the minimum necessary

## Additional Resources

For more information on deploying Flask applications on cPanel, refer to:
- [cPanel Python Application documentation](https://docs.cpanel.net/knowledge-base/web-services/python-application/)