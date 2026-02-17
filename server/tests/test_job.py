"""
Job Module Tests for AIVIUE Backend

Tests covered:
1. Create job - success
2. Create job - validation errors
3. Create job - employer not found
4. Get job by ID - success
5. Get job by ID - not found
6. List jobs - with filters
7. Update job - success
8. Update job - version conflict
9. Publish job - success
10. Publish job - invalid status transition
11. Close job - success
12. Delete job - soft delete

Run: pytest tests/test_job.py -v
"""

import pytest
from tests.test_data import (
    SAMPLE_EMPLOYER,
    SAMPLE_JOB,
    SAMPLE_JOB_MINIMAL,
    SAMPLE_JOB_UPDATE,
    JOB_RESPONSE_FIELDS,
    JOB_STATUSES,
    WORK_TYPES,
    generate_unique_email,
)
from tests.conftest import assert_response_success, assert_response_error, assert_has_fields


API_PREFIX = "/api/v1/jobs"
EMPLOYER_PREFIX = "/api/v1/employers"


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def test_employer(api_client):
    """Create a test employer and clean up after test."""
    from tests.test_data import generate_unique_phone
    
    employer_data = SAMPLE_EMPLOYER.copy()
    employer_data["email"] = generate_unique_email("job_test_employer")
    employer_data["phone"] = generate_unique_phone()  # Ensure unique phone
    
    response = api_client.post(EMPLOYER_PREFIX, json=employer_data)
    employer = response.json()
    
    # Check if creation succeeded
    if "error" in employer:
        pytest.fail(f"Failed to create test employer: {employer}")
    
    yield employer
    
    # Cleanup (only if we have an ID)
    if "id" in employer and "version" in employer:
        api_client.delete(f"{EMPLOYER_PREFIX}/{employer['id']}?version={employer['version']}")


# =============================================================================
# CREATE JOB TESTS
# =============================================================================

class TestCreateJob:
    """Tests for POST /api/v1/jobs"""
    
    def test_create_job_success_full_data(self, api_client, test_employer):
        """
        Test creating a job with all fields.
        Expected: 201 Created with job in draft status.
        """
        job_data = SAMPLE_JOB.copy()
        job_data["employer_id"] = test_employer["id"]
        
        response = api_client.post(API_PREFIX, json=job_data)
        
        assert_response_success(response, 201)
        data = response.json()
        
        # Verify required fields
        assert_has_fields(data, JOB_RESPONSE_FIELDS)
        
        # Verify data matches
        assert data["title"] == job_data["title"]
        assert data["employer_id"] == test_employer["id"]
        assert data["status"] == "draft"  # Default status
        assert data["is_active"] == True
        assert data["version"] == 1
        
        # Cleanup
        api_client.delete(f"{API_PREFIX}/{data['id']}?version=1")
    
    def test_create_job_success_minimal_data(self, api_client, test_employer):
        """
        Test creating a job with only required fields.
        Expected: 201 Created.
        """
        job_data = SAMPLE_JOB_MINIMAL.copy()
        job_data["employer_id"] = test_employer["id"]
        
        response = api_client.post(API_PREFIX, json=job_data)
        
        assert_response_success(response, 201)
        data = response.json()
        
        assert data["title"] == job_data["title"]
        assert data["status"] == "draft"
        
        # Cleanup
        api_client.delete(f"{API_PREFIX}/{data['id']}?version=1")
    
    def test_create_job_employer_not_found(self, api_client):
        """
        Test creating job with non-existent employer.
        Expected: 404 Not Found.
        """
        job_data = SAMPLE_JOB.copy()
        job_data["employer_id"] = "00000000-0000-0000-0000-000000000000"
        
        response = api_client.post(API_PREFIX, json=job_data)
        
        # Should fail because employer doesn't exist
        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "EMPLOYER_NOT_FOUND"
    
    def test_create_job_invalid_work_type(self, api_client, test_employer):
        """
        Test creating job with invalid work type.
        Expected: 422 Validation Error.
        """
        job_data = SAMPLE_JOB.copy()
        job_data["employer_id"] = test_employer["id"]
        job_data["work_type"] = "invalid_type"
        
        response = api_client.post(API_PREFIX, json=job_data)
        
        assert response.status_code == 422
    
    def test_create_job_invalid_salary_range(self, api_client, test_employer):
        """
        Test creating job with min salary > max salary.
        Expected: 422 Validation Error.
        """
        job_data = SAMPLE_JOB.copy()
        job_data["employer_id"] = test_employer["id"]
        job_data["salary_range_min"] = 200000
        job_data["salary_range_max"] = 100000
        
        response = api_client.post(API_PREFIX, json=job_data)
        
        assert response.status_code == 422


