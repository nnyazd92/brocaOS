# Browse Tool Usage Guide for Agents

This guide provides comprehensive information for agents on how to effectively use the browser-based search and navigation tools.

## Overview

The browse system provides two main tools:
1. **web_search**: Search the web using browser-based search engines
2. **browser_navigation**: Navigate and interact with websites directly

Both tools work together to provide comprehensive web access with citation tracking, safety controls, and provenance.

## Web Search Tool

### When to Use

Use `web_search` when you need to:
- Find current information, facts, or news
- Research topics or verify information
- Get multiple perspectives on a subject
- Find recent developments or updates
- Locate specific documentation or resources

### Search Query Best Practices

**Be Specific and Descriptive:**
- ✅ Good: "python asyncio error handling best practices 2024"
- ❌ Poor: "python errors"

**Include Relevant Context:**
- ✅ Good: "quantum computing applications in cryptography"
- ❌ Poor: "quantum"

**Use Natural Language:**
- ✅ Good: "how does machine learning transformer architecture work"
- ❌ Poor: "ML transformer AND architecture"

**Include Time Context for Recent Information:**
- ✅ Good: "latest AI safety research December 2024"
- ✅ Good: "recent developments in renewable energy"
- ❌ Poor: "AI safety" (too vague, may get old results)

**Combine Keywords for Technical Topics:**
- ✅ Good: "python async await performance optimization"
- ✅ Good: "react hooks useState useEffect patterns"

### Search Engine Selection

The tool automatically uses the configured search engine (default: DuckDuckGo). Different engines have different strengths:

- **DuckDuckGo (default)**: Privacy-focused, no API key needed, good for general queries
- **Bing**: Good for recent news, Microsoft ecosystem content
- **Google**: Comprehensive results, respects rate limits

### Understanding Search Results

Each search result includes:
- **title**: Page title
- **url**: Direct link to the source
- **content**: Snippet or extracted content from the page
- **score**: Relevance score (higher is better)
- **reliability_score**: Domain reputation (0.0-1.0, higher is more reliable)

**Result Interpretation:**
1. Read titles and snippets to assess relevance
2. Check URLs to verify source domain
3. Use reliability_score to prioritize trustworthy sources
4. Click through to full pages using browser_navigation if needed

### Example Queries

```json
// General information search
{"query": "how does quantum computing work", "max_results": 5}

// Recent news search
{"query": "breaking news technology December 2024", "max_results": 10}

// Technical documentation
{"query": "python asyncio documentation examples", "max_results": 3}

// Scientific/academic topics
{"query": "machine learning transformer architecture research paper", "max_results": 5}

// Troubleshooting
{"query": "python import error module not found solution", "max_results": 5}
```

### Error Handling

**Common Issues and Solutions:**

1. **No results returned:**
   - Refine query with more specific terms
   - Try different keyword combinations
   - Check if topic is too niche or recent

2. **Search fails:**
   - Verify browser navigation is enabled
   - Check Playwright installation
   - Verify network connectivity

3. **Empty results:**
   - May indicate query needs refinement
   - Try broader or different keywords
   - Some queries legitimately return no results

## Browser Navigation Tool

### When to Use

Use `browser_navigation` when you need to:
- Access specific URLs from search results
- Extract full content from web pages
- Interact with web pages (forms, buttons)
- Navigate multi-page content
- Take screenshots for verification
- Access content that requires JavaScript

### Action Workflows

#### Workflow 1: Simple Content Extraction

```json
// Step 1: Navigate to URL
{"action": "navigate", "url": "https://example.com/article"}

// Step 2: Wait for page to fully load
{"action": "wait", "wait_for": "networkidle"}

// Step 3: Extract content
{"action": "extract", "selector": "article.main-content"}
```

#### Workflow 2: Multi-Page Navigation

```json
// Navigate to main page
{"action": "navigate", "url": "https://example.com"}

// Click a link
{"action": "click", "text": "Read More"}

// Wait for new page
{"action": "wait", "wait_for": "networkidle"}

// Extract content
{"action": "extract"}
```

#### Workflow 3: Form Interaction

