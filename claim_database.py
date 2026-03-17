"""
Claim Database Manager - Tracks customer submissions to prevent duplicates
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple


class ClaimDatabase:
    """Manages claim submissions and prevents duplicates"""

    def __init__(self, db_file="claims_database.json"):
        """Initialize the claim database"""
        self.db_file = db_file
        self.claims = self._load_database()

    def _load_database(self) -> Dict:
        """Load claims database from file"""
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {"submissions": []}
        else:
            return {"submissions": []}

    def _save_database(self):
        """Save claims database to file"""
        with open(self.db_file, "w") as f:
            json.dump(self.claims, f, indent=2)

    def check_duplicate(
        self, email: str, flight_number: str, flight_date: str
    ) -> Tuple[bool, Optional[Dict]]:
        """
        Check if a claim already exists for this customer and flight
        
        Args:
            email: Customer email address
            flight_number: Flight number (e.g., KL1234)
            flight_date: Flight date (YYYY-MM-DD)
            
        Returns:
            Tuple of (is_duplicate, existing_claim_info)
        """
        for submission in self.claims.get("submissions", []):
            if (
                submission["email"].lower() == email.lower()
                and submission["flight_number"].upper() == flight_number.upper()
                and submission["flight_date"] == flight_date
            ):
                return True, submission
        return False, None

    def add_submission(
        self,
        email: str,
        flight_number: str,
        flight_date: str,
        passenger_name: str,
        compensation_amount: float,
        delay_hours: float,
        route: str,
        status: str = "pending",
    ) -> Dict:
        """
        Add a new claim submission to the database
        
        Args:
            email: Customer email address
            flight_number: Flight number
            flight_date: Flight date (YYYY-MM-DD)
            passenger_name: Name of the passenger
            compensation_amount: Calculated compensation amount
            delay_hours: Hours of delay
            route: Flight route (e.g., "AMS -> JFK")
            status: Claim status (pending, approved, rejected)
            
        Returns:
            The created submission record
        """
        submission = {
            "submission_id": self._generate_submission_id(),
            "email": email,
            "passenger_name": passenger_name,
            "flight_number": flight_number.upper(),
            "flight_date": flight_date,
            "route": route,
            "delay_hours": delay_hours,
            "compensation_amount": compensation_amount,
            "status": status,
            "submitted_at": datetime.now().isoformat(),
        }

        self.claims["submissions"].append(submission)
        self._save_database()
        return submission

    def _generate_submission_id(self) -> str:
        """Generate a unique submission ID"""
        count = len(self.claims.get("submissions", [])) + 1
        return f"CLM{datetime.now().strftime('%Y%m%d')}{count:04d}"

    def get_customer_submissions(self, email: str) -> List[Dict]:
        """Get all submissions for a specific customer email"""
        return [
            sub
            for sub in self.claims.get("submissions", [])
            if sub["email"].lower() == email.lower()
        ]

    def update_claim_status(self, submission_id: str, new_status: str) -> bool:
        """Update the status of a claim"""
        for submission in self.claims.get("submissions", []):
            if submission["submission_id"] == submission_id:
                submission["status"] = new_status
                submission["updated_at"] = datetime.now().isoformat()
                self._save_database()
                return True
        return False
