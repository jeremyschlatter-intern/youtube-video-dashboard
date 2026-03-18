# Research Findings: House Committee YouTube Channels & Event IDs

## 1. House Committee YouTube Channels

Many House committees maintain YouTube channels, often split between Majority (Republican, in the 119th Congress) and Minority (Democrat) channels. Below is the most comprehensive list I could compile.

### Verified Committee YouTube Channels

| Committee | Channel Name | Handle | Channel URL | Party |
|-----------|-------------|--------|-------------|-------|
| Appropriations | House Appropriations Committee | @HouseAppropriationsCommittee | youtube.com/channel/... | Majority |
| Armed Services | U.S. House Armed Services Committee | @HouseArmedServices | youtube.com/channel/UCD506yORW2voSanqEgLOUIQ | Majority |
| Agriculture | House Committee on Agriculture | @AgRepublicans | youtube.com/channel/UCWtWf-QUTnJ-UMP5ZNWVB5Q | Majority |
| Education & Workforce | House Committee on Education & Workforce | @EdWorkforceCmte | youtube.com/channel/UC8Ewe7WqGg01KRNjJCO5cjg | Majority |
| Energy & Commerce | House Committee on Energy and Commerce | @energyandcommerce | youtube.com/channel/... | Majority |
| Financial Services | U.S. House Committee on Financial Services | @USHouseFSC | youtube.com/channel/UCiGw0gRK-daU7Xv4oDMr9Hg | Majority |
| Foreign Affairs | House Foreign Affairs Committee Republicans | @HouseForeignGOP | youtube.com/channel/UCtxAmeCl0xtSuo7tHZpgcQA | Majority |
| Homeland Security | Homeland Security Committee Events | @HouseHomeland | youtube.com/channel/UChdT2snPVxfp2m8n4VDdMag | Majority |
| House Administration | Committee on House Administration | @CommitteeonHouseAdministration | youtube.com/channel/UC8dXTgFnWF8NraBKhF040Qg | Majority |
| Intelligence | House Intelligence | @HouseIntel | youtube.com/channel/UCMF5z6BIrwwQTtcj2cacBPw | Majority |
| Judiciary (GOP) | House Judiciary GOP | @USHouseJudiciaryGOP | youtube.com/channel/... | Majority |
| Judiciary (Dems) | House Committee on the Judiciary | @JudiciaryDems | youtube.com/channel/UCVvv3JRCVQAl6ovogDum4hA | Minority |
| Natural Resources | House Committee on Natural Resources GOP | @NaturalResourcesGOP | youtube.com/channel/UCY08wEbJ8fztRofQ9eZs0-g | Majority |
| Oversight & Accountability | GOP Oversight | @OversightandGovernmentReform | youtube.com/channel/UCn8TJ6Tyq2aGvhybME_itDQ | Majority |
| Rules | HouseRules | @HouseRulesCommittee | youtube.com/channel/UCDNcorctkmOpBfr4sgu6t3w | Majority |
| Science, Space & Tech | House Science, Space, and Technology Committee | @housescience | youtube.com/channel/UCtoUE3dJ-mLUo5dwGs7hXOw | Majority |
| Small Business | House Committee on Small Business | @HouseSmallBiz | youtube.com/channel/UCoXvuW2IhFawuNyk4yL3EkQ | Majority |
| Transportation & Infrastructure | House Transportation & Infrastructure Committee | @transportdems | youtube.com/channel/UChc8bTPtZgTZDDLJ6UWJgxA | Minority |
| Veterans' Affairs | House Committee On Veterans' Affairs | @HouseVeteransAffairs | youtube.com/channel/UCvI8xjyh45-XAJbfPcjUdbQ | Majority |
| Ways & Means | Ways and Means Committee Republicans | @WaysandMeansCommittee | youtube.com/channel/... | Majority |
| Budget | House Budget Committee GOP | @HouseBudgetGOP | youtube.com/channel/UCHPaSWprI94UTePSMv0tqnw | Majority |

### Committees Without Found YouTube Channels
- Ethics Committee (no public YouTube channel found)
- Some minority-party channels not yet discovered

### Key Observations About Channels
- Most committees have a Majority (controlling party) channel that posts full hearings as livestreams
- Some committees also have a Minority channel (e.g., Judiciary has both @USHouseJudiciaryGOP and @JudiciaryDems)
- The Majority channel typically posts the official full-length hearing recordings
- Minority channels sometimes post clips, opening statements, or their own versions of full hearings
- Some channels post both short clips AND full hearings; distinguishing them requires checking video duration (full hearings typically >30 minutes, often multiple hours)