```json
// Navigate to form page
{"action": "navigate", "url": "https://example.com/login"}

// Wait for form to load
{"action": "wait", "wait_for": "networkidle"}

// Fill form fields
{"action": "fill", "selector": "input[name='email']", "value": "user@example.com"}
{"action": "fill", "selector": "input[name='password']", "value": "password123"}

// Submit form
{"action": "click", "selector": "button[type='submit']"}

// Wait for response
{"action": "wait", "wait_for": "networkidle"}

// Extract result
{"action": "extract"}
```

#### Workflow 4: Screenshot for Verification

```json
{"action": "navigate", "url": "https://example.com"}
{"action": "wait", "wait_for": "networkidle"}
{"action": "screenshot", "screenshot_path": "verification.png", "full_page": true}
```

### CSS Selector Best Practices

**Finding Reliable Selectors:**

1. **Use IDs (most reliable):**
   ```json
   {"action": "click", "selector": "#submit-button"}
   ```

2. **Use specific class combinations:**
   ```json
   {"action": "extract", "selector": "div.article-content > p"}
   ```

3. **Use attribute selectors:**
   ```json
   {"action": "fill", "selector": "input[name='email']"}
   {"action": "click", "selector": "button[type='submit']"}
   ```

4. **Avoid overly generic selectors:**
   - ❌ `"div"` (too generic, may match wrong element)
   - ✅ `"div.content.main-article"` (specific)

**Tips:**
- Use browser dev tools (F12) to inspect elements and find selectors
- Test selectors in browser console: `document.querySelector("your-selector")`
- Prefer stable selectors (IDs, data attributes) over CSS classes that may change

### Wait Conditions

**When to Use Each Wait Condition:**

- **`networkidle`**: After navigation, when page has dynamic content loaded via JavaScript
  ```json
  {"action": "wait", "wait_for": "networkidle"}
  ```

- **`load`**: When you need to wait for all resources (images, stylesheets) to load
  ```json
  {"action": "wait", "wait_for": "load"}
  ```

- **`domcontentloaded`**: When you only need the DOM structure (faster, for static content)
  ```json
  {"action": "wait", "wait_for": "domcontentloaded"}
  ```

- **Selector wait**: Wait for specific element to appear
  ```json
  {"action": "wait", "wait_for": "selector:.content-loaded"}
  ```

- **Text wait**: Wait for specific text to appear
  ```json
  {"action": "wait", "wait_for": "text:Loading complete"}
  ```

### Error Handling

**Common Errors and Solutions:**

1. **Timeout errors:**
   - Increase timeout parameter: `{"action": "navigate", "url": "...", "timeout": 60}`
   - Check if page is slow-loading
   - Verify network connectivity

2. **Element not found:**
   - Verify selector using browser dev tools
   - Check if element exists on the page
   - Try waiting for element first: `{"action": "wait", "wait_for": "selector:..."}`

3. **Navigation failures:**
   - Verify URL is correct and accessible
   - Check if site requires authentication
   - Some sites block automated access (normal)

4. **CAPTCHA detected:**
   - Tool will report CAPTCHA presence
   - Cannot bypass (by design for safety)
   - Try alternative sources or URLs

## Combined Workflows

### Search → Navigate → Extract → Cite

```json
// Step 1: Search for information
{"tool": "web_search", "query": "python async programming tutorial", "max_results": 5}

// Step 2: Navigate to most relevant result
{"action": "navigate", "url": "https://example.com/python-async-tutorial"}

// Step 3: Wait and extract
{"action": "wait", "wait_for": "networkidle"}
{"action": "extract", "selector": "article.tutorial-content"}

// Step 4: Use extracted content with citation
// (Citations are automatically tracked in browse traces)
```

### Multi-Source Research

```json
// Search for topic
{"tool": "web_search", "query": "climate change solutions 2024", "max_results": 10}

// Extract from top 3 results
{"action": "navigate", "url": "https://source1.com/article"}
{"action": "wait", "wait_for": "networkidle"}
{"action": "extract", "selector": "main.article"}

{"action": "navigate", "url": "https://source2.com/research"}
{"action": "wait", "wait_for": "networkidle"}
{"action": "extract", "selector": "div.research-content"}

// Compare and synthesize information from multiple sources
```

