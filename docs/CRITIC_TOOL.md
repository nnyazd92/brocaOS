# Critic Tool

The critic tool provides devils advocate feedback on any content. It acts as a critical second opinion, challenging assumptions, finding weaknesses, and providing alternative perspectives.

## Overview

The critic tool is a freely callable tool (no enforcement or binding) that uses a separate LLM instance to provide critical analysis of content. It can be used to:

- Get a second opinion on responses before finalizing them
- Identify potential weaknesses or blind spots
- Challenge assumptions and find alternative viewpoints
- Consider edge cases and unintended consequences
- Improve content quality through constructive criticism

## Usage

The critic tool can be called like any other tool in the system. It does not enforce any iteration loops or block final responses - it simply provides feedback that the LLM can use as it sees fit.

### Parameters

- **world_state** (object, required): Contains optional metadata and constraints
  - **metadata** (object, optional): Context information (e.g., domain, context type)
  - **constraints** (object, optional): Constraints or concerns to consider during analysis
- **content** (string, required): The content to analyze

### Return Format

The tool returns a JSON object with:

- **accepted** (boolean): `true` if content is generally acceptable, `false` if significant concerns are identified
- **feedback** (string): Detailed critical analysis and alternative perspectives
- **violations** (array): List of concern objects, each with:
  - **constraint** or **concern** (string): Name of the constraint/concern
  - **description** (string): Description of the issue

## Examples

### Basic Usage

```json
{
  "world_state": {
    "metadata": {
      "context": "code review",
      "domain": "software engineering"
    },
    "constraints": {
      "security": "Ensure no security vulnerabilities",
      "performance": "Consider performance implications"
    }
  },
  "content": "Here's my proposed solution..."
}
```

### Without Constraints (General Analysis)

```json
{
  "world_state": {},
  "content": "Here's my response to the user's question..."
}
```

The critic will provide general devils advocate feedback even without specific constraints.

### Response Format

The tool returns formatted feedback like:

```
The critic finds the content generally acceptable.

Feedback: The solution is well-structured, but consider edge cases where
the input might be null. Also, the error handling could be more robust.

Specific concerns:
1. edge_cases: Null input handling is not addressed
2. error_handling: Error messages could be more informative
```

## Configuration

The critic tool is enabled via the `BROCA_ENABLE_CRITIC` environment variable:

```bash
export BROCA_ENABLE_CRITIC=true
```

A custom system prompt template can be provided via `BROCA_CRITIC_SYSTEM_PROMPT`:

```bash
export BROCA_CRITIC_SYSTEM_PROMPT="Your custom prompt template here"
```

The template should include placeholders for:
- `{metadata_section}`: Formatted metadata
- `{constraints_section}`: Formatted constraints/considerations

## Registration

The critic tool is automatically registered in both:
- `main_repl.py` (REPL interface)
- `web_api.py` (via `main_repl_runtime.py`)

Registration occurs in `_initialize_tool_registry()` when `config.tools.enable_critic` is `True`.

## Important Notes

- **No Enforcement**: The critic tool does not enforce any iteration loops or block final responses. It is a free tool that provides feedback only.
- **Optional Constraints**: Constraints are optional - the tool can provide general critical analysis without specific constraints.
- **Devils Advocate**: The tool is designed to challenge assumptions and provide alternative perspectives, not just validate against constraints.
- **Constructive Criticism**: The feedback is meant to be constructive and help improve content quality.

## Implementation Details

The critic tool:
- Uses a separate LLM instance (via `create_llm_client()`)
- Formats system prompts from world_state metadata and constraints
- Parses JSON responses from the critic LLM
- Handles errors gracefully, returning structured error information
- Formats results for easy consumption by the main LLM

## Testing

Tests are located in:
- `broca/tests/test_critic_tool.py`: Unit tests for the tool itself
- `broca/tests/test_critic_enforcement.py`: Tests verifying it works as a free tool (no enforcement)

