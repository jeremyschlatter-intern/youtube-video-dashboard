"""Fetch upload dates for YouTube videos that are missing them."""

import subprocess
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial

print = partial(print, flush=True)

sys.path.insert(0, os.path.dirname(__file__))
from database import get_connection


def fetch_video_date(video_id):
    """Fetch upload date for a video."""
    try:
        result = subprocess.run(
            ['python3', '-m', 'yt_dlp', '--skip-download',
             '--print', '%(upload_date)s', '--no-warnings',
             f'https://www.youtube.com/watch?v={video_id}'],
            capture_output=True, text=True, timeout=30,
        )
        date = result.stdout.strip()
        return date if date and date != 'NA' else None
    except Exception:
        return None


def main():
    conn = get_connection()
    # Get all proceedings missing dates
    rows = conn.execute(
        "SELECT video_id FROM youtube_videos WHERE duration >= 1800 AND (upload_date IS NULL OR upload_date = 'NA')"
    ).fetchall()
    conn.close()

    vid_ids = [r['video_id'] for r in rows]
    print(f"Fetching dates for {len(vid_ids)} videos (10 workers)...")

    results = {}
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_video_date, vid): vid for vid in vid_ids}
        done = 0
        for future in as_completed(futures):
            vid = futures[future]
            done += 1
            try:
                results[vid] = future.result()
            except Exception:
                results[vid] = None
            if done % 50 == 0:
                print(f"  Progress: {done}/{len(vid_ids)}")
                # Write batch to DB
                batch = {k: v for k, v in results.items() if v is not None}
                if batch:
                    for attempt in range(10):
                        try:
                            wconn = get_connection()
                            for vid_id, date in batch.items():
                                wconn.execute(
                                    "UPDATE youtube_videos SET upload_date = ? WHERE video_id = ?",
                                    (date, vid_id)
                                )
                            wconn.commit()
                            wconn.close()
                            results = {k: v for k, v in results.items() if k not in batch}
                            break
                        except Exception as e:
                            import time; time.sleep(2)

    # Final write
    batch = {k: v for k, v in results.items() if v is not None}
    if batch:
        for attempt in range(10):
            try:
                wconn = get_connection()
                for vid_id, date in batch.items():
                    wconn.execute(
                        "UPDATE youtube_videos SET upload_date = ? WHERE video_id = ?",
                        (date, vid_id)
                    )
                wconn.commit()
                wconn.close()
                break
            except Exception as e:
                import time; time.sleep(2)

    # Count results
    conn = get_connection()
    with_dates = conn.execute(
        "SELECT COUNT(*) FROM youtube_videos WHERE duration >= 1800 AND upload_date IS NOT NULL AND upload_date != 'NA'"
    ).fetchone()[0]
    total = conn.execute("SELECT COUNT(*) FROM youtube_videos WHERE duration >= 1800").fetchone()[0]
    conn.close()
    print(f"\nDone. {with_dates}/{total} proceedings now have dates.")


if __name__ == "__main__":
    main()