## Best Practices Summary

### Search Best Practices

1. **Formulate specific queries** with relevant keywords
2. **Include time context** for recent information
3. **Use natural language** (not boolean operators)
4. **Review reliability scores** to assess source quality
5. **Check multiple results** for comprehensive understanding

### Navigation Best Practices

1. **Always wait after navigation** (`networkidle` for dynamic content)
2. **Use specific CSS selectors** (IDs, attributes)
3. **Chain actions logically**: navigate → wait → extract
4. **Extract immediately** after navigation for accuracy
5. **Use screenshots** for debugging or verification

### General Best Practices

1. **Start with search** to find relevant URLs
2. **Navigate to verify** information from search results
3. **Extract full content** when detailed information is needed
4. **Respect rate limits** - don't make excessive requests
5. **Handle errors gracefully** - some failures are normal

## Safety and Limitations

### Safety Features

- **Payment detection**: Tool detects and blocks purchase flows
- **Account modification**: Blocks password changes, account updates
- **Credential entry**: Blocked by default (can be allowed for specific domains)
- **Sensitive data redaction**: Cookies, tokens, auth headers are redacted in logs

### Known Limitations

- **CAPTCHAs**: Cannot bypass (by design)
- **Rate limiting**: Some sites may block automated access
- **JavaScript-heavy sites**: May require longer wait times
- **Paywalls**: Tool detects but cannot bypass
- **Dynamic content**: Always use `networkidle` wait for JavaScript-rendered content

## Troubleshooting

### Search Returns No Results

1. Check query specificity - try broader or different keywords
2. Verify browser navigation is enabled
3. Check Playwright installation
4. Some queries legitimately return no results

### Navigation Fails

1. Verify URL is correct and accessible
2. Check network connectivity
3. Some sites block automated access (normal)
4. Try increasing timeout

### Element Not Found

1. Use browser dev tools to verify selector
2. Wait for element to appear first
3. Check if page structure changed
4. Try more specific selector

### Timeout Errors

1. Increase timeout parameter
2. Check if page is slow-loading
3. Verify network speed
4. Some pages legitimately take longer

## Advanced Usage

### Session Management

Browser sessions persist across tool calls automatically. Each task gets its own isolated session with:
- Persistent cookies
- localStorage data
- Browser state

Sessions are cleaned up after 24 hours of inactivity.

### Citation and Provenance

All browse operations generate trace artifacts with:
- Visited URLs and timestamps
- Content hashes for verification
- Action history
- Error logs

These traces enable full auditability and citation building.

### Budget Management

Browse operations have built-in budgets:
- Max actions per task (default: 20)
- Max wallclock time (default: 60 seconds)
- Max unique domains (default: 5)
- Max total data (default: 10MB)

Budgets prevent runaway operations and ensure resource limits.

## Examples

### Example 1: Research a Technical Topic

```json
// Search for information
{"tool": "web_search", "query": "rust ownership borrowing explained", "max_results": 5}

// Navigate to best result
{"action": "navigate", "url": "https://doc.rust-lang.org/book/ch04-00-understanding-ownership.html"}

// Extract content
{"action": "wait", "wait_for": "networkidle"}
{"action": "extract", "selector": "main.content"}
```

### Example 2: Find Recent News

```json
{"tool": "web_search", "query": "breaking news technology December 2024", "max_results": 10}

// Review results, then navigate to most relevant
{"action": "navigate", "url": "https://technews.com/article/123"}
{"action": "wait", "wait_for": "networkidle"}
{"action": "extract", "selector": "article.news-content"}
```

### Example 3: Extract Documentation

```json
{"tool": "web_search", "query": "python requests library documentation", "max_results": 3}

{"action": "navigate", "url": "https://docs.python-requests.org/"}
{"action": "wait", "wait_for": "networkidle"}
{"action": "extract", "selector": "div.documentation-content"}
```

## Additional Resources

- Installation guide: See `BROWSER_NAVIGATION_INSTALL.md`
- Configuration: See `broca/config.py` BrowseConfig
- Domain reputation: See `data/browse_domain_reputation.json`

