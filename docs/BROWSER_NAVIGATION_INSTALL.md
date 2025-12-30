# Browser Navigation Tool Installation Guide

This guide explains how to install and configure the browser navigation tool for BrocaOS.

## Overview

The browser navigation tool uses Playwright to provide headless browser automation capabilities. It allows the agent to navigate websites, interact with pages, extract content, and take screenshots while minimizing CAPTCHA triggers through stealth features.

**Migration Status:** Browser-based search has fully replaced Tavily as the primary search method. Tavily is now only available as an optional emergency fallback if explicitly enabled. See `BROWSE_TOOL_USAGE.md` for comprehensive usage documentation.

## Installation Steps

### 1. Install Python Dependencies

Install all required Python packages:

```bash
pip install -r requirements.txt
```

This will install:
- `playwright>=1.40.0` - Browser automation
- `readability-lxml>=0.8.1` - Article extraction
- `trafilatura>=1.6.0` - Alternative article extraction
- `PyPDF2>=3.0.0` - PDF text extraction
- `beautifulsoup4>=4.12.0` - HTML parsing
- `lxml>=4.9.0` - XML/HTML processing

Or install individually:

```bash
pip install playwright readability-lxml trafilatura PyPDF2 beautifulsoup4 lxml
```

### 2. Install Browser Binaries

Playwright requires browser binaries to be installed separately. Install Chromium (recommended):

```bash
playwright install chromium
```

You can also install other browsers:

```bash
playwright install firefox    # Firefox
playwright install webkit     # WebKit (Safari)
```

**Note:** The tool is configured to use Chromium by default. If you want to use a different browser, you'll need to modify the tool implementation.

### 3. Install System Dependencies (Linux)

On Linux systems, you may need to install additional system dependencies:

```bash
playwright install-deps chromium
```

This installs required libraries like:
- libnss3
- libnspr4
- libatk1.0-0
- libatk-bridge2.0-0
- libcups2
- libdrm2
- libxkbcommon0
- libxcomposite1
- libxdamage1
- libxfixes3
- libxrandr2
- libgbm1
- libasound2

### 4. Verify Installation

Verify that Playwright is installed correctly:

```bash
python -c "from playwright.sync_api import sync_playwright; print('Playwright installed successfully')"
```

Test browser launch:

```bash
python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); b = p.chromium.launch(headless=True); b.close(); p.stop(); print('Browser launch successful')"
```

## Configuration

### Environment Variables

Configure the browser navigation tool using environment variables:

```bash
# Enable the browser navigation tool
export BROCA_ENABLE_BROWSER_NAVIGATION=true

# Run in headless mode (default: true)
export BROCA_BROWSER_HEADLESS=true

# Default timeout in seconds (default: 30)
export BROCA_BROWSER_TIMEOUT=30

# Enable stealth mode (default: true)
export BROCA_BROWSER_STEALTH_MODE=true

# Browse system configuration (for browser-based search)
export BROCA_BROWSE_DEFAULT_ENGINE=ddg  # "ddg" | "bing" | "google" | "auto"
export BROCA_BROWSE_ENABLE_TAVILY_FALLBACK=false  # Tavily emergency fallback (default: false)
export BROCA_BROWSE_TAVILY_FALLBACK_ONLY=false  # Use Tavily only (emergency mode)
export BROCA_BROWSE_SESSION_PERSISTENCE=true  # Persist browser sessions
export BROCA_BROWSE_MAX_ACTIONS=20  # Budget: max actions per task
export BROCA_BROWSE_MAX_WALLCLOCK_MS=60000  # Budget: max time (60s)
export BROCA_BROWSE_MAX_DOMAINS=5  # Budget: max unique domains
export BROCA_BROWSE_MAX_TOTAL_BYTES=10000000  # Budget: max data (10MB)

# Viewport dimensions (default: 1920x1080)
export BROCA_BROWSER_VIEWPORT_WIDTH=1920
export BROCA_BROWSER_VIEWPORT_HEIGHT=1080

# Custom user agents (comma-separated, optional)
export BROCA_BROWSER_USER_AGENTS="Mozilla/5.0...,Mozilla/5.0..."
```

