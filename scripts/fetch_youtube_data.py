"""Fetch YouTube video metadata from House committee channels using yt-dlp."""

import subprocess
import re
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial

# Force unbuffered output
print = partial(print, flush=True)

sys.path.insert(0, os.path.dirname(__file__))
from database import get_connection, init_db, seed_committees

# Event ID patterns found in YouTube descriptions
EVENT_ID_PATTERNS = [
    r'Event\s*ID[\s:=]+(\d{5,6})',
    r'EventID[=:\s]+(\d{5,6})',
    r'event[_\-]?id[=:\s]+(\d{5,6})',
    r'docs\.house\.gov/.*EventID=(\d{5,6})',
    r'congress\.gov/event/\d+th-congress/house-event/(\d{5,6})',
]

MIN_PROCEEDING_DURATION = 1800  # 30 minutes


def extract_event_id(description):
    """Extract event ID from a YouTube video description."""
    if not description:
        return None
    for pattern in EVENT_ID_PATTERNS:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def fetch_channel_video_list(channel_url):
    """Get list of video IDs and basic info from a channel using yt-dlp flat playlist."""
    try:
        result = subprocess.run(
            [
                'python3', '-m', 'yt_dlp',
                '--skip-download',
                '--flat-playlist',
                '--print', '%(id)s\t%(title)s\t%(duration)s\t%(view_count)s\t%(upload_date)s',
                '--no-warnings',
                f'{channel_url}/videos',
            ],
            capture_output=True, text=True, timeout=600,
        )
        videos = []
        for line in result.stdout.strip().split('\n'):
            if not line.strip():
                continue
            parts = line.split('\t')
            if len(parts) >= 5:
                vid_id, title, duration, views, upload_date = parts[:5]
                try:
                    duration = int(float(duration)) if duration and duration != 'NA' else 0
                except (ValueError, TypeError):
                    duration = 0
                try:
                    views = int(views) if views and views != 'NA' else 0
                except (ValueError, TypeError):
                    views = 0
                videos.append({
                    'id': vid_id, 'title': title, 'duration': duration,
                    'view_count': views,
                    'upload_date': upload_date if upload_date != 'NA' else None,
                })
        return videos
    except subprocess.TimeoutExpired:
        print(f"  Timeout fetching {channel_url}")
        return []
    except Exception as e:
        print(f"  Error fetching {channel_url}: {e}")
        return []


def fetch_video_description(video_id):
    """Fetch the full description for a specific video."""
    try:
        result = subprocess.run(
            [
                'python3', '-m', 'yt_dlp',
                '--skip-download',
                '--print', '%(description)s',
                '--no-warnings',
                f'https://www.youtube.com/watch?v={video_id}',
            ],
            capture_output=True, text=True, timeout=60,
        )
        desc = result.stdout.strip()
        return desc if desc and desc != 'NA' else ''
    except Exception:
        return ''


def fetch_descriptions_parallel(video_ids, max_workers=5):
    """Fetch descriptions for multiple videos in parallel."""
    results = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch_video_description, vid): vid for vid in video_ids}
        done = 0
        for future in as_completed(futures):
            vid = futures[future]
            done += 1
            try:
                results[vid] = future.result()
            except Exception:
                results[vid] = ''
            if done % 25 == 0:
                print(f"    Descriptions: {done}/{len(video_ids)}")
    return results


