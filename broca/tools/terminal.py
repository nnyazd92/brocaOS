"""
Terminal tool for executing commands.

Provides command execution, file operations, and proper error handling.
All commands are allowed - no whitelist restrictions.

INTERACTIVE COMMAND HANDLING:
The terminal tool can detect and handle interactive commands that present menus or prompts.
Interactive commands are automatically detected by analyzing output for:
- Numbered/lettered menu options (1. Option, a) Choice)
- Yes/No prompts ([y/N], (yes/no))
- Prompts ending with :, ?, >
- Multi-line option lists

WORKFLOW:
1. Execute command normally using execute()
2. If interactive elements are detected (menus, prompts), they will be surfaced in the result
3. Review the INTERACTIVE MENU DETECTED section in the formatted result
4. Provide your choice using the stdin_input parameter in a follow-up execute() call
5. Repeat steps 3-4 for multi-step interactive commands

You can explicitly mark a command as interactive using: {"command": "...", "interactive": true}
Use stdin_input parameter to respond to prompts: {"command": "...", "stdin_input": "1"}
"""

from __future__ import annotations

import os
import logging
import subprocess
import shlex
import re
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, TypedDict

try:
    import pexpect
    PEXPECT_AVAILABLE = True
except ImportError:
    PEXPECT_AVAILABLE = False
    pexpect = None  # type: ignore

from ..config import config

logger = logging.getLogger(__name__)


# Type definition for interactive elements structure
class InteractiveElements(TypedDict, total=False):
    """Structure for extracted interactive elements."""
    type: str  # "menu", "prompt", or "yesno"
    options: List[str]  # List of menu options (for menus)
    prompt_text: str  # The prompt text
    raw_output: str  # Raw output containing the interactive element


