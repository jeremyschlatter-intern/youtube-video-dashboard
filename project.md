## Dashboard for YouTube Videos
As mentioned in *Unified Hearing & Markup Data*, House committees do not always put the event ID on Youtube videos. (The Senate doesn't publish their proceedings on YouTube.)

The purpose is to either encourage committees to put event IDs in their video descriptions on youtube or alert committees when they've failed to do so.

We should track all the various committee youtube videos and crosscheck them against official event id information either from congress.gov (API?) or docs.house.gov. 

There should be a dashboard that lists all committee names. Under each committee it should indicate how many proceedings the committee has held and whether the youtube video includes the event ID. (If it does not, the video won't show up on congress.gov). We can match the existence of the videos by looking at the date of the video and its title and fuzzy match against official notice of hearings from the committee. Probably should look at video length to make sure it's the full proceeding.

You then want the dashboard that does a few thing
* Ranks committee consistency of putting event ids on videos. Committees with the highest consistency get a good grade, those with low consistency get a bad grade.

* Also consider a feature where once a week the committee is emailed with a list of videos that don't have event IDs, with a link to the youtube page for the video and the event ID they should include.

At the June 2025 Congressional Data Task Force Meeting, the Library of Congress was able to use a tool created by the House Digital Service to identify unlabeled youtube videos with the proper event ID. However, HDS only could provide the data for 2025. This process needs to be run for prior years and provided to the Library for incorporation. We likely will not need this to work for the House in the future.
