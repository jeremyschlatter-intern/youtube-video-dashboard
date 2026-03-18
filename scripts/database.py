"""Database schema and helper functions for the YouTube Dashboard."""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'dashboard.db')


def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=30000")
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.executescript("""
    CREATE TABLE IF NOT EXISTS committees (
        system_code TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        youtube_channel_handle TEXT,
        youtube_channel_url TEXT,
        chamber TEXT DEFAULT 'House',
        is_current INTEGER DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS official_events (
        event_id INTEGER PRIMARY KEY,
        congress INTEGER NOT NULL,
        committee_code TEXT,
        committee_name TEXT,
        date TEXT,
        title TEXT,
        type TEXT,
        status TEXT,
        url TEXT
    );

    CREATE TABLE IF NOT EXISTS youtube_videos (
        video_id TEXT PRIMARY KEY,
        channel_handle TEXT,
        committee_code TEXT,
        title TEXT,
        description TEXT,
        upload_date TEXT,
        duration INTEGER,
        view_count INTEGER,
        has_event_id INTEGER DEFAULT 0,
        extracted_event_id INTEGER,
        url TEXT,
    );

    CREATE TABLE IF NOT EXISTS matches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        video_id TEXT NOT NULL,
        event_id INTEGER NOT NULL,
        confidence REAL NOT NULL,
        match_method TEXT,
        UNIQUE(video_id, event_id)
    );

    CREATE INDEX IF NOT EXISTS idx_events_congress ON official_events(congress);
    CREATE INDEX IF NOT EXISTS idx_events_committee ON official_events(committee_code);
    CREATE INDEX IF NOT EXISTS idx_events_date ON official_events(date);
    CREATE INDEX IF NOT EXISTS idx_videos_channel ON youtube_videos(channel_handle);
    CREATE INDEX IF NOT EXISTS idx_videos_committee ON youtube_videos(committee_code);
    CREATE INDEX IF NOT EXISTS idx_videos_date ON youtube_videos(upload_date);
    CREATE INDEX IF NOT EXISTS idx_matches_video ON matches(video_id);
    CREATE INDEX IF NOT EXISTS idx_matches_event ON matches(event_id);
    """)

    conn.commit()
    conn.close()


def seed_committees():
    """Seed the database with known House committee YouTube channels."""
    committees = [
        ("hsag00", "Agriculture", "AgRepublicans", "https://www.youtube.com/@AgRepublicans"),
        ("hsap00", "Appropriations", "HouseAppropriationsCommittee", "https://www.youtube.com/@HouseAppropriationsCommittee"),
        ("hsas00", "Armed Services", "HouseArmedServices", "https://www.youtube.com/@HouseArmedServices"),
        ("hsba00", "Financial Services", "USHouseFSC", "https://www.youtube.com/@USHouseFSC"),
        ("hsbu00", "Budget", "HouseBudgetGOP", "https://www.youtube.com/@HouseBudgetGOP"),
        ("hsed00", "Education and the Workforce", "EdWorkforceCmte", "https://www.youtube.com/@EdWorkforceCmte"),
        ("hsif00", "Energy and Commerce", "energyandcommerce", "https://www.youtube.com/@energyandcommerce"),
        ("hsfa00", "Foreign Affairs", "HouseForeignGOP", "https://www.youtube.com/@HouseForeignGOP"),
        ("hsha00", "House Administration", "CommitteeonHouseAdministration", "https://www.youtube.com/@CommitteeonHouseAdministration"),
        ("hshm00", "Homeland Security", "HouseHomeland", "https://www.youtube.com/@HouseHomeland"),
        ("hsii00", "Natural Resources", "NaturalResourcesGOP", "https://www.youtube.com/@NaturalResourcesGOP"),
        ("hsju00", "Judiciary", "USHouseJudiciaryGOP", "https://www.youtube.com/@USHouseJudiciaryGOP"),
        ("hsgo00", "Oversight and Accountability", "OversightandGovernmentReform", "https://www.youtube.com/@OversightandGovernmentReform"),
        ("hsru00", "Rules", "HouseRulesCommittee", "https://www.youtube.com/@HouseRulesCommittee"),
        ("hssm00", "Small Business", "HouseSmallBiz", "https://www.youtube.com/@HouseSmallBiz"),
        ("hssy00", "Science, Space, and Technology", "HouseScienceGOP", "https://www.youtube.com/@HouseScienceGOP"),
        ("hspw00", "Transportation and Infrastructure", "Transport", "https://www.youtube.com/@Transport"),
        ("hsvr00", "Veterans' Affairs", "HouseVetsAffairs", "https://www.youtube.com/@HouseVetsAffairs"),
        ("hswm00", "Ways and Means", "WaysandMeansCommittee", "https://www.youtube.com/@WaysandMeansCommittee"),
        ("hsig00", "Intelligence", "HouseIntel", "https://www.youtube.com/@HouseIntel"),
    ]

    conn = get_connection()
    c = conn.cursor()
    for code, name, handle, url in committees:
        c.execute("""
            INSERT OR REPLACE INTO committees (system_code, name, youtube_channel_handle, youtube_channel_url)
            VALUES (?, ?, ?, ?)
        """, (code, name, handle, url))
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    seed_committees()
    print("Database initialized and committees seeded.")
