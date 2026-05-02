import pytest


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_success(self, client):
        """Test fetching all activities"""
        # Arrange
        expected_activities = ["Chess Club", "Programming Class"]
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert set(data.keys()) == set(expected_activities)
        assert data["Chess Club"]["max_participants"] == 3
        assert len(data["Chess Club"]["participants"]) == 1


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self, client):
        """Test successful signup for an activity"""
        # Arrange
        email = "new_student@mergington.edu"
        activity = "Chess Club"
        
        # Act
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {email} for {activity}"
        
        # Verify signup persisted
        activities_response = client.get("/activities")
        assert email in activities_response.json()[activity]["participants"]

    def test_signup_duplicate_student(self, client):
        """Test signup fails when student already registered"""
        # Arrange
        email = "michael@mergington.edu"  # Already in Chess Club
        activity = "Chess Club"
        
        # Act
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_invalid_activity(self, client):
        """Test signup fails for non-existent activity"""
        # Arrange
        email = "test@mergington.edu"
        activity = "Nonexistent Club"
        
        # Act
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_signup_at_capacity(self, client):
        """Test signup fails when activity is at max capacity"""
        # Arrange
        email1 = "student1@mergington.edu"
        email2 = "student2@mergington.edu"
        email3 = "student3@mergington.edu"
        activity = "Chess Club"  # Max 3, currently has 1
        
        # Act: Fill the activity to capacity
        response1 = client.post(
            f"/activities/{activity}/signup?email={email1}"
        )
        response2 = client.post(
            f"/activities/{activity}/signup?email={email2}"
        )
        # Try to signup when at capacity
        response3 = client.post(
            f"/activities/{activity}/signup?email={email3}"
        )
        
        # Assert: First two succeed, third fails
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response3.status_code == 400
        assert "maximum capacity" in response3.json()["detail"]
        
        # Verify capacity is reached
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity]["participants"]
        assert len(participants) == 3


class TestUnregisterFromActivity:
    """Tests for POST /activities/{activity_name}/unregister endpoint"""

    def test_unregister_success(self, client):
        """Test successful unregistration from an activity"""
        # Arrange
        email = "michael@mergington.edu"  # Already in Chess Club
        activity = "Chess Club"
        
        # Act
        response = client.post(
            f"/activities/{activity}/unregister?email={email}"
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Unregistered {email} from {activity}"
        
        # Verify removal persisted
        activities_response = client.get("/activities")
        assert email not in activities_response.json()[activity]["participants"]

    def test_unregister_participant_not_found(self, client):
        """Test unregister fails for non-registered participant"""
        # Arrange
        email = "not_registered@mergington.edu"
        activity = "Chess Club"
        
        # Act
        response = client.post(
            f"/activities/{activity}/unregister?email={email}"
        )
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_unregister_invalid_activity(self, client):
        """Test unregister fails for non-existent activity"""
        # Arrange
        email = "test@mergington.edu"
        activity = "Nonexistent Club"
        
        # Act
        response = client.post(
            f"/activities/{activity}/unregister?email={email}"
        )
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_unregister_frees_capacity(self, client):
        """Test that unregistering frees up a spot"""
        # Arrange
        email_to_remove = "michael@mergington.edu"
        email_to_add = "new_student@mergington.edu"
        activity = "Chess Club"
        
        # Act: Remove existing participant
        response1 = client.post(
            f"/activities/{activity}/unregister?email={email_to_remove}"
        )
        
        # Act: Add new participant (should succeed since spot is freed)
        response2 = client.post(
            f"/activities/{activity}/signup?email={email_to_add}"
        )
        
        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Verify new participant is registered
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity]["participants"]
        assert email_to_add in participants
        assert email_to_remove not in participants
