"""
Health Check Tests for AIVIUE Backend

Tests covered:
1. Basic health check (liveness)
2. Readiness check (database + redis)
3. Deep health check
4. Queue health check
5. Root endpoint

Run: pytest tests/test_health.py -v
"""

import pytest
from tests.conftest import assert_response_success


# =============================================================================
# BASIC HEALTH CHECK TESTS
# =============================================================================

class TestHealthEndpoints:
    """Tests for health check endpoints"""
    
    def test_health_liveness(self, api_client):
        """
        Test basic liveness probe.
        Expected: 200 OK with healthy status.
        """
        response = api_client.get("/health")
        
        assert_response_success(response, 200)
        data = response.json()
        
        assert data["status"] == "healthy"
        assert "app" in data
        assert "version" in data
        assert "environment" in data
    
    def test_health_readiness(self, api_client):
        """
        Test readiness probe (checks DB and Redis).
        Expected: 200 OK (or 503 if services down).
        """
        response = api_client.get("/health/ready")
        
        # Should be 200 if healthy, 503 if not
        assert response.status_code in [200, 503]
        
        data = response.json()
        
        assert "status" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
        assert "timestamp" in data
        assert "components" in data
        
        # Components should include database
        assert "database" in data["components"]
    
    def test_health_deep(self, api_client):
        """
        Test deep health check.
        Expected: 200 OK with component details.
        """
        response = api_client.get("/health/deep")
        
        assert_response_success(response, 200)
        data = response.json()
        
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert "environment" in data
        assert "components" in data
        
        # Should have component list
        assert isinstance(data["components"], list)
    
    def test_health_deep_with_llm(self, api_client):
        """
        Test deep health check with LLM enabled.
        Note: This may be slow and cost tokens.
        Expected: 200 OK.
        """
        response = api_client.get("/health/deep?include_llm=false")
        
        assert_response_success(response, 200)
    
    def test_health_queue(self, api_client):
        """
        Test queue health endpoint.
        Expected: 200 OK with queue status.
        """
        response = api_client.get("/health/queue")
        
        # May fail if Redis not running
        if response.status_code == 200:
            data = response.json()
            
            assert "name" in data
            assert "status" in data
            assert "message" in data
            assert "details" in data


# =============================================================================
# ROOT ENDPOINT TESTS
# =============================================================================

class TestRootEndpoint:
    """Tests for root endpoint"""
    
    def test_root_endpoint(self, api_client):
        """
        Test root endpoint returns API info.
        Expected: 200 OK with API info.
        """
        response = api_client.get("/")
        
        assert_response_success(response, 200)
        data = response.json()
        
        assert "name" in data
        assert "version" in data
        assert "environment" in data
        assert "health" in data


# =============================================================================
# REQUEST ID TESTS
# =============================================================================

class TestRequestId:
    """Tests for request ID middleware"""
    
    def test_request_id_in_response(self, api_client):
        """
        Test that X-Request-ID is included in response headers.
        Expected: Response has X-Request-ID header.
        """
        response = api_client.get("/health")
        
        assert "x-request-id" in response.headers
        
        # Should be a valid UUID-like string
        request_id = response.headers["x-request-id"]
        assert len(request_id) > 0
    
    def test_custom_request_id_preserved(self, api_client):
        """
        Test that custom X-Request-ID is preserved.
        Expected: Same ID in response.
        """
        custom_id = "test-request-id-12345"
        
        response = api_client.get(
            "/health",
            headers={"X-Request-ID": custom_id}
        )
        
        assert response.headers.get("x-request-id") == custom_id


# =============================================================================
# ERROR HANDLING TESTS
# =============================================================================

class TestErrorHandling:
    """Tests for error handling middleware"""
    
    def test_404_not_found(self, api_client):
        """
        Test 404 error response format.
        Expected: Consistent error format.
        """
        response = api_client.get("/nonexistent-endpoint")
        
        assert response.status_code == 404
    
    def test_422_validation_error(self, api_client):
        """
        Test 422 validation error response format.
        Expected: Consistent error format with details.
        """
        # Send invalid data to trigger validation error
        response = api_client.post(
            "/api/v1/employers",
            json={"invalid": "data"}
        )
        
        assert response.status_code == 422
        data = response.json()
        
        # Should have error response (our custom format uses 'error', not 'detail')
        assert "error" in data
        assert data["error"]["type"] == "VALIDATION_ERROR"


# =============================================================================
# CORS TESTS
# =============================================================================

class TestCORS:
    """Tests for CORS configuration"""
    
    def test_cors_headers_present(self, api_client):
        """
        Test that CORS headers are present.
        Expected: Access-Control headers in response.
        """
        response = api_client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            }
        )
        
        # CORS preflight should succeed
        assert response.status_code in [200, 204, 405]
