"""
Z3 validator tool for LLM-driven logical validation.

Allows the LLM to construct and execute Z3 code to validate plan logic,
check satisfiability, and ensure logical soundness of reasoning.
"""

from __future__ import annotations

import os
import sys
import logging
import subprocess
import tempfile
import json
from pathlib import Path
from typing import Dict, Any, Optional
import traceback

try:
    import z3
    Z3_AVAILABLE = True
except ImportError:
    Z3_AVAILABLE = False
    z3 = None  # type: ignore

from ..config import config

logger = logging.getLogger(__name__)


class Z3ValidatorTool:
    """
    Tool for LLM to construct and execute Z3 code for plan validation.
    
    Allows LLM to:
    - Encode plan steps, assumptions, and goals as Z3 constraints
    - Check satisfiability and logical soundness
    - Get counterexamples if plan is unsound
    - Iteratively improve plan based on Z3 results
    """
    
    def __init__(self, timeout: float = 5.0, max_output_size: int = 10000):
        """
        Initialize Z3 validator tool.
        
        Args:
            timeout: Execution timeout in seconds (default: 5.0)
            max_output_size: Maximum output size in bytes (default: 10000)
        """
        self.timeout = timeout
        self.max_output_size = max_output_size
        
        if not Z3_AVAILABLE:
            logger.warning("Z3 not available. Install with: pip install z3-solver")
        
        logger.info(f"Initialized Z3ValidatorTool (timeout={timeout}s, Z3_AVAILABLE={Z3_AVAILABLE})")
    
    @property
    def name(self) -> str:
        """Tool identifier."""
        return "z3_validate"
    
    @property
    def description(self) -> str:
        """Tool description for the LLM."""
        return (
            "Validate logical constraints using Z3 theorem prover. "
            "Write Z3 Python code to encode your plan's logic and check if it's satisfiable. "
            "\n\n"
            "Use this tool during planning to verify your plan is logically sound. "
            "Encode plan steps, assumptions, and goals as Z3 constraints, then check satisfiability. "
            "\n\n"
            "The tool executes your Z3 Python code and returns: "
            "- Result: 'sat' (satisfiable), 'unsat' (unsatisfiable), 'unknown', or 'error' "
            "- Model: If sat, provides satisfying assignment "
            "- Unsat core: If unsat, provides minimal unsatisfiable subset "
            "- Error: If execution failed, provides error message "
            "\n\n"
            "Example usage:\n"
            "```python\n"
            "from z3 import *\n"
            "solver = Solver()\n"
            "# Encode plan logic\n"
            "step1 = Bool('step1')\n"
            "step2 = Bool('step2')\n"
            "goal = Bool('goal')\n"
            "solver.add(Implies(And(step1, step2), goal))\n"
            "solver.add(step1)\n"
            "solver.add(step2)\n"
            "result = solver.check()\n"
            "if result == sat:\n"
            "    model = solver.model()\n"
            "    print(f'Satisfiable: {model}')\n"
            "else:\n"
            "    print(f'Unsatisfiable or unknown: {result}')\n"
            "```\n"
            "\n"
            "The tool will execute this code and return the results for you to interpret."
        )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """JSON schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "z3_code": {
                    "type": "string",
                    "description": "Python code using Z3 to validate logical constraints. Must import z3 and use Z3 API."
                },
                "timeout": {
                    "type": "number",
                    "description": "Optional execution timeout in seconds (default: 5.0)",
                    "default": 5.0,
                    "minimum": 0.1,
                    "maximum": 30.0
                }
            },
            "required": ["z3_code"]
        }
    
    def execute(self, z3_code: str, timeout: Optional[float] = None) -> Dict[str, Any]:
        """
        Execute Z3 Python code safely.
        
        Args:
            z3_code: Python code using Z3 (must import z3)
            timeout: Optional execution timeout override (uses instance default if not provided)
            
        Returns:
            {
                "result": "sat" | "unsat" | "unknown" | "error",
                "model": {...} if sat,
                "unsat_core": [...] if unsat,
                "error": str if error,
                "output": str stdout/stderr,
                "z3_available": bool
            }
        """
        if not Z3_AVAILABLE:
            return {
                "result": "error",
                "error": "Z3 is not available. Install with: pip install z3-solver",
                "z3_available": False,
                "output": ""
            }
        
        exec_timeout = timeout if timeout is not None else self.timeout
        
        # Create a temporary Python script
        script_content = self._create_validation_script(z3_code)
        
        try:
            # Execute in a subprocess with timeout
            result = subprocess.run(
                [sys.executable, "-c", script_content],
                capture_output=True,
                text=True,
                timeout=exec_timeout,
                env=os.environ.copy()
            )
            
            # Parse output
            output = result.stdout + result.stderr
            
            # Truncate output if too large
            if len(output) > self.max_output_size:
                output = output[:self.max_output_size] + "\n... (truncated)"
            
            if result.returncode != 0:
                return {
                    "result": "error",
                    "error": f"Execution failed with return code {result.returncode}",
                    "output": output,
                    "z3_available": True
                }
            
            # Try to parse JSON result from output (between markers)
            try:
                start_marker = "===Z3_RESULT_START==="
                end_marker = "===Z3_RESULT_END==="
                start_idx = output.find(start_marker)
                end_idx = output.find(end_marker)
                
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = output[start_idx + len(start_marker):end_idx].strip()
                    parsed_result = json.loads(json_str)
                    parsed_result["output"] = output
                    parsed_result["z3_available"] = True
                    return parsed_result
            except (json.JSONDecodeError, ValueError, AttributeError):
                pass
            
            # Fallback: try to find JSON anywhere in output
            try:
                json_start = output.rfind("{")
                json_end = output.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = output[json_start:json_end]
                    parsed_result = json.loads(json_str)
                    parsed_result["output"] = output
                    parsed_result["z3_available"] = True
                    return parsed_result
            except (json.JSONDecodeError, ValueError):
                pass
            
            # If no JSON found, try to infer result from output
            output_lower = output.lower()
            if "sat" in output_lower and "unsat" not in output_lower:
                return {
                    "result": "sat",
                    "output": output,
                    "z3_available": True,
                    "note": "Result inferred from output - model not captured"
                }
            elif "unsat" in output_lower:
                return {
                    "result": "unsat",
                    "output": output,
                    "z3_available": True,
                    "note": "Result inferred from output - unsat core not captured"
                }
            elif "unknown" in output_lower:
                return {
                    "result": "unknown",
                    "output": output,
                    "z3_available": True
                }
            else:
                return {
                    "result": "unknown",
                    "output": output,
                    "z3_available": True,
                    "note": "Could not determine result from output"
                }
                
        except subprocess.TimeoutExpired:
            return {
                "result": "error",
                "error": f"Execution timed out after {exec_timeout} seconds",
                "z3_available": True,
                "output": ""
            }
        except Exception as e:
            logger.error(f"Error executing Z3 code: {e}", exc_info=True)
            return {
                "result": "error",
                "error": f"Execution error: {str(e)}",
                "z3_available": True,
                "output": traceback.format_exc()
            }
    
    def _create_validation_script(self, z3_code: str) -> str:
        """
        Create a Python script that executes Z3 code and returns structured results.
        
        Args:
            z3_code: User-provided Z3 Python code
            
        Returns:
            Complete Python script string
        """
        # Escape the code for embedding in f-string
        escaped_code = z3_code.replace('{', '{{').replace('}', '}}')
        
        # Wrap user code in a script that captures results
        script = f"""
