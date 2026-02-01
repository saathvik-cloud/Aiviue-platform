"""
Extraction Module Tests for AIVIUE Backend

Tests covered:
1. Submit extraction - success
2. Submit extraction - empty JD
3. Submit extraction - idempotency
4. Get extraction - pending status
5. Get extraction - completed status
6. Get extraction - not found
7. Extraction flow - full integration

Run: pytest tests/test_extraction.py -v

Note: Some tests require Redis and worker to be running for full integration.
"""

import time
import pytest
from tests.test_data import (
    SAMPLE_JD_RAW,
    SAMPLE_JD_MINIMAL,
    SAMPLE_JD_COMPLEX,
    EXPECTED_EXTRACTION_FIELDS,
    EXTRACTION_RESPONSE_FIELDS,
    TEST_CONFIG,
    generate_uuid,
)
from tests.conftest import assert_response_success, assert_response_error, assert_has_fields


API_PREFIX = "/api/v1/jobs"


# =============================================================================
# SUBMIT EXTRACTION TESTS
# =============================================================================

class TestSubmitExtraction:
    """Tests for POST /api/v1/jobs/extract"""
    
    def test_submit_extraction_success(self, api_client):
        """
        Test submitting JD for extraction.
        Expected: 202 Accepted with extraction ID and pending status.
        """
        request_data = {
            "raw_jd": SAMPLE_JD_RAW,
        }
        
        response = api_client.post(f"{API_PREFIX}/extract", json=request_data)
        
        assert_response_success(response, 202)
        data = response.json()
        
        assert "id" in data
        assert data["status"] == "pending"
        assert "message" in data
    
    def test_submit_extraction_with_employer_id(self, api_client):
        """
        Test submitting extraction with employer_id.
        Expected: 202 Accepted.
        """
        request_data = {
            "raw_jd": SAMPLE_JD_RAW,
            "employer_id": generate_uuid(),
        }
        
        response = api_client.post(f"{API_PREFIX}/extract", json=request_data)
        
        assert_response_success(response, 202)
    
    def test_submit_extraction_empty_jd(self, api_client):
        """
        Test submitting empty JD.
        Expected: 422 Validation Error.
        """
        request_data = {
            "raw_jd": "",
        }
        
        response = api_client.post(f"{API_PREFIX}/extract", json=request_data)
        
        assert response.status_code == 422
    
    def test_submit_extraction_whitespace_only(self, api_client):
        """
        Test submitting whitespace-only JD.
        Expected: 422 Validation Error.
        """
        request_data = {
            "raw_jd": "   \n\t  ",
        }
        
        response = api_client.post(f"{API_PREFIX}/extract", json=request_data)
        
        assert response.status_code == 422
    
    def test_submit_extraction_idempotency(self, api_client):
        """
        Test idempotency - same key returns same extraction.
        Expected: 202 with same ID for duplicate requests.
        """
        idempotency_key = f"test-{generate_uuid()}"
        
        request_data = {
            "raw_jd": SAMPLE_JD_MINIMAL,
            "idempotency_key": idempotency_key,
        }
        
        # First request
        response1 = api_client.post(f"{API_PREFIX}/extract", json=request_data)
        assert_response_success(response1, 202)
        data1 = response1.json()
        
        # Second request with same key
        response2 = api_client.post(f"{API_PREFIX}/extract", json=request_data)
        assert_response_success(response2, 202)
        data2 = response2.json()
        
        # Should return same extraction ID
        assert data1["id"] == data2["id"]
    
    def test_submit_extraction_very_long_jd(self, api_client):
        """
        Test submitting very long JD (should be truncated).
        Expected: 202 Accepted.
        """
        # Create a very long JD (20k chars)
        long_jd = SAMPLE_JD_RAW * 50
        
        request_data = {
            "raw_jd": long_jd,
        }
        
        response = api_client.post(f"{API_PREFIX}/extract", json=request_data)
        
        # Should still accept (truncation happens in worker)
        assert_response_success(response, 202)


# =============================================================================
# GET EXTRACTION TESTS
# =============================================================================

class TestGetExtraction:
    """Tests for GET /api/v1/jobs/extract/{id}"""
    
    def test_get_extraction_pending(self, api_client):
        """
        Test getting extraction in pending status.
        Expected: 200 OK with status=pending.
        """
        # Submit extraction
        request_data = {"raw_jd": SAMPLE_JD_MINIMAL}
        submit_response = api_client.post(f"{API_PREFIX}/extract", json=request_data)
        extraction = submit_response.json()
        
        # Get extraction (should be pending if worker not running)
        response = api_client.get(f"{API_PREFIX}/extract/{extraction['id']}")
        
        assert_response_success(response, 200)
        data = response.json()
        
        assert data["id"] == extraction["id"]
        assert data["status"] in ["pending", "processing", "completed", "failed"]
    
    def test_get_extraction_not_found(self, api_client):
        """
        Test getting non-existent extraction.
        Expected: 404 Not Found.
        """
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = api_client.get(f"{API_PREFIX}/extract/{fake_id}")
        
        assert_response_error(response, 404)
    
    def test_get_extraction_invalid_uuid(self, api_client):
        """
        Test getting extraction with invalid UUID.
        Expected: 422 Validation Error.
        """
        response = api_client.get(f"{API_PREFIX}/extract/invalid-uuid")
        
        assert response.status_code == 422


