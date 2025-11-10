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
            await asyncio.sleep(3)

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
            # Try to extract episodes using common selectors
            # Most podcast sites use article tags or divs with specific classes
            episode_selectors = [
                'article',
                '[class*="episode"]',
                '[class*="podcast-item"]',
                '[data-episode]',
                '[class*="list-item"]'
            ]

            for selector in episode_selectors:
                elements = await page.query_selector_all(selector)
                if elements:
                    print(f"Found {len(elements)} elements with selector: {selector}")

                    for elem in elements:
                        episode = await self._extract_episode_data(elem)
                        if episode and episode.get('title'):
                            episodes.append(episode)

                    if episodes:  # If we found episodes, don't try other selectors
                        break

        except Exception as e:
            print(f"Error extracting episodes: {e}")

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
                # Try common keys
                for key in ['episodes', 'items', 'data', 'results', 'content']:
                    if key in data:
                        items = data[key]
                        if isinstance(items, list):
                            break

            if items and isinstance(items, list):
                for item in items:
                    if isinstance(item, dict):
                        episode = {
                            'episode_id': item.get('id', item.get('guid', '')),
                            'title': item.get('title', item.get('name', '')),
                            'description': item.get('description', item.get('summary', '')),
                            'publish_date': self._normalize_date(
                                item.get('publishDate', item.get('published', item.get('date', '')))
                            ),
                            'audio_url': item.get('audioUrl', item.get('url', item.get('enclosure', {}).get('url', ''))),
                            'duration': str(item.get('duration', '')),
                            'image_url': item.get('image', item.get('thumbnail', '')),
                            'metadata': item
                        }
                        if episode['title']:
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
