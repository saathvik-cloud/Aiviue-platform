"""
Employer Module Tests for AIVIUE Backend

Tests covered:
1. Create employer - success
2. Create employer - validation errors
3. Create employer - duplicate email
4. Get employer by ID - success
5. Get employer by ID - not found
6. Get employer by email - success
7. List employers - pagination
8. Update employer - success
9. Update employer - version conflict
10. Delete employer - soft delete
11. Delete employer - not found

Run: pytest tests/test_employer.py -v
"""

import asyncio
import pytest
from tests.test_data import (
    SAMPLE_EMPLOYER,
    SAMPLE_EMPLOYER_MINIMAL,
    SAMPLE_EMPLOYER_UPDATE,
    INVALID_EMPLOYER_PAYLOADS,
    EMPLOYER_RESPONSE_FIELDS,
    generate_unique_email,
)
from tests.conftest import assert_response_success, assert_response_error, assert_has_fields


API_PREFIX = "/api/v1/employers"


# =============================================================================
# CREATE EMPLOYER TESTS
# =============================================================================

class TestCreateEmployer:
    """Tests for POST /api/v1/employers"""
    
    def test_create_employer_success_full_data(self, api_client, sample_employer_data):
        """
        Test creating an employer with all fields.
        Expected: 201 Created with employer data returned.
        """
        response = api_client.post(API_PREFIX, json=sample_employer_data)
        
        assert_response_success(response, 201)
        data = response.json()
        
        # Verify required fields
        assert_has_fields(data, EMPLOYER_RESPONSE_FIELDS)
        
        # Verify data matches
        assert data["name"] == sample_employer_data["name"]
        assert data["email"] == sample_employer_data["email"]
        assert data["company_name"] == sample_employer_data["company_name"]
        assert data["is_active"] == True
        assert data["version"] == 1
        
        # Cleanup
        api_client.delete(f"{API_PREFIX}/{data['id']}?version=1")
    
    def test_create_employer_success_minimal_data(self, api_client):
        """
        Test creating an employer with only required fields.
        Expected: 201 Created.
        """
        data = SAMPLE_EMPLOYER_MINIMAL.copy()
        data["email"] = generate_unique_email("minimal")
        
        response = api_client.post(API_PREFIX, json=data)
        
        assert_response_success(response, 201)
        result = response.json()
        
        assert result["name"] == data["name"]
        assert result["email"] == data["email"]
        assert result["company_name"] == data["company_name"]
        
        # Optional fields should be None
        assert result.get("phone") is None
        assert result.get("company_website") is None
        
        # Cleanup
        api_client.delete(f"{API_PREFIX}/{result['id']}?version=1")
    
    def test_create_employer_duplicate_email(self, api_client, sample_employer_data):
        """
        Test creating employer with duplicate email.
        Expected: 409 Conflict.
        """
        # Create first employer
        response1 = api_client.post(API_PREFIX, json=sample_employer_data)
        assert_response_success(response1, 201)
        employer1 = response1.json()
        
        # Try to create with same email
        response2 = api_client.post(API_PREFIX, json=sample_employer_data)
        assert_response_error(response2, 409)
        
        # Cleanup
        api_client.delete(f"{API_PREFIX}/{employer1['id']}?version=1")
    
    @pytest.mark.parametrize("invalid_data", [
        {"name": "Test"},  # Missing email and company
        {"email": "test@test.com"},  # Missing name and company
        {"company_name": "Test Co"},  # Missing name and email
        {"name": "Test", "email": "invalid-email", "company_name": "Co"},  # Invalid email
        {"name": "", "email": "test@test.com", "company_name": "Co"},  # Empty name
    ])
    def test_create_employer_validation_errors(self, api_client, invalid_data):
        """
        Test creating employer with invalid data.
        Expected: 422 Validation Error.
        """
        response = api_client.post(API_PREFIX, json=invalid_data)
        assert response.status_code == 422


