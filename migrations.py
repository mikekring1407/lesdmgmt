"""
Database migration script for the lead management system.
This script adds the new fields to the Lead table if they don't already exist.
"""
import os
import sys
import logging
from sqlalchemy import text, inspect
from app import app, db

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_column_exists(table_name, column_name):
    """Check if a column exists in a table"""
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def run_migrations():
    """Run all necessary migrations"""
    conn = None
    try:
        # Set up application context
        with app.app_context():
            # Connect to the database
            conn = db.engine.connect()
            logger.info("Connected to database, starting migrations...")
            
            # List of columns to add to the Lead table with their SQL definitions
            columns_to_add = [
                ('first_name', 'VARCHAR(50)'),
                ('last_name', 'VARCHAR(50)'),
                ('city', 'VARCHAR(50)'),
                ('state', 'VARCHAR(50)'),
                ('zipcode', 'VARCHAR(20)'),
                ('bank_name', 'VARCHAR(100)'),
                ('date_captured', 'VARCHAR(20)'),
                ('time_captured', 'VARCHAR(20)')
            ]
            
            # Add each column if it doesn't already exist
            for column_name, column_type in columns_to_add:
                if not check_column_exists('lead', column_name):
                    logger.info(f"Adding column {column_name} to lead table...")
                    sql = f"ALTER TABLE lead ADD COLUMN {column_name} {column_type};"
                    conn.execute(text(sql))
                    logger.info(f"Column {column_name} added successfully.")
                else:
                    logger.info(f"Column {column_name} already exists in lead table.")
            
            # Update workspace_id to be a foreign key if not already set
            if check_column_exists('lead', 'workspace_id'):
                logger.info("workspace_id column already exists, checking foreign key...")
                # Check if foreign key exists
                inspector = inspect(db.engine)
                foreign_keys = [fk['referred_table'] for fk in inspector.get_foreign_keys('lead')]
                if 'workspace' not in foreign_keys:
                    logger.info("Adding foreign key constraint for workspace_id...")
                    try:
                        sql = """
                        ALTER TABLE lead 
                        ADD CONSTRAINT fk_lead_workspace 
                        FOREIGN KEY (workspace_id) 
                        REFERENCES workspace (id);
                        """
                        conn.execute(text(sql))
                        logger.info("Foreign key constraint added successfully.")
                    except Exception as e:
                        logger.warning(f"Could not add foreign key constraint: {e}")
            else:
                logger.info("Adding workspace_id column to lead table...")
                sql = """
                ALTER TABLE lead 
                ADD COLUMN workspace_id INTEGER,
                ADD CONSTRAINT fk_lead_workspace 
                FOREIGN KEY (workspace_id) 
                REFERENCES workspace (id);
                """
                try:
                    conn.execute(text(sql))
                    logger.info("workspace_id column added successfully.")
                except Exception as e:
                    logger.warning(f"Error adding workspace_id column: {e}")
            
            logger.info("All migrations completed successfully!")
            return True
    except Exception as e:
        logger.error(f"Error during migration: {e}")
        return False
    finally:
        if conn is not None:
            conn.close()

def main():
    """Main function to run migrations"""
    success = run_migrations()
    if success:
        logger.info("Database migration completed successfully.")
        sys.exit(0)
    else:
        logger.error("Database migration failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()