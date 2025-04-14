"""
Database migration script to increase column lengths for lead data.
Run this script to update PostgreSQL database schema for CSV import.
"""

import os
import sys
import psycopg2
import psycopg2.extras
import logging

# Set up logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the database using the DATABASE_URL environment variable"""
    try:
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            logger.error("DATABASE_URL environment variable not set")
            sys.exit(1)
            
        conn = psycopg2.connect(database_url)
        conn.autocommit = False  # We'll manage the transaction ourselves
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        sys.exit(1)

def run_migrations():
    """Run all migrations to increase column lengths"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Start a transaction
        logger.info("Starting database migration to increase column lengths...")
        
        # List of column updates needed for the Lead table
        column_updates = [
            ("phone", "VARCHAR(50)"),
            ("first_name", "VARCHAR(100)"),
            ("last_name", "VARCHAR(100)"),
            ("city", "VARCHAR(100)"),
            ("state", "VARCHAR(100)"),
            ("zipcode", "VARCHAR(50)"),
            ("date_captured", "VARCHAR(50)"),
            ("time_captured", "VARCHAR(50)"),
            ("bank_name", "VARCHAR(200)"),
            ("name", "VARCHAR(200)"),
            ("company", "VARCHAR(200)"),
            ("status", "VARCHAR(50)"),
            ("source", "VARCHAR(100)")
        ]
        
        # Execute each column update
        for column, new_type in column_updates:
            logger.info(f"Altering column {column} to {new_type}")
            cur.execute(f"ALTER TABLE lead ALTER COLUMN {column} TYPE {new_type};")
        
        # Commit the transaction
        conn.commit()
        logger.info("Migration completed successfully")
        
    except Exception as e:
        # Roll back in case of error
        conn.rollback()
        logger.error(f"Error during migration: {str(e)}")
        sys.exit(1)
        
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    run_migrations()