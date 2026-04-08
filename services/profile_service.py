"""
Profile Service - Handles all profile-related business logic.
Used by both Qt app and API.
"""

from database.database import Database
from database.profile import Profile


class ProfileService:
    """Service for profile operations."""
    
    def __init__(self, db: Database):
        self.db = db
    
    def get_all_profiles(self) -> list[Profile]:
        """Get all profiles."""
        return self.db.fetch_profiles()
    
    def get_profile_by_id(self, profile_id: int) -> Profile:
        """Get a specific profile by ID."""
        from api.profile import ProfileAPI
        profile_api = ProfileAPI(self.db)
        return profile_api.get_profile_by_id(profile_id)
    
    def create_profile(self, name: str) -> Profile:
        """Create a new profile."""
        return self.db.create_profile(name)
    
    def delete_profile(self, profile_id: int) -> None:
        """Delete a profile."""
        self.db.delete_profile(profile_id)