# =============================================================================
# GET JOB TESTS
# =============================================================================

class TestGetJob:
    """Tests for GET /api/v1/jobs/{id}"""
    
    def test_get_job_by_id_success(self, api_client, test_employer):
        """
        Test getting job by ID.
        Expected: 200 OK with job data.
        """
        # Create job
        job_data = SAMPLE_JOB.copy()
        job_data["employer_id"] = test_employer["id"]
        create_response = api_client.post(API_PREFIX, json=job_data)
        job = create_response.json()
        
        # Get by ID
        response = api_client.get(f"{API_PREFIX}/{job['id']}")
        
        assert_response_success(response, 200)
        data = response.json()
        
        assert data["id"] == job["id"]
        assert data["title"] == job_data["title"]
        
        # Cleanup
        api_client.delete(f"{API_PREFIX}/{job['id']}?version=1")
    
    def test_get_job_not_found(self, api_client):
        """
        Test getting non-existent job.
        Expected: 404 Not Found.
        """
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = api_client.get(f"{API_PREFIX}/{fake_id}")
        
        assert_response_error(response, 404)


# =============================================================================
# LIST JOBS TESTS
# =============================================================================

class TestListJobs:
    """Tests for GET /api/v1/jobs"""
    
    def test_list_jobs_empty(self, api_client):
        """
        Test listing jobs.
        Expected: 200 OK with items array.
        """
        response = api_client.get(API_PREFIX)
        
        assert_response_success(response, 200)
        data = response.json()
        
        assert "items" in data
        assert isinstance(data["items"], list)
    
    def test_list_jobs_filter_by_employer(self, api_client, test_employer):
        """
        Test filtering jobs by employer_id.
        Expected: 200 OK with filtered results.
        """
        # Create job
        job_data = SAMPLE_JOB.copy()
        job_data["employer_id"] = test_employer["id"]
        create_response = api_client.post(API_PREFIX, json=job_data)
        job = create_response.json()
        
        # Filter by employer
        response = api_client.get(f"{API_PREFIX}?employer_id={test_employer['id']}")
        
        assert_response_success(response, 200)
        data = response.json()
        
        # All returned jobs should belong to this employer
        for j in data["items"]:
            assert j["employer_id"] == test_employer["id"]
        
        # Cleanup
        api_client.delete(f"{API_PREFIX}/{job['id']}?version=1")
    
    def test_list_jobs_filter_by_status(self, api_client, test_employer):
        """
        Test filtering jobs by status.
        Expected: 200 OK with filtered results.
        """
        # Create job (draft status)
        job_data = SAMPLE_JOB.copy()
        job_data["employer_id"] = test_employer["id"]
        create_response = api_client.post(API_PREFIX, json=job_data)
        job = create_response.json()
        
        # Filter by status
        response = api_client.get(f"{API_PREFIX}?status=draft")
        
        assert_response_success(response, 200)
        data = response.json()
        
        for j in data["items"]:
            assert j["status"] == "draft"
        
        # Cleanup
        api_client.delete(f"{API_PREFIX}/{job['id']}?version=1")
    
    def test_list_jobs_filter_by_work_type(self, api_client, test_employer):
        """
        Test filtering jobs by work type.
        Expected: 200 OK with filtered results.
        """
        # Create remote job
        job_data = SAMPLE_JOB.copy()
        job_data["employer_id"] = test_employer["id"]
        job_data["work_type"] = "remote"
        create_response = api_client.post(API_PREFIX, json=job_data)
        job = create_response.json()
        
        # Filter by work type
        response = api_client.get(f"{API_PREFIX}?work_type=remote")
        
        assert_response_success(response, 200)
        
        # Cleanup
        api_client.delete(f"{API_PREFIX}/{job['id']}?version=1")
    
    def test_list_jobs_pagination(self, api_client):
        """
        Test pagination.
        Expected: 200 OK with limited results.
        """
        response = api_client.get(f"{API_PREFIX}?limit=5")
        
        assert_response_success(response, 200)
        data = response.json()
        
        assert len(data["items"]) <= 5

    def test_list_jobs_filter_by_category_id(self, api_client):
        """
        Test filtering jobs by category_id (recommendation use case).
        Expected: 200 OK; API accepts category_id and returns valid list.
        """
        from tests.test_data import generate_uuid
        category_id = generate_uuid()
        response = api_client.get(f"{API_PREFIX}?status=published&category_id={category_id}")
        assert_response_success(response, 200)
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_list_jobs_filter_by_role_id(self, api_client):
        """
        Test filtering jobs by role_id (recommendation use case).
        Expected: 200 OK; API accepts role_id and returns valid list.
        """
        from tests.test_data import generate_uuid
        role_id = generate_uuid()
        response = api_client.get(f"{API_PREFIX}?status=published&role_id={role_id}")
        assert_response_success(response, 200)
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_list_jobs_recommendation_filters_experience_skills_salary(self, api_client):
        """
        Test recommendation filters: candidate_experience_years, skills, min_salary_expectation.
        Expected: 200 OK; API accepts params and returns valid list.
        """
        response = api_client.get(
            f"{API_PREFIX}?status=published"
            "&candidate_experience_years=3"
            "&skills=Python,React"
            "&min_salary_expectation=50000"
        )
        assert_response_success(response, 200)
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)


