#!/bin/bash
# run_full_test_suite.sh - Comprehensive test suite runner for BrocaOS
# Usage: ./run_full_test_suite.sh [options]

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default options
QUICK=false
FULL=false
COVERAGE=true
MUTATION=false
VERBOSE=false
HTML_REPORT=true
PARALLEL=false
FAIL_FAST=false
MODULE=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --quick|-q)
            QUICK=true
            COVERAGE=false
            MUTATION=false
            HTML_REPORT=false
            ;;
        --full|-f)
            FULL=true
            COVERAGE=true
            MUTATION=true
            HTML_REPORT=true
            ;;
        --no-coverage)
            COVERAGE=false
            ;;
        --mutation|-m)
            MUTATION=true
            ;;
        --no-mutation)
            MUTATION=false
            ;;
        --no-html)
            HTML_REPORT=false
            ;;
        --verbose|-v)
            VERBOSE=true
            ;;
        --parallel|-p)
            PARALLEL=true
            ;;
        --fail-fast|-x)
            FAIL_FAST=true
            ;;
        --module)
            MODULE="$2"
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --quick, -q           Run quick test suite (no coverage, no mutation)"
            echo "  --full, -f            Run full test suite (coverage + mutation)"
            echo "  --no-coverage         Skip coverage reporting"
            echo "  --mutation, -m        Run mutation testing"
            echo "  --no-mutation         Skip mutation testing (default unless --full)"
            echo "  --no-html             Skip HTML coverage report"
            echo "  --verbose, -v         Verbose output"
            echo "  --parallel, -p        Run tests in parallel"
            echo "  --fail-fast, -x       Stop on first failure"
            echo "  --module MODULE       Run tests for specific module (e.g., summarization)"
            echo "  --help, -h            Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
    shift
done

# Default to full if no mode specified
if [[ "$QUICK" == false && "$FULL" == false ]]; then
    FULL=true
fi

# Print header
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║          BrocaOS Full Test Suite Runner                   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Build pytest command
PYTEST_CMD="python -m pytest"

# Test directory
if [[ -n "$MODULE" ]]; then
    TEST_PATH="broca/tests/test_${MODULE}*.py"
    echo -e "${YELLOW}Running tests for module: ${MODULE}${NC}"
else
    TEST_PATH="broca/tests/"
    echo -e "${YELLOW}Running all tests${NC}"
fi

# Build pytest arguments
PYTEST_ARGS=()

if [[ "$VERBOSE" == true ]]; then
    PYTEST_ARGS+=("-v")
else
    PYTEST_ARGS+=("-q")
fi

if [[ "$FAIL_FAST" == true ]]; then
    PYTEST_ARGS+=("-x")
fi

if [[ "$PARALLEL" == true ]]; then
    if command -v pytest-xdist &> /dev/null; then
        PYTEST_ARGS+=("-n" "auto")
        echo -e "${YELLOW}Running tests in parallel${NC}"
    else
        echo -e "${YELLOW}Warning: pytest-xdist not installed, running sequentially${NC}"
    fi
fi

# Coverage options
if [[ "$COVERAGE" == true ]]; then
    PYTEST_ARGS+=("--cov=broca")
    PYTEST_ARGS+=("--cov-branch")
    PYTEST_ARGS+=("--cov-report=term")
    
    if [[ "$HTML_REPORT" == true ]]; then
        PYTEST_ARGS+=("--cov-report=html")
    fi
    
    # Coverage thresholds (adjust as needed)
    PYTEST_ARGS+=("--cov-fail-under=50")  # Minimum 50% overall coverage
fi

# Additional pytest options
PYTEST_ARGS+=("--tb=short")  # Shorter traceback format
PYTEST_ARGS+=("--strict-markers")  # Strict marker validation
PYTEST_ARGS+=("--disable-warnings")  # Suppress warnings (optional)

# Function to run tests
run_tests() {
    local start_time=$(date +%s)
    
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}Step 1: Running pytest${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    if [[ "$VERBOSE" == true ]]; then
        echo "Command: $PYTEST_CMD $TEST_PATH ${PYTEST_ARGS[*]}"
        echo ""
    fi
    
    if $PYTEST_CMD "$TEST_PATH" "${PYTEST_ARGS[@]}"; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        echo ""
        echo -e "${GREEN}✓ Tests completed successfully in ${duration}s${NC}"
        return 0
    else
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        echo ""
        echo -e "${RED}✗ Tests failed after ${duration}s${NC}"
        return 1
    fi
}

# Function to run mutation testing
run_mutation_tests() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}Step 2: Running Mutation Testing${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    if ! command -v mutmut &> /dev/null; then
        echo -e "${YELLOW}Warning: mutmut not installed, skipping mutation testing${NC}"
        echo "Install with: pip install mutmut"
        return 0
    fi
    
    local start_time=$(date +%s)
    
    # Run mutation testing for summarization module (most critical)
    echo -e "${YELLOW}Running mutation tests for summarization module...${NC}"
    echo -e "${YELLOW}(This may take 10-30 minutes)${NC}"
    echo ""
    
    if mutmut run --paths-to-mutate=broca/summarization/summarizer.py; then
        echo ""
        echo -e "${GREEN}Mutation testing completed${NC}"
        echo ""
        echo -e "${BLUE}Mutation test results:${NC}"
        mutmut results
        echo ""
        
        # Check for surviving mutations
        local surviving=$(mutmut results 2>/dev/null | grep -i "survived" || echo "")
        if [[ -n "$surviving" ]]; then
            echo -e "${YELLOW}Warning: Some mutations survived!${NC}"
            echo "Run 'mutmut show' to see surviving mutations"
        fi
        
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        echo -e "${GREEN}✓ Mutation testing completed in ${duration}s${NC}"
        return 0
    else
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        echo -e "${RED}✗ Mutation testing failed after ${duration}s${NC}"
        return 1
    fi
}

# Function to show summary
show_summary() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}Test Suite Summary${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    if [[ "$COVERAGE" == true && "$HTML_REPORT" == true ]]; then
        echo ""
        echo -e "${GREEN}Coverage report:${NC} htmlcov/index.html"
        echo "  Open in browser to view detailed coverage"
    fi
    
    if [[ "$MUTATION" == true ]]; then
        echo ""
        echo -e "${GREEN}Mutation testing:${NC}"
        echo "  Run 'mutmut show <id>' to see specific mutations"
        echo "  Run 'mutmut results' to see summary"
    fi
    
    echo ""
    echo -e "${GREEN}✓ Test suite completed!${NC}"
    echo ""
}

# Main execution
main() {
    local overall_start=$(date +%s)
    local test_passed=true
    
    # Run tests
    if ! run_tests; then
        test_passed=false
    fi
    
    # Run mutation tests if requested and tests passed
    if [[ "$MUTATION" == true && "$test_passed" == true ]]; then
        if ! run_mutation_tests; then
            test_passed=false
        fi
    fi
    
    # Show summary
    show_summary
    
    local overall_end=$(date +%s)
    local total_duration=$((overall_end - overall_start))
    
    echo -e "${BLUE}Total time: ${total_duration}s${NC}"
    echo ""
    
    if [[ "$test_passed" == true ]]; then
        echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║              All tests passed! ✓                          ║${NC}"
        echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
        exit 0
    else
        echo -e "${RED}╔════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${RED}║              Some tests failed! ✗                          ║${NC}"
        echo -e "${RED}╚════════════════════════════════════════════════════════════╝${NC}"
        exit 1
    fi
}

# Run main
main