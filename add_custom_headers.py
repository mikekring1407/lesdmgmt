"""
Script to add custom headers to an existing workspace.
"""
from app import app, db
from models import Workspace, WorkspaceHeader

def add_custom_headers_to_workspace(workspace_id=1):
    """
    Add custom headers to an existing workspace.
    """
    with app.app_context():
        # Check if workspace exists
        workspace = Workspace.query.get(workspace_id)
        if not workspace:
            print(f"Workspace with ID {workspace_id} not found.")
            return False
        
        # Get current highest order
        max_order = db.session.query(db.func.max(WorkspaceHeader.order))\
            .filter_by(workspace_id=workspace_id).scalar() or 0
        
        # Add custom headers
        custom_headers = ["source", "notes", "priority"]
        for i, header in enumerate(custom_headers):
            # Check if header already exists
            existing = WorkspaceHeader.query.filter_by(
                workspace_id=workspace_id, 
                header_name=header
            ).first()
            
            if existing:
                print(f"Header '{header}' already exists for workspace '{workspace.name}'.")
                continue
                
            header_obj = WorkspaceHeader(
                workspace_id=workspace_id,
                header_name=header,
                is_default=False,
                order=max_order + i + 1
            )
            db.session.add(header_obj)
            print(f"Added custom header '{header}' to workspace '{workspace.name}'.")
        
        db.session.commit()
        print(f"Custom headers added to workspace '{workspace.name}'.")
        return True

if __name__ == "__main__":
    add_custom_headers_to_workspace()