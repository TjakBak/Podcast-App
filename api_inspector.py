"""
Script to inspect network requests and find API endpoints used by Audacy
"""
import asyncio
import json
from playwright.async_api import async_playwright

async def inspect_api():
    """Capture network requests to find the API endpoint"""
    api_calls = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Capture all network requests
        async def handle_request(request):
            if 'api' in request.url.lower() or 'episode' in request.url.lower():
                api_calls.append({
                    'url': request.url,
                    'method': request.method,
                    'headers': request.headers,
                    'post_data': request.post_data
                })
                print(f"[API REQUEST] {request.method} {request.url}")

        async def handle_response(response):
            if 'api' in response.url.lower() or 'episode' in response.url.lower():
                try:
                    # Try to get JSON response
                    if 'json' in response.headers.get('content-type', ''):
                        data = await response.json()
                        print(f"[API RESPONSE] {response.url}")
                        print(f"Sample data: {json.dumps(data, indent=2)[:500]}...")
                except:
                    pass

        page.on('request', handle_request)
        page.on('response', handle_response)

        print("Loading page...")
        await page.goto('https://www.audacy.com/podcast/kleinally-show-the-podcast-599ed/episodes',
                       wait_until='networkidle', timeout=30000)

        # Wait a bit more for any delayed requests
        await asyncio.sleep(3)

        # Try to click "load more" if it exists
        try:
            load_more_button = await page.query_selector('button:has-text("Load More"), button:has-text("Show More")')
            if load_more_button:
                print("\nClicking 'Load More' button...")
                await load_more_button.click()
                await asyncio.sleep(2)
        except:
            print("No 'Load More' button found or error clicking it")

        await browser.close()

    print(f"\n\n=== SUMMARY ===")
    print(f"Found {len(api_calls)} API calls")
    for call in api_calls:
        print(f"\n{call['method']} {call['url']}")

    return api_calls

if __name__ == '__main__':
    asyncio.run(inspect_api())
