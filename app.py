"""Flask web application for the House Committee YouTube Dashboard."""

import os
import sys
import csv
import io
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))
from database import get_connection, init_db, seed_committees

from flask import Flask, render_template, jsonify, request, Response

app = Flask(__name__)

# Data last updated timestamp (set when data collection runs)
DATA_UPDATED = datetime.now().strftime('%Y-%m-%d')

# Duration threshold: 45 minutes minimum for a "proceeding"
MIN_DURATION = 2700  # 45 minutes in seconds


def get_grade(percentage):
    """Convert a percentage to a letter grade. Scale adjusted for realistic ranges."""
    if percentage >= 50:
        return 'A'
    elif percentage >= 30:
        return 'B'
    elif percentage >= 15:
        return 'C'
    elif percentage >= 5:
        return 'D'
    else:
        return 'F'


def get_grade_color(grade):
    colors = {
        'A': '#22c55e', 'B': '#84cc16', 'C': '#eab308',
        'D': '#f97316', 'F': '#ef4444', 'N/A': '#94a3b8',
    }
    return colors.get(grade, '#94a3b8')


def format_date(date_str):
    """Format a date string for display."""
    if not date_str:
        return None
    if len(date_str) == 8 and date_str.isdigit():
        return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
    if 'T' in date_str:
        return date_str[:10]
    return date_str


def is_likely_proceeding(title):
    """Filter out videos that are unlikely to be official proceedings."""
    if not title:
        return True
    lower = title.lower()
    # Exclude clear non-proceedings
    exclude_keywords = [
        'press conference', 'press event', 'news conference',
        'interview', 'joins fox', 'joins cnn', 'joins msnbc',
        'joins bloomberg', 'on fox news', 'on fox business',
        'opening statement', 'opening remarks', 'closing remarks',
        'member day statement',
    ]
    for kw in exclude_keywords:
        if kw in lower:
            return False
    return True


def get_congress_for_date(date_str):
    """Determine which Congress a date falls in."""
    if not date_str:
        return None
    try:
        if len(date_str) == 8:
            year = int(date_str[:4])
        else:
            year = int(date_str[:4])
        # Congress sessions: 119th = 2025-2026, 118th = 2023-2024, etc.
        congress = 119 - (2025 - year) // 2
        if year % 2 == 1:  # Odd years start new Congress
            congress = 119 - (2025 - year) // 2
        else:
            congress = 119 - (2026 - year) // 2
        return max(congress, 110)  # Don't go below 110th
    except (ValueError, TypeError):
        return None


@app.route('/')
def dashboard():
    return render_template('dashboard.html')


