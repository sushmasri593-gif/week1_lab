"""Tests for the Mergington High School Activities API"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

# Create test client
client = TestClient(app)


class TestActivitiesEndpoint:
    """Test the /activities endpoint"""

    def test_get_activities_returns_list(self):
        """Test that GET /activities returns a list of activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0

    def test_activities_have_required_fields(self):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        required_fields = [
            "name",
            "description",
            "schedule",
            "max_participants",
            "participants",
        ]
        for activity_name, activity_data in data.items():
            for field in required_fields:
                assert field in activity_data, f"Activity {activity_name} missing {field}"

    def test_activities_have_valid_participants(self):
        """Test that participants lists are valid"""
        response = client.get("/activities")
        data = response.json()
        for activity_name, activity_data in data.items():
            assert isinstance(
                activity_data["participants"], list
            ), f"{activity_name} participants should be a list"
            assert len(activity_data["participants"]) <= activity_data[
                "max_participants"
            ], f"{activity_name} has too many participants"


class TestSignupEndpoint:
    """Test the signup endpoint"""

    def test_signup_for_valid_activity(self):
        """Test signing up for a valid activity"""
        response = client.post(
            "/activities/Tennis Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "test@mergington.edu" in data["message"]

    def test_signup_adds_participant(self):
        """Test that signup actually adds the participant"""
        email = "newstudent@mergington.edu"
        activity = "Basketball Team"

        # Get initial count
        response = client.get("/activities")
        initial_count = len(response.json()[activity]["participants"])

        # Sign up
        client.post(f"/activities/{activity}/signup?email={email}")

        # Check count increased
        response = client.get("/activities")
        final_count = len(response.json()[activity]["participants"])
        assert final_count == initial_count + 1

    def test_signup_for_invalid_activity(self):
        """Test signing up for an activity that doesn't exist"""
        response = client.post(
            "/activities/Nonexistent Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_with_invalid_email(self):
        """Test that signup accepts any email format"""
        response = client.post("/activities/Tennis Club/signup?email=invalid-email")
        assert response.status_code == 200


class TestRemoveParticipantEndpoint:
    """Test the delete participant endpoint"""

    def test_remove_existing_participant(self):
        """Test removing a participant that exists"""
        activity = "Tennis Club"
        # First, get the current participants
        response = client.get("/activities")
        initial_participants = response.json()[activity]["participants"].copy()

        if initial_participants:
            email_to_remove = initial_participants[0]
            # Remove the participant
            response = client.delete(
                f"/activities/{activity}/participants/{email_to_remove}"
            )
            assert response.status_code == 200
            data = response.json()
            assert "Removed" in data["message"]

            # Verify participant was removed
            response = client.get("/activities")
            final_participants = response.json()[activity]["participants"]
            assert email_to_remove not in final_participants

    def test_remove_nonexistent_participant(self):
        """Test removing a participant that doesn't exist in the activity"""
        activity = "Tennis Club"
        email = "nonexistent@mergington.edu"
        response = client.delete(
            f"/activities/{activity}/participants/{email}"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Participant not found" in data["detail"]

    def test_remove_from_invalid_activity(self):
        """Test removing a participant from an activity that doesn't exist"""
        response = client.delete(
            "/activities/Nonexistent Club/participants/test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]


class TestRootEndpoint:
    """Test the root endpoint"""

    def test_root_redirects_to_static(self):
        """Test that / redirects to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"
