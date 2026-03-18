"""Match YouTube videos to official congress.gov events using fuzzy matching."""

import os
import sys
import re
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))
from database import get_connection

try:
    from thefuzz import fuzz
except ImportError:
    from fuzzywuzzy import fuzz


def normalize_title(title):
    """Normalize a title for comparison."""
    if not title:
        return ""
    # Remove common prefixes
    title = re.sub(r'^(Full Committee|Subcommittee on.*?)\s*[-|:]\s*', '', title, flags=re.IGNORECASE)
    title = re.sub(r'^(Hearing|Markup|Meeting)\s*[-|:]\s*', '', title, flags=re.IGNORECASE)
    # Remove "Full" prefix often in YouTube titles
    title = re.sub(r'^Full\s+', '', title, flags=re.IGNORECASE)
    # Remove extra whitespace
    title = re.sub(r'\s+', ' ', title).strip()
    return title.lower()


def parse_date(date_str):
    """Parse a date string into a date object."""
    if not date_str:
        return None
    try:
        # YouTube format: YYYYMMDD
        if len(date_str) == 8 and date_str.isdigit():
            return datetime.strptime(date_str, '%Y%m%d').date()
        # Congress.gov format: 2023-03-24T13:00:00Z
        if 'T' in date_str:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00')).date()
        # Other ISO format
        return datetime.fromisoformat(date_str).date()
    except (ValueError, TypeError):
        return None


def dates_match(date1_str, date2_str, tolerance_days=1):
    """Check if two dates are within tolerance of each other."""
    d1 = parse_date(date1_str)
    d2 = parse_date(date2_str)
    if d1 is None or d2 is None:
        return False, 999
    diff = abs((d1 - d2).days)
    return diff <= tolerance_days, diff


def compute_match_score(video, event):
    """Compute a match confidence score between a video and an event."""
    score = 0.0
    methods = []

    # 1. Direct event ID match (highest confidence)
    if video['extracted_event_id'] and video['extracted_event_id'] == event['event_id']:
        return 1.0, "event_id_match"

    # 2. Date matching (required for fuzzy matching)
    dates_ok, day_diff = dates_match(video['upload_date'], event['date'])
    if not dates_ok:
        return 0.0, "no_date_match"

    # Same day = full date score, 1 day off = partial
    if day_diff == 0:
        score += 0.4
        methods.append("same_day")
    elif day_diff == 1:
        score += 0.2
        methods.append("adjacent_day")

    # 3. Committee match
    if video['committee_code'] and event['committee_code']:
        # Direct committee match
        if video['committee_code'] == event['committee_code']:
            score += 0.2
            methods.append("same_committee")
        # Subcommittee of same parent
        elif video['committee_code'][:4] == event['committee_code'][:4]:
            score += 0.1
            methods.append("same_parent_committee")

    # 4. Title similarity
    v_title = normalize_title(video['title'])
    e_title = normalize_title(event['title'])
    if v_title and e_title:
        ratio = fuzz.token_sort_ratio(v_title, e_title)
        if ratio >= 80:
            score += 0.3
            methods.append(f"title_match_{ratio}")
        elif ratio >= 60:
            score += 0.2
            methods.append(f"title_partial_{ratio}")
        elif ratio >= 40:
            score += 0.1
            methods.append(f"title_weak_{ratio}")

    # 5. Duration check - proceedings are typically 1+ hours
    if video['duration'] and video['duration'] >= 3600:
        score += 0.05
        methods.append("long_duration")

    return min(score, 0.95), "+".join(methods)


def match_all_videos(min_confidence=0.4):
    """Match all YouTube videos to official events."""
    conn = get_connection()

    # Get all proceeding-length videos (30+ minutes)
    videos = conn.execute("""
        SELECT * FROM youtube_videos
        WHERE duration >= 1800
        ORDER BY upload_date DESC
    """).fetchall()

    # Get all events
    events = conn.execute("""
        SELECT * FROM official_events
        WHERE status != 'Canceled'
        ORDER BY date DESC
    """).fetchall()

    print(f"Matching {len(videos)} videos against {len(events)} events...")

    # Build event index by date for faster lookup
    events_by_date = {}
    for e in events:
        d = parse_date(e['date'])
        if d:
            key = d.isoformat()
            if key not in events_by_date:
                events_by_date[key] = []
            events_by_date[key].append(e)
            # Also index adjacent days
            for offset in [-1, 1]:
                adj = (d + timedelta(days=offset)).isoformat()
                if adj not in events_by_date:
                    events_by_date[adj] = []
                events_by_date[adj].append(e)

    # Clear existing matches
    conn.execute("DELETE FROM matches")

    matched = 0
    direct_matches = 0

    for video in videos:
        v_date = parse_date(video['upload_date'])
        if not v_date:
            continue

        # Check direct event ID match first
        if video['extracted_event_id']:
            event = conn.execute(
                "SELECT * FROM official_events WHERE event_id = ?",
                (video['extracted_event_id'],)
            ).fetchone()
            if event:
                conn.execute("""
                    INSERT OR REPLACE INTO matches (video_id, event_id, confidence, match_method)
                    VALUES (?, ?, ?, ?)
                """, (video['video_id'], event['event_id'], 1.0, "event_id_match"))
                matched += 1
                direct_matches += 1
                continue

        # Fuzzy match against events on same/adjacent dates
        best_score = 0
        best_event = None
        best_method = ""

        key = v_date.isoformat()
        candidate_events = events_by_date.get(key, [])

        for event in candidate_events:
            score, method = compute_match_score(dict(video), dict(event))
            if score > best_score:
                best_score = score
                best_event = event
                best_method = method

        if best_score >= min_confidence and best_event:
            conn.execute("""
                INSERT OR REPLACE INTO matches (video_id, event_id, confidence, match_method)
                VALUES (?, ?, ?, ?)
            """, (video['video_id'], best_event['event_id'], best_score, best_method))
            matched += 1

    conn.commit()

    print(f"\nMatching complete:")
    print(f"  Total proceedings: {len(videos)}")
    print(f"  Matched: {matched} ({direct_matches} direct event ID matches)")
    print(f"  Unmatched: {len(videos) - matched}")

    conn.close()


if __name__ == "__main__":
    match_all_videos()