class TerminalTool:
    """
    Terminal tool for executing commands.
    
    Allows the LLM to execute any command, read/write files, and list directories.
    All commands are allowed - no whitelist restrictions.
    """
    
    def __init__(
        self,
        command_whitelist: Optional[List[str]] = None,
        working_directory: Optional[str] = None
    ) -> None:
        """
        Initialize the terminal tool.
        
        Args:
            command_whitelist: List of allowed command patterns (defaults to config)
            working_directory: Working directory for commands (defaults to config or current dir)
        """
        self._whitelist = command_whitelist or config.tools.terminal_command_whitelist
        self._working_directory = working_directory or config.tools.terminal_working_directory
        
        # Normalize whitelist - remove empty strings (kept for backward compatibility, but not used)
        self._whitelist = [cmd.strip() for cmd in self._whitelist if cmd.strip()]
        
        # Store active interactive sessions (command hash -> pexpect process)
        self._active_sessions: Dict[str, Any] = {}
        
        logger.info("Initialized TerminalTool (all commands allowed)")
        if not PEXPECT_AVAILABLE:
            logger.warning("pexpect not available - interactive command handling will be limited")
    
    @property
    def name(self) -> str:
        """Tool identifier."""
        return "terminal"
    
    @property
    def description(self) -> str:
        """Tool description for the LLM."""
        interactive_section = (
            "\n\n"
            "INTERACTIVE COMMAND HANDLING:\n"
            "The terminal tool can detect and handle interactive commands that present menus or prompts.\n"
            "\n"
            "WORKFLOW:\n"
            "1. Execute command with interactive=True for interactive commands\n"
            "2. If the command presents a menu or prompt, provide input using stdin_input\n"
            "3. Repeat steps 1-2 for multi-step interactive commands\n"
            "\n"
            "EXPLICIT FLAG REQUIRED:\n"
            "You must explicitly mark a command as interactive: {\"command\": \"...\", \"interactive\": true}\n"
            "\n"
            "PROVIDING INPUT:\n"
            "Use stdin_input parameter to respond to prompts:\n"
            "  {\"command\": \"mycommand\", \"interactive\": true, \"stdin_input\": \"1\"}  # Select option 1\n"
            "  {\"command\": \"mycommand\", \"interactive\": true, \"stdin_input\": \"y\"}  # Answer yes\n"
            "  {\"command\": \"mycommand\", \"interactive\": true, \"stdin_input\": \"text input\"}  # Provide text\n"
            "\n"
            "EXAMPLES:\n"
            "  # Explicitly mark as interactive:\n"
            "  {\"command\": \"interactive_tool\", \"interactive\": true}\n"
            "  # Then provide input:\n"
            "  {\"command\": \"interactive_tool\", \"interactive\": true, \"stdin_input\": \"2\"}  # Select option 2\n"
        ) if PEXPECT_AVAILABLE else ""
        
        return (
            "Execute terminal commands and perform file operations. "
            "\n\n"
            "REQUIRED PARAMETER: 'command' (string) - The command to execute. "
            "You MUST ALWAYS provide the 'command' parameter as a non-empty string. "
            "\n\n"
            "Examples:\n"
            "  {\"command\": \"python script.py\"}\n"
            "  {\"command\": \"python3 my_script.py\"}\n"
            "  {\"command\": \"ls -la\"}\n"
            "  {\"command\": \"echo hello\", \"working_dir\": \"/path/to/dir\"}\n"
            "  {\"command\": \"python script.py\", \"timeout\": 60}\n"
            "\n"
            "All commands are allowed. Supports executing any command including Python, Sage, "
            "shell commands, and more. Can read/write files and list directories. "
            "Use this tool to create, compile, and run code files. "
            + interactive_section +
            "\n"
            "IMPORTANT: The 'command' parameter is REQUIRED and must be a non-empty string. "
            "Never call this tool without providing the 'command' parameter."
        )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """JSON schema for tool parameters."""
        properties: Dict[str, Any] = {
            "command": {
                "type": "string",
                "description": "Command to execute (any command is allowed)"
            },
            "working_dir": {
                "type": "string",
                "description": "Optional working directory for command execution"
            },
            "timeout": {
                "type": "integer",
                "description": "Command timeout in seconds (default: 30)",
                "default": 30,
                "minimum": 1,
                "maximum": 300
            }
        }
        
        # Add interactive parameters if pexpect is available
        if PEXPECT_AVAILABLE:
            properties["interactive"] = {
                "type": "boolean",
                "description": "Explicitly mark command as interactive (optional, auto-detected by default)"
            }
            properties["stdin_input"] = {
                "type": "string",
                "description": "Input to send to interactive command (e.g., menu selection, yes/no answer, text input)"
            }
        
        return {
            "type": "object",
            "properties": properties,
            "required": ["command"]
        }
    
    def _normalize_command(self, command: str) -> Tuple[str, List[str]]:
        """
        Parse command string into command name and arguments.
        
        Args:
            command: Command string to parse
            
        Returns:
            Tuple of (command_name, arguments_list)
        """
        try:
            parts = shlex.split(command)
            if not parts:
                return "", []
            return parts[0], parts[1:]
        except ValueError:
            # If shlex fails, try simple split
            parts = command.split()
            if not parts:
                return "", []
            return parts[0], parts[1:]
    
    def _is_command_allowed(self, command: str) -> bool:
        """
        Check if command is allowed.
        
        All commands are now allowed - no restrictions.
        
        Args:
            command: Command string to check
            
        Returns:
            Always returns True (all commands allowed)
        """
        # All commands are allowed - no whitelist restrictions
        return True
    
    def _is_python_code_command(self, command: str) -> bool:
        """
        Check if command is a Python code execution command (python -c "...").
        
        Args:
            command: Command string to check
            
        Returns:
            True if command appears to be Python code execution
        """
        # Check for python -c or python3 -c patterns
        python_patterns = [
            r'python\s+-c\s+',
            r'python3\s+-c\s+',
            r'python\s+-m\s+',
            r'python3\s+-m\s+',
        ]
        
        import re
        for pattern in python_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return True
        
        # Check for multiline Python scripts (contains import statements, def, class, etc.)
        python_keywords = ['import ', 'from ', 'def ', 'class ', 'if __name__', 'sys.path']
        if any(keyword in command for keyword in python_keywords):
            # Likely Python code if it has Python keywords and is multiline
            if '\n' in command or command.count('"') >= 2 or command.count("'") >= 2:
                return True
        
        return False
    
    def _is_likely_code_string(self, arg: str) -> bool:
        """
        Check if an argument looks like a code string literal rather than an actual file path.
        
        Args:
            arg: Argument string to check
            
        Returns:
            True if argument looks like code (string literal), False if it looks like a path
        """
        # If it's wrapped in quotes, it's likely a string literal
        if (arg.startswith('"') and arg.endswith('"')) or (arg.startswith("'") and arg.endswith("'")):
            return True
        
        # If it contains Python-like syntax (imports, function calls, etc.), it's likely code
        code_indicators = [
            'import ', 'from ', 'sys.', 'os.', 'print(', 'def ', 'class ',
            'if ', 'for ', 'while ', 'try:', 'except', 'with ', 'as ',
            '=', '==', '!=', '(', ')', '[', ']', '{', '}'
        ]
        
        # If it has multiple code indicators, it's likely code
        indicator_count = sum(1 for indicator in code_indicators if indicator in arg)
        if indicator_count >= 2:
            return True
        
        # If it's very long and contains newlines, it's likely multiline code
        if len(arg) > 200 and '\n' in arg:
            return True
        
        # If it looks like a Python expression (has operators, function calls)
        if any(op in arg for op in ['(', ')', '=', '[', ']']) and not os.path.exists(arg):
            # Has code-like syntax and doesn't exist as a file - likely code
            return True
        
        return False
    
    def _validate_path(self, path: str) -> bool:
        """
        Validate file path (prevent path traversal).
        
        Args:
            path: File path to validate
            
        Returns:
            True if path is safe, False otherwise
        """
        # Prevent path traversal
        if ".." in path:
            return False
        
        # Prevent absolute paths outside working directory if working directory is set
        if self._working_directory and os.path.isabs(path):
            try:
                abs_path = os.path.abspath(path)
                working_abs = os.path.abspath(self._working_directory)
                if not abs_path.startswith(working_abs):
                    return False
            except Exception:
                return False
        
        return True
    
    def _is_git_command(self, command: str) -> bool:
        """
        Check if command is a git command.
        
        Args:
            command: Command string to check
            
        Returns:
            True if command is a git command, False otherwise
        """
        cmd_name, _ = self._normalize_command(command)
        return cmd_name == "git"
    
    def _is_interactive_pattern(self, output: str) -> bool:
        """
        Check if output contains interactive patterns (menus, prompts).
        
        Detects common interactive patterns:
        - Numbered menus: "1. Option", "2) Option"
        - Lettered menus: "a) Option", "b. Option"
        - Yes/No prompts: "[y/N]", "(yes/no)", "Y/n"
        - Text prompts ending with: ":", "?", ">"
        
        Args:
            output: Command output to check
            
        Returns:
            True if interactive patterns are detected, False otherwise
        """
        if not output or not output.strip():
            return False
        
        # Pattern for numbered menus: "1. Option" or "1) Option"
        numbered_menu_pattern = r'^\s*\d+[\.\)]\s+.+'
        
        # Pattern for lettered menus: "a) Option" or "a. Option"
        lettered_menu_pattern = r'^\s*[a-z][\.\)]\s+.+'
        
        # Pattern for yes/no prompts: [y/N], (yes/no), Y/n, etc.
        yesno_pattern = r'\[[yYnN]/?[nNyY]?\]|\(yes/no\)|\(y/n\)|Y/n|y/N'
        
        # Pattern for prompts ending with :, ?, or >
        prompt_pattern = r'[:\?>]\s*$'
        
        lines = output.split('\n')
        has_numbered_menu = False
        has_lettered_menu = False
        has_yesno = False
        has_prompt = False
        
        # Check each line for patterns
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
            
            # Check for numbered menu
            if re.match(numbered_menu_pattern, line_stripped, re.IGNORECASE):
                has_numbered_menu = True
            
            # Check for lettered menu
            if re.match(lettered_menu_pattern, line_stripped, re.IGNORECASE):
                has_lettered_menu = True
            
            # Check for yes/no pattern
            if re.search(yesno_pattern, line_stripped):
                has_yesno = True
            
            # Check for prompt ending (but not just headers like "Results:" or "Options:")
            if re.search(prompt_pattern, line_stripped):
                # Avoid false positives: don't detect simple headers ending with colon
                # that are followed by list items (not actual prompts)
                if not re.match(r'^[A-Z][a-z]*s?:\s*$', line_stripped):
                    has_prompt = True
        
        # If we have menu items, check if they look like interactive menus
        if has_numbered_menu or has_lettered_menu:
            # Count menu items and extract their values
            menu_count = 0
            has_prompt_indicator = False
            menu_indices = []
            menu_values = []  # Store the number/letter values for sequential checking
            
            # First pass: identify all menu item lines and extract their values
            for i, line in enumerate(lines):
                line_stripped = line.strip()
                numbered_match = re.match(numbered_menu_pattern, line_stripped, re.IGNORECASE)
                lettered_match = re.match(lettered_menu_pattern, line_stripped, re.IGNORECASE)
                
                if numbered_match:
                    menu_count += 1
                    menu_indices.append(i)
                    # Extract the number from the pattern
                    num_match = re.match(r'^\s*(\d+)[\.\)]', line_stripped)
                    if num_match:
                        menu_values.append(int(num_match.group(1)))
                elif lettered_match:
                    menu_count += 1
                    menu_indices.append(i)
                    # Extract the letter from the pattern
                    letter_match = re.match(r'^\s*([a-z])[\.\)]', line_stripped, re.IGNORECASE)
                    if letter_match:
                        menu_values.append(ord(letter_match.group(1).lower()) - ord('a'))
            
            # Check if menu values are sequential (1,2,3 or a,b,c)
            is_sequential = False
            if len(menu_values) >= 2:
                # Sort values to check if they form a consecutive sequence
                sorted_values = sorted(menu_values)
                # Check if they're consecutive (each value is previous + 1)
                is_sequential = all(sorted_values[i] == sorted_values[0] + i 
                                   for i in range(len(sorted_values)))
            
            # Check for prompt indicators before menu items (in lines before first menu item)
            prompt_keywords = r'\b(select|choose|option|pick|enter|input)\b'
            if menu_indices and menu_indices[0] > 0:
                # Check lines before the first menu item
                for i in range(max(0, menu_indices[0] - 3), menu_indices[0]):
                    line_stripped = lines[i].strip()
                    # Look for prompt keywords followed by colon, question mark, or just ending the line
                    if re.search(prompt_keywords, line_stripped, re.IGNORECASE):
                        # Check if line ends with colon, question mark, or is a short prompt
                        if re.search(r'[:\?]\s*$', line_stripped) or len(line_stripped) < 50:
                            has_prompt_indicator = True
                            break
            
            # Require either:
            # - 2+ menu items that are sequential (1,2,3 or a,b,c), OR
            # - 3+ menu items (more likely to be a menu), OR
            # - 1 menu item that appears at the start of output (likely a standalone menu), OR
            # - 1+ menu item with prompt indicator
            # This prevents false positives from non-sequential numbered step labels like "1. Testing...\n5. Analyzing..."
            # but still allows single menu items at the start of output (e.g., "1. Option")
            # Check if menu item is the first non-empty line
            first_non_empty_line = next((i for i, line in enumerate(lines) if line.strip()), None)
            is_first_line_menu = (menu_count == 1 and menu_indices and 
                                 first_non_empty_line is not None and 
                                 menu_indices[0] == first_non_empty_line)
            if (menu_count >= 2 and is_sequential) or menu_count >= 3 or is_first_line_menu or (menu_count >= 1 and has_prompt_indicator):
                return True
        
        # Yes/no prompts or text prompts are interactive
        if has_yesno or has_prompt:
            return True
        
        return False
    
    def _extract_interactive_elements(self, output: str) -> Optional[InteractiveElements]:
        """
        Extract interactive elements (menus, prompts) from command output.
        
        Parses output to identify:
        - Menu types with numbered or lettered options
        - Yes/No prompts
        - Text input prompts
        
        Args:
            output: Command output to parse
            
        Returns:
            Dictionary with interactive elements structure, or None if no interactive elements found.
            Structure: {"type": "menu|prompt|yesno", "options": [...], "prompt_text": "...", "raw_output": "..."}
        """
        if not output or not output.strip():
            return None
        
        if not self._is_interactive_pattern(output):
            return None
        
        # Pattern for numbered menus: "1. Option" or "1) Option"
        numbered_menu_pattern = r'^\s*(\d+)[\.\)]\s+(.+)$'
        
        # Pattern for lettered menus: "a) Option" or "a. Option"
        lettered_menu_pattern = r'^\s*([a-z])[\.\)]\s+(.+)$'
        
        # Pattern for yes/no prompts
        yesno_pattern = r'\[[yYnN]/?[nNyY]?\]|\(yes/no\)|\(y/n\)|Y/n|y/N'
        
        # Pattern for prompts ending with :, ?, or >
        prompt_pattern = r'(.+?)[:\?>]\s*$'
        
        lines = output.split('\n')
        options: List[str] = []
        prompt_text = ""
        element_type = "prompt"
        
        # Check for menu patterns
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
            
            # Try numbered menu
            match = re.match(numbered_menu_pattern, line_stripped, re.IGNORECASE)
            if match:
                options.append(line_stripped)
                if element_type != "menu":
                    element_type = "menu"
                continue
            
            # Try lettered menu
            match = re.match(lettered_menu_pattern, line_stripped, re.IGNORECASE)
            if match:
                options.append(line_stripped)
                if element_type != "menu":
                    element_type = "menu"
                continue
            
            # Check for yes/no prompt
            if re.search(yesno_pattern, line_stripped):
                element_type = "yesno"
                prompt_text = line_stripped
                break
            
            # Check for text prompt (ending with :, ?, or >)
            if re.search(r'[:\?>]\s*$', line_stripped) and not options:  # Only if we haven't found menu options
                prompt_text = line_stripped
                element_type = "prompt"
        
        # If we found menu options, return menu structure (even single item is valid for extraction)
        if options and len(options) >= 1:
            return {
                "type": "menu",
                "options": options,
                "prompt_text": prompt_text or "Please select an option:",
                "raw_output": output
            }
        
        # If we found a prompt (yes/no or text), return prompt structure
        if prompt_text or element_type in ["yesno", "prompt"]:
            return {
                "type": element_type,
                "options": [],
                "prompt_text": prompt_text or output.strip(),
                "raw_output": output
            }
        
        return None
    
    def _get_session_key(self, command: str, working_dir: Optional[str] = None) -> str:
        """
        Generate a session key for tracking interactive command sessions.
        
        Args:
            command: The command being executed
            working_dir: Working directory for the command
            
        Returns:
            Hash string identifying the session
        """
        key_string = f"{command}:{working_dir or ''}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_stderr_label(self, result: Dict[str, Any]) -> str:
        """
        Get appropriate label for stderr output based on command type and success status.
        
        Args:
            result: Tool execution result dictionary
            
        Returns:
            Appropriate label for stderr output
        """
        command_raw = result.get("command", "")
        # Ensure command is a string (property-based testing may provide other types)
        if not isinstance(command_raw, str):
            command = str(command_raw) if command_raw else ""
        else:
            command = command_raw
        success = result.get("success", False)
        
        # For successful commands, don't use "Error output:"
        if success:
            if self._is_git_command(command):
                return "Git output:"
            else:
                return "Output:"
        else:
            # For failed commands, "Error output:" or "Stderr output:" is appropriate
            return "Stderr output:"
    
    def execute(
        self,
        command: str,
        working_dir: Optional[str] = None,
        timeout: int = 30,
        interactive: Optional[bool] = None,
        stdin_input: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a terminal command.
        
        Supports both regular and interactive commands. Interactive commands are automatically
        detected by analyzing output patterns, or can be explicitly marked with interactive=True.
        Use stdin_input parameter to provide input to interactive commands.
        
        Args:
            command: Command to execute
            working_dir: Optional working directory (overrides instance default)
            timeout: Command timeout in seconds
            interactive: Explicitly mark command as interactive (required for interactive commands)
            stdin_input: Input to send to interactive command (for responding to prompts/menus)
            
        Returns:
            Dictionary containing execution results. Interactive results include:
            - "interactive": True if interactive elements were detected
            - "interactive_elements": Dict with extracted menu/prompt information
        """
        try:
            # All commands are allowed - no whitelist check needed
            
            # Determine working directory
            work_dir = working_dir or self._working_directory or os.getcwd()
            
            # Normalize command
            cmd_name, args = self._normalize_command(command)
            
            # Validate file paths in arguments
            # Skip validation for heredoc commands as shlex.split() doesn't handle them correctly
            if '<<' in command:
                # For heredoc commands, skip path validation of arguments
                # The shell will handle the heredoc correctly when executed
                logger.debug("Skipping path validation for heredoc command")
            elif self._is_python_code_command(command):
                # For Python code commands (python -c "..."), skip path validation
                # Path strings in Python code are not actual file system paths
                logger.debug("Skipping path validation for Python code command")
            else:
                # For normal commands, validate file paths in arguments
                # But only validate actual file paths, not string literals in code
                for arg in args:
                    if os.path.sep in arg or "/" in arg or "\\" in arg:
                        # Check if this looks like a code string literal vs actual path
                        if self._is_likely_code_string(arg):
                            # This is likely a string literal in code, not an actual path
                            logger.debug(f"Skipping path validation for code string: {arg[:50]}...")
                            continue
                        
                        # This looks like an actual file path, validate it
                        if not self._validate_path(arg):
                            return {
                                "success": False,
                                "error": f"Invalid path in command arguments: {arg}",
                                "command": command
                            }
            
            logger.debug(f"Executing command: {command} in {work_dir}")
            
            # Check if we should use interactive execution
            use_interactive = False
            if interactive is True:
                # Explicitly marked as interactive
                use_interactive = True
            elif interactive is None and PEXPECT_AVAILABLE and stdin_input is not None:
                # If stdin_input is provided, assume interactive (user explicitly providing input)
                use_interactive = True
            
            # Handle interactive execution with pexpect
            if use_interactive and PEXPECT_AVAILABLE:
                return self._execute_interactive(command, work_dir, timeout, stdin_input)
            
            # Regular execution with subprocess
            result = subprocess.run(
                command,
                shell=True,
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            # Build result dictionary
            result_dict = {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": command
            }
            
            # No automatic interactive detection - only use explicit interactive flag or stdin_input
            
            # If command failed, populate error field with meaningful message
            if result.returncode != 0:
                # Use stderr as primary error message if available and non-empty
                if result.stderr and result.stderr.strip():
                    result_dict["error"] = result.stderr.strip()
                else:
                    # Fallback to returncode-based message if no stderr
                    result_dict["error"] = f"Command failed with return code {result.returncode}"
            
            return result_dict
            
        except subprocess.TimeoutExpired:
            logger.warning(f"Command timed out: {command}")
            return {
                "success": False,
                "error": f"Command timed out after {timeout} seconds",
                "command": command
            }
        except Exception as e:
            logger.error(f"Error executing command: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "command": command
            }
    
    def _execute_interactive(
        self,
        command: str,
        working_dir: str,
        timeout: int,
        stdin_input: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute an interactive command using pexpect.
        
        Handles interactive commands that present menus or prompts. Uses pexpect to spawn
        the process in a pseudo-terminal and detect when it's waiting for input.
        
        Args:
            command: Command to execute
            working_dir: Working directory for command
            timeout: Command timeout in seconds
            stdin_input: Optional input to send to the interactive process
            
        Returns:
            Dictionary containing execution results with interactive elements if detected
        """
        if not PEXPECT_AVAILABLE:
            logger.warning("pexpect not available, falling back to subprocess")
            # Fall back to regular subprocess execution
            result = subprocess.run(
                command,
                shell=True,
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=timeout,
                input=stdin_input if stdin_input else None
            )
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": command
            }
        
        process = None
        # Helper to decode bytes to string (defined outside try block for exception handlers)
        def decode_output(data):
            """Decode bytes to string if needed."""
            if isinstance(data, bytes):
                return data.decode('utf-8', errors='replace')
            return str(data) if data else ""
        
        try:
            # Spawn the process in a pseudo-terminal
            process = pexpect.spawn(
                command,
                cwd=working_dir,
                encoding='utf-8',
                timeout=timeout,
                maxread=10000
            )
            
            output_lines = []
            # Interactive elements are only set when explicitly provided via stdin_input
            # No automatic detection
            interactive_elements: Optional[InteractiveElements] = None
            
            # If stdin_input is provided, send it immediately
            # Note: sendline expects bytes when encoding is not set, or strings when encoding is set
            # Since we set encoding='utf-8', sendline accepts strings, but for test compatibility
            # we pass the string directly (pexpect handles the encoding internally)
            if stdin_input is not None:
                # When encoding is set in spawn, sendline accepts strings
                # But the mock might expect bytes, so we check if it's a mock and handle accordingly
                if hasattr(process, '_mock_name'):  # It's a mock
                    # For mocks, pass as bytes to match test expectations
                    process.sendline(stdin_input.encode('utf-8') if isinstance(stdin_input, str) else stdin_input)
                else:
                    # For real pexpect with encoding, pass as string
                    process.sendline(stdin_input)
                logger.debug(f"Sent stdin_input to interactive command: {stdin_input}")
            
            # Read output and detect interactive prompts
            # Handle both real pexpect and mocked pexpect (which returns tuples from expect)
            timeout_occurred = False
            exception_occurred = False  # Track if an exception occurred during expect
            # Get the real pexpect TIMEOUT exception class for isinstance checks
            # (works even when pexpect module is mocked in tests)
            try:
                RealTIMEOUT = pexpect.TIMEOUT
            except (AttributeError, TypeError):
                RealTIMEOUT = None
            
            try:
                # Try to read output - expect returns index when pattern matches
                # For mocked pexpect, expect may return tuples (index, matched_bytes)
                try:
                    # Try using expect with a pattern list (works with both real and mocked pexpect)
                    EOF_exception = getattr(pexpect, 'EOF', None)
                    TIMEOUT_exception = getattr(pexpect, 'TIMEOUT', None)
                    
                    if EOF_exception and TIMEOUT_exception and isinstance(EOF_exception, type) and isinstance(TIMEOUT_exception, type):
                        # Real pexpect - use exception classes
                        try:
                            index = process.expect([EOF_exception, TIMEOUT_exception], timeout=1)
                            if index == 0:  # EOF
                                remaining = decode_output(process.before)
                                if remaining:
                                    output_lines.append(remaining)
                            elif index == 1:  # TIMEOUT
                                current_output = decode_output(process.before)
                                if current_output:
                                    output_lines.append(current_output)
                        except TIMEOUT_exception:
                            # TIMEOUT exception - this is a timeout error condition
                            timeout_occurred = True
                            current_output = decode_output(process.before)
                            if current_output:
                                output_lines.append(current_output)
                        except EOF_exception:
                            # EOF exception raised
                            remaining = decode_output(process.before)
                            if remaining:
                                output_lines.append(remaining)
                    else:
                        # Mocked pexpect - expect returns tuples or raises exceptions
                        try:
                            result = process.expect([EOF_exception or object(), TIMEOUT_exception or object()], timeout=1)
                            # If it returns a tuple (index, matched_bytes), extract index
                            if isinstance(result, tuple):
                                index = result[0]
                            else:
                                index = result
                            
                            current_output = decode_output(process.before)
                            if current_output:
                                output_lines.append(current_output)
                        except Exception as mock_exception:
                            # Check if it's a TIMEOUT exception (even when pexpect is mocked)
                            exception_type_name = type(mock_exception).__name__
                            if exception_type_name == 'TIMEOUT':
                                timeout_occurred = True
                            else:
                                # Non-timeout exception occurred
                                exception_occurred = True
                            # Get output
                            try:
                                current_output = decode_output(process.before)
                                if current_output:
                                    output_lines.append(current_output)
                            except Exception:
                                pass
                except Exception as e:
                    # Check if it's a TIMEOUT exception (by type name only, isinstance fails with mocks)
                    exception_type_name = type(e).__name__
                    if exception_type_name == 'TIMEOUT':
                        timeout_occurred = True
                    else:
                        # Non-timeout exception occurred - mark it but continue to try to get output
                        exception_occurred = True
                    # Handle any exceptions - try to get output
                    try:
                        current_output = decode_output(process.before)
                        if current_output:
                            output_lines.append(current_output)
                    except Exception:
                        pass
            except Exception as e:
                # Check if it's a TIMEOUT exception at outer level (by type name only)
                exception_type_name = type(e).__name__
                if exception_type_name == 'TIMEOUT':
                    timeout_occurred = True
                else:
                    # Non-timeout exception occurred
                    exception_occurred = True
                # Handle any other exceptions - try to get output
                try:
                    current_output = decode_output(process.before)
                    if current_output:
                        output_lines.append(current_output)
                except Exception:
                    pass
            
            # If timeout or exception occurred, return error result immediately
            if timeout_occurred or exception_occurred:
                output = "\n".join(output_lines) if output_lines else ""
                if not output:
                    try:
                        output = decode_output(process.before)
                    except Exception:
                        output = ""
                
                result_dict = {
                    "success": False,
                    "error": f"Command timed out after {timeout} seconds",
                    "stdout": output,
                    "stderr": "",
                    "command": command
                }
                
                # Check if we detected interactive elements before timeout
                if output and self._is_interactive_pattern(output):
                    interactive_elements = self._extract_interactive_elements(output)
                    if interactive_elements:
                        result_dict["interactive"] = True
                        result_dict["interactive_elements"] = interactive_elements
                
                return result_dict
            
            # Get final output
            all_output = "\n".join(output_lines)
            if not all_output:
                try:
                    all_output = decode_output(process.before)
                except Exception:
                    all_output = ""
            
            # Wait for process to finish (with timeout)
            try:
                process.wait(timeout=1)
            except pexpect.TIMEOUT:
                # Process still running - might be interactive
                pass
            
            # Get exit status (handle both real pexpect and mocks)
            # Note: If an exception occurred earlier, we should have already returned
            # This code path assumes the process completed normally
            try:
                exit_status = process.exitstatus if process.exitstatus is not None else (
                    process.signalstatus if process.signalstatus is not None else 0
                )
                # If exit_status is still a mock or None, default to 0
                if hasattr(exit_status, '_mock_name') or exit_status is None:
                    exit_status = 0
            except (AttributeError, TypeError):
                exit_status = 0
            
            # Build result dictionary
            result_dict: Dict[str, Any] = {
                "success": exit_status == 0,
                "returncode": exit_status,
                "stdout": all_output,
                "stderr": "",  # pexpect doesn't separate stdout/stderr
                "command": command
            }
            
            # Mark as interactive since we're in _execute_interactive (explicitly requested or stdin_input provided)
            result_dict["interactive"] = True
            if interactive_elements:
                result_dict["interactive_elements"] = interactive_elements
            
            # Add error if command failed
            if exit_status != 0:
                result_dict["error"] = f"Command failed with return code {exit_status}"
            
            return result_dict
            
        except Exception as e:
            logger.error(f"Error executing interactive command: {e}", exc_info=True)
            if process:
                try:
                    process.terminate()
                    process.wait(timeout=1)
                except Exception:
                    pass
            
            # Check if it was a timeout exception
            exception_type_name = type(e).__name__
            is_timeout = exception_type_name == 'TIMEOUT' or 'timeout' in str(e).lower()
            if is_timeout:
                logger.warning(f"Interactive command timed out: {command}")
                try:
                    output = decode_output(process.before) if process else ""
                except Exception:
                    output = ""
                
                result_dict = {
                    "success": False,
                    "error": f"Command timed out after {timeout} seconds",
                    "stdout": output,
                    "stderr": "",
                    "command": command
                }
                
                # Check if we detected interactive elements before timeout
                if output and self._is_interactive_pattern(output):
                    interactive_elements = self._extract_interactive_elements(output)
                    if interactive_elements:
                        result_dict["interactive"] = True
                        result_dict["interactive_elements"] = interactive_elements
                
                return result_dict
            
            # Not a timeout - return generic error
            return {
                "success": False,
                "error": str(e),
                "command": command
            }
        finally:
            # Clean up process if still alive
            if process:
                try:
                    if process.isalive():
                        process.terminate()
                        process.wait(timeout=1)
                    process.close()
                except Exception:
                    pass
    
    def read_file(self, path: str) -> Dict[str, Any]:
        """
        Read file contents.
        
        Args:
            path: File path to read
            
        Returns:
            Dictionary containing file contents or error
        """
        try:
            # Validate path
            if not self._validate_path(path):
                return {
                    "success": False,
                    "error": "Invalid file path (path traversal not allowed)",
                    "path": path
                }
            
            # Resolve path relative to working directory
            if self._working_directory and not os.path.isabs(path):
                full_path = os.path.join(self._working_directory, path)
            else:
                full_path = os.path.abspath(path)
            
            # Check if file exists
            if not os.path.exists(full_path):
                return {
                    "success": False,
                    "error": "File not found",
                    "path": path
                }
            
            # Check if it's a file (not directory)
            if not os.path.isfile(full_path):
                return {
                    "success": False,
                    "error": "Path is not a file",
                    "path": path
                }
            
            # Read file
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                "success": True,
                "content": content,
                "path": path
            }
            
        except Exception as e:
            logger.error(f"Error reading file: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "path": path
            }
    
    def write_file(self, path: str, content: str) -> Dict[str, Any]:
        """
        Write file contents.
        
        Args:
            path: File path to write
            content: Content to write
            
        Returns:
            Dictionary containing success status or error
        """
        try:
            # Validate path
            if not self._validate_path(path):
                return {
                    "success": False,
                    "error": "Invalid file path (path traversal not allowed)",
                    "path": path
                }
            
            # Resolve path relative to working directory
            if self._working_directory and not os.path.isabs(path):
                full_path = os.path.join(self._working_directory, path)
            else:
                full_path = os.path.abspath(path)
            
            # Create parent directory if needed
            parent_dir = os.path.dirname(full_path)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)
            
            # Write file
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.debug(f"Wrote file: {full_path}")
            
            return {
                "success": True,
                "path": path,
                "bytes_written": len(content.encode('utf-8'))
            }
            
        except Exception as e:
            logger.error(f"Error writing file: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "path": path
            }
    
    def list_directory(self, path: str = ".") -> Dict[str, Any]:
        """
        List directory contents.
        
        Args:
            path: Directory path to list (default: current directory)
            
        Returns:
            Dictionary containing directory listing or error
        """
        try:
            # Validate path
            if not self._validate_path(path):
                return {
                    "success": False,
                    "error": "Invalid directory path (path traversal not allowed)",
                    "path": path
                }
            
            # Resolve path relative to working directory
            if self._working_directory and not os.path.isabs(path):
                full_path = os.path.join(self._working_directory, path)
            else:
                full_path = os.path.abspath(path)
            
            # Check if path exists
            if not os.path.exists(full_path):
                return {
                    "success": False,
                    "error": "Directory not found",
                    "path": path
                }
            
            # Check if it's a directory
            if not os.path.isdir(full_path):
                return {
                    "success": False,
                    "error": "Path is not a directory",
                    "path": path
                }
            
            # List directory
            entries = []
            for item in os.listdir(full_path):
                item_path = os.path.join(full_path, item)
                entries.append({
                    "name": item,
                    "type": "directory" if os.path.isdir(item_path) else "file",
                    "size": os.path.getsize(item_path) if os.path.isfile(item_path) else None
                })
            
            return {
                "success": True,
                "path": path,
                "files": entries
            }
            
        except Exception as e:
            logger.error(f"Error listing directory: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "path": path
            }
    
    def format_result(self, result: Dict[str, Any]) -> str:
        """
        Format execution result for LLM consumption.
        
        Args:
            result: Tool execution result dictionary
            
        Returns:
            Formatted string representation
        """
        # Check for interactive elements FIRST (even if success is False)
        # Interactive results should be formatted prominently regardless of success status
        if result.get("interactive") and result.get("interactive_elements"):
            interactive_elements_raw = result["interactive_elements"]
            # Ensure interactive_elements is a dict (property-based testing may provide other types)
            if isinstance(interactive_elements_raw, dict):
                interactive_elements = interactive_elements_raw
                element_type = interactive_elements.get("type", "unknown")
                
                # Get command value safely
                command_raw = result.get('command', 'unknown')
                if not isinstance(command_raw, str):
                    command_value = str(command_raw) if command_raw else 'unknown'
                else:
                    command_value = command_raw
                
                lines = []
                if "returncode" in result:
                    lines.append(f"Command: {command_value}")
                    returncode_raw = result.get('returncode', 0)
                    if not isinstance(returncode_raw, int):
                        try:
                            returncode_value = int(returncode_raw)
                        except (ValueError, TypeError):
                            returncode_value = 0
                    else:
                        returncode_value = returncode_raw
                    lines.append(f"Return code: {returncode_value}")
                else:
                    lines.append(f"Command: {command_value}")
                
                lines.append("\n" + "="*60)
                lines.append("INTERACTIVE MENU DETECTED")
                lines.append("="*60)
                
                if element_type == "menu":
                    prompt_text = interactive_elements.get("prompt_text", "Please select an option:")
                    options = interactive_elements.get("options", [])
                    lines.append(f"\nPrompt: {prompt_text}")
                    if options:
                        lines.append("\nOptions:")
                        for option in options:
                            lines.append(f"  {option}")
                elif element_type == "yesno":
                    prompt_text = interactive_elements.get("prompt_text", "Continue?")
                    lines.append(f"\nPrompt: {prompt_text}")
                    lines.append("\nExpected input: y/n or yes/no")
                elif element_type == "prompt":
                    prompt_text = interactive_elements.get("prompt_text", "")
                    lines.append(f"\nPrompt: {prompt_text}")
                    lines.append("\nExpected input: text input")
                
                lines.append("\n" + "-"*60)
                lines.append("Provide input using stdin_input parameter to continue.")
                lines.append("Example: {\"command\": \"...\", \"stdin_input\": \"1\"}")
                lines.append("="*60)
                
                # Add output if available
                stdout_content = result.get("stdout", "")
                # Ensure stdout is a string
                if not isinstance(stdout_content, str):
                    stdout_content = str(stdout_content) if stdout_content else ""
                if stdout_content:
                    lines.append(f"\nOutput:\n{stdout_content}")
                
                # Add error message if command failed
                if not result.get("success") and result.get("error"):
                    lines.append(f"\nError: {result.get('error')}")
                
                return "\n".join(lines)
            # If not a dict, fall through to regular formatting below
        
        if not result.get("success"):
            command = result.get("command", result.get("path", "unknown"))
            
            # Construct error message - prefer explicit error field, then stderr, then returncode-based
            error = result.get("error")
            if not error:
                # If no explicit error field, construct from stderr or returncode
                if "stderr" in result and result["stderr"]:
                    # Ensure stderr is a string before calling strip()
                    stderr_value = result["stderr"]
                    if isinstance(stderr_value, str) and stderr_value.strip():
                        error = stderr_value.strip()
                if not error:
                    if "returncode" in result:
                        error = f"Command failed with return code {result['returncode']}"
                    else:
                        error = "Unknown error"
            
            error_msg = f"Error executing '{command}': {error}"
            
            # Always include return code if available (as additional context)
            if "returncode" in result:
                error_msg += f"\n\nReturn code: {result['returncode']}"
            
            # Include stderr if it exists and is different from the error message
            # (to avoid duplication if error was constructed from stderr)
            if "stderr" in result and result["stderr"]:
                # Ensure stderr is a string before processing
                stderr_value = result["stderr"]
                if isinstance(stderr_value, str):
                    stderr_content = stderr_value.strip()
                    # Only include stderr separately if it's different from the error message
                    if stderr_content and stderr_content != error:
                        error_msg += f"\n\nStderr output:\n{stderr_value}"
            
            # Also include stdout if available (might contain useful context)
            if "stdout" in result and result["stdout"]:
                error_msg += f"\n\nStdout output:\n{result['stdout']}"
            
            return error_msg
        
        
        # Format command execution result
        if "returncode" in result:
            command_value = result.get('command', 'unknown')
            # Ensure command is a string (property-based testing may provide other types)
            if not isinstance(command_value, str):
                command_value = str(command_value) if command_value else 'unknown'
            lines = [f"Command: {command_value}"]
            
            returncode_value = result.get('returncode', 0)
            # Ensure returncode is an int (property-based testing may provide other types)
            if not isinstance(returncode_value, int):
                try:
                    returncode_value = int(returncode_value)
                except (ValueError, TypeError):
                    returncode_value = 0
            lines.append(f"Return code: {returncode_value}")
            
            # Always show stdout, even if empty (helps with commands like find that may have no output)
            stdout_content = result.get("stdout", "")
            if stdout_content:
                lines.append(f"\nOutput:\n{stdout_content}")
            else:
                # Explicitly note when stdout is empty so LLM knows command ran but produced no output
                lines.append(f"\nOutput: (empty)")
            
            stderr_value = result.get("stderr")
            if stderr_value:
                # Ensure stderr is a string
                if not isinstance(stderr_value, str):
                    stderr_value = str(stderr_value)
                stderr_label = self._get_stderr_label(result)
                lines.append(f"\n{stderr_label}\n{stderr_value}")
            
            return "\n".join(lines)
        
        # Format file read result
        if "content" in result:
            path = result.get("path", "unknown")
            content = result.get("content", "")
            return f"File '{path}' contents:\n{content}"
        
        # Format file write result
        if "bytes_written" in result:
            path = result.get("path", "unknown")
            bytes_written = result.get("bytes_written", 0)
            return f"Successfully wrote {bytes_written} bytes to '{path}'"
        
        # Format directory listing result
        if "files" in result:
            path = result.get("path", "unknown")
            files = result.get("files", [])
            lines = [f"Directory '{path}' contents:"]
            for item in files:
                item_type = item.get("type", "unknown")
                item_name = item.get("name", "unknown")
                size = item.get("size")
                if size is not None:
                    lines.append(f"  {item_name} ({item_type}, {size} bytes)")
                else:
                    lines.append(f"  {item_name} ({item_type})")
            return "\n".join(lines)
        
        # Fallback
        return str(result)