def fetch_videos_for_committee(committee_code, channel_handle, channel_url):
    """Fetch all videos for a committee and store in the database."""
    conn = get_connection()

    # Check if we already have videos for this committee
    existing = conn.execute(
        "SELECT COUNT(*) as cnt FROM youtube_videos WHERE committee_code = ?",
        (committee_code,)
    ).fetchone()['cnt']

    if existing > 0:
        print(f"  Already have {existing} videos, checking for missing descriptions...")
        missing = conn.execute(
            "SELECT video_id FROM youtube_videos WHERE committee_code = ? AND description IS NULL AND duration >= ?",
            (committee_code, MIN_PROCEEDING_DURATION)
        ).fetchall()
        if missing:
            print(f"  Fetching {len(missing)} missing descriptions (parallel)...")
            vid_ids = [r['video_id'] for r in missing]
            descs = fetch_descriptions_parallel(vid_ids)
            items = list(descs.items())
            batch_size = 10
            for i in range(0, len(items), batch_size):
                batch = items[i:i+batch_size]
                for attempt in range(10):
                    try:
                        wconn = get_connection()
                        for vid_id, desc in batch:
                            event_id = extract_event_id(desc)
                            wconn.execute(
                                "UPDATE youtube_videos SET description = ?, has_event_id = ?, extracted_event_id = ? WHERE video_id = ?",
                                (desc, 1 if event_id else 0, event_id, vid_id)
                            )
                        wconn.commit()
                        wconn.close()
                        break
                    except Exception as e:
                        if attempt < 9:
                            import time; time.sleep(2)
                        else:
                            print(f"  Failed to write batch: {e}")
        else:
            print(f"  All descriptions fetched already.")
        conn.close()
        return

    print(f"  Fetching video list from {channel_url}...")
    videos = fetch_channel_video_list(channel_url)
    print(f"  Found {len(videos)} total videos")

    if not videos:
        conn.close()
        return

    proceedings = [v for v in videos if v['duration'] >= MIN_PROCEEDING_DURATION]
    print(f"  {len(proceedings)} videos are 30+ minutes (likely proceedings)")

    # Insert all videos with retry for DB locks
    for attempt in range(5):
        try:
            for v in videos:
                conn.execute("""
                    INSERT OR IGNORE INTO youtube_videos
                    (video_id, channel_handle, committee_code, title, upload_date, duration, view_count, url)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    v['id'], channel_handle, committee_code, v['title'],
                    v['upload_date'], v['duration'], v['view_count'],
                    f"https://www.youtube.com/watch?v={v['id']}"
                ))
            conn.commit()
            break
        except Exception as e:
            print(f"  DB write retry {attempt+1}: {e}")
            import time; time.sleep(5)

    # Fetch descriptions in parallel for proceedings
    if proceedings:
        print(f"  Fetching descriptions for {len(proceedings)} proceedings (parallel, 5 workers)...")
        vid_ids = [v['id'] for v in proceedings]
        descs = fetch_descriptions_parallel(vid_ids)
        # Write results in small batches with retry
        items = list(descs.items())
        batch_size = 10
        for i in range(0, len(items), batch_size):
            batch = items[i:i+batch_size]
            for attempt in range(10):
                try:
                    wconn = get_connection()
                    for vid_id, desc in batch:
                        event_id = extract_event_id(desc)
                        wconn.execute("""
                            UPDATE youtube_videos SET description = ?, has_event_id = ?, extracted_event_id = ?
                            WHERE video_id = ?
                        """, (desc, 1 if event_id else 0, event_id, vid_id))
                    wconn.commit()
                    wconn.close()
                    break
                except Exception as e:
                    if attempt < 9:
                        import time; time.sleep(2)
                    else:
                        print(f"  Failed to write batch after 10 retries: {e}")

    conn.close()


def fetch_all_committees():
    """Fetch YouTube data for all committees."""
    conn = get_connection()
    committees = conn.execute(
        "SELECT system_code, name, youtube_channel_handle, youtube_channel_url FROM committees WHERE youtube_channel_url IS NOT NULL"
    ).fetchall()
    conn.close()

    print(f"Fetching YouTube data for {len(committees)} committees...\n")
    for comm in committees:
        print(f"\n[{comm['system_code']}] {comm['name']} (@{comm['youtube_channel_handle']})")
        fetch_videos_for_committee(
            comm['system_code'], comm['youtube_channel_handle'], comm['youtube_channel_url']
        )
    print("\n\nDone fetching YouTube data.")


if __name__ == "__main__":
    try:
        init_db()
        seed_committees()
    except Exception:
        pass
    fetch_all_committees()