# =============================================================================
# GET EMPLOYER TESTS
# =============================================================================

class TestGetEmployer:
    """Tests for GET /api/v1/employers/{id}"""
    
    def test_get_employer_by_id_success(self, api_client, sample_employer_data):
        """
        Test getting employer by ID.
        Expected: 200 OK with employer data.
        """
        # Create employer
        create_response = api_client.post(API_PREFIX, json=sample_employer_data)
        employer = create_response.json()
        
        # Get by ID
        response = api_client.get(f"{API_PREFIX}/{employer['id']}")
        
        assert_response_success(response, 200)
        data = response.json()
        
        assert data["id"] == employer["id"]
        assert data["email"] == sample_employer_data["email"]
        
        # Cleanup
        api_client.delete(f"{API_PREFIX}/{employer['id']}?version=1")
    
    def test_get_employer_not_found(self, api_client):
        """
        Test getting non-existent employer.
        Expected: 404 Not Found.
        """
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = api_client.get(f"{API_PREFIX}/{fake_id}")
        
        assert_response_error(response, 404)
    
    def test_get_employer_invalid_uuid(self, api_client):
        """
        Test getting employer with invalid UUID format.
        Expected: 422 Validation Error.
        """
        response = api_client.get(f"{API_PREFIX}/invalid-uuid")
        
        assert response.status_code == 422
    
    def test_get_employer_by_email_success(self, api_client, sample_employer_data):
        """
        Test getting employer by email.
        Expected: 200 OK with employer data.
        """
        # Create employer
        create_response = api_client.post(API_PREFIX, json=sample_employer_data)
        employer = create_response.json()
        
        # Get by email
        response = api_client.get(f"{API_PREFIX}/email/{sample_employer_data['email']}")
        
        assert_response_success(response, 200)
        data = response.json()
        
        assert data["email"] == sample_employer_data["email"]
        
        # Cleanup
        api_client.delete(f"{API_PREFIX}/{employer['id']}?version=1")
    
    def test_get_employer_by_email_not_found(self, api_client):
        """
        Test getting employer by non-existent email.
        Expected: 404 Not Found.
        """
        response = api_client.get(f"{API_PREFIX}/email/nonexistent@email.com")
        
        assert_response_error(response, 404)


# =============================================================================
# LIST EMPLOYERS TESTS
# =============================================================================

class TestListEmployers:
    """Tests for GET /api/v1/employers"""
    
    def test_list_employers_empty(self, api_client):
        """
        Test listing employers when database might be empty.
        Expected: 200 OK with items array.
        """
        response = api_client.get(API_PREFIX)
        
        assert_response_success(response, 200)
        data = response.json()
        
        assert "items" in data
        assert isinstance(data["items"], list)
    
    def test_list_employers_with_data(self, api_client, sample_employer_data):
        """
        Test listing employers returns created employer.
        Expected: 200 OK with employer in list.
        """
        # Create employer
        create_response = api_client.post(API_PREFIX, json=sample_employer_data)
        employer = create_response.json()
        
        # List employers
        response = api_client.get(API_PREFIX)
        
        assert_response_success(response, 200)
        data = response.json()
        
        # Find our employer in list
        emails = [e["email"] for e in data["items"]]
        assert sample_employer_data["email"] in emails
        
        # Cleanup
        api_client.delete(f"{API_PREFIX}/{employer['id']}?version=1")
    
    def test_list_employers_pagination(self, api_client):
        """
        Test pagination parameters.
        Expected: 200 OK with limited results.
        """
        response = api_client.get(f"{API_PREFIX}?limit=5")
        
        assert_response_success(response, 200)
        data = response.json()
        
        assert len(data["items"]) <= 5
    
    def test_list_employers_filter_by_company(self, api_client, sample_employer_data):
        """
        Test filtering by company name.
        Expected: 200 OK with filtered results.
        """
        # Create employer
        create_response = api_client.post(API_PREFIX, json=sample_employer_data)
        employer = create_response.json()
        
        # Filter by company
        response = api_client.get(f"{API_PREFIX}?search={sample_employer_data['company_name'][:5]}")
        
        assert_response_success(response, 200)
        
        # Cleanup
        api_client.delete(f"{API_PREFIX}/{employer['id']}?version=1")