---

## 2. How YouTube Descriptions Include (or Don't Include) Event IDs

### Committees That DO Include Event IDs

**Judiciary Democrats (@JudiciaryDems):**
Format: `Title | Type | Event ID: XXXXXX`
Example: `Oversight of the Department of Justice | Full Committee Hearing | Event ID: 118951`
- Uses pipe-separated format
- Includes meeting type (Full Committee Hearing, Subcommittee Hearing, etc.)
- Event ID clearly labeled with "Event ID:" prefix

**Appropriations (@HouseAppropriationsCommittee):**
Format: Committee name and subcommittee, then `(EventID=XXXXXX)` on a new line
Example:
```
House Committee on Appropriations, Subcommittee on Labor, Health and Human Services, Education, and Related Agencies

(EventID=119006)
```
- Uses parenthesized format with equals sign
- No space in "EventID"
- Appears at the end of the description

**Homeland Security (@HouseHomeland):**
Format: Title description then `| EventID=XXXXXX`
Example:
```
A House Committee on Homeland Security hearing entitled, "Highway Safety Under Threat..." | EventID=118972
```
- Uses pipe separator with "EventID=" format

**Armed Services (@HouseArmedServices):**
Format: Event ID embedded in a committee website URL
Example:
```
Learn more here: https://armedservices.house.gov/calendar/eventsingle.aspx?EventID=6408
```
- NOTE: This appears to be a different/internal event ID numbering system (4-digit vs 6-digit)

### Committees That DO NOT Include Event IDs (Sampled)
- **Judiciary GOP** (@USHouseJudiciaryGOP): Only includes website URL and social media links
- **Ways & Means** (@WaysandMeansCommittee): Completely empty descriptions
- **Energy & Commerce** (@energyandcommerce): Boilerplate committee description, no event ID
- **Education & Workforce** (@EdWorkforceCmte): Committee about page text, no event ID
- **Agriculture** (@AgRepublicans): Date/time/location info but no event ID
- **Veterans' Affairs** (@HouseVeteransAffairs): Hearing title only, no event ID
- **Science, Space & Tech** (@housescience): Has link to committee website but no event ID
- **Small Business** (@HouseSmallBiz): Description of hearing but no event ID
- **House Administration** (@CommitteeonHouseAdministration): Hearing description but no event ID
- **Rules** (@HouseRulesCommittee): Empty or minimal description
- **Transportation & Infrastructure** (@transportdems): Hearing title, no event ID
- **Budget** (@HouseBudgetGOP): Hearing details but no event ID
- **Financial Services** (@USHouseFSC): Empty description
- **Foreign Affairs GOP** (@HouseForeignGOP): Empty description
- **Natural Resources GOP** (@NaturalResourcesGOP): Empty description
- **Intelligence** (@HouseIntel): Hearing details but no event ID
- **Oversight GOP** (@OversightandGovernmentReform): Not sampled yet

### Summary of Event ID Inclusion Rates (from sampling)
- **Include Event IDs**: Judiciary Dems, Appropriations, Homeland Security, Armed Services (URL-embedded)
- **Do NOT include Event IDs**: ~12+ other committees
- **Approximate compliance**: ~20-25% of committees include Event IDs (3-4 out of ~20)

---

## 3. Event ID Format

### Official House Event IDs (docs.house.gov)
- **Format**: 6-digit number (e.g., 118951, 119006, 118972)
- **Source**: Assigned by docs.house.gov Committee Repository
- **URL pattern on docs.house.gov**: `https://docs.house.gov/Committee/Calendar/ByEvent.aspx?EventID=XXXXXX`
- **URL pattern on congress.gov**: `https://www.congress.gov/event/119th-congress/house-event/XXXXXX`
- **Range**: Current IDs are in the 118000-119000+ range for the 119th Congress

### How Event IDs Appear in YouTube Descriptions (When Present)
Three observed formats:
1. `Event ID: 118951` (Judiciary Dems - colon-separated, with space)
2. `(EventID=119006)` (Appropriations - parenthesized, equals sign, no space)
3. `EventID=118972` (Homeland Security - equals sign, no space, sometimes with pipe)

### Regex Pattern for Matching
To catch all observed formats:
```
Event\s*ID[\s:=]*(\d{5,6})
```

### Other Event ID Systems (Caution)
- Armed Services uses their own internal event ID system (e.g., EventID=6408) in armedservices.house.gov URLs -- these are NOT the same as docs.house.gov event IDs

