"""
Debug script to inspect the Audacy page structure
"""
import asyncio
from playwright.async_api import async_playwright

async def debug_page():
    """Inspect the page structure to understand how episodes are loaded"""

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # visible browser
        page = await browser.new_page()

        print("Loading page...")
        await page.goto('https://www.audacy.com/podcast/kleinally-show-the-podcast-599ed/episodes',
                       wait_until='networkidle', timeout=60000)

        print("\nWaiting for page to fully load...")
        await asyncio.sleep(5)

        # Save page content for inspection
        content = await page.content()
        with open('page_debug.html', 'w', encoding='utf-8') as f:
            f.write(content)
        print("Saved page HTML to: page_debug.html")

        # Take a screenshot
        await page.screenshot(path='page_debug.png', full_page=True)
        print("Saved screenshot to: page_debug.png")

        # Try to find common elements
        print("\n=== Looking for episode elements ===")

        selectors_to_try = [
            'article',
            '[class*="episode"]',
            '[class*="Episode"]',
            '[class*="podcast"]',
            '[class*="Podcast"]',
            '[data-testid*="episode"]',
            '[role="article"]',
            'li[class*="list"]',
            'div[class*="card"]',
            'div[class*="item"]',
            'a[href*="episode"]',
        ]

        for selector in selectors_to_try:
            elements = await page.query_selector_all(selector)
            if elements:
                print(f"✓ Found {len(elements)} elements with selector: {selector}")

                # Get details of first element
                if elements:
                    first = elements[0]
                    html = await first.evaluate('el => el.outerHTML')
                    print(f"  First element HTML (truncated): {html[:200]}...")
            else:
                print(f"✗ No elements found with: {selector}")

        # Look for load more button
        print("\n=== Looking for 'Load More' button ===")
        load_more_selectors = [
            'button:has-text("Load More")',
            'button:has-text("Show More")',
            'button:has-text("See More")',
            'button[class*="load"]',
            'button[class*="more"]',
            '[class*="load"][class*="more"]',
        ]

        for selector in load_more_selectors:
            button = await page.query_selector(selector)
            if button:
                text = await button.inner_text()
                print(f"✓ Found button with selector: {selector}")
                print(f"  Button text: {text}")
                html = await button.evaluate('el => el.outerHTML')
                print(f"  Button HTML: {html[:200]}...")
                break
        else:
            print("✗ No 'Load More' button found")

        # Check for any API calls
        print("\n=== Checking page for data ===")

        # Try to find JSON data in page
        data_scripts = await page.query_selector_all('script[type="application/json"]')
        print(f"Found {len(data_scripts)} JSON script tags")

        if data_scripts:
            for i, script in enumerate(data_scripts[:3]):  # Check first 3
                content = await script.inner_text()
                if 'episode' in content.lower() or 'podcast' in content.lower():
                    print(f"\n  Script {i} contains episode data (first 500 chars):")
                    print(f"  {content[:500]}...")

        print("\n=== Page inspection complete ===")
        print("Check page_debug.html and page_debug.png for details")
        print("\nPress Enter to close browser...")

        # Keep browser open for manual inspection
        await asyncio.sleep(30)  # 30 seconds to inspect manually

        await browser.close()

if __name__ == '__main__':
    asyncio.run(debug_page())
