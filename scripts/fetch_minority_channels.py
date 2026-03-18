"""Fetch YouTube data from minority-party committee channels."""

import subprocess
import re
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial

print = partial(print, flush=True)

sys.path.insert(0, os.path.dirname(__file__))
from database import get_connection

EVENT_ID_PATTERNS = [
    r'Event\s*ID[\s:=]+(\d{5,6})',
    r'EventID[=:\s]+(\d{5,6})',
    r'event[_\-]?id[=:\s]+(\d{5,6})',
    r'docs\.house\.gov/.*EventID=(\d{5,6})',
    r'congress\.gov/event/\d+th-congress/house-event/(\d{5,6})',
]

MIN_DURATION = 2700


def extract_event_id(description):
    if not description:
        return None
    for pattern in EVENT_ID_PATTERNS:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def fetch_video_metadata(video_id):
    """Fetch description and upload date for a video."""
    try:
        result = subprocess.run(
            ['python3', '-m', 'yt_dlp', '--skip-download',
             '--print', '%(description)s\t%(upload_date)s', '--no-warnings',
             f'https://www.youtube.com/watch?v={video_id}'],
            capture_output=True, text=True, timeout=30,
        )
        parts = result.stdout.strip().split('\t')
        desc = parts[0] if parts[0] != 'NA' else ''
        date = parts[1] if len(parts) > 1 and parts[1] != 'NA' else None
        return desc, date
    except Exception:
        return '', None


def fetch_channel(handle, url, parent_code):
    """Fetch all videos from a minority-party channel and assign to parent committee."""
    conn = get_connection()

    # Check existing
    existing = conn.execute(
        "SELECT COUNT(*) FROM youtube_videos WHERE channel_handle = ?", (handle,)
    ).fetchone()[0]
    if existing > 0:
        print(f"  Already have {existing} videos from @{handle}")
        conn.close()
        return

    print(f"  Fetching video list from @{handle}...")
    try:
        result = subprocess.run(
            ['python3', '-m', 'yt_dlp', '--skip-download', '--flat-playlist',
             '--print', '%(id)s\t%(title)s\t%(duration)s\t%(view_count)s',
             '--no-warnings', f'{url}/videos'],
            capture_output=True, text=True, timeout=600,
        )
    except Exception as e:
        print(f"  Error: {e}")
        conn.close()
        return

    videos = []
    for line in result.stdout.strip().split('\n'):
        if not line.strip():
            continue
        parts = line.split('\t')
        if len(parts) >= 4:
            vid_id, title = parts[0], parts[1]
            try:
                duration = int(float(parts[2])) if parts[2] != 'NA' else 0
            except:
                duration = 0
            try:
                views = int(parts[3]) if parts[3] != 'NA' else 0
            except:
                views = 0
            videos.append({'id': vid_id, 'title': title, 'duration': duration, 'view_count': views})

    print(f"  Found {len(videos)} total videos")
    proceedings = [v for v in videos if v['duration'] >= MIN_DURATION]
    print(f"  {len(proceedings)} are 45+ minutes")

    # Insert videos
    for v in videos:
        for attempt in range(5):
            try:
                conn.execute("""INSERT OR IGNORE INTO youtube_videos
                    (video_id, channel_handle, committee_code, title, duration, view_count, url)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (v['id'], handle, parent_code, v['title'], v['duration'], v['view_count'],
                     f"https://www.youtube.com/watch?v={v['id']}"))
                break
            except Exception:
                import time; time.sleep(2)
    conn.commit()

    # Fetch descriptions and dates in parallel for proceedings
    if proceedings:
        print(f"  Fetching metadata for {len(proceedings)} proceedings...")
        results = {}
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(fetch_video_metadata, v['id']): v['id'] for v in proceedings}
            done = 0
            for future in as_completed(futures):
                vid = futures[future]
                done += 1
                try:
                    results[vid] = future.result()
                except:
                    results[vid] = ('', None)
                if done % 50 == 0:
                    print(f"    Progress: {done}/{len(proceedings)}")

        # Write results in batches
        items = list(results.items())
        for i in range(0, len(items), 10):
            batch = items[i:i+10]
            for attempt in range(10):
                try:
                    wconn = get_connection()
                    for vid_id, (desc, date) in batch:
                        event_id = extract_event_id(desc)
                        wconn.execute("""UPDATE youtube_videos SET description=?, upload_date=?,
                            has_event_id=?, extracted_event_id=? WHERE video_id=?""",
                            (desc, date, 1 if event_id else 0, event_id, vid_id))
                    wconn.commit()
                    wconn.close()
                    break
                except:
                    import time; time.sleep(2)

    conn.close()


def main():
    minority_channels = [
        ('JudiciaryDems', 'https://www.youtube.com/@JudiciaryDems', 'hsju00'),
        ('HFACDemocrats', 'https://www.youtube.com/@HFACDemocrats', 'hsfa00'),
        ('OversightDems', 'https://www.youtube.com/@OversightDems', 'hsgo00'),
        ('HouseBudgetDems', 'https://www.youtube.com/@HouseBudgetDems', 'hsbu00'),
        ('HouseScience', 'https://www.youtube.com/@HouseScience', 'hssy00'),
    ]

    print("Fetching minority-party YouTube channels...\n")
    for handle, url, parent_code in minority_channels:
        print(f"\n[{parent_code}] @{handle}")
        fetch_channel(handle, url, parent_code)
    print("\nDone.")


if __name__ == "__main__":
    main()