---

## 4. YouTube Playlists

### Playlist Organization Patterns
- Most committee channels organize by the "Streams" tab (livestreamed hearings) vs. "Videos" tab (all uploads including clips)
- Some channels have dedicated playlists for specific Congresses, subcommittees, or hearing topics
- The "Streams" tab is generally the best way to find full-length hearing recordings
- Playlists are accessible at: `https://www.youtube.com/@ChannelHandle/playlists`

### Practical Implication
- To find full hearings, filter by the "streams" tab or by duration (>30 minutes)
- Short clips (<15 minutes) are typically member statements, not full proceedings

---

## 5. Programmatic Methods for Fetching YouTube Metadata

### yt-dlp (Recommended - No API Key Needed)

**Installation:**
```bash
pip install yt-dlp
```

**Fetch single video metadata (no download):**
```bash
yt-dlp --skip-download --print "%(title)s|%(upload_date)s|%(duration)s|%(description)s" "https://www.youtube.com/watch?v=VIDEO_ID"
```

**List all videos from a channel:**
```bash
yt-dlp --skip-download --flat-playlist --print "%(id)s|%(title)s" "https://www.youtube.com/@ChannelHandle/videos"
```

**List only livestreams (full hearings):**
```bash
yt-dlp --skip-download --flat-playlist --print "%(id)s|%(title)s|%(duration)s" "https://www.youtube.com/@ChannelHandle/streams"
```

**Get full metadata as JSON:**
```bash
yt-dlp --skip-download -j "https://www.youtube.com/watch?v=VIDEO_ID"
```

**Python usage:**
```python
import yt_dlp

opts = {'skip_download': True, 'quiet': True}
with yt_dlp.YoutubeDL(opts) as ydl:
    info = ydl.extract_info(url, download=False)
    # info['title'], info['description'], info['upload_date'], info['duration']
```

**Available metadata fields:**
- `title` - Video title
- `description` - Full description text (where Event IDs are found)
- `upload_date` - Date in YYYYMMDD format
- `duration` - Duration in seconds
- `channel` - Channel name
- `channel_id` - YouTube channel ID
- `id` - Video ID
- `view_count` - Number of views
- `like_count` - Number of likes
- `uploader_id` - Channel handle (@name)

**Performance notes:**
- Flat playlist mode (`--flat-playlist`) is fast for listing video IDs/titles
- Full metadata extraction requires one request per video
- A channel with ~1000+ videos can be enumerated in seconds with flat mode
- Rate limiting may occur with heavy use; adding delays between requests is recommended

### Alternative Methods

**youtube-search-python**: Python library for searching YouTube without API key, but less reliable for channel enumeration.

**YouTube Data API v3**: Requires an API key (free tier available with quota limits). More structured but has daily quota limits. Best for production use.

**Scraping/RSS**: YouTube RSS feeds at `https://www.youtube.com/feeds/videos.xml?channel_id=CHANNEL_ID` provide recent videos but limited to ~15 entries.

### Recommendation
**yt-dlp is the best option** for this project because:
1. No API key required
2. Can enumerate all videos in a channel (not just recent 15)
3. Extracts full descriptions including Event IDs
4. Returns structured data (title, date, duration, description)
5. Active open-source project with regular updates
6. Works well for batch processing

---

## 6. Data Source for Official Event Information

### docs.house.gov Committee Repository
- URL: `https://docs.house.gov/Committee/Calendar/ByDay.aspx?DayID=MMDDYYYY`
- Contains all scheduled meetings with Event IDs
- HTML can be scraped to extract Event IDs, committee names, dates, and meeting types
- Example: For Feb 11, 2026, returns 14 events including EventID=118951

### congress.gov API
- Endpoint: `https://api.congress.gov/v3/committee-meeting/{congress}/{chamber}?api_key=KEY`
- Requires API key (free, apply at api.congress.gov)
- Returns JSON/XML with meeting details
- Fields include: event ID, committee, date, title, meeting type
- Rate limited

### Matching Strategy
To cross-reference YouTube videos with official events:
1. **Date matching**: Match `upload_date` from YouTube with meeting dates from docs.house.gov
2. **Title/topic fuzzy matching**: Compare video titles with hearing titles
3. **Committee matching**: Map YouTube channel to committee code
4. **Duration filtering**: Filter out short clips (< 30 min) to find full proceedings
5. **Event ID extraction**: Use regex `Event\s*ID[\s:=]*(\d{5,6})` on descriptions
