# Dashboard for YouTube Videos - Implementation Plan

## Overview
Build a web dashboard that tracks House committee YouTube videos and cross-references them against official event IDs from congress.gov, grading committees on compliance.

## Architecture
- **Backend**: Python (Flask) with SQLite database
- **Frontend**: Single-page dashboard with vanilla HTML/CSS/JS (no heavy frameworks)
- **Data Collection**: yt-dlp for YouTube metadata, congress.gov API for official hearing data
- **Matching**: Fuzzy matching on date + title + duration to pair videos with official events

## Data Sources
1. **Congress.gov API** (`/committee-meeting/{congress}/house`) - official events with eventIDs, dates, titles, committees
2. **YouTube** (via yt-dlp) - video metadata from ~20 House committee channels
3. **docs.house.gov** - supplementary event data if needed

## Key Components

### 1. Data Collection Scripts
- `fetch_congress_data.py` - Pull all House committee meetings from congress.gov API for congresses 114-119
- `fetch_youtube_data.py` - Use yt-dlp to scrape video metadata from all committee YouTube channels
- `match_videos.py` - Fuzzy match YouTube videos to official events, detect event ID presence

### 2. Database Schema (SQLite)
- `committees` - name, system_code, youtube_channel, chamber
- `official_events` - event_id, congress, committee, date, title, type, status
- `youtube_videos` - video_id, channel, title, description, date, duration, has_event_id, extracted_event_id
- `matches` - links youtube_videos to official_events (with confidence score)

### 3. Dashboard (Flask web app)
- **Overview page**: All committees ranked by event ID compliance grade (A-F)
- **Committee detail**: List of proceedings, which have videos, which videos have event IDs
- **Missing IDs report**: Videos missing event IDs with suggested matches
- **Email draft generator**: Weekly summary emails for committees

### 4. Grading System
- A: 90%+ videos have event IDs
- B: 75-89%
- C: 60-74%
- D: 40-59%
- F: <40%

## Implementation Order
1. Set up project structure and dependencies
2. Build congress.gov data fetcher
3. Build YouTube data fetcher
4. Build matching engine
5. Build Flask app with dashboard
6. Polish UI and iterate with feedback

## API Key Needs
- Congress.gov API key (free, from api.data.gov)
- No YouTube API key needed (yt-dlp works without one)

## Port
- Will use port 5123 (avoiding common ports since other projects may be running)
