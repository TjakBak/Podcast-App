"""
Advanced diagnostic script to analyze Audacy page and generate custom scraper
This script will inspect the page and show you exactly what data is available
"""
import asyncio
import json
import re
from playwright.async_api import async_playwright

async def analyze_audacy_page():
    """Comprehensive analysis of the Audacy podcast page"""

    print("="*70)
    print("AUDACY PAGE ANALYZER")
    print("="*70)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Visible browser
        page = await browser.new_page()

        # Capture all network requests
        api_requests = []

        async def log_request(request):
            if 'episode' in request.url.lower() or 'podcast' in request.url.lower():
                api_requests.append({
                    'url': request.url,
                    'method': request.method,
                })

        async def log_response(response):
            url = response.url
            if ('episode' in url.lower() or 'podcast' in url.lower()) and response.status == 200:
                try:
                    if 'json' in response.headers.get('content-type', ''):
                        data = await response.json()
                        api_requests.append({
                            'url': url,
                            'method': 'GET',
                            'response': data,
                            'has_data': True
                        })
                except:
                    pass

        page.on('request', log_request)
        page.on('response', log_response)

        print("\n1. Loading page...")
        try:
            await page.goto('https://www.audacy.com/podcast/kleinally-show-the-podcast-599ed/episodes',
                           wait_until='networkidle', timeout=60000)
            print("   ✓ Page loaded successfully")
        except Exception as e:
            print(f"   ✗ Error: {e}")
            await browser.close()
            return

        print("\n2. Waiting for content to load (10 seconds)...")
        await asyncio.sleep(10)

        # Get page content
        html_content = await page.content()

        # Save full HTML
        with open('audacy_page_analysis.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        print("   ✓ Saved page HTML to: audacy_page_analysis.html")

        # Take screenshot
        await page.screenshot(path='audacy_page_analysis.png', full_page=True)
        print("   ✓ Saved screenshot to: audacy_page_analysis.png")

        # ==========================================
        # ANALYSIS 1: Check for JSON in script tags
        # ==========================================
        print("\n3. Analyzing embedded JSON data...")
        script_tags = await page.query_selector_all('script:not([src])')

        found_json_data = []
        for i, script in enumerate(script_tags):
            try:
                content = await script.inner_text()
                if len(content) < 100:
                    continue

                content = content.strip()
                if content.startswith('{') or content.startswith('['):
                    # Try to parse as JSON
                    try:
                        data = json.loads(content)
                        if 'episode' in str(data).lower() or 'podcast' in str(data).lower():
                            found_json_data.append({
                                'script_index': i,
                                'size': len(content),
                                'data': data
                            })
                            print(f"   ✓ Found JSON data in script tag #{i} (size: {len(content)} chars)")
                    except:
                        pass
            except:
                pass

        if found_json_data:
            print(f"\n   Found {len(found_json_data)} script tags with episode data!")
            for item in found_json_data[:2]:  # Show first 2
                print(f"\n   Script #{item['script_index']} sample data:")
                print(f"   {str(item['data'])[:500]}...")

                # Save to file
                with open(f'json_data_script_{item["script_index"]}.json', 'w', encoding='utf-8') as f:
                    json.dump(item['data'], f, indent=2)
                print(f"   Saved to: json_data_script_{item['script_index']}.json")
        else:
            print("   ✗ No JSON episode data found in script tags")

        # ==========================================
        # ANALYSIS 2: Find episode elements in DOM
        # ==========================================
        print("\n4. Searching for episode elements in DOM...")

        selectors_to_test = [
            ('article', 'Article tags'),
            ('[class*="episode"]', 'Elements with "episode" in class'),
            ('[class*="Episode"]', 'Elements with "Episode" in class'),
            ('[data-testid*="episode"]', 'Elements with episode test ID'),
            ('li[class*="item"]', 'List items'),
            ('div[class*="card"]', 'Card elements'),
            ('a[href*="episode"]', 'Links to episodes'),
        ]

        for selector, description in selectors_to_test:
            elements = await page.query_selector_all(selector)
            if elements and len(elements) > 2:
                print(f"   ✓ Found {len(elements)} {description}")

                # Get sample HTML from first element
                first_html = await elements[0].evaluate('el => el.outerHTML')
                print(f"     Sample HTML (first 300 chars):")
                print(f"     {first_html[:300]}...")

                # Try to extract text content
                first_text = await elements[0].inner_text()
                print(f"     Sample text content:")
                print(f"     {first_text[:200]}...")
                print()
            elif elements:
                print(f"   - Found {len(elements)} {description} (too few)")

        # ==========================================
        # ANALYSIS 3: Check API requests
        # ==========================================
        print("\n5. Analyzing API requests...")

        if api_requests:
            print(f"   ✓ Captured {len(api_requests)} API requests related to episodes/podcasts")

            for i, req in enumerate(api_requests):
                print(f"\n   Request #{i+1}:")
                print(f"   URL: {req['url']}")
                print(f"   Method: {req['method']}")

                if req.get('has_data'):
                    print(f"   ✓ Contains JSON response data")

                    # Save response data
                    with open(f'api_response_{i}.json', 'w', encoding='utf-8') as f:
                        json.dump(req['response'], f, indent=2)
                    print(f"   Saved to: api_response_{i}.json")

                    # Show sample
                    print(f"   Sample data: {str(req['response'])[:300]}...")
        else:
            print("   ✗ No API requests captured")

        # ==========================================
        # ANALYSIS 4: Look for load more button
        # ==========================================
        print("\n6. Looking for 'Load More' button...")

        load_more_selectors = [
            'button:has-text("Load More")',
            'button:has-text("Show More")',
            'button:has-text("See More")',
            '[class*="load"]',
            '[class*="more"]',
        ]

        found_button = False
        for selector in load_more_selectors:
            button = await page.query_selector(selector)
            if button:
                text = await button.inner_text()
                html = await button.evaluate('el => el.outerHTML')
                print(f"   ✓ Found button: '{text.strip()}'")
                print(f"     HTML: {html[:200]}...")
                found_button = True
                break

        if not found_button:
            print("   ✗ No 'Load More' button found")

        # ==========================================
        # FINAL SUMMARY
        # ==========================================
        print("\n" + "="*70)
        print("ANALYSIS COMPLETE")
        print("="*70)

        print("\nFiles created:")
        print("  - audacy_page_analysis.html (full page HTML)")
        print("  - audacy_page_analysis.png (screenshot)")
        if found_json_data:
            print(f"  - json_data_script_*.json ({len(found_json_data)} files)")
        if api_requests:
            print(f"  - api_response_*.json ({len([r for r in api_requests if r.get('has_data')])} files)")

        print("\n" + "="*70)
        print("RECOMMENDATIONS:")
        print("="*70)

        if api_requests:
            print("\n✓ BEST OPTION: Use the API directly")
            print("  API URLs found - this is the fastest and most reliable method")
            print("  Check the api_response_*.json files for the data structure")

        elif found_json_data:
            print("\n✓ GOOD OPTION: Extract from embedded JSON")
            print("  JSON data found in script tags")
            print("  Check the json_data_script_*.json files")

        else:
            print("\n⚠ Need to analyze further")
            print("  Open audacy_page_analysis.html in a browser")
            print("  Check if episodes are visible")
            print("  We may need to adjust the scraping strategy")

        print("\n" + "="*70)
        print("Press Enter to close browser and exit...")
        print("="*70)

        await asyncio.sleep(30)  # Keep browser open for 30 seconds

        await browser.close()

if __name__ == '__main__':
    print("\nThis script will:")
    print("  1. Open a browser window (so you can see what's happening)")
    print("  2. Load the Audacy podcast page")
    print("  3. Analyze the page structure")
    print("  4. Save diagnostic files")
    print("  5. Provide recommendations\n")

    input("Press Enter to start...")

    asyncio.run(analyze_audacy_page())
