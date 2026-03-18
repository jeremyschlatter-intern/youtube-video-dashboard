# After Action Report: House Committee YouTube Event ID Tracker

## Project Overview

I built a web dashboard that tracks whether House committees include official Event IDs in their YouTube video descriptions. Event IDs are how the Library of Congress links committee proceeding videos to their official records on congress.gov. Without them, hearings effectively go "missing" from the legislative record.

The dashboard is live at `http://127.0.0.1:5123` and includes:
- **Committee Report Card**: Grades 19 committees (A-F) on Event ID compliance
- **Missing Event IDs**: Searchable list of 4,000+ proceedings without Event IDs
- **Export for LOC**: CSV export for the Library of Congress to backfill records
- **Email Draft Generator**: Templates for notifying committees about missing IDs

## Key Finding

**Overall compliance is approximately 0.9%.** Out of 4,069 YouTube proceedings tracked across 19 House committees, only 37 include an Event ID. The best performer is Financial Services at 38.9%. Most committees are at 0%.

---

## Process and Obstacles

### 1. Identifying YouTube Channels (Obstacle: Incorrect Handles)

**Problem**: House committees don't have standardized YouTube channel naming. Initial research produced handles that were wrong for 12 out of 20 committees (404 errors or wrong channels).

**What I tried**: First, I used web search to find channel handles. Many were outdated or incorrect.

**Resolution**: I spawned a dedicated agent to systematically test each handle against YouTube, trying common variations (committee name, "GOP" suffix, "Dems" suffix). This identified the correct handles for all committees. Examples:
- Agriculture: `@HouseAgCommittee` (wrong) → `@AgRepublicans` (correct)
- Financial Services: `@FinancialCmte` (wrong) → `@USHouseFSC` (correct)
- Oversight: `@OversightGOP` (wrong) → `@OversightandGovernmentReform` (correct)

### 2. Congress.gov API Integration (Obstacle: 403 Errors)

**Problem**: The congress.gov API returned 403 Forbidden when called from Python's `urllib`, despite working fine with `curl`.

**What I tried**: First used the DEMO_KEY (rate-limited). Then got a real API key from the user, but Python requests still failed.

**Resolution**: Added a `User-Agent` header to requests. The API apparently requires a non-default User-Agent. Also fixed the response parsing — the API returns `committees` as a direct list, not nested under `items` as the documentation suggested.

### 3. Concurrent Database Access (Obstacle: SQLite Locks)

**Problem**: Running YouTube data collection and congress.gov data collection simultaneously caused persistent `database is locked` errors despite using WAL mode and 30-second busy timeouts.

**What I tried**:
- Increased SQLite busy timeout
- Used WAL journal mode
- Tried running processes sequentially

**Resolution**: Implemented batch writes with retry logic — each write opens a fresh connection, writes a small batch (10 records), commits, and closes. If locked, retries up to 10 times with 2-second delays. This allowed both data collection processes to run concurrently without blocking each other.

### 4. Missing Upload Dates (Obstacle: yt-dlp Flat Playlist Limitation)

**Problem**: yt-dlp's `--flat-playlist` mode (used for fast channel scanning) returns `NA` for upload dates. Without dates, the fuzzy matching engine couldn't match any videos to official events.

**What I tried**: Initially relied on flat playlist mode for all metadata.

**Resolution**: Wrote a separate `fetch_dates.py` script that fetches individual video metadata in parallel (10 workers) for all 3,600+ proceedings. This took about 13 minutes and recovered dates for 2,585 of 3,603 videos.

### 5. Data Quality / Credibility (Obstacle: DC Agent Feedback)

**Problem**: My first version counted any 30+ minute video as a "proceeding," inflating counts dramatically. The Oversight committee showed 1,215 proceedings when the real number of hearings was closer to 300. A DC reviewer pointed out this would destroy credibility instantly.

**What I tried**: Initial 30-minute threshold was too low.

**Resolution**:
- Raised threshold to 45 minutes
- Added title-based filtering to exclude press conferences, interviews, and opening statements
- Added official event counts alongside YouTube counts so users can cross-reference
- Adjusted the grading scale from academic (A=90%) to realistic (A=50%) given that compliance is universally terrible

