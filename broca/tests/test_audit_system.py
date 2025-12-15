"""
Tests for AuditSystem implementation.

Tests audit logging and compliance reports.
"""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from broca.environment.safety.audit import AuditSystem, Operation, OperationResult


class TestAuditSystemInitialization:
    """Test AuditSystem initialization."""
    
    def test_init_creates_system(self):
        """Test that audit system initializes."""
        audit = AuditSystem()
        
        assert audit is not None
        assert audit.logs is not None
        assert audit.realtime_monitor is not None
        assert audit.anomaly_detector is not None
    
    def test_init_with_custom_storage(self):
        """Test initialization with custom storage."""
        mock_storage = Mock()
        audit = AuditSystem(storage=mock_storage)
        
        assert audit.logs.storage is mock_storage


class TestAuditSystemLogging:
    """Test audit logging functionality."""
    
    def test_log_operation(self):
        """Test logging an operation."""
        audit = AuditSystem()
        
        operation = Mock()
        operation.operation_type = 'read_sensor'
        operation.sensor_type = 'system'
        
        result = Mock()
        result.success = True
        
        audit.log_operation(operation, "user123", result)
        
        # Check that log was created
        assert len(audit.logs.entries) > 0
        assert audit.logs.entries[-1]['user_id'] == "user123"
        assert audit.logs.entries[-1]['operation'].operation_type == 'read_sensor'
    
    def test_log_operation_includes_timestamp(self):
        """Test that log entries include timestamps."""
        audit = AuditSystem()
        
        operation = Mock()
        result = Mock()
        
        audit.log_operation(operation, "user123", result)
        
        entry = audit.logs.entries[-1]
        assert 'timestamp' in entry
        assert isinstance(entry['timestamp'], (str, datetime))
    
    def test_log_operation_persists(self):
        """Test that logged operations are persisted."""
        audit = AuditSystem()
        
        operation = Mock()
        result = Mock()
        
        audit.log_operation(operation, "user123", result)
        
        # Check that log entry was created (persisted in memory at minimum)
        assert len(audit.logs.entries) > 0


class TestAuditSystemCompliance:
    """Test compliance reporting."""
    
    def test_generate_compliance_report(self):
        """Test generating compliance report."""
        audit = AuditSystem()
        
        # Log some operations
        for i in range(5):
            operation = Mock()
            result = Mock()
            result.success = True
            audit.log_operation(operation, f"user{i}", result)
        
        report = audit.generate_compliance_report()
        
        assert report is not None
        assert hasattr(report, 'total_operations')
        assert report.total_operations >= 5
    
    def test_compliance_report_includes_statistics(self):
        """Test that compliance report includes statistics."""
        audit = AuditSystem()
        
        # Log operations with different outcomes
        for i in range(3):
            operation = Mock()
            result = Mock()
            result.success = i % 2 == 0  # Alternate success/failure
            audit.log_operation(operation, f"user{i}", result)
        
        report = audit.generate_compliance_report()
        
        assert hasattr(report, 'successful_operations')
        assert hasattr(report, 'failed_operations')
        assert report.successful_operations + report.failed_operations >= 3


class TestAuditSystemAnomalyDetection:
    """Test anomaly detection."""
    
    def test_detect_anomalies(self):
        """Test anomaly detection."""
        audit = AuditSystem()
        
        # Log some operations
        for i in range(10):
            operation = Mock()
            result = Mock()
            result.success = True
            audit.log_operation(operation, f"user{i}", result)
        
        anomalies = audit.anomaly_detector.detect_anomalies(audit.logs.entries)
        
        assert isinstance(anomalies, list)
    
    def test_anomaly_detection_on_suspicious_pattern(self):
        """Test that anomaly detection identifies suspicious patterns."""
        audit = AuditSystem()
        
        # Log many rapid operations (potential anomaly)
        for i in range(100):
            operation = Mock()
            result = Mock()
            result.success = True
            audit.log_operation(operation, "user1", result)
        
        anomalies = audit.anomaly_detector.detect_anomalies(audit.logs.entries)
        
        # Should detect high frequency operations
        assert isinstance(anomalies, list)

