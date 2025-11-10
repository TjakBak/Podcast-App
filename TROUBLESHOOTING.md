# Troubleshooting Guide

## Issue: Scraper finds 0 episodes

If the scraper runs but finds no episodes, it means the Audacy website structure doesn't match our expected patterns. Here's how to fix it:

### Step 1: Run the Debug Script

I've created a debug script that will help us understand the page structure:

```powershell
python debug_page.py
```

This will:
- Open a visible browser window (you can watch it load)
- Save the page HTML to `page_debug.html`
- Take a screenshot (`page_debug.png`)
- Print information about what elements it finds
- Stay open for 30 seconds so you can inspect manually

### Step 2: Check the Saved Files

After running the scraper (or debug script), check these files:

1. **page_snapshot.html** - The HTML content the scraper saw
2. **page_debug.html** - Detailed page structure (from debug script)
3. **page_debug.png** - Screenshot of the page

Open `page_snapshot.html` in a web browser. Do you see the episode list?
- **If YES**: The page loaded correctly, we just need to adjust selectors
- **If NO**: The page didn't fully load or requires interaction

### Step 3: Inspect the Page Manually

Open the Audacy page in your browser with Developer Tools:

1. Go to: https://www.audacy.com/podcast/kleinally-show-the-podcast-599ed/episodes
2. Press F12 to open Developer Tools
3. Go to the "Network" tab
4. Reload the page
5. Look for XHR/Fetch requests that contain episode data
   - Filter by "XHR" or "Fetch"
   - Look for URLs containing "episode", "podcast", or "content"
   - Click on them and check the "Preview" or "Response" tab

### Step 4: Share Information for Custom Fix

If you can't get it working, share this information:

1. The output from running `python debug_page.py`
2. The `page_debug.html` file (or relevant snippets)
3. Any API URLs you found in the Network tab

With this information, I can create a custom scraper specifically for the Audacy site structure.

## Alternative: Manual Extraction from API

If you found API URLs in the Network tab:

### Option A: Direct API Access

If you see an API endpoint like:
```
https://api.audacy.com/v1/podcast/599ed/episodes?page=1
```

You can modify the scraper to call this directly. Create a new file `api_scraper.py`:

```python
import requests
import json
from database import PodcastDatabase

# Replace with the actual API URL you found
API_URL = "https://api.audacy.com/v1/podcast/599ed/episodes"

db = PodcastDatabase()

page = 1
total_episodes = 0

while True:
    print(f"Fetching page {page}...")
    response = requests.get(f"{API_URL}?page={page}")

    if response.status_code != 200:
        print(f"Failed to fetch page {page}")
        break

    data = response.json()

    # Adjust this based on the actual API response structure
    episodes = data.get('episodes', data.get('items', []))

    if not episodes:
        print("No more episodes")
        break

    for ep in episodes:
        episode = {
            'episode_id': str(ep.get('id')),
            'title': ep.get('title'),
            'description': ep.get('description'),
            'publish_date': ep.get('publishDate'),
            'audio_url': ep.get('audioUrl'),
            'duration': str(ep.get('duration', '')),
            'image_url': ep.get('image'),
            'metadata': ep
        }
        db.add_episode(episode)
        total_episodes += 1

    print(f"Saved {len(episodes)} episodes (total: {total_episodes})")
    page += 1

print(f"\nDone! Total episodes saved: {total_episodes}")
```

Run it:
```powershell
python api_scraper.py
```

### Option B: RSS Feed

Many podcasts have RSS feeds. Try:

1. View page source (Ctrl+U) on the Audacy page
2. Search for "rss" or "feed"
3. Look for URLs ending in `.xml` or `/feed`

If you find an RSS feed URL, you can use a simple RSS parser:

```python
import feedparser
from database import PodcastDatabase

# Replace with actual RSS URL
RSS_URL = "https://www.audacy.com/podcast/kleinally-show-the-podcast-599ed/feed"

print("Fetching RSS feed...")
feed = feedparser.parse(RSS_URL)

db = PodcastDatabase()

for entry in feed.entries:
    episode = {
        'episode_id': entry.get('id', entry.get('guid', '')),
        'title': entry.get('title', ''),
        'description': entry.get('summary', ''),
        'publish_date': entry.get('published', ''),
        'audio_url': entry.enclosures[0].href if entry.get('enclosures') else '',
        'duration': entry.get('itunes_duration', ''),
        'image_url': entry.get('image', {}).get('href', ''),
        'metadata': dict(entry)
    }
    db.add_episode(episode)

print(f"Saved {len(feed.entries)} episodes")
```

You'll need to install feedparser:
```powershell
pip install feedparser
```

## Common Issues

### "Cannot find element"
The page structure changed. Run `debug_page.py` to inspect.

### "Page loads but no content"
The site might use lazy loading. Try increasing wait time in scraper.py (change `await asyncio.sleep(5)` to `await asyncio.sleep(10)`).

### "Access denied" or "403 error"
The site might be blocking automated access. Try:
1. Running with `headless=False` to use a real browser
2. Adding a user agent string
3. Using the API directly instead of scraping

### JSON extraction fails
The data might be loaded via API after page load. Check Network tab in browser DevTools.

## Need More Help?

Create an issue with:
1. Output from `python debug_page.py`
2. The `page_snapshot.html` file
3. Screenshot of the actual Audacy page showing episodes
4. Any error messages

I'll create a custom solution for your specific case!
