# NEXTUS Lead Management System

A powerful lead management system built with Flask that allows admins to manage leads, workspaces, and users.

## Features

- Role-based access control (Admin and User roles)
- CSV import/export with custom headers per workspace
- Lead assignment and management
- User management
- Comprehensive reporting
- Responsive design

## Deployment on Render

This application is configured for easy deployment on Render.com:

1. Sign up for a [Render account](https://render.com)
2. Click on "New" and select "Blueprint" from the dropdown
3. Connect your GitHub/GitLab repository
4. Render will automatically detect the render.yaml configuration
5. Click "Apply" to deploy the application

### What Gets Deployed

- **Web Service**: The Flask application with Gunicorn as the WSGI server
- **PostgreSQL Database**: A dedicated database for the application

### Environment Variables

The following environment variables are configured automatically:

- `DATABASE_URL`: Connection string for the PostgreSQL database
- `SESSION_SECRET`: Randomly generated secret key for JWT and sessions
- `PYTHONUNBUFFERED`: Set to true for proper logging

## Initial Setup After Deployment

After the first deployment, you need to set up an admin user. You have two options:

### Option 1: Using the Setup Route (Recommended)

1. Access your deployed application with the setup route:
   ```
   https://your-app-url.render.com/create-admin?key=SETUP_KEY
   ```
   Replace `SETUP_KEY` with the value of the SETUP_KEY environment variable in your Render dashboard.

2. You'll receive a JSON response with the admin username and password.

3. Log in with these credentials (default: username: `admin`, password: `Admin@123`).

### Option 2: Using the Render Shell

If you have shell access:

1. Access the Render shell for your web service
2. Run the following command to create an admin user:
   ```
   python create_admin.py --username admin --email admin@example.com --password secure_password
   ```

3. Run the following command to create a default workspace:
   ```
   python create_workspace.py
   ```

4. Log in with the admin credentials

## Local Development

1. Clone the repository
2. Copy `.env.example` to `.env` and update the variables
3. Install dependencies: `pip install -r render-requirements.txt`
4. Run the application: `gunicorn main:app --bind 0.0.0.0:5000`

## Support

For any issues or questions, please contact support@nextus.com