### 6. Missing Historical Data (Obstacle: Majority-Only Channels)

**Problem**: I initially only tracked majority-party YouTube channels. But in the 116th-117th Congress, Democrats controlled the House, so their channels had the proceedings. This meant I was missing most historical data.

**Resolution**: Added 5 minority-party channels (Judiciary Dems, Foreign Affairs Dems, Oversight Dems, Budget Dems, Science bipartisan). This dramatically improved coverage — Judiciary went from 4 to 268 proceedings, Science from 0 to 511.

---

## Team Structure

I worked primarily as a single agent with specialized sub-agents:

| Agent | Role | Key Contribution |
|-------|------|-----------------|
| **API Researcher** | Researched congress.gov API | Mapped all available endpoints, documented response formats |
| **YouTube Researcher** | Researched committee YouTube channels | Identified Event ID patterns, tested channel handles |
| **Handle Checker** | Verified/corrected YouTube handles | Found correct handles for 12 committees |
| **DC Reviewer** (Daniel Schuman persona) | Provided domain-expert feedback | Two rounds of detailed review, identified data quality issues |

---

## Technical Architecture

```
dashboard-for-youtube-videos/
├── app.py                    # Flask web server (port 5123)
├── data/dashboard.db         # SQLite database
├── templates/dashboard.html  # Main dashboard page
├── static/
│   ├── css/style.css         # Stylesheet
│   └── js/dashboard.js       # Frontend JavaScript
├── scripts/
│   ├── database.py           # Schema and helpers
│   ├── fetch_youtube_data.py # YouTube channel scraper
│   ├── fetch_congress_data.py# Congress.gov API client
│   ├── fetch_minority_channels.py # Minority party channels
│   ├── fetch_dates.py        # Upload date backfiller
│   └── match_videos.py       # Fuzzy matching engine
└── .env                      # API key
```

### Data Pipeline
1. `fetch_youtube_data.py` → Scans 25 YouTube channels via yt-dlp
2. `fetch_congress_data.py` → Pulls official event data from congress.gov API
3. `fetch_dates.py` → Backfills upload dates for date-based matching
4. `match_videos.py` → Fuzzy matches videos to events by date + title + committee

### Matching Algorithm
- **Direct match**: Event ID found in video description matches an official event (100% confidence)
- **Fuzzy match**: Same date + same committee + similar title (scored 0-95%)
- Minimum confidence threshold: 40%

---

## Data Summary

| Metric | Count |
|--------|-------|
| Committees tracked | 19 (with both majority and minority channels) |
| YouTube channels scanned | 25 |
| Total YouTube videos | ~18,000 |
| Proceedings (45+ min) | 4,069 |
| With Event ID | 37 (0.9%) |
| Official events (congress.gov) | 5,630 |
| Fuzzy matches | 121 |

### Top Performers
| Committee | Compliance | Grade |
|-----------|-----------|-------|
| Financial Services | 38.9% | B |
| Homeland Security | 11.1% | D |
| Appropriations | 7.2% | D |
| Armed Services | 4.3% | F |

---

## What I Would Improve With More Time

1. **Complete congress.gov data**: Currently have data for 4 congress sessions; 114th and 115th are incomplete
2. **Better fuzzy matching**: Current match rate is low (~3%); could improve with NLP-based title comparison
3. **Congress session filter**: Backend supports it but UI doesn't expose it yet
4. **Automated weekly email sending**: Currently generates drafts; could automate with an email service
5. **Minority channel identification for all committees**: Only added 5; some committees may have additional channels
6. **Video part deduplication**: Multi-part videos (Part 1, Part 2) inflate proceedings counts

---

## Conclusion

This project demonstrates that AI can build practical, data-driven tools for congressional transparency. The dashboard surfaces a real problem — that 99% of House committee YouTube proceedings lack the Event ID needed for the Library of Congress to index them — and provides actionable data to fix it. The CSV export directly addresses the Congressional Data Task Force's need for backfill data for prior years.

The biggest technical challenges were data quality (ensuring the right YouTube channels were tracked with the right handles) and data engineering (managing concurrent API calls and database access). The biggest design challenge was ensuring the dashboard would be credible to DC stakeholders who know their own data intimately — a problem addressed through two rounds of expert review.
