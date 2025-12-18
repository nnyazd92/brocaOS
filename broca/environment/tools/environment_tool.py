"""
Environment access tool for LLM integration.

Implements the Tool protocol to provide environment access capabilities.
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional

from ...tools import Tool
from ..access_system import EnvironmentAccessSystem
from ..access_types import AccessLevel
from ..access_control import AccessControl
import logging

logger = logging.getLogger(__name__)


class EnvironmentAccessTool:
    """
    Tool for environment access system.
    
    Implements the Tool protocol for integration with the LLM tool system.
    """
    
    def __init__(self, access_system: Optional[EnvironmentAccessSystem] = None) -> None:
        """
        Initialize environment access tool.
        
        Args:
            access_system: Optional EnvironmentAccessSystem instance
        """
        self.access_system = access_system or EnvironmentAccessSystem()
        self._user_id = "llm"  # Default user ID for audit logging
    
    def _log_operation(self, operation: str, parameters: Dict[str, Any], result: Dict[str, Any]) -> None:
        """
        Log operation to audit trail.
        
        Args:
            operation: Operation name
            parameters: Operation parameters
            result: Operation result
        """
        self.access_system.policy_manager.log_operation(
            operation=operation,
            parameters=parameters,
            user_id=self._user_id,
            result=result
        )
    
    def _check_access(self, operation: str, sensor_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Check if operation is allowed at current access level.
        
        Args:
            operation: Operation name
            sensor_type: Optional sensor type
            
        Returns:
            None if allowed, error dict if not allowed
        """
        # Check if emergency access has expired (auto-expire)
        self.access_system.policy_manager.check_emergency_access_expired()
        
        current_level = self.access_system.get_access_level()
        is_emergency = self.access_system.policy_manager.is_emergency_access_active()
        check_result = AccessControl.check_operation_access(
            operation=operation,
            current_level=current_level,
            sensor_type=sensor_type,
            is_emergency=is_emergency
        )
        
        if not check_result.allowed:
            return {
                "success": False,
                "error": check_result.error,
                "required_level": check_result.required_level.name if check_result.required_level else None
            }
        
        return None
    
    @property
    def name(self) -> str:
        """Tool identifier."""
        return "environment_access"
    
    @property
    def description(self) -> str:
        """Tool description for the LLM."""
        return (
            "Access environment sensors and actuators with safety controls. "
            "Provides real-time sensor reading, environmental monitoring, and actuator control "
            "(with approval). Supports multiple access levels: SANDBOXED, SUPERVISED, AUTONOMOUS, EMERGENCY. "
            "Actions: read_sensor, list_sensors, get_access_level, request_escalation, "
            "approve_escalation, check_escalation_status, downgrade_access, list_actuators, "
            "control_actuator, request_actuator_approval, approve_actuator_request, "
            "generate_approval_token, verify_approval_token, request_emergency_access, "
            "exit_emergency_access, get_audit_log."
        )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """JSON schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "read_sensor",
                        "list_sensors",
                        "get_access_level",
                        "request_escalation",
                        "approve_escalation",
                        "check_escalation_status",
                        "downgrade_access",
                        "list_actuators",
                        "control_actuator",
                        "request_actuator_approval",
                        "approve_actuator_request",
                        "generate_approval_token",
                        "verify_approval_token",
                        "request_emergency_access",
                        "exit_emergency_access",
                        "get_audit_log"
                    ],
                    "description": "Action to perform"
                },
                "sensor_id": {
                    "type": "string",
                    "description": "Sensor ID for read_sensor action"
                },
                "request_id": {
                    "type": "string",
                    "description": "Request ID for approve_escalation, check_escalation_status"
                },
                "target_level": {
                    "type": "string",
                    "enum": ["SANDBOXED", "SUPERVISED", "AUTONOMOUS"],
                    "description": "Target access level for escalation or downgrade"
                },
                "rationale": {
                    "type": "string",
                    "description": "Rationale for escalation request"
                },
                "actuator_id": {
                    "type": "string",
                    "description": "Actuator ID for control_actuator action"
                },
                "operation": {
                    "type": "string",
                    "description": "Operation for control_actuator (e.g., create_file, delete_file)"
                },
                "parameters": {
                    "type": "object",
                    "description": "Parameters for control_actuator operation"
                },
                "approval_request_id": {
                    "type": "string",
                    "description": "Approval request ID for approve_actuator_request, generate_approval_token"
                },
                "approval_token": {
                    "type": "string",
                    "description": "Approval token for verify_approval_token or control_actuator"
                },
                "rationale": {
                    "type": "string",
                    "description": "Rationale for request_actuator_approval or request_emergency_access"
                },
                "duration_seconds": {
                    "type": "integer",
                    "description": "Duration in seconds for request_emergency_access (default: 300)"
                }
            },
            "required": ["action"]
        }
    
    def execute(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Execute tool with given parameters.
        
        Args:
            **kwargs: Tool parameters
            
        Returns:
            Dictionary containing execution results
        """
        action = kwargs.get("action")
        action_params = {k: v for k, v in kwargs.items() if k != "action"}
        
        # Check access level before executing
        access_error = self._check_access(action)
        if access_error:
            result = access_error
            self._log_operation(action, action_params, result)
            return result
        
        # Execute action
        if action == "read_sensor":
            result = self._read_sensor(kwargs.get("sensor_id"))
        elif action == "list_sensors":
            result = self._list_sensors()
        elif action == "get_access_level":
            result = self._get_access_level()
        elif action == "request_escalation":
            result = self._request_escalation(
                kwargs.get("target_level"),
                kwargs.get("rationale", "")
            )
        elif action == "approve_escalation":
            result = self._approve_escalation(kwargs.get("request_id"))
        elif action == "check_escalation_status":
            result = self._check_escalation_status(kwargs.get("request_id"))
        elif action == "downgrade_access":
            result = self._downgrade_access(kwargs.get("target_level"))
        elif action == "list_actuators":
            result = self._list_actuators()
        elif action == "control_actuator":
            result = self._control_actuator(
                kwargs.get("actuator_id"),
                kwargs.get("operation"),
                kwargs.get("parameters", {})
            )
        elif action == "request_actuator_approval":
            result = self._request_actuator_approval(
                kwargs.get("actuator_id"),
                kwargs.get("operation"),
                kwargs.get("parameters", {}),
                kwargs.get("rationale", "")
            )
        elif action == "approve_actuator_request":
            result = self._approve_actuator_request(kwargs.get("approval_request_id"))
        elif action == "generate_approval_token":
            result = self._generate_approval_token(kwargs.get("approval_request_id"))
        elif action == "verify_approval_token":
            result = self._verify_approval_token(kwargs.get("approval_token"))
        elif action == "request_emergency_access":
            result = self._request_emergency_access(
                kwargs.get("rationale", ""),
                kwargs.get("duration_seconds", 300)
            )
        elif action == "exit_emergency_access":
            result = self._exit_emergency_access()
        elif action == "get_audit_log":
            result = self._get_audit_log()
        else:
            result = {
                "success": False,
                "error": f"Unknown action: {action}"
            }
        
        # Add action to result for logging
        result["action"] = action
        
        # Log operation
        self._log_operation(action, action_params, result)
        
        return result
    
    def _read_sensor(self, sensor_id: Optional[str]) -> Dict[str, Any]:
        """Read from a sensor."""
        if not sensor_id:
            return {"success": False, "error": "sensor_id required"}
        
        sensor = self.access_system.sensor_registry.get_sensor(sensor_id)
        if not sensor:
            return {"success": False, "error": f"Sensor '{sensor_id}' not found"}
        
        # Check sensor type access
        sensor_type = getattr(sensor, 'sensor_type', None)
        access_error = self._check_access("read_sensor", sensor_type=sensor_type)
        if access_error:
            return access_error
        
        try:
            reading = sensor.read()
            return {
                "success": True,
                "sensor_id": reading.sensor_id,
                "sensor_type": reading.sensor_type,
                "value": reading.value,
                "timestamp": reading.timestamp.isoformat() if reading.timestamp else None
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _list_sensors(self) -> Dict[str, Any]:
        """List available sensors."""
        sensors = self.access_system.sensor_registry.discover_sensors()
        
        sensor_list = []
        for sensor_id, sensor in self.access_system.sensor_registry.sensors.items():
            try:
                capabilities = sensor.get_capabilities()
                sensor_list.append({
                    "sensor_id": sensor_id,
                    "sensor_type": capabilities.sensor_type,
                    "metrics": capabilities.metrics
                })
            except Exception:
                sensor_list.append({
                    "sensor_id": sensor_id,
                    "sensor_type": getattr(sensor, 'sensor_type', 'unknown')
                })
        
        return {
            "success": True,
            "sensors": sensor_list,
            "count": len(sensor_list)
        }
    
    def _get_access_level(self) -> Dict[str, Any]:
        """Get current access level."""
        level = self.access_system.get_access_level()
        return {
            "success": True,
            "access_level": level.name,
            "value": level.value
        }
    
    def _request_escalation(self, target_level: Optional[str], rationale: str) -> Dict[str, Any]:
        """Request access level escalation."""
        if not target_level:
            return {"success": False, "error": "target_level required"}
        
        try:
            level = AccessLevel[target_level]
        except KeyError:
            return {"success": False, "error": f"Invalid access level: {target_level}"}
        
        try:
            request = self.access_system.policy_manager.request_escalation(level, rationale)
            return {
                "success": True,
                "request_id": request.request_id,
                "target_level": target_level,
                "approved": request.approved,
                "message": "Escalation request created. Requires user approval."
            }
        except ValueError as e:
            # Rate limit exceeded
            return {"success": False, "error": str(e)}
    
    def _approve_escalation(self, request_id: Optional[str]) -> Dict[str, Any]:
        """Approve an escalation request."""
        if not request_id:
            return {"success": False, "error": "request_id required"}
        
        success = self.access_system.approve_escalation(request_id)
        if success:
            level = self.access_system.get_access_level()
            return {
                "success": True,
                "request_id": request_id,
                "new_access_level": level.name,
                "message": f"Escalation approved. Access level is now {level.name}."
            }
        else:
            return {"success": False, "error": f"Escalation request '{request_id}' not found or already processed"}
    
    def _check_escalation_status(self, request_id: Optional[str]) -> Dict[str, Any]:
        """Check status of an escalation request."""
        if not request_id:
            return {"success": False, "error": "request_id required"}
        
        request = self.access_system.policy_manager.get_escalation_request(request_id)
        if not request:
            return {"success": False, "error": f"Escalation request '{request_id}' not found"}
        
        return {
            "success": True,
            "request_id": request_id,
            "target_level": request.target_level.name,
            "approved": request.approved,
            "rationale": request.rationale,
            "created_at": request.created_at.isoformat() if request.created_at else None,
            "approved_at": request.approved_at.isoformat() if request.approved_at else None
        }
    
    def _downgrade_access(self, target_level: Optional[str]) -> Dict[str, Any]:
        """Downgrade access level."""
        if not target_level:
            return {"success": False, "error": "target_level required"}
        
        try:
            level = AccessLevel[target_level]
        except KeyError:
            return {"success": False, "error": f"Invalid access level: {target_level}"}
        
        success = self.access_system.policy_manager.downgrade_access(level)
        if success:
            return {
                "success": True,
                "new_access_level": level.name,
                "message": f"Access level downgraded to {level.name}."
            }
        else:
            return {
                "success": False,
                "error": f"Cannot downgrade to {target_level}. Must be lower than current level."
            }
    
    def _list_actuators(self) -> Dict[str, Any]:
        """List available actuators."""
        actuators = self.access_system.actuator_registry.discover_actuators()
        
        actuator_list = []
        for actuator_id, actuator in self.access_system.actuator_registry.actuators.items():
            actuator_list.append({
                "actuator_id": actuator_id,
                "max_power": actuator.max_power,
                "current_state": actuator.current_state
            })
        
        return {
            "success": True,
            "actuators": actuator_list,
            "count": len(actuator_list)
        }
    
    def _control_actuator(self, actuator_id: Optional[str], operation: Optional[str], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Control an actuator with optional approval token.
        
        Executes an actuator operation, checking for approval requirements and
        verifying approval tokens if provided. Emergency access bypasses approval.
        
        Args:
            actuator_id: ID of the actuator to control
            operation: Operation name to execute
            parameters: Operation parameters (may include approval_token)
            
        Returns:
            Dictionary with success status and operation results or error details
            
        Workflow:
            1. Validate actuator_id and operation
            2. Check if operation requires approval
            3. If approval required and no token: return approval_request_id
            4. If approval required and token provided: verify token
            5. Execute operation and return results
        """
        if not actuator_id:
            return {"success": False, "error": "actuator_id required"}
        
        if not operation:
            return {"success": False, "error": "operation required"}
        
        actuator = self.access_system.actuator_registry.get_actuator(actuator_id)
        if not actuator:
            logger.warning(f"Actuator '{actuator_id}' not found")
            return {"success": False, "error": f"Actuator '{actuator_id}' not found"}
        
        # Check if emergency access is active (bypasses approval)
        is_emergency = self.access_system.policy_manager.is_emergency_access_active()
        
        # Check if operation requires approval
        operation_config = actuator.allowed_operations.get(operation, {})
        requires_approval = operation_config.get('requires_approval', True)
        
        # Actuator operations require approval unless in emergency mode or operation doesn't require approval
        approval_token = parameters.get("approval_token")
        if requires_approval and not approval_token and not is_emergency:
            # Generate approval request
            logger.info(
                f"Approval required for actuator '{actuator_id}' operation '{operation}'. "
                f"Creating approval request."
            )
            request = self.access_system.approval_system.request_approval(
                operation=operation,
                parameters={k: v for k, v in parameters.items() if k != "approval_token"},
                rationale=f"Actuator {actuator_id} operation {operation}"
            )
            
            return {
                "success": False,
                "error": "Actuator operations require approval",
                "approval_request_id": request.request_id,
                "message": (
                    "Actuator operation requires approval. "
                    "Use request_actuator_approval and approve_actuator_request to get an approval_token, "
                    "or provide approval_token in parameters."
                )
            }
        
        # Verify approval token if provided (and not in emergency, and operation requires approval)
        if requires_approval and approval_token and not is_emergency:
            logger.debug(f"Verifying approval token for actuator '{actuator_id}' operation '{operation}'")
            verification = self.access_system.approval_system.verify_approval(
                approval_token,
                actuator_id=actuator_id
            )
            if not verification.valid:
                logger.warning(
                    f"Token verification failed for actuator '{actuator_id}' operation '{operation}': "
                    f"{verification.error}"
                )
                return {
                    "success": False,
                    "error": f"Invalid approval token: {verification.error}"
                }
            logger.debug(f"Token verification successful for actuator '{actuator_id}' operation '{operation}'")
        
        # Execute actuator operation
        try:
            actuator_params = {k: v for k, v in parameters.items() if k != "approval_token"}
            actuator_params["operation"] = operation
            logger.debug(f"Executing actuator '{actuator_id}' operation '{operation}'")
            result = actuator.activate(actuator_params)
            
            if result.success:
                logger.info(f"Actuator '{actuator_id}' operation '{operation}' completed successfully")
                return {
                    "success": True,
                    "actuator_id": actuator_id,
                    "operation": operation,
                    "data": result.data
                }
            else:
                logger.warning(
                    f"Actuator '{actuator_id}' operation '{operation}' failed: "
                    f"{result.error or 'Unknown error'}"
                )
                return {
                    "success": False,
                    "error": result.error or "Actuator operation failed"
                }
        except Exception as e:
            logger.error(
                f"Exception during actuator '{actuator_id}' operation '{operation}': {e}",
                exc_info=True
            )
            return {"success": False, "error": str(e)}
    
    def _request_actuator_approval(
        self,
        actuator_id: Optional[str],
        operation: Optional[str],
        parameters: Dict[str, Any],
        rationale: str
    ) -> Dict[str, Any]:
        """
        Request approval for an actuator operation.
        
        Creates an approval request that must be approved before a token can be generated.
        This is the first step in the approval workflow.
        
        Args:
            actuator_id: ID of the actuator (e.g., "filesystem_actuator")
            operation: Operation name (e.g., "create_file", "delete_file")
            parameters: Operation-specific parameters
            rationale: Reason/justification for the operation
            
        Returns:
            Dictionary with success status, approval_request_id, safety_analysis, and rationale
            
        Example:
            >>> result = tool._request_actuator_approval(
            ...     actuator_id="filesystem_actuator",
            ...     operation="create_file",
            ...     parameters={"path": "/tmp/test.txt", "content": "data"},
            ...     rationale="Creating test file"
            ... )
            >>> approval_request_id = result["approval_request_id"]
        """
        if not actuator_id:
            return {"success": False, "error": "actuator_id required"}
        
        if not operation:
            return {"success": False, "error": "operation required"}
        
        request = self.access_system.approval_system.request_approval(
            operation=operation,
            parameters=parameters,
            rationale=rationale or f"Actuator {actuator_id} operation {operation}",
            actuator_id=actuator_id
        )
        
        return {
            "success": True,
            "approval_request_id": request.request_id,
            "safety_analysis": request.safety_analysis,
            "rationale": request.rationale,
            "created_at": request.created_at.isoformat() if request.created_at else None
        }
    
    def _approve_actuator_request(self, approval_request_id: Optional[str]) -> Dict[str, Any]:
        """
        Approve an actuator approval request and generate an approval token.
        
        This is the second step in the approval workflow. Approves the request
        (sets approved=True) and automatically generates a reusable approval token
        that expires in 5 minutes.
        
        Args:
            approval_request_id: ID of the approval request to approve
            
        Returns:
            Dictionary with success status, approval_token, and expiration info
            
        Example:
            >>> result = tool._approve_actuator_request(approval_request_id)
            >>> token = result["approval_token"]
            >>> # Token expires in 300 seconds (5 minutes)
        """
        if not approval_request_id:
            return {"success": False, "error": "approval_request_id required"}
        
        # Get the approval request
        request = self.access_system.approval_system.get_approval_request(approval_request_id)
        if not request:
            return {"success": False, "error": f"Approval request '{approval_request_id}' not found"}
        
        # Approve the request
        request.approved = True
        
        # Generate approval token (pass actuator_id if available in request)
        try:
            token = self.access_system.approval_system.generate_token(
                request_id=approval_request_id,
                expires_in_seconds=300.0,  # 5 minutes default
                actuator_id=request.actuator_id
            )
        except ValueError as e:
            return {"success": False, "error": str(e)}
        
        return {
            "success": True,
            "approval_request_id": approval_request_id,
            "approval_token": token,
            "expires_in_seconds": 300.0,
            "message": "Approval request approved. Use the approval_token in control_actuator."
        }
    
    def _generate_approval_token(self, approval_request_id: Optional[str]) -> Dict[str, Any]:
        """
        Generate approval token for an approved request.
        
        Manually generates a token from an already-approved request. This is
        useful if you need to regenerate a token or need a new token from an
        existing approved request.
        
        Requires AUTONOMOUS access level.
        
        Args:
            approval_request_id: ID of an approved request
            
        Returns:
            Dictionary with success status, approval_token, and expiration info
            
        Raises:
            Access level check: Returns error if not at AUTONOMOUS level
            
        Example:
            >>> # Request must be approved first
            >>> tool._approve_actuator_request(approval_request_id)
            >>> # Then generate token (or use token from approve_actuator_request)
            >>> result = tool._generate_approval_token(approval_request_id)
            >>> token = result["approval_token"]
        """
        if not approval_request_id:
            return {"success": False, "error": "approval_request_id required"}
        
        # Check access level - requires AUTONOMOUS
        current_level = self.access_system.get_access_level()
        if current_level.value < AccessLevel.AUTONOMOUS.value:
            return {
                "success": False,
                "error": "Generating approval tokens requires AUTONOMOUS access level"
            }
        
        # Get the approval request
        request = self.access_system.approval_system.get_approval_request(approval_request_id)
        if not request:
            return {"success": False, "error": f"Approval request '{approval_request_id}' not found"}
        
        if not request.approved:
            return {"success": False, "error": "Approval request must be approved before generating token"}
        
        # Generate token (pass actuator_id if available in request)
        try:
            token = self.access_system.approval_system.generate_token(
                request_id=approval_request_id,
                expires_in_seconds=300.0,  # 5 minutes default
                actuator_id=request.actuator_id
            )
        except ValueError as e:
            return {"success": False, "error": str(e)}
        
        return {
            "success": True,
            "approval_token": token,
            "approval_request_id": approval_request_id,
            "expires_in_seconds": 300.0
        }
    
    def _verify_approval_token(self, approval_token: Optional[str]) -> Dict[str, Any]:
        """
        Verify an approval token.
        
        Checks if the provided token is valid (exists, not expired, etc.).
        
        Args:
            approval_token: Token string to verify
            
        Returns:
            Dictionary with success=True, valid (bool), and error (if invalid)
        """
        if not approval_token:
            logger.warning("verify_approval_token called without token")
            return {"success": False, "error": "approval_token required"}
        
        logger.debug(f"Verifying approval token (token: {approval_token[:8]}...)")
        verification = self.access_system.approval_system.verify_approval(approval_token)
        
        if verification.valid:
            logger.debug(f"Token verification successful")
        else:
            logger.debug(f"Token verification failed: {verification.error}")
        
        return {
            "success": True,
            "valid": verification.valid,
            "error": verification.error if not verification.valid else None
        }
    
    def _request_emergency_access(self, rationale: str, duration_seconds: int = 300) -> Dict[str, Any]:
        """Request emergency access level."""
        if not rationale:
            return {"success": False, "error": "rationale required for emergency access"}
        
        success = self.access_system.policy_manager.request_emergency_access(
            rationale=rationale,
            duration_seconds=duration_seconds
        )
        
        if success:
            expires_at = self.access_system.policy_manager._emergency_access_expires_at
            return {
                "success": True,
                "emergency_access_granted": True,
                "access_level": "EMERGENCY",
                "expires_at": expires_at.isoformat() if expires_at else None,
                "duration_seconds": duration_seconds,
                "message": "Emergency access granted. All restrictions bypassed."
            }
        else:
            return {"success": False, "error": "Failed to grant emergency access"}
    
    def _exit_emergency_access(self) -> Dict[str, Any]:
        """Exit emergency access level."""
        success = self.access_system.policy_manager.exit_emergency_access()
        
        if success:
            level = self.access_system.get_access_level()
            return {
                "success": True,
                "new_access_level": level.name,
                "message": f"Emergency access exited. Access level is now {level.name}."
            }
        else:
            return {"success": False, "error": "Failed to exit emergency access"}
    
    def _get_audit_log(self) -> Dict[str, Any]:
        """Get audit log entries."""
        log_entries = self.access_system.policy_manager.get_audit_log(limit=50)
        return {
            "success": True,
            "entries": log_entries,
            "count": len(log_entries)
        }
    
    def format_result(self, result: Dict[str, Any]) -> str:
        """
        Format tool result for LLM consumption.
        
        Args:
            result: Tool execution result dictionary
            
        Returns:
            Formatted string representation
        """
        if not result.get("success"):
            error = result.get("error", "Unknown error")
            return f"Error: {error}"
        
        action = result.get("action", "unknown")
        
        if action == "read_sensor":
            return f"Sensor reading: {result.get('value', {})}"
        elif action == "list_sensors":
            sensors = result.get("sensors", [])
            return f"Available sensors ({result.get('count', 0)}): {sensors}"
        elif action == "get_access_level":
            return f"Current access level: {result.get('access_level')}"
        elif action == "request_escalation":
            return f"Escalation request created: {result.get('request_id')}"
        elif action == "approve_escalation":
            return f"Escalation approved. New access level: {result.get('new_access_level')}"
        elif action == "check_escalation_status":
            status = "approved" if result.get("approved") else "pending"
            return f"Escalation request {result.get('request_id')}: {status}"
        elif action == "downgrade_access":
            return f"Access level downgraded to {result.get('new_access_level')}"
        elif action == "list_actuators":
            actuators = result.get("actuators", [])
            return f"Available actuators ({result.get('count', 0)}): {actuators}"
        elif action == "control_actuator":
            return f"Actuator operation completed: {result.get('operation')}"
        elif action == "request_actuator_approval":
            return f"Approval request created: {result.get('approval_request_id')}"
        elif action == "approve_actuator_request":
            return f"Approval request approved. Token: {result.get('approval_token', 'N/A')[:20]}..."
        elif action == "generate_approval_token":
            return f"Approval token generated: {result.get('approval_token', 'N/A')[:20]}..."
        elif action == "verify_approval_token":
            status = "valid" if result.get("valid") else "invalid"
            return f"Approval token: {status}"
        elif action == "request_emergency_access":
            return f"Emergency access granted. Expires at: {result.get('expires_at', 'N/A')}"
        elif action == "exit_emergency_access":
            return f"Emergency access exited. New level: {result.get('new_access_level')}"
        elif action == "get_audit_log":
            return f"Audit log entries: {result.get('count', 0)}"
        
        return str(result)
