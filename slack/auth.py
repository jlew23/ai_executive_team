"""
Authentication and user management for Slack integration.
"""

import os
import json
import logging
import time
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class SlackUser:
    """
    Representation of a Slack user.
    """
    id: str
    name: str
    real_name: Optional[str] = None
    email: Optional[str] = None
    is_admin: bool = False
    is_bot: bool = False
    team_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class SlackAuth:
    """
    Authentication and user management for Slack.
    
    This class provides functionality for:
    1. Managing user authentication
    2. Storing and retrieving user information
    3. Handling workspace-specific settings
    4. Managing permissions and access control
    """
    
    def __init__(self, slack_client, user_store_path: Optional[str] = None):
        """
        Initialize the authentication manager.
        
        Args:
            slack_client: Slack client instance
            user_store_path: Path to store user information (defaults to in-memory storage)
        """
        self.slack_client = slack_client
        self.user_store_path = user_store_path
        self.users: Dict[str, SlackUser] = {}
        self.workspaces: Dict[str, Dict[str, Any]] = {}
        
        # Load users if store path is provided
        if user_store_path:
            self._load_users()
    
    def authenticate_user(self, user_id: str) -> SlackUser:
        """
        Authenticate a user and retrieve their information.
        
        Args:
            user_id: Slack user ID
            
        Returns:
            SlackUser object
            
        Raises:
            ValueError: If user cannot be authenticated
        """
        # Check if we already have this user
        if user_id in self.users:
            return self.users[user_id]
            
        # Fetch user info from Slack
        try:
            user_info = self.slack_client.get_user_info(user_id)
            user = user_info["user"]
            
            # Create SlackUser object
            slack_user = SlackUser(
                id=user_id,
                name=user.get("name", ""),
                real_name=user.get("real_name"),
                email=user.get("profile", {}).get("email"),
                is_admin=user.get("is_admin", False),
                is_bot=user.get("is_bot", False),
                team_id=user.get("team_id"),
                metadata={
                    "tz": user.get("tz"),
                    "tz_offset": user.get("tz_offset"),
                    "updated": int(time.time())
                }
            )
            
            # Store user
            self.users[user_id] = slack_user
            
            # Persist users if store path is provided
            if self.user_store_path:
                self._save_users()
                
            return slack_user
            
        except Exception as e:
            logger.error(f"Error authenticating user {user_id}: {e}")
            raise ValueError(f"Could not authenticate user {user_id}")
    
    def get_user(self, user_id: str) -> Optional[SlackUser]:
        """
        Get a user by ID.
        
        Args:
            user_id: Slack user ID
            
        Returns:
            SlackUser object if found, None otherwise
        """
        return self.users.get(user_id)
    
    def update_user(self, user_id: str) -> Optional[SlackUser]:
        """
        Update a user's information.
        
        Args:
            user_id: Slack user ID
            
        Returns:
            Updated SlackUser object if successful, None otherwise
        """
        try:
            # Remove existing user
            if user_id in self.users:
                del self.users[user_id]
                
            # Re-authenticate to get fresh info
            return self.authenticate_user(user_id)
            
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {e}")
            return None
    
    def register_workspace(
        self,
        team_id: str,
        team_name: str,
        settings: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Register a Slack workspace.
        
        Args:
            team_id: Slack team ID
            team_name: Slack team name
            settings: Optional workspace settings
        """
        self.workspaces[team_id] = {
            "id": team_id,
            "name": team_name,
            "settings": settings or {},
            "registered_at": int(time.time())
        }
        
        # Persist workspaces if store path is provided
        if self.user_store_path:
            self._save_users()
    
    def get_workspace(self, team_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a workspace by ID.
        
        Args:
            team_id: Slack team ID
            
        Returns:
            Workspace information if found, None otherwise
        """
        return self.workspaces.get(team_id)
    
    def update_workspace_settings(
        self,
        team_id: str,
        settings: Dict[str, Any]
    ) -> bool:
        """
        Update settings for a workspace.
        
        Args:
            team_id: Slack team ID
            settings: New settings
            
        Returns:
            True if successful, False otherwise
        """
        if team_id not in self.workspaces:
            return False
            
        # Update settings
        self.workspaces[team_id]["settings"].update(settings)
        
        # Persist workspaces if store path is provided
        if self.user_store_path:
            self._save_users()
            
        return True
    
    def check_permission(
        self,
        user_id: str,
        permission: str,
        team_id: Optional[str] = None
    ) -> bool:
        """
        Check if a user has a specific permission.
        
        Args:
            user_id: Slack user ID
            permission: Permission to check
            team_id: Optional team ID for team-specific permissions
            
        Returns:
            True if the user has the permission, False otherwise
        """
        # Get user
        user = self.get_user(user_id)
        if not user:
            return False
            
        # Admin users have all permissions
        if user.is_admin:
            return True
            
        # Check workspace-specific permissions
        if team_id and team_id in self.workspaces:
            workspace = self.workspaces[team_id]
            
            # Check user-specific permissions in this workspace
            user_permissions = workspace.get("user_permissions", {}).get(user_id, [])
            if permission in user_permissions:
                return True
                
            # Check role-based permissions
            user_roles = workspace.get("user_roles", {}).get(user_id, [])
            role_permissions = workspace.get("role_permissions", {})
            
            for role in user_roles:
                if permission in role_permissions.get(role, []):
                    return True
        
        return False
    
    def _load_users(self) -> None:
        """
        Load users and workspaces from disk.
        """
        if not os.path.exists(self.user_store_path):
            return
            
        try:
            with open(self.user_store_path, 'r') as f:
                data = json.load(f)
                
            # Load users
            for user_id, user_data in data.get("users", {}).items():
                self.users[user_id] = SlackUser(
                    id=user_id,
                    name=user_data.get("name", ""),
                    real_name=user_data.get("real_name"),
                    email=user_data.get("email"),
                    is_admin=user_data.get("is_admin", False),
                    is_bot=user_data.get("is_bot", False),
                    team_id=user_data.get("team_id"),
                    metadata=user_data.get("metadata", {})
                )
                
            # Load workspaces
            self.workspaces = data.get("workspaces", {})
                
        except Exception as e:
            logger.error(f"Error loading users from {self.user_store_path}: {e}")
    
    def _save_users(self) -> None:
        """
        Save users and workspaces to disk.
        """
        if not self.user_store_path:
            return
            
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.user_store_path), exist_ok=True)
            
            # Convert users to dict
            users_dict = {}
            for user_id, user in self.users.items():
                users_dict[user_id] = {
                    "name": user.name,
                    "real_name": user.real_name,
                    "email": user.email,
                    "is_admin": user.is_admin,
                    "is_bot": user.is_bot,
                    "team_id": user.team_id,
                    "metadata": user.metadata
                }
                
            # Save to file
            with open(self.user_store_path, 'w') as f:
                json.dump({
                    "users": users_dict,
                    "workspaces": self.workspaces
                }, f)
                
        except Exception as e:
            logger.error(f"Error saving users to {self.user_store_path}: {e}")
