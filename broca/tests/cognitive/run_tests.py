#!/usr/bin/env python3
"""
Test runner for cognitive web app.
Runs tests in order: unit -> integration -> smoke (if playwright available).
"""

import subprocess
import sys
import os

def run_command(cmd, description):
    """Run a command and print results."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {cmd}")
    print(f"{'='*60}\n")
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    print(f"\nExit code: {result.returncode}")
    return result.returncode == 0

def main():
    """Run all tests."""
    test_dir = os.path.dirname(__file__)
    
    # 1. Run unit tests (fast)
    print("🧪 PHASE 1: Unit Tests")
    success = run_command(
        f"cd {os.path.dirname(test_dir)} && python -m pytest tests/cognitive/test_web_endpoints_integration.py -v",
        "Cognitive endpoint unit tests"
    )
    
    if not success:
        print("❌ Unit tests failed. Stopping.")
        return 1
    
    # 2. Check if web server is running
    print("\n🌐 PHASE 2: Web Server Check")
    import requests
    try:
        response = requests.get("http://localhost:5173/cognitive", timeout=5)
        print(f"✅ Web server is running (status: {response.status_code})")
    except:
        print("❌ Web server not running on localhost:5173")
        print("   Start it with: cd /home/wizard/broca-www && npm run dev")
        return 1
    
    # 3. Run smoke tests if playwright available
    print("\n🚀 PHASE 3: Smoke Tests (if playwright installed)")
    playwright_test = os.path.join(test_dir, "test_smoke_playwright.py")
    if os.path.exists(playwright_test):
        success = run_command(
            f"cd {os.path.dirname(test_dir)} && python -m pytest {playwright_test} -v --base-url http://localhost:5173",
            "Playwright smoke tests"
        )
        if not success:
            print("⚠️  Smoke tests failed, but continuing...")
    else:
        print("⚠️  Playwright tests not found, skipping...")
    
    print("\n🎉 All tests completed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
