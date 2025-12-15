"""
File system operations actuator.

Provides file create, delete, modify operations with approval.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Dict, Any
from datetime import datetime, timezone

from .base import Actuator, ActivationResult, DeactivationResult, EmergencyStopResult


class FileSystemActuator(Actuator):
    """
    File system operations actuator.
    
    Handles file create, delete, modify operations with approval requirements.
    """
    
    def __init__(self) -> None:
        """Initialize filesystem actuator."""
        super().__init__('filesystem_actuator', max_power=0.1)
        self.allowed_operations = {
            # Write operations (require approval)
            'create_file': {'requires_approval': True},
            'delete_file': {'requires_approval': True, 'safety_level': 'high'},
            'modify_file': {'requires_approval': True},
            'move_file': {'requires_approval': True},
            'rename_file': {'requires_approval': True},
            'copy_file': {'requires_approval': True},
            'create_directory': {'requires_approval': False},
            'delete_directory': {'requires_approval': True, 'safety_level': 'high'},
            'set_permissions': {'requires_approval': True},
            'set_file_permissions': {'requires_approval': True},
            'create_symlink': {'requires_approval': True},
            # Read operations (no approval required)
            'read_file': {'requires_approval': False},
            'list_directory': {'requires_approval': False},
            'check_file_exists': {'requires_approval': False},
            'get_file_info': {'requires_approval': False},
            'read_symlink': {'requires_approval': False}
        }
    
    def activate(self, parameters: Dict[str, Any]) -> ActivationResult:
        """
        Activate actuator with parameters.
        
        Args:
            parameters: Must contain 'operation' and operation-specific parameters
            
        Returns:
            ActivationResult
        """
        operation = parameters.get('operation')
        if not operation:
            return ActivationResult(success=False, error="Operation not specified")
        
        if operation not in self.allowed_operations:
            return ActivationResult(success=False, error=f"Operation '{operation}' not allowed")
        
        # Check safety interlock
        if not self.safety_interlock.check_interlock(operation, parameters):
            return ActivationResult(success=False, error="Safety interlock failed")
        
        try:
            if operation == 'create_file':
                return self._create_file(parameters)
            elif operation == 'delete_file':
                return self._delete_file(parameters)
            elif operation == 'modify_file':
                return self._modify_file(parameters)
            elif operation == 'create_directory':
                return self._create_directory(parameters)
            elif operation == 'read_file':
                return self._read_file(parameters)
            elif operation == 'list_directory':
                return self._list_directory(parameters)
            elif operation == 'move_file':
                return self._move_file(parameters)
            elif operation == 'rename_file':
                return self._move_file(parameters)  # rename is same as move
            elif operation == 'copy_file':
                return self._copy_file(parameters)
            elif operation == 'delete_directory':
                return self._delete_directory(parameters)
            elif operation == 'check_file_exists':
                return self._check_file_exists(parameters)
            elif operation == 'get_file_info':
                return self._get_file_info(parameters)
            elif operation == 'set_file_permissions':
                return self._set_file_permissions(parameters)
            elif operation == 'create_symlink':
                return self._create_symlink(parameters)
            elif operation == 'read_symlink':
                return self._read_symlink(parameters)
            else:
                return ActivationResult(success=False, error=f"Operation '{operation}' not implemented")
        except Exception as e:
            return ActivationResult(success=False, error=str(e))
    
    def _create_file(self, parameters: Dict[str, Any]) -> ActivationResult:
        """Create a file."""
        path = parameters.get('path')
        content = parameters.get('content', '')
        
        if not path:
            return ActivationResult(success=False, error="Path not specified")
        
        try:
            file_path = Path(path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
            
            self.current_state = 'active'
            return ActivationResult(success=True, data={'path': str(file_path)})
        except Exception as e:
            return ActivationResult(success=False, error=str(e))
    
    def _delete_file(self, parameters: Dict[str, Any]) -> ActivationResult:
        """Delete a file."""
        path = parameters.get('path')
        
        if not path:
            return ActivationResult(success=False, error="Path not specified")
        
        try:
            file_path = Path(path)
            if not file_path.exists():
                return ActivationResult(success=False, error="File does not exist")
            
            file_path.unlink()
            self.current_state = 'idle'
            return ActivationResult(success=True, data={'path': str(file_path)})
        except Exception as e:
            return ActivationResult(success=False, error=str(e))
    
    def _modify_file(self, parameters: Dict[str, Any]) -> ActivationResult:
        """Modify a file."""
        path = parameters.get('path')
        content = parameters.get('content')
        
        if not path:
            return ActivationResult(success=False, error="Path not specified")
        
        try:
            file_path = Path(path)
            if content is not None:
                file_path.write_text(content)
            else:
                return ActivationResult(success=False, error="Content not specified")
            
            self.current_state = 'active'
            return ActivationResult(success=True, data={'path': str(file_path)})
        except Exception as e:
            return ActivationResult(success=False, error=str(e))
    
    def _create_directory(self, parameters: Dict[str, Any]) -> ActivationResult:
        """Create a directory."""
        path = parameters.get('path')
        
        if not path:
            return ActivationResult(success=False, error="Path not specified")
        
        try:
            dir_path = Path(path)
            dir_path.mkdir(parents=True, exist_ok=True)
            
            self.current_state = 'idle'
            return ActivationResult(success=True, data={'path': str(dir_path)})
        except Exception as e:
            return ActivationResult(success=False, error=str(e))
    
    def deactivate(self) -> DeactivationResult:
        """Deactivate actuator."""
        self.current_state = 'idle'
        return DeactivationResult(success=True)
    
    def _read_file(self, parameters: Dict[str, Any]) -> ActivationResult:
        """Read file contents."""
        path = parameters.get('path')
        
        if not path:
            return ActivationResult(success=False, error="Path not specified")
        
        try:
            file_path = Path(path)
            if not file_path.exists():
                return ActivationResult(success=False, error="File does not exist")
            
            if not file_path.is_file():
                return ActivationResult(success=False, error="Path is not a file")
            
            content = file_path.read_text()
            
            self.current_state = 'idle'
            return ActivationResult(success=True, data={'path': str(file_path), 'content': content})
        except Exception as e:
            return ActivationResult(success=False, error=str(e))
    
    def _list_directory(self, parameters: Dict[str, Any]) -> ActivationResult:
        """List directory contents."""
        path = parameters.get('path', '.')
        
        try:
            dir_path = Path(path)
            if not dir_path.exists():
                return ActivationResult(success=False, error="Directory does not exist")
            
            if not dir_path.is_dir():
                return ActivationResult(success=False, error="Path is not a directory")
            
            items = []
            for item in dir_path.iterdir():
                item_info = {
                    'name': item.name,
                    'path': str(item),
                    'is_file': item.is_file(),
                    'is_directory': item.is_dir(),
                    'is_symlink': item.is_symlink()
                }
                items.append(item_info)
            
            self.current_state = 'idle'
            return ActivationResult(success=True, data={'path': str(dir_path), 'items': items})
        except Exception as e:
            return ActivationResult(success=False, error=str(e))
    
    def _move_file(self, parameters: Dict[str, Any]) -> ActivationResult:
        """Move or rename a file."""
        source_path = parameters.get('source_path') or parameters.get('path')
        destination_path = parameters.get('destination_path') or parameters.get('new_path')
        
        if not source_path:
            return ActivationResult(success=False, error="Source path not specified")
        
        if not destination_path:
            return ActivationResult(success=False, error="Destination path not specified")
        
        try:
            src = Path(source_path)
            dst = Path(destination_path)
            
            if not src.exists():
                return ActivationResult(success=False, error="Source file does not exist")
            
            # Create parent directory if needed
            dst.parent.mkdir(parents=True, exist_ok=True)
            
            src.rename(dst)
            
            self.current_state = 'active'
            return ActivationResult(success=True, data={'source_path': str(src), 'destination_path': str(dst)})
        except Exception as e:
            return ActivationResult(success=False, error=str(e))
    
    def _copy_file(self, parameters: Dict[str, Any]) -> ActivationResult:
        """Copy a file."""
        source_path = parameters.get('source_path')
        destination_path = parameters.get('destination_path')
        
        if not source_path:
            return ActivationResult(success=False, error="Source path not specified")
        
        if not destination_path:
            return ActivationResult(success=False, error="Destination path not specified")
        
        try:
            src = Path(source_path)
            dst = Path(destination_path)
            
            if not src.exists():
                return ActivationResult(success=False, error="Source file does not exist")
            
            if not src.is_file():
                return ActivationResult(success=False, error="Source path is not a file")
            
            # Create parent directory if needed
            dst.parent.mkdir(parents=True, exist_ok=True)
            
            import shutil
            shutil.copy2(src, dst)
            
            self.current_state = 'active'
            return ActivationResult(success=True, data={'source_path': str(src), 'destination_path': str(dst)})
        except Exception as e:
            return ActivationResult(success=False, error=str(e))
    
    def _delete_directory(self, parameters: Dict[str, Any]) -> ActivationResult:
        """Delete a directory."""
        path = parameters.get('path')
        recursive = parameters.get('recursive', False)
        
        if not path:
            return ActivationResult(success=False, error="Path not specified")
        
        try:
            dir_path = Path(path)
            if not dir_path.exists():
                return ActivationResult(success=False, error="Directory does not exist")
            
            if not dir_path.is_dir():
                return ActivationResult(success=False, error="Path is not a directory")
            
            if recursive:
                import shutil
                shutil.rmtree(dir_path)
            else:
                # Only delete if empty
                try:
                    dir_path.rmdir()
                except OSError:
                    return ActivationResult(success=False, error="Directory is not empty. Use recursive=True to delete non-empty directories.")
            
            self.current_state = 'idle'
            return ActivationResult(success=True, data={'path': str(dir_path)})
        except Exception as e:
            return ActivationResult(success=False, error=str(e))
    
    def _check_file_exists(self, parameters: Dict[str, Any]) -> ActivationResult:
        """Check if file or directory exists."""
        path = parameters.get('path')
        
        if not path:
            return ActivationResult(success=False, error="Path not specified")
        
        try:
            file_path = Path(path)
            exists = file_path.exists()
            
            data = {'path': str(file_path), 'exists': exists}
            if exists:
                data['is_file'] = file_path.is_file()
                data['is_directory'] = file_path.is_dir()
                data['is_symlink'] = file_path.is_symlink()
            
            self.current_state = 'idle'
            return ActivationResult(success=True, data=data)
        except Exception as e:
            return ActivationResult(success=False, error=str(e))
    
    def _get_file_info(self, parameters: Dict[str, Any]) -> ActivationResult:
        """Get file metadata."""
        path = parameters.get('path')
        
        if not path:
            return ActivationResult(success=False, error="Path not specified")
        
        try:
            file_path = Path(path)
            if not file_path.exists():
                return ActivationResult(success=False, error="File or directory does not exist")
            
            stat_info = file_path.stat()
            
            data = {
                'path': str(file_path),
                'size': stat_info.st_size,
                'is_file': file_path.is_file(),
                'is_directory': file_path.is_dir(),
                'is_symlink': file_path.is_symlink(),
                'permissions': oct(stat_info.st_mode)[-3:],
                'modified_time': stat_info.st_mtime,
                'modified_time_iso': datetime.fromtimestamp(stat_info.st_mtime, tz=timezone.utc).isoformat(),
                'created_time': stat_info.st_ctime if hasattr(stat_info, 'st_ctime') else None
            }
            
            self.current_state = 'idle'
            return ActivationResult(success=True, data=data)
        except Exception as e:
            return ActivationResult(success=False, error=str(e))
    
    def _set_file_permissions(self, parameters: Dict[str, Any]) -> ActivationResult:
        """Set file permissions."""
        path = parameters.get('path')
        permissions = parameters.get('permissions')
        
        if not path:
            return ActivationResult(success=False, error="Path not specified")
        
        if permissions is None:
            return ActivationResult(success=False, error="Permissions not specified")
        
        try:
            file_path = Path(path)
            if not file_path.exists():
                return ActivationResult(success=False, error="File or directory does not exist")
            
            # Parse permissions (can be octal string like "755" or integer)
            if isinstance(permissions, str):
                if permissions.startswith('0o') or permissions.startswith('0'):
                    mode = int(permissions, 8)
                else:
                    mode = int(permissions, 8)
            else:
                mode = int(permissions)
            
            file_path.chmod(mode)
            
            self.current_state = 'active'
            return ActivationResult(success=True, data={'path': str(file_path), 'permissions': oct(mode)})
        except Exception as e:
            return ActivationResult(success=False, error=str(e))
    
    def _create_symlink(self, parameters: Dict[str, Any]) -> ActivationResult:
        """Create a symbolic link."""
        target_path = parameters.get('target_path')
        link_path = parameters.get('link_path')
        
        if not target_path:
            return ActivationResult(success=False, error="Target path not specified")
        
        if not link_path:
            return ActivationResult(success=False, error="Link path not specified")
        
        try:
            target = Path(target_path)
            link = Path(link_path)
            
            # Create parent directory if needed
            link.parent.mkdir(parents=True, exist_ok=True)
            
            link.symlink_to(target)
            
            self.current_state = 'active'
            return ActivationResult(success=True, data={'target_path': str(target), 'link_path': str(link)})
        except Exception as e:
            return ActivationResult(success=False, error=str(e))
    
    def _read_symlink(self, parameters: Dict[str, Any]) -> ActivationResult:
        """Read symlink target."""
        path = parameters.get('path')
        
        if not path:
            return ActivationResult(success=False, error="Path not specified")
        
        try:
            link_path = Path(path)
            if not link_path.exists():
                return ActivationResult(success=False, error="Path does not exist")
            
            if not link_path.is_symlink():
                return ActivationResult(success=False, error="Path is not a symlink")
            
            target = link_path.readlink()
            
            self.current_state = 'idle'
            return ActivationResult(success=True, data={'path': str(link_path), 'target': str(target)})
        except Exception as e:
            return ActivationResult(success=False, error=str(e))
    
    def emergency_stop(self) -> EmergencyStopResult:
        """Immediate emergency stop."""
        self.current_state = 'idle'
        return EmergencyStopResult(success=True)

