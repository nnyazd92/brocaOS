"""
Audit system for environment operations.

Provides comprehensive audit logging, real-time monitoring, and anomaly detection.
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, field


@dataclass
class Operation:
    """Represents an environment operation."""
    
    operation_type: str
    sensor_type: Optional[str] = None
    actuator_power: float = 0.0
    sampling_rate: float = 0.0
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OperationResult:
    """Represents the result of an operation."""
    
    success: bool
    error: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class PersistentAuditLog:
    """Persistent storage for audit logs."""
    
    def __init__(self, storage: Optional[Any] = None) -> None:
        """
        Initialize persistent audit log.
        
        Args:
            storage: Optional storage backend (uses in-memory if None)
        """
        self.storage = storage
        self.entries: List[Dict[str, Any]] = []
    
    def append(self, entry: Dict[str, Any]) -> None:
        """
        Append entry to audit log.
        
        Args:
            entry: Log entry dictionary
        """
        self.entries.append(entry)
        if self.storage:
            self.storage.save(entry)


class RealtimeMonitor:
    """Real-time monitoring of operations."""
    
    def __init__(self) -> None:
        """Initialize real-time monitor."""
        self.active_operations: List[Dict[str, Any]] = []
    
    def register_operation(self, operation: Operation) -> None:
        """
        Register an active operation.
        
        Args:
            operation: Operation to register
        """
        self.active_operations.append({
            'operation': operation,
            'started_at': datetime.now(timezone.utc)
        })
    
    def unregister_operation(self, operation: Operation) -> None:
        """
        Unregister a completed operation.
        
        Args:
            operation: Operation to unregister
        """
        self.active_operations = [
            op for op in self.active_operations
            if op['operation'] != operation
        ]


class AnomalyDetector:
    """Detects anomalies in audit logs."""
    
    def __init__(self) -> None:
        """Initialize anomaly detector."""
        pass
    
    def detect_anomalies(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detect anomalies in audit log entries.
        
        Args:
            entries: List of audit log entries
            
        Returns:
            List of detected anomalies
        """
        anomalies = []
        
        # Detect high frequency operations (potential DoS)
        if len(entries) > 50:
            recent_entries = entries[-50:]
            time_span = self._calculate_time_span(recent_entries)
            if time_span < 1.0:  # Less than 1 second for 50 operations
                anomalies.append({
                    'type': 'high_frequency',
                    'severity': 'warning',
                    'message': 'High frequency operations detected'
                })
        
        return anomalies
    
    def _calculate_time_span(self, entries: List[Dict[str, Any]]) -> float:
        """Calculate time span of entries in seconds."""
        if len(entries) < 2:
            return 0.0
        
        timestamps = []
        for entry in entries:
            ts = entry.get('timestamp')
            if isinstance(ts, str):
                try:
                    timestamps.append(datetime.fromisoformat(ts.replace('Z', '+00:00')))
                except (ValueError, AttributeError):
                    pass
            elif isinstance(ts, datetime):
                timestamps.append(ts)
        
        if len(timestamps) < 2:
            return 0.0
        
        timestamps.sort()
        span = (timestamps[-1] - timestamps[0]).total_seconds()
        return span if span > 0 else 0.0


@dataclass
class ComplianceReport:
    """Compliance report for audit logs."""
    
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    anomalies_detected: int = 0
    time_period: str = ""


class AuditSystem:
    """
    Comprehensive audit logging for all environment operations.
    
    Provides persistent logging, real-time monitoring, and anomaly detection.
    """
    
    def __init__(self, storage: Optional[Any] = None) -> None:
        """
        Initialize audit system.
        
        Args:
            storage: Optional storage backend for persistent logging
        """
        self.logs = PersistentAuditLog(storage=storage)
        self.realtime_monitor = RealtimeMonitor()
        self.anomaly_detector = AnomalyDetector()
    
    def log_operation(
        self,
        operation: Operation,
        user_id: str,
        result: OperationResult
    ) -> None:
        """
        Log operation with full context and result.
        
        Args:
            operation: Operation object
            user_id: User identifier
            result: Operation result
        """
        log_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'operation': operation,
            'user_id': user_id,
            'result': result,
            'success': result.success
        }
        
        self.logs.append(log_entry)
        self.realtime_monitor.register_operation(operation)
        
        # Unregister after a short delay (in real implementation)
        # For now, we'll just track it
    
    def generate_compliance_report(self) -> ComplianceReport:
        """
        Generate regulatory compliance reports.
        
        Returns:
            ComplianceReport with statistics
        """
        entries = self.logs.entries
        
        successful = sum(1 for e in entries if e.get('success', False))
        failed = len(entries) - successful
        
        anomalies = self.anomaly_detector.detect_anomalies(entries)
        
        return ComplianceReport(
            total_operations=len(entries),
            successful_operations=successful,
            failed_operations=failed,
            anomalies_detected=len(anomalies),
            time_period="all_time"
        )