### Configuration File

Alternatively, you can set these in your `.env` file:

```env
BROCA_ENABLE_BROWSER_NAVIGATION=true
BROCA_BROWSER_HEADLESS=true
BROCA_BROWSER_TIMEOUT=30
BROCA_BROWSER_STEALTH_MODE=true
BROCA_BROWSER_VIEWPORT_WIDTH=1920
BROCA_BROWSER_VIEWPORT_HEIGHT=1080
```

## Usage

Once installed and configured, both browser navigation and web search tools will be automatically available to the agent.

**Web Search Tool:**
- Uses browser-based search engines (DuckDuckGo, Bing, Google)
- No API key required (unlike Tavily)
- Provides citations and provenance tracking
- See `BROWSE_TOOL_USAGE.md` for comprehensive usage guide

**Browser Navigation Tool:**
- Navigate to any URL
- Click buttons and links
- Fill forms and submit data
- Extract text content from pages
- Take screenshots
- Wait for page elements or conditions

See `BROWSE_TOOL_USAGE.md` for detailed usage examples and workflows.

## Troubleshooting

### Browser Launch Fails

If browser launch fails, check:

1. Browser binaries are installed: `playwright install chromium`
2. System dependencies are installed (Linux): `playwright install-deps chromium`
3. Permissions: Ensure the user has permission to launch browsers
4. Display (if not headless): Ensure DISPLAY is set if running in non-headless mode

### Import Errors

If you see `ImportError: No module named 'playwright'`:

1. Verify Playwright is installed: `pip list | grep playwright`
2. Ensure you're using the correct Python environment
3. Reinstall: `pip install playwright`

### Timeout Errors

If operations timeout frequently:

1. Increase timeout: `export BROCA_BROWSER_TIMEOUT=60`
2. Check network connectivity
3. Verify the target website is accessible

### CAPTCHA Issues

The tool includes stealth features to minimize CAPTCHA triggers:

- User agent rotation
- Viewport randomization
- Human-like delays
- Browser flags to avoid detection

If CAPTCHAs still appear frequently:

1. Ensure stealth mode is enabled: `BROCA_BROWSER_STEALTH_MODE=true`
2. Consider adding more user agents to the rotation
3. Increase delays between actions (modify tool code)

## Security Considerations

- The browser navigation tool can access any website
- Be cautious when enabling this tool in production
- Consider implementing rate limiting or access restrictions
- Monitor browser resource usage (memory, CPU)

## Performance

- Browser instances are reused for efficiency
- Each tool execution may create a new page
- Browser cleanup happens automatically on tool destruction
- For high-volume usage, consider implementing connection pooling

## Migration from Tavily

**Status:** Browser-based search has fully replaced Tavily as the primary method.

**What Changed:**
- Web search now uses browser-based search engines by default
- No Tavily API key required
- Tavily is only available as emergency fallback (if explicitly enabled)

**Configuration:**
- Default: Browser search only (no Tavily needed)
- Emergency fallback: Set `BROCA_BROWSE_ENABLE_TAVILY_FALLBACK=true` AND provide `TAVILY_API_KEY`
- Tavily-only mode: Set `BROCA_BROWSE_TAVILY_FALLBACK_ONLY=true` (not recommended)

**Benefits:**
- No API key required
- Direct access to search engines
- Better citation and provenance tracking
- More control over search behavior
- Cost-effective (no API costs)

## Additional Resources

- **Usage Guide**: See `BROWSE_TOOL_USAGE.md` for comprehensive agent usage documentation
- [Playwright Python Documentation](https://playwright.dev/python/)
- [Playwright Installation Guide](https://playwright.dev/python/docs/intro#installation)
- [Browser Automation Best Practices](https://playwright.dev/python/docs/best-practices)

