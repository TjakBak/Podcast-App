# Windows Installation Guide

## Quick Fix for Installation Issues

If you're getting build errors with `lxml` or `greenlet`, follow these steps:

### Step 1: Update requirements.txt

The requirements.txt has been updated to remove problematic dependencies. Make sure you're using the latest version.

### Step 2: Clean Install

```powershell
# Remove any partially installed packages
pip uninstall -y playwright requests flask beautifulsoup4 lxml python-dateutil greenlet

# Install with updated requirements
pip install -r requirements.txt

# Install Playwright browsers
python -m playwright install chromium
```

### Step 3: If Still Having Issues

Try installing packages one at a time:

```powershell
# Install core packages first
pip install requests beautifulsoup4 python-dateutil flask

# Install playwright (this should work on Windows with Python 3.7+)
pip install playwright

# Install the browser
python -m playwright install chromium
```

### Step 4: Verify Installation

```powershell
# Check if playwright is installed
python -c "import playwright; print('Playwright installed successfully!')"

# Check all dependencies
python -c "import requests, flask, bs4, playwright; print('All dependencies installed!')"
```

## Common Windows Issues

### Issue: "playwright is not recognized"

**Solution**: Use `python -m playwright` instead of just `playwright`:

```powershell
# Instead of:
playwright install chromium

# Use:
python -m playwright install chromium
```

### Issue: "Failed building wheel for lxml"

**Solution**: lxml is no longer required! The updated requirements.txt removes it. BeautifulSoup4 will use Python's built-in HTML parser instead.

### Issue: "Failed building wheel for greenlet"

**Solution**: Update to the latest playwright version which includes pre-built Windows wheels:

```powershell
pip install --upgrade playwright
```

### Issue: Python 3.13 Compatibility

If you're using Python 3.13 (very new), some packages might not have wheels yet. Options:

1. **Recommended**: Use Python 3.11 or 3.12 (most compatible)
2. Wait a few weeks for package maintainers to release 3.13 wheels
3. Install Microsoft C++ Build Tools (advanced)

## Running the Scraper

Once installed, use these commands:

```powershell
# Scrape episodes (takes 5-15 minutes)
python scraper.py

# Start web interface
python app.py

# CLI search
python search.py --help
python search.py "search term"
python search.py --oldest --limit 10
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'playwright'"

Run: `pip install playwright`

### "No browser installed"

Run: `python -m playwright install chromium`

### Web interface won't start

Make sure Flask is installed: `pip install flask`

### Database errors

Delete `podcast_episodes.db` if it exists and run the scraper again.

## Need Help?

If you're still having issues, you can:

1. Check your Python version: `python --version` (need 3.7+, recommend 3.11 or 3.12)
2. Update pip: `python -m pip install --upgrade pip`
3. Create a Python virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
