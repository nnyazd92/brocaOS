#!/bin/bash
# Test execution script for message validation tests
# Runs all test types: unit, integration, property-based, fault injection, golden traces,
# mutation testing, and coverage reports

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Message Validation Test Suite${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Step 1: Unit Tests
echo -e "${YELLOW}Step 1: Running Unit Tests${NC}"
echo ""
if python -m pytest broca/tests/test_session_message_validation.py -v; then
    echo -e "${GREEN}✓ Unit tests passed${NC}"
else
    echo -e "${RED}✗ Unit tests failed${NC}"
    exit 1
fi
echo ""

# Step 2: Integration Tests
echo -e "${YELLOW}Step 2: Running Integration Tests${NC}"
echo ""
if python -m pytest broca/tests/test_session_message_filtering.py -v; then
    echo -e "${GREEN}✓ Integration tests passed${NC}"
else
    echo -e "${RED}✗ Integration tests failed${NC}"
    exit 1
fi
echo ""

# Step 3: Property-Based Tests
echo -e "${YELLOW}Step 3: Running Property-Based Tests (Hypothesis)${NC}"
echo ""
if python -m pytest broca/tests/test_session_message_property.py -v; then
    echo -e "${GREEN}✓ Property-based tests passed${NC}"
else
    echo -e "${RED}✗ Property-based tests failed${NC}"
    exit 1
fi
echo ""

# Step 4: Fault Injection Tests
echo -e "${YELLOW}Step 4: Running Fault Injection Tests${NC}"
echo ""
if python -m pytest broca/tests/test_session_message_fault_injection.py -v; then
    echo -e "${GREEN}✓ Fault injection tests passed${NC}"
else
    echo -e "${RED}✗ Fault injection tests failed${NC}"
    exit 1
fi
echo ""

# Step 5: Golden Trace Replay Tests
echo -e "${YELLOW}Step 5: Running Golden Trace Replay Tests${NC}"
echo ""
if python -m pytest broca/tests/test_session_message_golden_traces.py -v; then
    echo -e "${GREEN}✓ Golden trace tests passed${NC}"
else
    echo -e "${RED}✗ Golden trace tests failed${NC}"
    exit 1
fi
echo ""

# Step 6: Coverage Report
echo -e "${YELLOW}Step 6: Generating Coverage Report${NC}"
echo ""
coverage run --source=broca/repl -m pytest broca/tests/test_session_message_validation.py broca/tests/test_session_message_filtering.py broca/tests/test_session_message_property.py broca/tests/test_session_message_fault_injection.py broca/tests/test_session_message_golden_traces.py
coverage report --show-missing --include="broca/repl/session.py" --precision=2
coverage html --include="broca/repl/session.py" -d htmlcov_message_validation

# Check coverage thresholds
COVERAGE_LINE=$(coverage report --include="broca/repl/session.py" | grep "TOTAL" | awk '{print $4}' | sed 's/%//')
COVERAGE_BRANCH=$(coverage report --include="broca/repl/session.py" | grep "TOTAL" | awk '{print $5}' | sed 's/%//')

echo ""
echo -e "${BLUE}Coverage Results:${NC}"
echo -e "  Line Coverage: ${COVERAGE_LINE}%"
echo -e "  Branch Coverage: ${COVERAGE_BRANCH}%"

# Simple coverage check (basic comparison)
LINE_VAL=$(echo "$COVERAGE_LINE" | sed 's/%//' | cut -d. -f1)
BRANCH_VAL=$(echo "$COVERAGE_BRANCH" | sed 's/%//' | cut -d. -f1)

if [ "$LINE_VAL" -ge 95 ] && [ "$BRANCH_VAL" -ge 90 ] 2>/dev/null; then
    echo -e "${GREEN}✓ Coverage thresholds met (95%+ line, 90%+ branch)${NC}"
else
    echo -e "${YELLOW}⚠ Coverage thresholds not met (target: 95%+ line, 90%+ branch)${NC}"
fi
echo ""

# Step 7: Mutation Testing (optional, may take a while)
echo -e "${YELLOW}Step 7: Running Mutation Testing (optional)${NC}"
echo ""
if command -v mutmut &> /dev/null; then
    echo "Running mutation tests for message validation logic..."
    if mutmut run --paths-to-mutate=broca/repl/session.py --tests-dir=broca/tests --runner="python -m pytest broca/tests/test_session_message_validation.py broca/tests/test_session_message_filtering.py -x"; then
        echo ""
        echo -e "${BLUE}Mutation test results:${NC}"
        mutmut results
        echo ""
        
        # Check for surviving mutations
        SURVIVING=$(mutmut results 2>/dev/null | grep -i "survived" || echo "")
        if [[ -n "$SURVIVING" ]]; then
            echo -e "${YELLOW}⚠ Some mutations survived!${NC}"
            echo "Run 'mutmut show' to see surviving mutations"
        else
            echo -e "${GREEN}✓ No surviving mutations${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ Mutation testing failed or timed out${NC}"
    fi
else
    echo -e "${YELLOW}⚠ mutmut not installed, skipping mutation testing${NC}"
    echo "Install with: pip install mutmut"
fi
echo ""

# Summary
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Test Suite Complete${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${GREEN}All tests passed!${NC}"
echo ""