import json
import sys
from z3 import *

# Execute user's Z3 code
try:
    # Create a namespace for user code
    user_namespace = {{}}
    user_namespace.update(globals())
    
    # Execute the code in the namespace
    exec('''{escaped_code}''', user_namespace)
    
    # Try to extract results from common variable names
    result_dict = {{}}
    solver = user_namespace.get('solver')
    result = user_namespace.get('result')
    model = user_namespace.get('model')
    
    if solver is not None:
        # User created a solver, check its state
        if hasattr(solver, 'check'):
            check_result = solver.check()
            if check_result == sat:
                model = solver.model()
                result_dict["result"] = "sat"
                # Convert model to dict
                model_dict = {{}}
                for decl in model:
                    model_dict[str(decl)] = str(model[decl])
                result_dict["model"] = model_dict
            elif check_result == unsat:
                result_dict["result"] = "unsat"
                # Try to get unsat core
                try:
                    core = solver.unsat_core()
                    result_dict["unsat_core"] = [str(c) for c in core]
                except:
                    pass
            else:
                result_dict["result"] = "unknown"
    elif result is not None:
        # User set a result variable
        if result == sat:
            result_dict["result"] = "sat"
            if model is not None:
                model_dict = {{}}
                for decl in model:
                    model_dict[str(decl)] = str(model[decl])
                result_dict["model"] = model_dict
        elif result == unsat:
            result_dict["result"] = "unsat"
        else:
            result_dict["result"] = "unknown"
    else:
        # No solver or result found - code may have printed results
        result_dict["result"] = "unknown"
        result_dict["note"] = "Could not automatically extract result. Check output for printed results."
    
    # Output JSON result
    print("\\n===Z3_RESULT_START===")
    print(json.dumps(result_dict))
    print("===Z3_RESULT_END===")
    
except Exception as e:
    import traceback
    error_msg = str(e)
    trace = traceback.format_exc()
    print(trace, file=sys.stderr)
    result_dict = {{
        "result": "error",
        "error": error_msg
    }}
    print("\\n===Z3_RESULT_START===")
    print(json.dumps(result_dict))
    print("===Z3_RESULT_END===")
"""
        return script

