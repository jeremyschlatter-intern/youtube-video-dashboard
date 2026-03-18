"""Fetch official House committee meeting data from congress.gov API."""

import os
import sys
import json
import time
import urllib.request
import urllib.error

sys.path.insert(0, os.path.dirname(__file__))
from database import get_connection, init_db, seed_committees

# Load API key
ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
API_KEY = None
if os.path.exists(ENV_PATH):
    with open(ENV_PATH) as f:
        for line in f:
            if line.startswith('CONGRESS_API_KEY='):
                API_KEY = line.strip().split('=', 1)[1]

if not API_KEY:
    API_KEY = os.environ.get('CONGRESS_API_KEY', 'DEMO_KEY')

BASE_URL = "https://api.congress.gov/v3"
RATE_LIMIT_DELAY = 0.75  # seconds between requests to stay under 5000/hr


def api_get(url, retries=3):
    """Make a GET request to the congress.gov API."""
    separator = '&' if '?' in url else '?'
    full_url = f"{url}{separator}api_key={API_KEY}&format=json"
    for attempt in range(retries):
        try:
            req = urllib.request.Request(full_url)
            req.add_header('Accept', 'application/json')
            req.add_header('User-Agent', 'HouseYouTubeDashboard/1.0')
            import ssl
            ctx = ssl.create_default_context()
            with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = 10 * (attempt + 1)
                print(f"  Rate limited, waiting {wait}s...")
                time.sleep(wait)
            else:
                print(f"  HTTP {e.code} for {url}")
                if attempt < retries - 1:
                    time.sleep(2)
        except Exception as e:
            print(f"  Error: {e}")
            if attempt < retries - 1:
                time.sleep(2)
    return None


def fetch_meeting_list(congress, chamber="house", limit=250):
    """Fetch all meeting IDs for a given congress and chamber."""
    meetings = []
    offset = 0
    while True:
        url = f"{BASE_URL}/committee-meeting/{congress}/{chamber}?limit={limit}&offset={offset}"
        data = api_get(url)
        if not data or 'committeeMeetings' not in data:
            break
        batch = data['committeeMeetings']
        if not batch:
            break
        meetings.extend(batch)
        print(f"  Fetched {len(meetings)} meeting IDs so far...")
        if len(batch) < limit:
            break
        offset += limit
        time.sleep(RATE_LIMIT_DELAY)
    return meetings


def fetch_meeting_detail(congress, chamber, event_id):
    """Fetch detailed info for a specific meeting."""
    url = f"{BASE_URL}/committee-meeting/{congress}/{chamber}/{event_id}"
    time.sleep(RATE_LIMIT_DELAY)
    return api_get(url)


def store_meeting(conn, congress, meeting_detail):
    """Store a meeting in the database."""
    m = meeting_detail
    if not m:
        return

    event_id = m.get('eventId')
    if not event_id:
        return

    # Get committee info - API returns committees as a list
    committees = m.get('committees', [])
    if isinstance(committees, dict):
        committees = committees.get('items', [])
    committee_code = None
    committee_name = None
    if committees:
        comm = committees[0]
        raw_code = comm.get('systemCode', '').lower()
        committee_name = comm.get('name', '')
        # Map subcommittee codes (e.g., hsii24) to parent committee (hsii00)
        if raw_code and len(raw_code) >= 4:
            committee_code = raw_code[:4] + '00'
        else:
            committee_code = raw_code

    date = m.get('date', '')
    title = m.get('title', '')
    meeting_type = m.get('type', '')
    status = m.get('meetingStatus', '')
    url = m.get('url', '')

    conn.execute("""
        INSERT OR REPLACE INTO official_events
        (event_id, congress, committee_code, committee_name, date, title, type, status, url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (int(event_id), congress, committee_code, committee_name, date, title, meeting_type, status, url))


def fetch_congress_meetings(congress, fetch_details=True):
    """Fetch all meetings for a congress and store them."""
    print(f"\n=== Congress {congress} ===")
    conn = get_connection()

    # Check what we already have
    existing = conn.execute(
        "SELECT COUNT(*) as cnt FROM official_events WHERE congress = ?",
        (congress,)
    ).fetchone()['cnt']

    if existing > 0 and not fetch_details:
        print(f"  Already have {existing} events, skipping")
        conn.close()
        return

    # Fetch meeting list
    print(f"  Fetching meeting list...")
    meetings = fetch_meeting_list(congress)
    print(f"  Found {len(meetings)} meetings")

    if not meetings:
        conn.close()
        return

    # Check which meetings we already have details for
    existing_ids = set()
    for row in conn.execute("SELECT event_id FROM official_events WHERE congress = ?", (congress,)):
        existing_ids.add(row['event_id'])

    # Fetch details for meetings we don't have
    to_fetch = [m for m in meetings if int(m['eventId']) not in existing_ids]
    print(f"  Need to fetch details for {len(to_fetch)} meetings ({len(existing_ids)} already in DB)")

    for i, m in enumerate(to_fetch):
        event_id = m['eventId']
        if (i + 1) % 25 == 0:
            print(f"  Progress: {i + 1}/{len(to_fetch)}")
        detail_data = fetch_meeting_detail(congress, "house", event_id)
        if detail_data:
            meeting = detail_data.get('committeeMeeting')
            if meeting:
                store_meeting(conn, congress, meeting)
        if (i + 1) % 50 == 0:
            conn.commit()

    conn.commit()

    total = conn.execute(
        "SELECT COUNT(*) as cnt FROM official_events WHERE congress = ?",
        (congress,)
    ).fetchone()['cnt']
    print(f"  Total events in DB for congress {congress}: {total}")

    conn.close()


def fetch_all():
    """Fetch meetings for congresses 114-119 (2015-2026)."""
    # Congress numbers and their date ranges:
    # 114: 2015-2017, 115: 2017-2019, 116: 2019-2021
    # 117: 2021-2023, 118: 2023-2025, 119: 2025-2027
    for congress in [119, 118, 117, 116, 115, 114]:
        fetch_congress_meetings(congress)


if __name__ == "__main__":
    try:
        init_db()
        seed_committees()
    except Exception as e:
        print(f"DB init skipped (likely locked by another process): {e}")
    fetch_all()
