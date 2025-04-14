# Deployment Guide for Next US Lead Management System

## April 2025 Updates

### 1. Workspace-Specific Header Mappings for Imports

We've enhanced the system to support workspace-specific header mappings for both CSV and Google Sheets imports:

- Added workspace and header mapping selection fields to the import forms
- Implemented Google Sheets CSV conversion for consistent import handling
- Updated import routes to work with the new mapping options

### 2. Database Schema Updates

To fix the "string data right truncation" error during CSV imports, we've increased column lengths in the Lead model:

| Field | Old Size | New Size |
|-------|----------|----------|
| phone | VARCHAR(20) | VARCHAR(50) |
| first_name | VARCHAR(50) | VARCHAR(100) |
| last_name | VARCHAR(50) | VARCHAR(100) |
| city | VARCHAR(50) | VARCHAR(100) |
| state | VARCHAR(50) | VARCHAR(100) |
| zipcode | VARCHAR(20) | VARCHAR(50) |
| date_captured | VARCHAR(20) | VARCHAR(50) |
| time_captured | VARCHAR(20) | VARCHAR(50) |
| bank_name | VARCHAR(100) | VARCHAR(200) |
| name | VARCHAR(100) | VARCHAR(200) |
| company | VARCHAR(100) | VARCHAR(200) |
| status | VARCHAR(20) | VARCHAR(50) |
| source | VARCHAR(50) | VARCHAR(100) |

## Deployment Steps for Render.com

### 1. Backup Your Database

**Important:** Always backup your database before schema changes:

```bash
pg_dump $DATABASE_URL > nextus_backup_apr2025.sql
```

### 2. Update Dependency Files

We've included updated dependency files for your deployment:

- **pyproject.toml** - For Poetry-based deployment on Render.com
- **requirements-render.txt** - Standard pip requirements file if needed

Make sure these files are included in your repository or deployment package.

### 3. Deploy Code Changes

#### Option A: Git Integration (Recommended)

If your Render app is linked to a Git repository:

1. Commit all changes including the updated models and dependency files
2. Push changes to your repository
3. Render will automatically detect and deploy the changes

#### Option B: Manual Deploy

If not using Git integration:

1. Log in to your Render dashboard
2. Select your Next US application
3. Click "Manual Deploy" and select "Deploy latest commit" or upload your code

### 3. Run Database Migrations

After deployment, you'll need to run the migration to update column lengths:

1. Navigate to your Render dashboard
2. Open a Shell for your service
3. Run the migration script:

```bash
python migrate_column_lengths.py
```

This will increase all column lengths to match the updated model definitions.

### 4. Verify the Deployment

1. Log in to your application
2. Navigate to Admin > Imports
3. Verify that workspace and header mapping dropdowns appear correctly
4. Try importing a CSV file with the previously failing data
5. Check that the import completes without the truncation error

## Troubleshooting

If you encounter issues during deployment:

1. **Database Connection Errors**: Check that your DATABASE_URL environment variable is correctly set in Render
2. **Migration Failures**: Examine the logs from the migration script for specific error messages
3. **Import Errors**: If CSV imports still fail, check that the migration completed successfully

For persistent issues, refer to the application logs in your Render dashboard or contact support for assistance.