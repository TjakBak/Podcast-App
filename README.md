# Podcast Search & Scraper

A powerful tool to scrape and search through all episodes of "The KleinAlly Show" podcast from Audacy - **no more endless clicking "Load More"!**

## Features

- **Automatic scraping**: Automatically clicks "load more" until all episodes are loaded - no manual work!
- **Full episode database**: Downloads all episode metadata including audio links
- **Powerful search**: Full-text search by title, date, description, or any keyword
- **Sort by date**: Instantly find the oldest or newest episodes
- **Beautiful web interface**: Modern, responsive web UI for easy browsing
- **CLI interface**: Command-line tools for power users and automation
- **Fast & efficient**: Search thousands of episodes in milliseconds

## Quick Start

### 1. Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browser (required for scraping)
playwright install chromium
```

### 2. Scrape Episodes

Run the scraper to download all episodes (this only needs to be done once, or when you want to update with new episodes):

```bash
python scraper.py
```

This will:
- Open a headless browser
- Navigate to the Audacy podcast page
- Automatically click "Load More" until all episodes are loaded
- Extract all episode data
- Save everything to a local SQLite database

**Note**: The first scrape may take 5-15 minutes depending on the number of episodes. Be patient!

### 3. Search Episodes

#### Option A: Web Interface (Recommended)

```bash
python app.py
```

Then open your browser to **http://localhost:5000**

Features:
- Live search as you type
- Sort by oldest/newest
- View episode details
- Play audio directly in browser
- Beautiful, responsive design

#### Option B: Command Line Interface

```bash
# Search for episodes
python search.py "guest name"

# Show oldest episodes
python search.py --oldest --limit 10

# Show newest episodes
python search.py --newest --limit 10

# Filter by title
python search.py --filter --title "trump"

# Show database statistics
python search.py --stats
```

## Usage Examples

### Find the Oldest Episode

**Web UI**: Open http://localhost:5000, select "Oldest First", and press Enter

**CLI**:
```bash
python search.py --oldest --limit 1
```

### Search for Specific Topics

```bash
# Search for episodes about politics
python search.py "politics"

# Search for episodes with a specific guest
python search.py "donald trump"

# Search for episodes from a specific date range
python search.py --filter --from-date "2020-01-01" --to-date "2020-12-31"
```

### Browse All Episodes

**Web UI**: Just open http://localhost:5000 and press Enter (or leave search blank)

**CLI**:
```bash
python search.py
```

## How It Works

### Architecture

1. **Scraper** (`scraper.py`): Uses Playwright to automate a real browser
   - Visits the Audacy podcast page
   - Automatically clicks "Load More" hundreds of times if needed
   - Extracts episode metadata (title, date, description, audio URL)
   - Saves to SQLite database

2. **Database** (`database.py`): SQLite with full-text search
   - Stores all episode metadata
   - Uses FTS5 (Full-Text Search) for fast searching
   - Supports filtering, sorting, and complex queries

3. **Search** (`search.py`): CLI interface
   - Search episodes from command line
   - Filter by date, title, or content
   - Show statistics

4. **Web App** (`app.py`): Flask web server
   - Modern web interface
   - Live search with instant results
   - Audio player integration
   - Responsive design

### Why This Approach?

The Audacy website requires JavaScript and loads episodes dynamically. The "Load More" button must be clicked many times to access older episodes. This tool:
- Automates all the clicking for you
- Captures ALL episodes in one run
- Stores them locally for instant searching
- Never needs to scrape again (unless you want new episodes)

## Troubleshooting

### "No episodes in database"
Run `python scraper.py` first to scrape episodes.

### Network errors during scraping
The scraper needs internet access. If you're behind a proxy or firewall, you may need to configure Playwright to use it.

### Scraper not finding episodes
The Audacy website structure may have changed. The scraper tries multiple selectors, but if it fails:
1. Open an issue on GitHub
2. Check the website manually to see if the structure changed
3. Try running the scraper with `--debug` flag (if implemented)

### Web interface not loading
Make sure Flask is installed: `pip install flask`

## Advanced Usage

### Update with New Episodes

Just run the scraper again:
```bash
python scraper.py
```

It will add new episodes without duplicating existing ones.

### Export Episode Data

The database is SQLite format (`podcast_episodes.db`). You can:
- Open it with any SQLite browser
- Export to CSV/JSON using Python scripts
- Query directly using SQL

### Customize the Web Interface

Edit the files in:
- `templates/` - HTML templates
- `static/css/` - Stylesheets
- `static/js/` - JavaScript

## File Structure

```
Podcast-App/
├── scraper.py          # Main scraper script
├── database.py         # Database operations
├── search.py           # CLI search interface
├── app.py              # Flask web server
├── requirements.txt    # Python dependencies
├── templates/          # HTML templates
│   ├── index.html     # Main search page
│   └── episode.html   # Episode detail page
├── static/
│   ├── css/
│   │   └── style.css  # Styles
│   └── js/
│       └── app.js     # JavaScript for search
└── podcast_episodes.db # SQLite database (created after scraping)
```

## Requirements

- Python 3.7+
- Internet connection (for initial scraping)
- Modern web browser (for viewing web interface)

## License

This is a personal project for educational purposes. Respect Audacy's terms of service when using this tool.
