"""
Integration tests for web API cognitive architecture endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from broca.web_api import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


class TestWebAPICognitiveArchitecture:
    """Integration tests for web API cognitive architecture endpoints."""
    
    def test_health_endpoint_exists(self, client):
        """Test that health endpoint exists."""
        response = client.get("/api/cognitive-architecture/health")
        # Should either return 200 (if enabled) or 503 (if not enabled)
        assert response.status_code in [200, 503]
    
    def test_statistics_endpoint_exists(self, client):
        """Test that statistics endpoint exists."""
        response = client.get("/api/cognitive-architecture/statistics")
        # Should return 200 with statistics
        assert response.status_code == 200
        data = response.json()
        assert "components" in data
        assert "timestamp" in data
    
    def test_reconfiguration_endpoint_exists(self, client):
        """Test that reconfiguration endpoint exists."""
        response = client.post("/api/cognitive-architecture/reconfigure")
        # Should either return 200 (if enabled) or 503 (if not enabled)
        assert response.status_code in [200, 503]
    
    def test_statistics_response_structure(self, client):
        """Test that statistics response has correct structure."""
        response = client.get("/api/cognitive-architecture/statistics")
        assert response.status_code == 200
        data = response.json()
        
        # Check structure
        assert isinstance(data, dict)
        assert "components" in data
        assert "timestamp" in data
        assert isinstance(data["components"], dict)

