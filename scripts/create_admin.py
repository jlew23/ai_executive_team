"""
Create an admin user for the web dashboard.
"""

import os
import logging
import sys
import getpass
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_admin():
    """Create an admin user."""
    from web_dashboard import create_app
    from web_dashboard.models import db, User, Role, UserRole
    
    logger.info("Creating admin user...")
    
    # Create app context
    app = create_app()
    
    with app.app_context():
        # Check if admin role exists
        admin_role = Role.query.filter_by(name='admin').first()
        if not admin_role:
            logger.info("Creating admin role...")
            admin_role = Role(name='admin', description='Administrator')
            db.session.add(admin_role)
            db.session.commit()
        
        # Check if admin user exists
        admin_user = User.query.filter_by(username='admin').first()
        if admin_user:
            logger.info("Admin user already exists.")
            return
        
        # Get admin username and password
        username = input("Enter admin username (default: admin): ") or "admin"
        email = input("Enter admin email: ")
        password = getpass.getpass("Enter admin password: ")
        confirm_password = getpass.getpass("Confirm admin password: ")
        
        if password != confirm_password:
            logger.error("Passwords do not match.")
            return
        
        # Create admin user
        admin_user = User(
            username=username,
            email=email,
            is_active=True
        )
        admin_user.set_password(password)
        
        db.session.add(admin_user)
        db.session.commit()
        
        # Assign admin role to user
        user_role = UserRole(user_id=admin_user.id, role_id=admin_role.id)
        db.session.add(user_role)
        db.session.commit()
        
        logger.info(f"Admin user '{username}' created successfully.")

if __name__ == "__main__":
    create_admin()
