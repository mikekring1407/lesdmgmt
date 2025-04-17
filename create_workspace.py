"""
Script to create a sample workspace in the Lead Management System.
"""
from app import app, db
from models import User, Workspace, WorkspaceHeader

def create_default_workspace():
    """
    Create a default workspace with standard headers if none exists.
    """
    with app.app_context():
        # Get admin user
        admin = User.query.filter_by(role='admin').first()
        
        if not admin:
            print("No admin user found. Please create an admin user first.")
            return False
        
        # Check if workspace already exists
        existing = Workspace.query.first()
        if existing:
            print(f"Workspace '{existing.name}' already exists.")
            return False
        
        # Create a new workspace
        workspace = Workspace(
            name="Default Workspace",
            created_by=admin.id
        )
        
        db.session.add(workspace)
        db.session.flush()  # Flush to get the workspace ID
        
        # Create default headers
        default_headers = [
            "first_name", "last_name", "email", "phone", 
            "city", "state", "status", "bank", "date"
        ]
        
        # Add each default header
        for i, header in enumerate(default_headers):
            header_obj = WorkspaceHeader(
                workspace_id=workspace.id,
                header_name=header,
                is_default=True,
                order=i
            )
            db.session.add(header_obj)
        
        # Add some custom headers as examples
        custom_headers = ["source", "notes", "priority"]
        for i, header in enumerate(custom_headers):
            header_obj = WorkspaceHeader(
                workspace_id=workspace.id,
                header_name=header,
                is_default=False,
                order=len(default_headers) + i
            )
            db.session.add(header_obj)
            
        db.session.commit()
        
        print(f"Workspace '{workspace.name}' created successfully with default and custom headers.")
        return True

if __name__ == "__main__":
    success = create_default_workspace()
    if success:
        print("You can now upload leads to this workspace.")