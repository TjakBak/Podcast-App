"""
Podcast scraper with hybrid API + browser automation approach
"""
import asyncio
import json
import re
from typing import List, Dict, Optional
from datetime import datetime
from playwright.async_api import async_playwright
from database import PodcastDatabase

class PodcastScraper:
    def __init__(self, podcast_url: str, db: PodcastDatabase):
        self.podcast_url = podcast_url
        self.db = db
        self.episodes = []

    async def scrape_with_browser(self, max_episodes: Optional[int] = None) -> List[Dict]:
        """
        Scrape episodes using headless browser automation
        This method clicks 'Load More' until all episodes are loaded
        """
        print("Starting browser-based scraping...")
        episodes = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # Listen for API responses that might contain episode data
            api_data = []

            async def capture_response(response):
                """Capture any API responses with episode data"""
                try:
                    if response.status == 200 and ('json' in response.headers.get('content-type', '')):
                        url = response.url
                        if 'episode' in url.lower() or 'podcast' in url.lower():
                            data = await response.json()
                            api_data.append({'url': url, 'data': data})
                            print(f"Captured API response from: {url}")
                except Exception as e:
                    pass

            page.on('response', capture_response)

            print(f"Loading page: {self.podcast_url}")
            try:
                await page.goto(self.podcast_url, wait_until='networkidle', timeout=60000)
            except Exception as e:
                print(f"Error loading page: {e}")
                await browser.close()
                return []

            # Wait for content to load
            print("Waiting for page content to load...")
            await asyncio.sleep(5)

            # Debug: Check if page loaded properly
            content = await page.content()
            if len(content) < 10000:
                print("⚠ Warning: Page content seems very small, might not have loaded properly")

            # Save page for debugging if needed
            with open('page_snapshot.html', 'w', encoding='utf-8') as f:
                f.write(content)
            print("Saved page snapshot to: page_snapshot.html")

            # Click "Load More" button repeatedly until all episodes are loaded
            load_more_count = 0
            max_clicks = 1000 if max_episodes is None else (max_episodes // 20) + 5

            while load_more_count < max_clicks:
                try:
                    # Try multiple selectors for the load more button
                    load_more_selectors = [
                        'button:has-text("Load More")',
                        'button:has-text("Show More")',
                        'button:has-text("See More")',
                        'a:has-text("Load More")',
                        '[class*="load"][class*="more"]',
                        '[class*="show"][class*="more"]'
                    ]

                    button_found = False
                    for selector in load_more_selectors:
                        load_more_button = await page.query_selector(selector)
                        if load_more_button:
                            # Check if button is visible and enabled
                            is_visible = await load_more_button.is_visible()
                            is_enabled = await load_more_button.is_enabled()

                            if is_visible and is_enabled:
                                print(f"Clicking 'Load More' button (click #{load_more_count + 1})...")
                                await load_more_button.click()
                                await asyncio.sleep(2)  # Wait for new content to load
                                load_more_count += 1
                                button_found = True
                                break

                    if not button_found:
                        print("No more 'Load More' button found")
                        break

                except Exception as e:
                    print(f"No more episodes to load or error: {e}")
                    break

            print(f"Clicked 'Load More' {load_more_count} times")

            # Extract episodes from the page
            print("Extracting episode data from page...")
            episodes = await self._extract_episodes_from_page(page)

            # Also try to extract from captured API responses
            if api_data:
                print(f"Processing {len(api_data)} API responses...")
                for item in api_data:
                    api_episodes = self._extract_episodes_from_api(item['data'])
                    episodes.extend(api_episodes)

            await browser.close()

        # Deduplicate episodes by title + date
        seen = set()
        unique_episodes = []
        for ep in episodes:
            key = (ep.get('title', ''), ep.get('publish_date', ''))
            if key not in seen:
                seen.add(key)
                unique_episodes.append(ep)

        print(f"Found {len(unique_episodes)} unique episodes")
        return unique_episodes

    async def _extract_episodes_from_page(self, page) -> List[Dict]:
        """Extract episode information from the page DOM"""
        episodes = []

        try:
            # First, try to find JSON data embedded in the page (many React apps do this)
            print("\nSearching for embedded JSON data...")
            json_episodes = await self._extract_from_json_scripts(page)
            if json_episodes:
                print(f"✓ Found {len(json_episodes)} episodes from JSON data")
                return json_episodes

            # Try to extract episodes using common selectors
            # Most podcast sites use article tags or divs with specific classes
            print("\nSearching for episodes in page DOM...")
            episode_selectors = [
                'article',
                '[class*="episode" i]',
                '[class*="Episode" i]',
                '[class*="podcast-item" i]',
                '[data-episode]',
                '[data-testid*="episode"]',
                '[class*="list-item" i]',
                '[class*="card" i]',
                'li[class*="item"]',
                'div[class*="item"]',
                'a[href*="episode"]'
            ]

            for selector in episode_selectors:
                elements = await page.query_selector_all(selector)
                if elements and len(elements) > 2:  # Need at least 3 elements to consider it valid
                    print(f"✓ Found {len(elements)} elements with selector: {selector}")

                    for elem in elements:
                        episode = await self._extract_episode_data(elem)
                        if episode and episode.get('title') and len(episode.get('title', '')) > 5:
                            episodes.append(episode)

                    if episodes:  # If we found episodes, don't try other selectors
                        print(f"✓ Successfully extracted {len(episodes)} episodes")
                        break
                elif elements:
                    print(f"  Found {len(elements)} elements with '{selector}' (too few, trying next)")

            if not episodes:
                print("\n⚠ No episodes found with standard selectors")
                print("Run 'python debug_page.py' to inspect the page structure")

        except Exception as e:
            print(f"Error extracting episodes: {e}")
            import traceback
            traceback.print_exc()

        return episodes

    async def _extract_from_json_scripts(self, page) -> List[Dict]:
        """Extract episode data from JSON embedded in script tags"""
        episodes = []

        try:
            # Find all script tags that might contain JSON data
            scripts = await page.query_selector_all('script[type="application/json"], script[type="application/ld+json"], script:not([src])')

            for script in scripts:
                try:
                    content = await script.inner_text()
                    if not content or len(content) < 100:
                        continue

                    # Check if it looks like JSON
                    content = content.strip()
                    if not (content.startswith('{') or content.startswith('[')):
                        continue

                    # Try to parse as JSON
                    data = json.loads(content)

                    # Look for episode data in the JSON
                    if 'episode' in content.lower() or 'podcast' in content.lower():
                        extracted = self._extract_episodes_from_api(data)
                        if extracted:
                            episodes.extend(extracted)

                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    continue

        except Exception as e:
            print(f"Error extracting from JSON scripts: {e}")

        return episodes

    async def _extract_episode_data(self, element) -> Optional[Dict]:
        """Extract data from a single episode element"""
        try:
            # Extract title
            title_elem = await element.query_selector('h1, h2, h3, h4, [class*="title"], a')
            title = await title_elem.inner_text() if title_elem else ''

            # Extract description
            desc_elem = await element.query_selector('p, [class*="description"], [class*="summary"]')
            description = await desc_elem.inner_text() if desc_elem else ''

            # Extract date
            date_elem = await element.query_selector('time, [class*="date"], [datetime]')
            date = ''
            if date_elem:
                date = await date_elem.get_attribute('datetime') or await date_elem.inner_text()

            # Extract audio URL
            audio_elem = await element.query_selector('audio source, [href*=".mp3"], [src*=".mp3"]')
            audio_url = ''
            if audio_elem:
                audio_url = await audio_elem.get_attribute('src') or await audio_elem.get_attribute('href') or ''

            # Extract image URL
            img_elem = await element.query_selector('img')
            image_url = ''
            if img_elem:
                image_url = await img_elem.get_attribute('src') or ''

            # Generate episode ID
            episode_id = f"{title}_{date}".replace(' ', '_').replace('/', '_')[:100]

            return {
                'episode_id': episode_id,
                'title': title.strip(),
                'description': description.strip(),
                'publish_date': self._normalize_date(date),
                'audio_url': audio_url,
                'duration': '',
                'image_url': image_url,
                'metadata': {}
            }
        except Exception as e:
            return None

    def _extract_episodes_from_api(self, data: Dict) -> List[Dict]:
        """Extract episodes from API JSON response"""
        episodes = []

        try:
            # Try common JSON structures
            items = None

            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                # Try common keys (case-insensitive search)
                for key in data.keys():
                    key_lower = key.lower()
                    if key_lower in ['episodes', 'items', 'data', 'results', 'content', 'list', 'shows']:
                        items = data[key]
                        if isinstance(items, list):
                            print(f"  Found episode list under key: '{key}'")
                            break

                # Also check nested structures
                if not items:
                    for key in ['props', 'pageProps', 'initialState', 'state', '__NEXT_DATA__']:
                        if key in data and isinstance(data[key], dict):
                            nested_episodes = self._extract_episodes_from_api(data[key])
                            if nested_episodes:
                                return nested_episodes

            if items and isinstance(items, list):
                for item in items:
                    if isinstance(item, dict):
                        # Try to extract episode data with various key names
                        episode = {
                            'episode_id': str(item.get('id', item.get('guid', item.get('episodeId', '')))),
                            'title': item.get('title', item.get('name', item.get('episodeName', ''))),
                            'description': item.get('description', item.get('summary', item.get('desc', ''))),
                            'publish_date': self._normalize_date(
                                item.get('publishDate', item.get('published', item.get('date',
                                item.get('releaseDate', item.get('airDate', '')))))
                            ),
                            'audio_url': item.get('audioUrl', item.get('url', item.get('mediaUrl',
                                item.get('audio', item.get('enclosure', {}).get('url', ''))))),
                            'duration': str(item.get('duration', item.get('length', ''))),
                            'image_url': item.get('image', item.get('thumbnail', item.get('imageUrl',
                                item.get('artwork', '')))),
                            'metadata': item
                        }
                        if episode['title'] and len(episode['title']) > 3:
                            episodes.append(episode)

        except Exception as e:
            print(f"Error extracting from API data: {e}")

        return episodes

    def _normalize_date(self, date_str: str) -> str:
        """Normalize various date formats to ISO format"""
        if not date_str:
            return ''

        try:
            # Try parsing common date formats
            from dateutil import parser
            dt = parser.parse(date_str)
            return dt.isoformat()
        except:
            return date_str

    async def scrape_and_save(self, max_episodes: Optional[int] = None):
        """Scrape episodes and save to database"""
        print("\n=== Starting Podcast Scraper ===\n")

        # Try browser scraping
        episodes = await self.scrape_with_browser(max_episodes)

        if episodes:
            print(f"\nSaving {len(episodes)} episodes to database...")
            saved = self.db.add_episodes_bulk(episodes)
            print(f"Successfully saved {saved} episodes")
            print(f"\nTotal episodes in database: {self.db.get_episode_count()}")

            # Show oldest and newest
            oldest = self.db.get_oldest_episode()
            newest = self.db.get_newest_episode()

            if oldest:
                print(f"\nOldest episode: {oldest['title']} ({oldest['publish_date']})")
            if newest:
                print(f"Newest episode: {newest['title']} ({newest['publish_date']})")
        else:
            print("No episodes found. The website structure might have changed.")
            print("Please check the URL and try again.")

async def main():
    """Main entry point"""
    podcast_url = "https://www.audacy.com/podcast/kleinally-show-the-podcast-599ed/episodes"

    db = PodcastDatabase()
    scraper = PodcastScraper(podcast_url, db)

    await scraper.scrape_and_save()

if __name__ == '__main__':
    asyncio.run(main())