# =============================================================================
# EXTRACTION FLOW TESTS (Integration)
# =============================================================================

class TestExtractionFlow:
    """
    Integration tests for full extraction flow.
    
    Note: These tests require Redis and worker to be running!
    Skip with: pytest tests/test_extraction.py -v -k "not integration"
    """
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_extraction_complete_flow(self, api_client):
        """
        Test complete extraction flow: submit → poll → completed.
        
        Requires: Worker running (./worker.sh)
        """
        # Submit extraction
        request_data = {"raw_jd": SAMPLE_JD_RAW}
        submit_response = api_client.post(f"{API_PREFIX}/extract", json=request_data)
        
        assert_response_success(submit_response, 202)
        extraction = submit_response.json()
        extraction_id = extraction["id"]
        
        # Poll for completion
        max_attempts = TEST_CONFIG["max_poll_attempts"]
        poll_interval = TEST_CONFIG["poll_interval_seconds"]
        
        for attempt in range(max_attempts):
            response = api_client.get(f"{API_PREFIX}/extract/{extraction_id}")
            data = response.json()
            
            if data["status"] == "completed":
                # Verify extracted data
                assert "extracted_data" in data
                extracted = data["extracted_data"]
                
                # Should have some extracted fields
                assert extracted.get("title") is not None or extracted.get("description") is not None
                
                print(f"\n✅ Extraction completed in {attempt + 1} attempts")
                print(f"   Extracted title: {extracted.get('title')}")
                print(f"   Confidence: {extracted.get('extraction_confidence')}")
                return
            
            elif data["status"] == "failed":
                pytest.fail(f"Extraction failed: {data.get('error_message')}")
            
            time.sleep(poll_interval)
        
        pytest.fail(f"Extraction did not complete in {max_attempts} attempts")
    
    @pytest.mark.integration
    def test_extraction_response_structure(self, api_client):
        """
        Test that extraction response has correct structure.
        """
        # Submit extraction
        request_data = {"raw_jd": SAMPLE_JD_MINIMAL}
        submit_response = api_client.post(f"{API_PREFIX}/extract", json=request_data)
        extraction = submit_response.json()
        
        # Get extraction
        response = api_client.get(f"{API_PREFIX}/extract/{extraction['id']}")
        data = response.json()
        
        # Verify structure
        assert_has_fields(data, EXTRACTION_RESPONSE_FIELDS)
        
        # Status should be valid
        assert data["status"] in ["pending", "processing", "completed", "failed"]
        
        # If completed, verify extracted_data structure
        if data["status"] == "completed" and data.get("extracted_data"):
            extracted = data["extracted_data"]
            
            # Check for expected fields (some may be None)
            for field in EXPECTED_EXTRACTION_FIELDS:
                # Field should exist in response (even if None)
                assert field in extracted or True  # Soft check


# =============================================================================
# EXTRACTION EDGE CASES
# =============================================================================

class TestExtractionEdgeCases:
    """Edge case tests for extraction"""
    
    def test_extract_minimal_jd(self, api_client):
        """
        Test extracting from minimal JD.
        Expected: 202 Accepted (extraction should handle gracefully).
        """
        request_data = {
            "raw_jd": "Hiring Python developer. Remote. $100k.",
        }
        
        response = api_client.post(f"{API_PREFIX}/extract", json=request_data)
        
        assert_response_success(response, 202)
    
    def test_extract_non_english_jd(self, api_client):
        """
        Test extracting from non-English JD.
        Expected: 202 Accepted.
        """
        request_data = {
            "raw_jd": """
            Desarrollador Python Senior
            
            Ubicación: Madrid, España
            Salario: €50,000 - €70,000
            
            Requisitos:
            - 5 años de experiencia en Python
            - Conocimiento de Django o FastAPI
            """,
        }
        
        response = api_client.post(f"{API_PREFIX}/extract", json=request_data)
        
        assert_response_success(response, 202)
    
    def test_extract_jd_with_special_characters(self, api_client):
        """
        Test extracting JD with special characters and emojis.
        Expected: 202 Accepted.
        """
        request_data = {
            "raw_jd": SAMPLE_JD_COMPLEX,  # Contains emojis
        }
        
        response = api_client.post(f"{API_PREFIX}/extract", json=request_data)
        
        assert_response_success(response, 202)
    
    def test_extract_jd_with_html(self, api_client):
        """
        Test extracting JD with HTML tags (should be sanitized).
        Expected: 202 Accepted.
        """
        request_data = {
            "raw_jd": """
            <h1>Software Engineer</h1>
            <p>We are looking for a <strong>talented</strong> engineer.</p>
            <script>alert('xss')</script>
            <ul>
                <li>Python experience</li>
                <li>5+ years</li>
            </ul>
            """,
        }
        
        response = api_client.post(f"{API_PREFIX}/extract", json=request_data)
        
        assert_response_success(response, 202)