@app.route('/api/overview')
def api_overview():
    """Get overview statistics for all committees."""
    congress_filter = request.args.get('congress')
    conn = get_connection()

    committees = conn.execute("""
        SELECT c.system_code, c.name, c.youtube_channel_handle, c.youtube_channel_url
        FROM committees c WHERE c.is_current = 1 ORDER BY c.name
    """).fetchall()

    result = []
    for comm in committees:
        code = comm['system_code']

        # Build date filter for congress
        date_clause = ""
        if congress_filter:
            cong = int(congress_filter)
            start_year = 2025 - (119 - cong) * 2 - 1  # e.g., 119 -> 2025, 118 -> 2023
            end_year = start_year + 2
            date_clause = f" AND upload_date >= '{start_year}0101' AND upload_date < '{end_year}0101'"

        # Count total proceedings (45+ min, filtered)
        all_videos = conn.execute(f"""
            SELECT video_id, title, has_event_id FROM youtube_videos
            WHERE committee_code = ? AND duration >= {MIN_DURATION} {date_clause}
        """, (code,)).fetchall()

        proceedings = [v for v in all_videos if is_likely_proceeding(v['title'])]
        total_videos = len(proceedings)
        with_event_id = sum(1 for v in proceedings if v['has_event_id'])

        # Count matched videos
        matched = conn.execute(f"""
            SELECT COUNT(DISTINCT m.video_id) as cnt
            FROM matches m JOIN youtube_videos v ON m.video_id = v.video_id
            WHERE v.committee_code = ? AND v.duration >= {MIN_DURATION} {date_clause}
        """, (code,)).fetchone()['cnt']

        # Count official events
        event_date_clause = ""
        if congress_filter:
            event_date_clause = f" AND congress = {int(congress_filter)}"
        official_events = conn.execute(f"""
            SELECT COUNT(*) as cnt FROM official_events
            WHERE committee_code = ? AND status != 'Canceled' {event_date_clause}
        """, (code,)).fetchone()['cnt']

        if total_videos > 0:
            compliance_pct = round(with_event_id / total_videos * 100, 1)
        else:
            compliance_pct = 0

        grade = get_grade(compliance_pct) if total_videos > 0 else 'N/A'

        result.append({
            'system_code': code,
            'name': comm['name'],
            'youtube_handle': comm['youtube_channel_handle'],
            'youtube_url': comm['youtube_channel_url'],
            'total_proceedings': total_videos,
            'with_event_id': with_event_id,
            'without_event_id': total_videos - with_event_id,
            'matched': matched,
            'official_events': official_events,
            'compliance_pct': compliance_pct,
            'grade': grade,
            'grade_color': get_grade_color(grade),
        })

    grade_order = {'F': 0, 'D': 1, 'C': 2, 'B': 3, 'A': 4, 'N/A': 5}
    result.sort(key=lambda x: (grade_order.get(x['grade'], 5), x['name']))

    total_proceedings = sum(r['total_proceedings'] for r in result)
    total_with_id = sum(r['with_event_id'] for r in result)
    total_without_id = sum(r['without_event_id'] for r in result)
    overall_pct = round(total_with_id / total_proceedings * 100, 1) if total_proceedings > 0 else 0

    conn.close()

    return jsonify({
        'committees': result,
        'overall': {
            'total_proceedings': total_proceedings,
            'with_event_id': total_with_id,
            'without_event_id': total_without_id,
            'compliance_pct': overall_pct,
            'grade': get_grade(overall_pct) if total_proceedings > 0 else 'N/A',
            'committees_tracked': len([r for r in result if r['total_proceedings'] > 0]),
        },
        'data_updated': DATA_UPDATED,
    })


@app.route('/api/committee/<system_code>')
def api_committee_detail(system_code):
    conn = get_connection()
    committee = conn.execute(
        "SELECT * FROM committees WHERE system_code = ?", (system_code,)
    ).fetchone()
    if not committee:
        return jsonify({'error': 'Committee not found'}), 404

    videos = conn.execute(f"""
        SELECT v.*, m.event_id as matched_event_id, m.confidence as match_confidence,
            m.match_method, e.title as event_title, e.date as event_date, e.type as event_type
        FROM youtube_videos v
        LEFT JOIN matches m ON v.video_id = m.video_id
        LEFT JOIN official_events e ON m.event_id = e.event_id
        WHERE v.committee_code = ? AND v.duration >= {MIN_DURATION}
        ORDER BY v.upload_date DESC
    """, (system_code,)).fetchall()

    video_list = []
    for v in videos:
        if not is_likely_proceeding(v['title']):
            continue
        video_list.append({
            'video_id': v['video_id'],
            'title': v['title'],
            'upload_date': format_date(v['upload_date']),
            'duration_minutes': round(v['duration'] / 60) if v['duration'] else 0,
            'view_count': v['view_count'],
            'has_event_id': bool(v['has_event_id']),
            'extracted_event_id': v['extracted_event_id'],
            'matched_event_id': v['matched_event_id'],
            'match_confidence': v['match_confidence'],
            'match_method': v['match_method'],
            'event_title': v['event_title'],
            'event_date': format_date(v['event_date']),
            'event_type': v['event_type'],
            'url': v['url'],
            'docs_house_url': f"https://docs.house.gov/Committee/Calendar/ByEvent.aspx?EventID={v['matched_event_id']}" if v['matched_event_id'] else None,
        })

    conn.close()
    return jsonify({
        'committee': {
            'system_code': committee['system_code'],
            'name': committee['name'],
            'youtube_handle': committee['youtube_channel_handle'],
            'youtube_url': committee['youtube_channel_url'],
        },
        'videos': video_list,
    })


