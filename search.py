#!/usr/bin/env python3
"""
CLI search interface for podcast episodes
"""
import sys
import argparse
from database import PodcastDatabase
from datetime import datetime

def format_episode(episode, index=None):
    """Format episode for display"""
    prefix = f"{index}. " if index is not None else ""
    title = episode.get('title', 'Untitled')
    date = episode.get('publish_date', 'Unknown date')
    description = episode.get('description', '')
    audio_url = episode.get('audio_url', 'No audio URL')

    # Parse date for better display
    try:
        dt = datetime.fromisoformat(date.replace('Z', '+00:00'))
        date_str = dt.strftime('%Y-%m-%d')
    except:
        date_str = date

    # Truncate description
    desc_preview = description[:150] + '...' if len(description) > 150 else description

    output = f"\n{prefix}{title}\n"
    output += f"  Date: {date_str}\n"
    if desc_preview:
        output += f"  Description: {desc_preview}\n"
    if audio_url and audio_url != 'No audio URL':
        output += f"  Audio: {audio_url}\n"

    return output

def search_command(args):
    """Handle search command"""
    db = PodcastDatabase()

    if args.query:
        # Full-text search
        print(f"\nSearching for: '{args.query}'\n")
        results = db.search_episodes(args.query, limit=args.limit)
    else:
        # Get all episodes
        order = 'publish_date ASC' if args.oldest else 'publish_date DESC'
        results = db.get_all_episodes(order_by=order, limit=args.limit)

    if not results:
        print("No episodes found.")
        return

    print(f"Found {len(results)} episode(s):\n")
    print("=" * 80)

    for i, episode in enumerate(results, 1):
        print(format_episode(episode, i))
        print("-" * 80)

def stats_command(args):
    """Show database statistics"""
    db = PodcastDatabase()

    total = db.get_episode_count()
    oldest = db.get_oldest_episode()
    newest = db.get_newest_episode()

    print("\n=== Podcast Database Statistics ===\n")
    print(f"Total episodes: {total}")

    if oldest:
        try:
            dt = datetime.fromisoformat(oldest['publish_date'].replace('Z', '+00:00'))
            date_str = dt.strftime('%Y-%m-%d')
        except:
            date_str = oldest['publish_date']
        print(f"\nOldest episode:")
        print(f"  {oldest['title']}")
        print(f"  Date: {date_str}")
        if oldest.get('audio_url'):
            print(f"  URL: {oldest['audio_url']}")

    if newest:
        try:
            dt = datetime.fromisoformat(newest['publish_date'].replace('Z', '+00:00'))
            date_str = dt.strftime('%Y-%m-%d')
        except:
            date_str = newest['publish_date']
        print(f"\nNewest episode:")
        print(f"  {newest['title']}")
        print(f"  Date: {date_str}")
        if newest.get('audio_url'):
            print(f"  URL: {newest['audio_url']}")

    print()

def filter_command(args):
    """Filter episodes by criteria"""
    db = PodcastDatabase()

    results = db.filter_episodes(
        title_contains=args.title,
        date_from=args.from_date,
        date_to=args.to_date,
        limit=args.limit
    )

    if not results:
        print("No episodes found matching criteria.")
        return

    print(f"\nFound {len(results)} episode(s):\n")
    print("=" * 80)

    for i, episode in enumerate(results, 1):
        print(format_episode(episode, i))
        print("-" * 80)

def main():
    parser = argparse.ArgumentParser(
        description='Search and browse podcast episodes',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "guest name"              # Search for episodes with a guest
  %(prog)s --oldest --limit 10       # Show 10 oldest episodes
  %(prog)s --stats                   # Show database statistics
  %(prog)s --filter --title "trump"  # Filter by title
        """
    )

    parser.add_argument('query', nargs='?', help='Search query (searches title and description)')
    parser.add_argument('--oldest', action='store_true', help='Show oldest episodes first')
    parser.add_argument('--newest', action='store_true', help='Show newest episodes first (default)')
    parser.add_argument('--limit', type=int, default=50, help='Maximum number of results (default: 50)')
    parser.add_argument('--stats', action='store_true', help='Show database statistics')

    # Filter options
    parser.add_argument('--filter', action='store_true', help='Use filter mode instead of search')
    parser.add_argument('--title', help='Filter by title (partial match)')
    parser.add_argument('--from-date', dest='from_date', help='Filter from date (YYYY-MM-DD)')
    parser.add_argument('--to-date', dest='to_date', help='Filter to date (YYYY-MM-DD)')

    args = parser.parse_args()

    # Check if database exists
    db = PodcastDatabase()
    if db.get_episode_count() == 0:
        print("No episodes in database. Please run 'python scraper.py' first to scrape episodes.")
        sys.exit(1)

    if args.stats:
        stats_command(args)
    elif args.filter:
        filter_command(args)
    else:
        search_command(args)

if __name__ == '__main__':
    main()
