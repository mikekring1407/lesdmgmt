"""
Script to create an admin user for the Lead Management System.
Run this script to add an admin user to the database.
"""
import os
import sys
from app import app, db
from models import User

def create_admin_user(username, email, password):
    """
    Create an admin user if it doesn't already exist.
    """
    with app.app_context():
        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            print(f"User '{username}' already exists.")
            return False
        
        # Create new admin user
        admin = User(
            username=username,
            email=email,
            role='admin'
        )
        admin.set_password(password)
        
        # Add to database
        db.session.add(admin)
        db.session.commit()
        
        print(f"Admin user '{username}' created successfully with email '{email}'.")
        return True

if __name__ == "__main__":
    import argparse
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Create an admin user for the Lead Management System.')
    parser.add_argument('--username', default='admin', help='Admin username')
    parser.add_argument('--email', default='admin@example.com', help='Admin email')
    parser.add_argument('--password', default='Admin@123', help='Admin password')
    
    # Parse arguments
    args = parser.parse_args()
    
    success = create_admin_user(args.username, args.email, args.password)
    if success:
        print("Admin user created successfully. You can now log in with:")
        print(f"Username: {args.username}")
        print(f"Password: {args.password}")
    sys.exit(0 if success else 1)