@app.route('/api/missing-ids')
def api_missing_ids():
    conn = get_connection()
    videos = conn.execute(f"""
        SELECT v.*, c.name as committee_name,
            m.event_id as suggested_event_id, m.confidence as match_confidence,
            e.title as event_title, e.date as event_date
        FROM youtube_videos v
        JOIN committees c ON v.committee_code = c.system_code
        LEFT JOIN matches m ON v.video_id = m.video_id
        LEFT JOIN official_events e ON m.event_id = e.event_id
        WHERE v.duration >= {MIN_DURATION} AND v.has_event_id = 0
        ORDER BY v.upload_date DESC
    """).fetchall()

    result = []
    for v in videos:
        if not is_likely_proceeding(v['title']):
            continue
        result.append({
            'video_id': v['video_id'],
            'title': v['title'],
            'committee_name': v['committee_name'],
            'committee_code': v['committee_code'],
            'upload_date': format_date(v['upload_date']),
            'duration_minutes': round(v['duration'] / 60) if v['duration'] else 0,
            'url': v['url'],
            'suggested_event_id': v['suggested_event_id'],
            'match_confidence': v['match_confidence'],
            'event_title': v['event_title'],
            'event_date': format_date(v['event_date']),
            'docs_house_url': f"https://docs.house.gov/Committee/Calendar/ByEvent.aspx?EventID={v['suggested_event_id']}" if v['suggested_event_id'] else None,
        })

    conn.close()
    return jsonify({'videos': result})


@app.route('/api/email-draft/<system_code>')
def api_email_draft(system_code):
    conn = get_connection()
    committee = conn.execute(
        "SELECT * FROM committees WHERE system_code = ?", (system_code,)
    ).fetchone()
    if not committee:
        return jsonify({'error': 'Committee not found'}), 404

    videos = conn.execute(f"""
        SELECT v.*, m.event_id as suggested_event_id, e.title as event_title
        FROM youtube_videos v
        LEFT JOIN matches m ON v.video_id = m.video_id
        LEFT JOIN official_events e ON m.event_id = e.event_id
        WHERE v.committee_code = ? AND v.duration >= {MIN_DURATION} AND v.has_event_id = 0
        ORDER BY v.upload_date DESC LIMIT 20
    """, (system_code,)).fetchall()

    # Filter
    videos = [v for v in videos if is_likely_proceeding(v['title'])]
    if not videos:
        return jsonify({'subject': '', 'body': '', 'count': 0})

    subject = f"Action Needed: {len(videos)} YouTube Video(s) Missing Event IDs - {committee['name']}"
    lines = [
        f"Dear {committee['name']} Committee Clerk / Digital Director,",
        "",
        f"We identified {len(videos)} YouTube video(s) from the {committee['name']} channel that appear to be official committee proceedings but are missing the House Event ID in their video description.",
        "",
        "Including the Event ID allows the Library of Congress to properly index these proceedings on congress.gov, making them part of the official legislative record.",
        "",
        "Videos missing Event IDs:",
        "",
    ]

    for v in videos:
        ud = format_date(v['upload_date'])
        line = f'  - "{v["title"]}" ({ud or "Unknown date"})'
        line += f'\n    YouTube: {v["url"]}'
        if v['suggested_event_id']:
            line += f'\n    Suggested Event ID: {v["suggested_event_id"]}'
            line += f'\n    docs.house.gov: https://docs.house.gov/Committee/Calendar/ByEvent.aspx?EventID={v["suggested_event_id"]}'
        lines.append(line)
        lines.append("")

    lines.extend([
        "To add the Event ID, please edit each video's description on YouTube and add a line:",
        "",
        "  EventID=XXXXXX",
        "",
        "(where XXXXXX is the 5-6 digit event ID from docs.house.gov)",
        "",
        "This ensures proceedings are properly cataloged on congress.gov, making them accessible to researchers, journalists, other Members, and the public.",
        "",
        "This review was conducted in support of the Congressional Data Task Force's efforts to improve video discoverability on congress.gov, following the June 2025 meeting where the Library of Congress identified this gap.",
        "",
        "For questions about Event IDs, see: https://docs.house.gov",
        "",
        "Thank you for your attention to this matter.",
        "",
        "Sincerely,",
        "[Your Name]",
        "[Your Title/Organization]",
    ])

    conn.close()
    return jsonify({
        'subject': subject,
        'body': '\n'.join(lines),
        'count': len(videos),
    })