# =============================================================================
# UPDATE JOB TESTS
# =============================================================================

class TestUpdateJob:
    """Tests for PUT /api/v1/jobs/{id}"""
    
    def test_update_job_success(self, api_client, test_employer):
        """
        Test updating job.
        Expected: 200 OK with updated data.
        """
        # Create job
        job_data = SAMPLE_JOB.copy()
        job_data["employer_id"] = test_employer["id"]
        create_response = api_client.post(API_PREFIX, json=job_data)
        job = create_response.json()
        
        # Update
        update_data = {
            "title": "Updated Job Title",
            "salary_range_max": 200000,
            "version": job["version"],
        }
        
        response = api_client.put(f"{API_PREFIX}/{job['id']}", json=update_data)
        
        assert_response_success(response, 200)
        data = response.json()
        
        assert data["title"] == "Updated Job Title"
        assert data["salary_range_max"] == 200000
        assert data["version"] == job["version"] + 1
        
        # Cleanup
        api_client.delete(f"{API_PREFIX}/{job['id']}?version={data['version']}")
    
    def test_update_job_version_conflict(self, api_client, test_employer):
        """
        Test updating with wrong version.
        Expected: 409 Conflict.
        """
        # Create job
        job_data = SAMPLE_JOB.copy()
        job_data["employer_id"] = test_employer["id"]
        create_response = api_client.post(API_PREFIX, json=job_data)
        job = create_response.json()
        
        # Update with wrong version
        update_data = {
            "title": "Updated Title",
            "version": 999,
        }
        
        response = api_client.put(f"{API_PREFIX}/{job['id']}", json=update_data)
        
        assert_response_error(response, 409)
        
        # Cleanup
        api_client.delete(f"{API_PREFIX}/{job['id']}?version=1")


# =============================================================================
# PUBLISH JOB TESTS
# =============================================================================

