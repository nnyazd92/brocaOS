"""
Smoke test for cognitive web app - ensures basic functionality works.
"""

import pytest
from playwright.sync_api import Page, expect

@pytest.mark.playwright
def test_cognitive_playground_loads(page: Page, base_url: str):
    """Test that the cognitive playground page loads."""
    # Navigate to cognitive playground
    page.goto(f"{base_url}/cognitive")
    
    # Check page title
    expect(page).to_have_title("Cognitive Playground - Interact with BrocaOS Cognitive Architecture")
    
    # Check main heading
    expect(page.locator("h1")).to_contain_text("Interact with a Cognitive Architecture")
    
    # Check query input exists
    expect(page.locator("textarea")).to_be_visible()
    
    # Check control checkboxes exist
    expect(page.locator('input[type="checkbox"]')).to_have_count_at_least(3)
    
    # Check submit button exists
    expect(page.locator('button:has-text("Run Cognitive Query")')).to_be_visible()

@pytest.mark.playwright
def test_cognitive_query_submission(page: Page, base_url: str):
    """Test that submitting a cognitive query works."""
    page.goto(f"{base_url}/cognitive")
    
    # Enter a query
    page.fill("textarea", "Test cognitive query")
    
    # Submit the form
    page.click('button:has-text("Run Cognitive Query")')
    
    # Should show processing state
    expect(page.locator('button:has-text("Processing")')).to_be_visible()
    
    # Eventually should show response (or error)
    # This is a smoke test, so we just wait for state change
    page.wait_for_timeout(2000)
    
    # Either response shows or error shows
    response_or_error = page.locator('.glass-card').filter(has_text=("BrocaOS Response")).or_(
        page.locator('.bg-rose-500/10')
    )
    expect(response_or_error).to_be_visible(timeout=10000)

@pytest.mark.playwright  
def test_metrics_dashboard_updates(page: Page, base_url: str):
    """Test that the metrics dashboard shows live data."""
    page.goto(f"{base_url}/cognitive")
    
    # Check metrics dashboard exists
    expect(page.locator('text=Cognitive Metrics')).to_be_visible()
    
    # Check system health indicator exists
    expect(page.locator('text=HEALTHY') | page.locator('text=DEGRADED') | page.locator('text=CRITICAL')).to_be_visible()
    
    # Check at least some metrics are shown
    expect(page.locator('text=System Health')).to_be_visible()
    expect(page.locator('text=Reasoning Engine')).to_be_visible()
    expect(page.locator('text=Learning System')).to_be_visible()

@pytest.mark.playwright
def test_example_queries_work(page: Page, base_url: str):
    """Test that example queries can be clicked and populated."""
    page.goto(f"{base_url}/cognitive")
    
    # Click first example query
    example_button = page.locator('button:has-text("What is the formal")').first
    expect(example_button).to_be_visible()
    example_button.click()
    
    # Check that textarea now contains the example
    textarea = page.locator("textarea")
    expect(textarea).to_have_value(/formal logical proof/i)