@app.route('/api/export/loc')
def api_export_loc():
    """Export data for Library of Congress in CSV format."""
    conn = get_connection()
    videos = conn.execute(f"""
        SELECT v.video_id, v.url, v.title, v.upload_date, v.duration,
            c.name as committee_name, c.system_code as committee_code,
            v.has_event_id, v.extracted_event_id,
            m.event_id as matched_event_id, m.confidence as match_confidence, m.match_method
        FROM youtube_videos v
        JOIN committees c ON v.committee_code = c.system_code
        LEFT JOIN matches m ON v.video_id = m.video_id
        WHERE v.duration >= {MIN_DURATION}
        ORDER BY c.name, v.upload_date DESC
    """).fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'video_id', 'youtube_url', 'title', 'upload_date', 'duration_minutes',
        'committee', 'committee_code', 'has_event_id_in_description',
        'extracted_event_id', 'matched_event_id', 'match_confidence', 'match_method',
        'docs_house_gov_url'
    ])

    for v in videos:
        if not is_likely_proceeding(v['title']):
            continue
        event_id = v['extracted_event_id'] or v['matched_event_id']
        docs_url = f"https://docs.house.gov/Committee/Calendar/ByEvent.aspx?EventID={event_id}" if event_id else ''
        writer.writerow([
            v['video_id'], v['url'], v['title'],
            format_date(v['upload_date']),
            round(v['duration'] / 60) if v['duration'] else '',
            v['committee_name'], v['committee_code'],
            'Yes' if v['has_event_id'] else 'No',
            v['extracted_event_id'] or '',
            v['matched_event_id'] or '',
            round(v['match_confidence'] * 100) if v['match_confidence'] else '',
            v['match_method'] or '',
            docs_url,
        ])

    conn.close()
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=house_youtube_event_ids_{DATA_UPDATED}.csv'}
    )


@app.route('/api/stats')
def api_stats():
    conn = get_connection()
    stats = {
        'total_committees': conn.execute("SELECT COUNT(*) as c FROM committees").fetchone()['c'],
        'total_events': conn.execute("SELECT COUNT(*) as c FROM official_events").fetchone()['c'],
        'total_videos': conn.execute("SELECT COUNT(*) as c FROM youtube_videos").fetchone()['c'],
        'total_proceedings': conn.execute(f"SELECT COUNT(*) as c FROM youtube_videos WHERE duration >= {MIN_DURATION}").fetchone()['c'],
        'total_matches': conn.execute("SELECT COUNT(*) as c FROM matches").fetchone()['c'],
        'data_updated': DATA_UPDATED,
        'events_by_congress': {},
    }
    for row in conn.execute("SELECT congress, COUNT(*) as c FROM official_events GROUP BY congress ORDER BY congress"):
        stats['events_by_congress'][row['congress']] = row['c']
    conn.close()
    return jsonify(stats)


if __name__ == "__main__":
    try:
        init_db()
        seed_committees()
    except Exception:
        pass
    app.run(host='0.0.0.0', port=5123, debug=False)
