"""
Database module for storing and retrieving podcast episodes
"""
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional

class PodcastDatabase:
    def __init__(self, db_path: str = 'podcast_episodes.db'):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize the database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS episodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                episode_id TEXT UNIQUE,
                title TEXT NOT NULL,
                description TEXT,
                publish_date TEXT,
                audio_url TEXT,
                duration TEXT,
                image_url TEXT,
                metadata TEXT,
                scraped_at TEXT,
                UNIQUE(episode_id)
            )
        ''')

        # Create full-text search index
        cursor.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS episodes_fts USING fts5(
                title, description, content=episodes, content_rowid=id
            )
        ''')

        # Create triggers to keep FTS in sync
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS episodes_ai AFTER INSERT ON episodes BEGIN
                INSERT INTO episodes_fts(rowid, title, description)
                VALUES (new.id, new.title, new.description);
            END
        ''')

        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS episodes_ad AFTER DELETE ON episodes BEGIN
                DELETE FROM episodes_fts WHERE rowid = old.id;
            END
        ''')

        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS episodes_au AFTER UPDATE ON episodes BEGIN
                UPDATE episodes_fts SET title = new.title, description = new.description
                WHERE rowid = new.id;
            END
        ''')

        conn.commit()
        conn.close()

    def add_episode(self, episode: Dict) -> bool:
        """Add a new episode to the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT OR REPLACE INTO episodes
                (episode_id, title, description, publish_date, audio_url, duration, image_url, metadata, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                episode.get('episode_id', ''),
                episode.get('title', ''),
                episode.get('description', ''),
                episode.get('publish_date', ''),
                episode.get('audio_url', ''),
                episode.get('duration', ''),
                episode.get('image_url', ''),
                json.dumps(episode.get('metadata', {})),
                datetime.now().isoformat()
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error adding episode: {e}")
            return False
        finally:
            conn.close()

    def add_episodes_bulk(self, episodes: List[Dict]) -> int:
        """Add multiple episodes at once"""
        count = 0
        for episode in episodes:
            if self.add_episode(episode):
                count += 1
        return count

    def search_episodes(self, query: str, limit: int = 50) -> List[Dict]:
        """Search episodes using full-text search"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT e.* FROM episodes e
            JOIN episodes_fts fts ON e.id = fts.rowid
            WHERE episodes_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        ''', (query, limit))

        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def get_all_episodes(self, order_by: str = 'publish_date DESC', limit: Optional[int] = None) -> List[Dict]:
        """Get all episodes with optional ordering and limit"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = f'SELECT * FROM episodes ORDER BY {order_by}'
        if limit:
            query += f' LIMIT {limit}'

        cursor.execute(query)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def get_oldest_episode(self) -> Optional[Dict]:
        """Get the oldest episode"""
        episodes = self.get_all_episodes(order_by='publish_date ASC', limit=1)
        return episodes[0] if episodes else None

    def get_newest_episode(self) -> Optional[Dict]:
        """Get the newest episode"""
        episodes = self.get_all_episodes(order_by='publish_date DESC', limit=1)
        return episodes[0] if episodes else None

    def get_episode_count(self) -> int:
        """Get total number of episodes in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM episodes')
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def filter_episodes(self,
                       title_contains: Optional[str] = None,
                       date_from: Optional[str] = None,
                       date_to: Optional[str] = None,
                       limit: int = 100) -> List[Dict]:
        """Filter episodes by various criteria"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = 'SELECT * FROM episodes WHERE 1=1'
        params = []

        if title_contains:
            query += ' AND title LIKE ?'
            params.append(f'%{title_contains}%')

        if date_from:
            query += ' AND publish_date >= ?'
            params.append(date_from)

        if date_to:
            query += ' AND publish_date <= ?'
            params.append(date_to)

        query += ' ORDER BY publish_date DESC LIMIT ?'
        params.append(limit)

        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
