"""
Database module for managing middleman profiles and stats
Uses JSON file-based storage for simplicity
"""
import json
import os
from typing import Dict, Optional

DATABASE_FILE = 'mm_profiles.json'

class MMDatabase:
    """Manage middleman profiles and statistics"""
    
    def __init__(self):
        self.data = self._load_database()
    
    def _load_database(self) -> Dict:
        """Load the database from file"""
        if os.path.exists(DATABASE_FILE):
            try:
                with open(DATABASE_FILE, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {"profiles": {}}
        return {"profiles": {}}
    
    def _save_database(self):
        """Save the database to file"""
        with open(DATABASE_FILE, 'w') as f:
            json.dump(self.data, f, indent=4)
    
    def get_profile(self, user_id: int) -> Dict:
        """Get a middleman's profile"""
        user_id_str = str(user_id)
        if user_id_str not in self.data["profiles"]:
            self.data["profiles"][user_id_str] = {
                "rank": "Middleman",
                "completed_tickets": 0
            }
            self._save_database()
        return self.data["profiles"][user_id_str]
    
    def set_rank(self, user_id: int, rank: str):
        """Set a middleman's rank"""
        profile = self.get_profile(user_id)
        profile["rank"] = rank
        self._save_database()
    
    def set_completed_tickets(self, user_id: int, count: int):
        """Set the number of completed tickets for a middleman"""
        profile = self.get_profile(user_id)
        profile["completed_tickets"] = max(0, count)  # Ensure non-negative
        self._save_database()
    
    def increment_tickets(self, user_id: int):
        """Increment the completed tickets counter for a middleman"""
        profile = self.get_profile(user_id)
        profile["completed_tickets"] += 1
        self._save_database()
    
    def get_rank(self, user_id: int) -> str:
        """Get a middleman's rank"""
        return self.get_profile(user_id).get("rank", "Middleman")
    
    def get_completed_tickets(self, user_id: int) -> int:
        """Get the number of completed tickets for a middleman"""
        return self.get_profile(user_id).get("completed_tickets", 0)