class TestPublishJob:
    """Tests for POST /api/v1/jobs/{id}/publish"""
    
    def test_publish_job_success(self, api_client, test_employer):
        """
        Test publishing a draft job.
        Expected: 200 OK with status=published.
        """
        # Create job (draft)
        job_data = SAMPLE_JOB.copy()
        job_data["employer_id"] = test_employer["id"]
        create_response = api_client.post(API_PREFIX, json=job_data)
        job = create_response.json()
        
        assert job["status"] == "draft"
        
        # Publish
        response = api_client.post(
            f"{API_PREFIX}/{job['id']}/publish",
            json={"version": job["version"]}
        )
        
        assert_response_success(response, 200)
        data = response.json()
        
        assert data["status"] == "published"
        assert data["published_at"] is not None
        
        # Cleanup
        api_client.delete(f"{API_PREFIX}/{job['id']}?version={data['version']}")
    
    def test_publish_job_already_published(self, api_client, test_employer):
        """
        Test publishing an already published job.
        Expected: 422 Business Error.
        """
        # Create and publish job
        job_data = SAMPLE_JOB.copy()
        job_data["employer_id"] = test_employer["id"]
        create_response = api_client.post(API_PREFIX, json=job_data)
        job = create_response.json()
        
        # Publish first time
        publish_response = api_client.post(
            f"{API_PREFIX}/{job['id']}/publish",
            json={"version": job["version"]}
        )
        published_job = publish_response.json()
        
        # Try to publish again
        response = api_client.post(
            f"{API_PREFIX}/{job['id']}/publish",
            json={"version": published_job["version"]}
        )
        
        assert response.status_code == 422
        
        # Cleanup
        api_client.delete(f"{API_PREFIX}/{job['id']}?version={published_job['version']}")


# =============================================================================
# CLOSE JOB TESTS
# =============================================================================

class TestCloseJob:
    """Tests for POST /api/v1/jobs/{id}/close"""
    
    def test_close_job_success(self, api_client, test_employer):
        """
        Test closing a published job.
        Expected: 200 OK with status=closed.
        """
        # Create and publish job
        job_data = SAMPLE_JOB.copy()
        job_data["employer_id"] = test_employer["id"]
        create_response = api_client.post(API_PREFIX, json=job_data)
        job = create_response.json()
        
        # Publish
        publish_response = api_client.post(
            f"{API_PREFIX}/{job['id']}/publish",
            json={"version": job["version"]}
        )
        published_job = publish_response.json()
        
        # Close
        response = api_client.post(
            f"{API_PREFIX}/{job['id']}/close",
            json={"version": published_job["version"], "reason": "Position filled"}
        )
        
        assert_response_success(response, 200)
        data = response.json()
        
        assert data["status"] == "closed"
        assert data["closed_at"] is not None
        
        # Cleanup
        api_client.delete(f"{API_PREFIX}/{job['id']}?version={data['version']}")
    
    def test_close_job_already_closed(self, api_client, test_employer):
        """
        Test closing an already closed job.
        Expected: 422 Business Error.
        """
        # Create, publish, and close job
        job_data = SAMPLE_JOB.copy()
        job_data["employer_id"] = test_employer["id"]
        create_response = api_client.post(API_PREFIX, json=job_data)
        job = create_response.json()
        
        # Publish
        publish_response = api_client.post(
            f"{API_PREFIX}/{job['id']}/publish",
            json={"version": job["version"]}
        )
        published_job = publish_response.json()
        
        # Close first time
        close_response = api_client.post(
            f"{API_PREFIX}/{job['id']}/close",
            json={"version": published_job["version"]}
        )
        closed_job = close_response.json()
        
        # Try to close again
        response = api_client.post(
            f"{API_PREFIX}/{job['id']}/close",
            json={"version": closed_job["version"]}
        )
        
        assert response.status_code == 422
        
        # Cleanup
        api_client.delete(f"{API_PREFIX}/{job['id']}?version={closed_job['version']}")


# =============================================================================
# DELETE JOB TESTS
# =============================================================================

class TestDeleteJob:
    """Tests for DELETE /api/v1/jobs/{id}"""
    
    def test_delete_job_success(self, api_client, test_employer):
        """
        Test soft deleting a job.
        Expected: 204 No Content.
        """
        # Create job
        job_data = SAMPLE_JOB.copy()
        job_data["employer_id"] = test_employer["id"]
        create_response = api_client.post(API_PREFIX, json=job_data)
        job = create_response.json()
        
        # Delete
        response = api_client.delete(f"{API_PREFIX}/{job['id']}?version=1")
        
        assert response.status_code == 204
        
        # Verify job is not returned
        get_response = api_client.get(f"{API_PREFIX}/{job['id']}")
        assert get_response.status_code == 404
    
    def test_delete_job_not_found(self, api_client):
        """
        Test deleting non-existent job.
        Expected: 404 Not Found.
        """
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = api_client.delete(f"{API_PREFIX}/{fake_id}?version=1")
        
        assert_response_error(response, 404)
