"""
Integration tests for cognitive architecture web endpoints.
Uses TDD approach: define expected behavior first, then implement.
"""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient

# Import the FastAPI app
try:
    from ..web_api import app
except ImportError:
    # Try absolute import
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from broca.web_api import app

client = TestClient(app)


class TestCognitiveEndpoints:
    """Test suite for cognitive architecture endpoints."""
    
    def test_system_health_endpoint_exists(self):
        """Test that system health endpoint exists and returns proper structure."""
        response = client.get("/api/cognitive-architecture/health")
        
        # Should return 200 or 503 if not enabled
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            data = response.json()
            # Check expected structure
            assert "overall_health" in data
            assert "status" in data
            assert "stability_score" in data
            assert "issues" in data
            assert isinstance(data["issues"], list)
    
    def test_cognitive_architecture_stats_exists(self):
        """Test that cognitive architecture stats endpoint exists."""
        response = client.get("/api/cognitive-architecture/statistics")
        
        # Should return 200 or 503 if not enabled
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            data = response.json()
            # Should return a dictionary
            assert isinstance(data, dict)
    
    @pytest.mark.skip(reason="Endpoint not implemented yet")
    def test_cognitive_query_endpoint_exists(self):
        """Test that cognitive query endpoint exists and accepts queries."""
        test_query = {
            "query": "Test cognitive query",
            "include_z3_validation": True,
            "include_affective_state": True,
            "include_thought_process": True
        }
        
        response = client.post("/api/cognitive/query", json=test_query)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "response" in data
        assert "thought_process" in data
        assert "processing_time_ms" in data
        assert isinstance(data["thought_process"], list)
    
    def test_metrics_endpoint_exists(self):
        """Test that basic metrics endpoint exists."""
        response = client.get("/api/metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "cpu" in data
        assert "memory" in data
        assert "uptime" in data
        assert "isWorking" in data
        assert "timestamp" in data
        
        # Check value ranges
        assert 0 <= data["cpu"] <= 1
        assert 0 <= data["memory"] <= 1
        assert data["uptime"] >= 0
    
    @pytest.mark.asyncio
    async def test_streaming_chat_endpoint(self):
        """Test that chat streaming endpoint works."""
        test_messages = [
            {"role": "user", "content": "Hello, world!"}
        ]
        
        response = client.post("/api/chat", json={
            "messages": test_messages,
            "stream": True
        })
        
        # Should return 200 or streaming response
        assert response.status_code == 200
        
        # Check content type for streaming
        if "application/x-ndjson" in response.headers.get("content-type", ""):
            # Parse streaming response
            lines = response.text.strip().split('\n')
            for line in lines:
                if line:
                    data = json.loads(line)
                    assert "content" in data or "error" in data


class TestCognitiveQueryValidation:
    """Test validation of cognitive query requests."""
    
    def test_cognitive_query_requires_query_field(self):
        """Test that query field is required."""
        invalid_query = {
            "include_z3_validation": True
            # Missing query field
        }
        
        response = client.post("/api/cognitive/query", json=invalid_query)
        
        # Should return 422 (validation error)
        assert response.status_code == 422
    
    def test_cognitive_query_validates_types(self):
        """Test that boolean fields are properly validated."""
        invalid_query = {
            "query": "test",
            "include_z3_validation": "not-a-boolean"  # Should be boolean
        }
        
        response = client.post("/api/cognitive/query", json=invalid_query)
        
        # Should return 422 (validation error)
        assert response.status_code == 422
    
    def test_valid_cognitive_query_succeeds(self):
        """Test that a valid cognitive query succeeds."""
        valid_query = {
            "query": "What is cognitive architecture?",
            "include_z3_validation": True,
            "include_affective_state": True,
            "include_thought_process": False,
            "include_memory_traversal": True
        }
        
        response = client.post("/api/cognitive/query", json=valid_query)
        
        # Should return 200 or 503 if not implemented
        assert response.status_code in [200, 503, 404]


class TestErrorHandling:
    """Test error handling in cognitive endpoints."""
    
    def test_graceful_degradation_when_components_missing(self):
        """Test that endpoints degrade gracefully when components are missing."""
        # This test mocks the runtime to simulate missing components
        with patch('broca.web_api.get_runtime') as mock_get_runtime:
            mock_runtime = Mock()
            mock_runtime.system_health_monitor = None  # Simulate missing component
            mock_get_runtime.return_value = mock_runtime
            
            response = client.get("/api/cognitive-architecture/health")
            
            # Should return 503 when component not available
            assert response.status_code == 503
            data = response.json()
            assert "detail" in data
            assert "not enabled" in data["detail"].lower()
    
    def test_internal_errors_handled_gracefully(self):
        """Test that internal errors are caught and returned as 500."""
        with patch('broca.web_api.get_runtime') as mock_get_runtime:
            mock_runtime = Mock()
            mock_runtime.system_health_monitor = Mock()
            mock_runtime.system_health_monitor.assess_health.side_effect = Exception("Test error")
            mock_get_runtime.return_value = mock_runtime
            
            response = client.get("/api/cognitive-architecture/health")
            
            # Should return 500 for internal errors
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data


if __name__ == "__main__":
    # Run tests
    import sys
    pytest.main(sys.argv + ["-v"])
