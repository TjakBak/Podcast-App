#!/usr/bin/env python3
"""
Flask web interface for podcast search
"""
from flask import Flask, render_template, request, jsonify
from database import PodcastDatabase
from datetime import datetime
import os

app = Flask(__name__)
db = PodcastDatabase()

@app.route('/')
def index():
    """Main page"""
    stats = {
        'total': db.get_episode_count(),
        'oldest': db.get_oldest_episode(),
        'newest': db.get_newest_episode()
    }
    return render_template('index.html', stats=stats)

@app.route('/search')
def search():
    """Search endpoint"""
    query = request.args.get('q', '')
    sort = request.args.get('sort', 'newest')
    limit = int(request.args.get('limit', 50))

    if query:
        # Full-text search
        results = db.search_episodes(query, limit=limit)
    else:
        # Get all episodes
        order = 'publish_date ASC' if sort == 'oldest' else 'publish_date DESC'
        results = db.get_all_episodes(order_by=order, limit=limit)

    # Format dates for display
    for episode in results:
        try:
            dt = datetime.fromisoformat(episode['publish_date'].replace('Z', '+00:00'))
            episode['formatted_date'] = dt.strftime('%B %d, %Y')
            episode['short_date'] = dt.strftime('%Y-%m-%d')
        except:
            episode['formatted_date'] = episode.get('publish_date', 'Unknown')
            episode['short_date'] = episode.get('publish_date', 'Unknown')

    return jsonify({
        'results': results,
        'count': len(results)
    })

@app.route('/episode/<int:episode_id>')
def episode_detail(episode_id):
    """Episode detail page"""
    episodes = db.get_all_episodes()
    episode = next((ep for ep in episodes if ep['id'] == episode_id), None)

    if not episode:
        return "Episode not found", 404

    try:
        dt = datetime.fromisoformat(episode['publish_date'].replace('Z', '+00:00'))
        episode['formatted_date'] = dt.strftime('%B %d, %Y at %I:%M %p')
    except:
        episode['formatted_date'] = episode.get('publish_date', 'Unknown')

    return render_template('episode.html', episode=episode)

@app.route('/stats')
def stats():
    """Statistics page"""
    total = db.get_episode_count()
    oldest = db.get_oldest_episode()
    newest = db.get_newest_episode()

    return jsonify({
        'total': total,
        'oldest': oldest,
        'newest': newest
    })

if __name__ == '__main__':
    # Check if database has episodes
    if db.get_episode_count() == 0:
        print("\n" + "="*60)
        print("WARNING: No episodes in database!")
        print("Please run 'python scraper.py' first to scrape episodes.")
        print("="*60 + "\n")

    print("\n" + "="*60)
    print("Podcast Search Web Interface")
    print("="*60)
    print(f"Total episodes in database: {db.get_episode_count()}")
    print("\nStarting server at http://localhost:5000")
    print("Press Ctrl+C to stop")
    print("="*60 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5000)
