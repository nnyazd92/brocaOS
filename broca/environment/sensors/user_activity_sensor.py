"""
User activity monitoring sensor for environment access.

Provides user session and activity monitoring.
"""

from __future__ import annotations

import uuid
from typing import Dict, Any, List
from collections import Counter
from datetime import datetime, timezone

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None  # type: ignore

from .base import Sensor, SensorReading, SensorCapabilities, CalibrationResult


class UserActivitySensor(Sensor):
    """
    User activity monitoring sensor.
    
    Monitors active user sessions, logged-in users, and user process counts.
    """
    
    def __init__(self) -> None:
        """Initialize user activity sensor."""
        self.sensor_id = f"user_activity_sensor_{uuid.uuid4().hex[:8]}"
        self.sensor_type = "user_activity"
        self.metrics = [
            'active_sessions',
            'current_users',
            'user_process_counts',
            'session_durations'
        ]
    
    def read(self) -> SensorReading:
        """
        Read current user activity metrics.
        
        Returns:
            SensorReading with user activity metrics
        """
        value: Dict[str, Any] = {}
        
        if not PSUTIL_AVAILABLE:
            # Return empty data if psutil not available
            value['active_sessions'] = []
            value['current_users'] = []
            value['user_process_counts'] = {}
            value['session_durations'] = {}
            return SensorReading(
                sensor_id=self.sensor_id,
                sensor_type=self.sensor_type,
                value=value
            )
        
        # Active sessions
        try:
            value['active_sessions'] = self._get_active_sessions()
        except Exception:
            value['active_sessions'] = []
        
        # Current users
        try:
            value['current_users'] = self._get_current_users()
        except Exception:
            value['current_users'] = []
        
        # User process counts
        try:
            value['user_process_counts'] = self._get_user_process_counts()
        except Exception:
            value['user_process_counts'] = {}
        
        # Session durations
        try:
            value['session_durations'] = self._get_session_durations()
        except Exception:
            value['session_durations'] = {}
        
        return SensorReading(
            sensor_id=self.sensor_id,
            sensor_type=self.sensor_type,
            value=value
        )
    
    def _get_active_sessions(self) -> List[Dict[str, Any]]:
        """Get active user sessions."""
        sessions = []
        try:
            users = psutil.users()
            for user in users:
                session_info: Dict[str, Any] = {
                    'username': user.name,
                    'terminal': user.terminal,
                    'host': user.host,
                    'started': user.started,
                    'started_iso': datetime.fromtimestamp(user.started, tz=timezone.utc).isoformat() if user.started else None
                }
                sessions.append(session_info)
        except (AttributeError, OSError):
            # psutil.users() may not be available on all systems
            pass
        except Exception:
            pass
        
        return sessions
    
    def _get_current_users(self) -> List[str]:
        """Get list of currently logged-in users."""
        users = []
        try:
            for user in psutil.users():
                if user.name not in users:
                    users.append(user.name)
        except (AttributeError, OSError):
            pass
        except Exception:
            pass
        
        return users
    
    def _get_user_process_counts(self) -> Dict[str, int]:
        """Get process counts per user."""
        counts: Dict[str, int] = {}
        try:
            for proc in psutil.process_iter(['username']):
                try:
                    username = proc.info['username']
                    if username:
                        counts[username] = counts.get(username, 0) + 1
                except (psutil.NoSuchProcess, psutil.AccessDenied, KeyError):
                    continue
        except Exception:
            pass
        
        return counts
    
    def _get_session_durations(self) -> Dict[str, float]:
        """Get session durations in seconds."""
        durations: Dict[str, float] = {}
        try:
            current_time = datetime.now(timezone.utc).timestamp()
            users = psutil.users()
            for user in users:
                session_key = f"{user.name}@{user.terminal}"
                if user.started:
                    duration = current_time - user.started
                    durations[session_key] = duration
        except (AttributeError, OSError):
            pass
        except Exception:
            pass
        
        return durations
    
    def get_capabilities(self) -> SensorCapabilities:
        """
        Return sensor capabilities.
        
        Returns:
            SensorCapabilities describing user activity sensor capabilities
        """
        return SensorCapabilities(
            sensor_type=self.sensor_type,
            metrics=self.metrics,
            sampling_rate_max=2.0,  # Can sample up to 2 Hz (user activity changes slowly)
            accuracy=0.85,  # User activity monitoring accuracy
            description="User activity monitoring sensor for sessions, users, and process counts"
        )
    
    def calibrate(self) -> CalibrationResult:
        """
        Calibrate user activity sensor.
        
        Verifies that psutil user functions are working.
        
        Returns:
            CalibrationResult indicating success
        """
        if not PSUTIL_AVAILABLE:
            return CalibrationResult(
                success=False,
                error="psutil not available"
            )
        
        try:
            # Test that we can read user information
            # Note: psutil.users() may not be available on all systems
            try:
                psutil.users()
            except (AttributeError, OSError):
                # That's okay, we'll still work with process-based user detection
                pass
            
            # Test process iteration
            next(iter(psutil.process_iter(['username'])))
            
            return CalibrationResult(
                success=True,
                calibration_data={
                    'psutil_version': psutil.__version__ if hasattr(psutil, '__version__') else 'unknown',
                    'users_api_available': hasattr(psutil, 'users')
                }
            )
        except StopIteration:
            # No processes found, but that's okay for calibration
            return CalibrationResult(
                success=True,
                calibration_data={
                    'psutil_version': psutil.__version__ if hasattr(psutil, '__version__') else 'unknown'
                }
            )
        except Exception as e:
            return CalibrationResult(
                success=False,
                error=str(e)
            )