# =============================================================================
# UPDATE EMPLOYER TESTS
# =============================================================================

class TestUpdateEmployer:
    """Tests for PUT /api/v1/employers/{id}"""
    
    def test_update_employer_success(self, api_client, sample_employer_data):
        """
        Test updating employer.
        Expected: 200 OK with updated data.
        """
        # Create employer
        create_response = api_client.post(API_PREFIX, json=sample_employer_data)
        employer = create_response.json()
        
        # Update
        update_data = {
            "name": "Updated Name",
            "company_description": "Updated description",
            "version": employer["version"],
        }
        
        response = api_client.put(f"{API_PREFIX}/{employer['id']}", json=update_data)
        
        assert_response_success(response, 200)
        data = response.json()
        
        assert data["name"] == "Updated Name"
        assert data["company_description"] == "Updated description"
        assert data["version"] == employer["version"] + 1
        
        # Cleanup
        api_client.delete(f"{API_PREFIX}/{employer['id']}?version={data['version']}")
    
    def test_update_employer_version_conflict(self, api_client, sample_employer_data):
        """
        Test updating with wrong version (optimistic locking).
        Expected: 409 Conflict.
        """
        # Create employer
        create_response = api_client.post(API_PREFIX, json=sample_employer_data)
        employer = create_response.json()
        
        # Update with wrong version
        update_data = {
            "name": "Updated Name",
            "version": 999,  # Wrong version
        }
        
        response = api_client.put(f"{API_PREFIX}/{employer['id']}", json=update_data)
        
        assert_response_error(response, 409)
        
        # Cleanup
        api_client.delete(f"{API_PREFIX}/{employer['id']}?version=1")
    
    def test_update_employer_not_found(self, api_client):
        """
        Test updating non-existent employer.
        Expected: 404 Not Found.
        """
        fake_id = "00000000-0000-0000-0000-000000000000"
        update_data = {"name": "Test", "version": 1}
        
        response = api_client.put(f"{API_PREFIX}/{fake_id}", json=update_data)
        
        assert_response_error(response, 404)


# =============================================================================
# DELETE EMPLOYER TESTS
# =============================================================================

class TestDeleteEmployer:
    """Tests for DELETE /api/v1/employers/{id}"""
    
    def test_delete_employer_soft_delete(self, api_client, sample_employer_data):
        """
        Test soft deleting employer.
        Expected: 204 No Content, employer marked inactive.
        """
        # Create employer
        create_response = api_client.post(API_PREFIX, json=sample_employer_data)
        employer = create_response.json()
        
        # Delete
        response = api_client.delete(f"{API_PREFIX}/{employer['id']}?version=1")
        
        assert response.status_code == 204
        
        # Verify employer is not returned in normal GET
        get_response = api_client.get(f"{API_PREFIX}/{employer['id']}")
        assert get_response.status_code == 404
    
    def test_delete_employer_not_found(self, api_client):
        """
        Test deleting non-existent employer.
        Expected: 404 Not Found.
        """
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = api_client.delete(f"{API_PREFIX}/{fake_id}?version=1")
        
        assert_response_error(response, 404)
    
    def test_delete_employer_version_required(self, api_client, sample_employer_data):
        """
        Test deleting without version parameter.
        Expected: 422 Validation Error.
        """
        # Create employer
        create_response = api_client.post(API_PREFIX, json=sample_employer_data)
        employer = create_response.json()
        
        # Delete without version
        response = api_client.delete(f"{API_PREFIX}/{employer['id']}")
        
        assert response.status_code == 422
        
        # Cleanup
        api_client.delete(f"{API_PREFIX}/{employer['id']}?version=1")
