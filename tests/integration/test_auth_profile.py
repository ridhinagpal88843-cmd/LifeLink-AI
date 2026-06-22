import pytest


def test_complete_registration_and_auth_flow(client):
    """
    Test user signup, login, profile fetch, and profile updates.
    """
    signup_payload = {
        "email": "test.patient@lifelink.org",
        "password": "supersecretpassword",
        "full_name": "Alexander Pierce",
        "phone": "+1-555-0811",
        "emergency_health_profile": {
            "blood_group": "AB-",
            "medical_conditions": "Type 1 Diabetes",
            "allergies": "Gluten, Latex",
            "current_medications": "Insulin Glargine 10 units",
            "emergency_preferences": "Notify primary physician immediately"
        },
        "primary_doctor": {
            "name": "Dr. Susan Vance",
            "phone": "+1-555-9000",
            "email": "susan.vance@clinic.org",
            "specialty": "Endocrinology"
        },
        "emergency_contacts": [
            {
                "name": "Clara Pierce",
                "relationship": "Spouse",
                "phone": "+1-555-1111",
                "priority": 1
            },
            {
                "name": "Robert Pierce",
                "relationship": "Brother",
                "phone": "+1-555-2222",
                "priority": 2
            }
        ]
    }

    # 1. Test POST /signup
    signup_response = client.post("/signup", json=signup_payload)
    assert signup_response.status_code == 201
    signup_data = signup_response.json()
    assert signup_data["email"] == "test.patient@lifelink.org"
    assert "id" in signup_data
    assert signup_data["emergency_health_profile"]["blood_group"] == "AB-"
    assert signup_data["emergency_health_profile"]["primary_doctor"]["name"] == "Dr. Susan Vance"
    assert len(signup_data["emergency_contacts"]) == 2

    # 2. Test duplicate signup failure
    dup_response = client.post("/signup", json=signup_payload)
    assert dup_response.status_code == 400
    assert "already registered" in dup_response.json()["detail"]

    # 3. Test POST /login
    login_payload = {
        "email": "test.patient@lifelink.org",
        "password": "supersecretpassword"
    }
    login_response = client.post("/login", json=login_payload)
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    
    token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 4. Test unauthorized GET /profile
    unauth_response = client.get("/profile")
    assert unauth_response.status_code == 401

    # 5. Test authorized GET /profile
    profile_response = client.get("/profile", headers=headers)
    assert profile_response.status_code == 200
    profile_data = profile_response.json()
    assert profile_data["email"] == "test.patient@lifelink.org"
    assert profile_data["emergency_health_profile"]["blood_group"] == "AB-"

    # 6. Test PUT /profile update
    update_payload = {
        "full_name": "Alexander Pierce Updated",
        "phone": "+1-555-9999",
        "emergency_health_profile": {
            "blood_group": "AB-",
            "medical_conditions": "Type 1 Diabetes, Asthma",
            "allergies": "Gluten, Latex",
            "current_medications": "Insulin Glargine 10 units, Albuterol",
            "emergency_preferences": "Contact spouse immediately"
        },
        "emergency_contacts": [
            {
                "name": "Clara Pierce",
                "relationship": "Spouse",
                "phone": "+1-555-8888",
                "priority": 1
            }
        ]
    }
    update_response = client.put("/profile", json=update_payload, headers=headers)
    assert update_response.status_code == 200
    updated_data = update_response.json()
    assert updated_data["full_name"] == "Alexander Pierce Updated"
    assert updated_data["phone"] == "+1-555-9999"
    assert updated_data["emergency_health_profile"]["medical_conditions"] == "Type 1 Diabetes, Asthma"
    assert len(updated_data["emergency_contacts"]) == 1
    assert updated_data["emergency_contacts"][0]["phone"] == "+1-555-8888"

    # 7. Test contact limit violation (>5 contacts)
    excess_contacts_payload = {
        "emergency_contacts": [
            {"name": "C1", "relationship": "Friend", "phone": "1", "priority": 1},
            {"name": "C2", "relationship": "Friend", "phone": "2", "priority": 2},
            {"name": "C3", "relationship": "Friend", "phone": "3", "priority": 3},
            {"name": "C4", "relationship": "Friend", "phone": "4", "priority": 4},
            {"name": "C5", "relationship": "Friend", "phone": "5", "priority": 5},
            {"name": "C6", "relationship": "Friend", "phone": "6", "priority": 6}
        ]
    }
    excess_response = client.put("/profile", json=excess_contacts_payload, headers=headers)
    assert excess_response.status_code == 422 or excess_response.status_code == 400
