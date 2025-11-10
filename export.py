#!/usr/bin/env python3
"""
Export podcast episodes to various formats (CSV, JSON)
"""
import json
import csv
import sys
import argparse
from database import PodcastDatabase

def export_to_json(episodes, output_file):
    """Export episodes to JSON format"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(episodes, f, indent=2, ensure_ascii=False)
    print(f"Exported {len(episodes)} episodes to {output_file}")

def export_to_csv(episodes, output_file):
    """Export episodes to CSV format"""
    if not episodes:
        print("No episodes to export")
        return

    # Get all possible fields
    fieldnames = ['id', 'episode_id', 'title', 'description', 'publish_date',
                  'audio_url', 'duration', 'image_url', 'scraped_at']

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for episode in episodes:
            writer.writerow(episode)

    print(f"Exported {len(episodes)} episodes to {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Export podcast episodes to different formats')
    parser.add_argument('--format', choices=['json', 'csv'], default='json',
                       help='Export format (default: json)')
    parser.add_argument('--output', '-o', required=True,
                       help='Output file name')
    parser.add_argument('--query', '-q',
                       help='Search query to filter episodes (optional)')
    parser.add_argument('--oldest', action='store_true',
                       help='Sort by oldest first')
    parser.add_argument('--limit', type=int,
                       help='Maximum number of episodes to export')

    args = parser.parse_args()

    db = PodcastDatabase()

    if db.get_episode_count() == 0:
        print("Error: No episodes in database. Run 'python scraper.py' first.")
        sys.exit(1)

    # Get episodes based on arguments
    if args.query:
        episodes = db.search_episodes(args.query, limit=args.limit or 10000)
    else:
        order = 'publish_date ASC' if args.oldest else 'publish_date DESC'
        episodes = db.get_all_episodes(order_by=order, limit=args.limit)

    if not episodes:
        print("No episodes found matching criteria")
        sys.exit(1)

    # Export based on format
    if args.format == 'json':
        export_to_json(episodes, args.output)
    elif args.format == 'csv':
        export_to_csv(episodes, args.output)

    print(f"\nExport complete! File saved as: {args.output}")

if __name__ == '__main__':
    main()
