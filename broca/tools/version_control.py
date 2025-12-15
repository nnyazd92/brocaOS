"""
Version control tool for BrocaOS.

Provides safe git operations with automatic danger detection,
emergency backups, and recovery options to prevent accidental loss of work.
"""

from __future__ import annotations

import os
import json
import logging
import subprocess
import datetime
from typing import Dict, Any, List, Optional
import shlex

from . import Tool

logger = logging.getLogger(__name__)


class VersionControlTool:
    """
    Version control tool for BrocaOS.
    
    Provides safe git operations with automatic danger detection,
    emergency backups, and recovery options.
    """
    
    def __init__(self, repo_path: Optional[str] = None) -> None:
        """
        Initialize the version control tool.
        
        Args:
            repo_path: Path to git repository (defaults to current directory)
        """
        self._repo_path = repo_path or os.getcwd()
        self._repo_path = os.path.abspath(self._repo_path)
        logger.info(f"Initialized VersionControlTool for repository: {self._repo_path}")
    
    def _run_git(self, command: str) -> Dict[str, Any]:
        """Run a git command and return structured results."""
        full_command = f"git -C {shlex.quote(self._repo_path)} {command}"
        
        try:
            result = subprocess.run(
                full_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                "success": result.returncode == 0,
                "return_code": result.returncode,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "command": full_command
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "return_code": -1,
                "stdout": "",
                "stderr": "Command timed out",
                "command": full_command
            }
        except Exception as e:
            return {
                "success": False,
                "return_code": -1,
                "stdout": "",
                "stderr": str(e),
                "command": full_command
            }
    
    @property
    def name(self) -> str:
        """Tool identifier."""
        return "version_control"
    
    @property
    def description(self) -> str:
        """Tool description for the LLM."""
        return (
            "Version control operations using git. Provides safe operations with automatic "
            "danger detection to prevent accidental loss of work. Use this tool to check "
            "repository status, create safe snapshots, create emergency backups, check for "
            "dangerous operations, and explore recovery options. Always use this tool before "
            "performing file cleanup or major operations to prevent data loss."
        )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """JSON schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action to perform",
                    "enum": ["status", "snapshot", "emergency_backup", "check_danger", "recovery_options", "run_git"],
                    "default": "status"
                },
                "message": {
                    "type": "string",
                    "description": "Commit message for snapshot action"
                },
                "command": {
                    "type": "string",
                    "description": "Git command to run (for run_git action)"
                },
                "repo_path": {
                    "type": "string",
                    "description": "Repository path (defaults to current directory)"
                }
            },
            "required": ["action"]
        }
    
    def execute(self, action: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Execute version control operation.
        
        Args:
            action: Action to perform
            **kwargs: Additional parameters based on action
            
        Returns:
            Dictionary containing operation results
        """
        # Override repo_path if provided
        if "repo_path" in kwargs:
            self._repo_path = os.path.abspath(kwargs["repo_path"])
        
        if action == "status":
            return self._get_status()
        elif action == "snapshot":
            message = kwargs.get("message")
            return self._create_safe_snapshot(message)
        elif action == "emergency_backup":
            return self._create_emergency_backup()
        elif action == "check_danger":
            return self._check_for_dangerous_operations()
        elif action == "recovery_options":
            return self._get_recovery_options()
        elif action == "run_git":
            command = kwargs.get("command", "status")
            return self._run_git(command)
        else:
            return {
                "success": False,
                "error": f"Unknown action: {action}",
                "available_actions": [
                    "status", "snapshot", "emergency_backup", 
                    "check_danger", "recovery_options", "run_git"
                ]
            }
    
    def _get_status(self) -> Dict[str, Any]:
        """Get comprehensive git status."""
        result = self._run_git("status --porcelain -uall")
        
        if not result["success"]:
            return {
                "success": False,
                "error": result["stderr"],
                "status": {}
            }
        
        status = {
            "untracked": [],
            "modified": [],
            "staged": [],
            "deleted": [],
            "conflicts": []
        }
        
        for line in result["stdout"].split('\n'):
            if not line:
                continue
            
            code = line[:2]
            path = line[3:]
            
            if code == "??":
                status["untracked"].append(path)
            elif code[0] == "M" or code[1] == "M":
                status["modified"].append(path)
            elif code[0] == "A":
                status["staged"].append(path)
            elif code[0] == "D" or code[1] == "D":
                status["deleted"].append(path)
            elif code[0] == "U" or code[1] == "U":
                status["conflicts"].append(path)
        
        # Get branch info
        branch_result = self._run_git("branch --show-current")
        branch = branch_result["stdout"] if branch_result["success"] else "unknown"
        
        # Get commit count
        commit_result = self._run_git("rev-list --count HEAD")
        commit_count = int(commit_result["stdout"]) if commit_result["success"] else 0
        
        return {
            "success": True,
            "branch": branch,
            "commit_count": commit_count,
            "status": status,
            "summary": {
                "untracked_files": len(status["untracked"]),
                "modified_files": len(status["modified"]),
                "staged_files": len(status["staged"]),
                "deleted_files": len(status["deleted"]),
                "conflict_files": len(status["conflicts"])
            }
        }
    
    def _create_safe_snapshot(self, message: Optional[str] = None) -> Dict[str, Any]:
        """Create a snapshot safely, checking for untracked work first."""
        # First check status
        status = self._get_status()
        if not status["success"]:
            return {
                "success": False,
                "message": f"Failed to get status: {status.get('error', 'Unknown error')}",
                "action": "status_check_failed"
            }
        
        untracked_count = status["summary"]["untracked_files"]
        modified_count = status["summary"]["modified_files"]
        
        if untracked_count == 0 and modified_count == 0:
            return {
                "success": True,
                "message": "No changes to commit",
                "action": "no_changes",
                "untracked_files": 0,
                "modified_files": 0
            }
        
        # Create message if not provided
        if not message:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            changes_desc = []
            if untracked_count > 0:
                changes_desc.append(f"{untracked_count} untracked")
            if modified_count > 0:
                changes_desc.append(f"{modified_count} modified")
            message = f"Auto-snapshot: {timestamp} ({', '.join(changes_desc)})"
        
        # Add all files
        add_result = self._run_git("add -A")
        if not add_result["success"]:
            return {
                "success": False,
                "message": f"Failed to add files: {add_result['stderr']}",
                "action": "add_failed"
            }
        
        # Create commit
        commit_result = self._run_git(f'commit -m "{message}"')
        if not commit_result["success"]:
            return {
                "success": False,
                "message": f"Failed to commit: {commit_result['stderr']}",
                "action": "commit_failed"
            }
        
        # Get commit hash
        hash_result = self._run_git("rev-parse HEAD")
        commit_hash = hash_result["stdout"] if hash_result["success"] else "unknown"
        
        return {
            "success": True,
            "message": f"Snapshot created: {message}",
            "action": "snapshot_created",
            "commit_hash": commit_hash,
            "untracked_files": untracked_count,
            "modified_files": modified_count,
            "timestamp": datetime.datetime.now().isoformat()
        }
    
    def _create_emergency_backup(self) -> Dict[str, Any]:
        """Create an emergency backup branch."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        branch_name = f"emergency_backup/{timestamp}"
        
        # Create backup branch
        branch_result = self._run_git(f"checkout -b {branch_name}")
        if not branch_result["success"]:
            return {
                "success": False,
                "message": f"Failed to create backup branch: {branch_result['stderr']}",
                "action": "branch_creation_failed"
            }
        
        # Create snapshot on backup branch
        snapshot_result = self._create_safe_snapshot(f"Emergency backup: {timestamp}")
        
        # Switch back to master
        checkout_result = self._run_git("checkout master")
        
        return {
            "success": snapshot_result["success"],
            "message": f"Emergency backup created: {branch_name}",
            "action": "emergency_backup_created",
            "branch_name": branch_name,
            "snapshot_result": snapshot_result,
            "back_to_master": checkout_result["success"]
        }
    
    def _check_for_dangerous_operations(self) -> Dict[str, Any]:
        """Check for operations that could cause data loss."""
        status = self._get_status()
        
        if not status["success"]:
            return {
                "danger_level": "unknown",
                "warnings": ["Cannot determine git status"],
                "recommendations": ["Check git repository manually"],
                "status": status
            }
        
        warnings = []
        recommendations = []
        
        untracked = status["summary"]["untracked_files"]
        modified = status["summary"]["modified_files"]
        
        if untracked > 0:
            warnings.append(f"{untracked} untracked files could be lost")
            recommendations.append("Run 'create_safe_snapshot' to save untracked work")
        
        if modified > 0:
            warnings.append(f"{modified} modified files not staged for commit")
            recommendations.append("Run 'create_safe_snapshot' to save modifications")
        
        if untracked > 10 or modified > 10:
            danger_level = "high"
            warnings.append("Large amount of uncommitted work detected")
            recommendations.append("Consider creating emergency backup immediately")
        elif untracked > 0 or modified > 0:
            danger_level = "medium"
        else:
            danger_level = "low"
        
        return {
            "danger_level": danger_level,
            "warnings": warnings,
            "recommendations": recommendations,
            "status_summary": status["summary"],
            "timestamp": datetime.datetime.now().isoformat()
        }
    
    def _get_recovery_options(self) -> Dict[str, Any]:
        """Get options for recovering lost work."""
        # Check for stashed changes
        stash_result = self._run_git("stash list")
        stashes = []
        if stash_result["success"]:
            stashes = stash_result["stdout"].split('\n')
        
        # Check for backup branches
        branch_result = self._run_git("branch -a")
        backup_branches = []
        if branch_result["success"]:
            for line in branch_result["stdout"].split('\n'):
                line = line.strip()
                if "backup" in line.lower() or "emergency" in line.lower():
                    backup_branches.append(line)
        
        # Check reflog for recent commits
        reflog_result = self._run_git("reflog --oneline -10")
        reflog_entries = []
        if reflog_result["success"]:
            reflog_entries = reflog_result["stdout"].split('\n')
        
        return {
            "stashes_available": len(stashes) > 0,
            "stash_count": len(stashes),
            "stashes": stashes[:5],  # First 5 stashes
            "backup_branches": backup_branches,
            "reflog_entries": reflog_entries,
            "recovery_instructions": [
                "Use 'git stash list' to see stashed changes",
                "Use 'git stash apply' to restore stashed changes",
                "Use 'git checkout <branch>' to switch to backup branches",
                "Use 'git reflog' to find lost commits",
                "Use 'git reset --hard <commit>' to restore to specific commit"
            ]
        }
    
    def format_result(self, result: Dict[str, Any]) -> str:
        """
        Format tool result for LLM consumption.
        
        Args:
            result: Tool execution result dictionary
            
        Returns:
            Formatted string representation of the result
        """
        if not result.get("success", True):
            error_msg = result.get("error", result.get("message", "Unknown error"))
            return f"❌ Version control operation failed: {error_msg}"
        
        action = result.get("action", "")
        
        if action == "status":
            status = result
            summary = status.get("summary", {})
            return (
                f"📊 Repository Status:\n"
                f"• Branch: {status.get('branch', 'unknown')}\n"
                f"• Commits: {status.get('commit_count', 0)}\n"
                f"• Untracked files: {summary.get('untracked_files', 0)}\n"
                f"• Modified files: {summary.get('modified_files', 0)}\n"
                f"• Staged files: {summary.get('staged_files', 0)}\n"
                f"• Deleted files: {summary.get('deleted_files', 0)}\n"
                f"• Conflict files: {summary.get('conflict_files', 0)}"
            )
        
        elif action == "snapshot_created":
            return (
                f"✅ Snapshot created successfully!\n"
                f"• Commit: {result.get('commit_hash', 'unknown')}\n"
                f"• Message: {result.get('message', '')}\n"
                f"• Saved: {result.get('untracked_files', 0)} untracked + {result.get('modified_files', 0)} modified files"
            )
        
        elif action == "emergency_backup_created":
            return (
                f"🚨 Emergency backup created!\n"
                f"• Branch: {result.get('branch_name', 'unknown')}\n"
                f"• Status: {result.get('message', 'Backup completed')}"
            )
        
        elif action == "check_danger":
            danger = result
            warnings = danger.get("warnings", [])
            recommendations = danger.get("recommendations", [])
            
            output = f"⚠️  Danger Level: {danger.get('danger_level', 'unknown').upper()}\n"
            
            if warnings:
                output += "\nWarnings:\n"
                for warning in warnings:
                    output += f"• {warning}\n"
            
            if recommendations:
                output += "\nRecommendations:\n"
                for rec in recommendations:
                    output += f"• {rec}\n"
            
            return output
        
        elif action == "recovery_options":
            recovery = result
            output = "🔍 Recovery Options:\n"
            
            if recovery.get("stashes_available"):
                output += f"• {recovery.get('stash_count', 0)} stashed changes available\n"
            
            backup_branches = recovery.get("backup_branches", [])
            if backup_branches:
                output += f"• {len(backup_branches)} backup branches available\n"
                for branch in backup_branches[:3]:  # Show first 3
                    output += f"  - {branch}\n"
            
            return output
        
        else:
            # Generic formatting for other results
            message = result.get("message", "Operation completed")
            return f"✅ {message}"

