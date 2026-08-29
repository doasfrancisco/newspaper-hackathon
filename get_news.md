# Get the news from X with the user's taste

This document tells you how to read the X home timeline and report the new
posts that match the user's taste. The procedure worked on 2026-08-15 and
gave 122 new posts in one run.

## The file tree

```
news/
  seen_ids.json          <- all tweet ids from all runs
  taste_pool/            <- the old pool that trained taste.md
    raw_batch_1..4.json
    timeline.json
    images/
  2026-08-14_2221/       <- one folder per run: date + time (local, HHMM)
    raw_batch_1..4.json  <- the raw API responses
    timeline.json        <- the parsed posts of this run
    images/              <- the images of this run
      003_thdxr/1.jpg
      010_dok2001/quoted_1.jpg
```

- `taste.md` — the user's taste profile. Read it fully before you start.
- `reading_tweets_via_api.md` — the full reference for the timeline API,
  the parser rules, and the presentation rules.
- `parse_tweets.py` — the parser. Usage: `python3 parse_tweets.py <run_dir>`.
- `fetch_images.py` — the image downloader. Usage:
  `python3 fetch_images.py <run_dir>`.

## Step 1: Read the taste profile

1. Read `taste.md`.
2. Learn the LIKE list: new AI models, tools that connect to AI agents,
   product launches with substance, developer tools and releases,
   engineering write-ups, learning content, asset collections,
   AI-business playbooks, and robotics.
3. Learn the SKIP list: funding and VC news, anecdotes without an
   artifact, hot takes, vendor gossip, politics, memes, and personal
   posts.
4. Keep the key rule in mind: a post must show a NEW, concrete artifact
   that the user can use, try, collect, or learn from.

## Step 2: Make the run folder

1. Make a new folder with the local date and time:
   `mkdir -p news/$(date +%Y-%m-%d_%H%M)`.
2. The time part makes each run unique, so two runs on the same day get
   two folders.

## Step 3: Open the proxy browser

1. Load the tool schemas with ToolSearch:
   `playwright_open`, `playwright_close`, `browser_navigate`,
   `browser_wait_for`, `browser_evaluate`, `browser_network_requests`,
   `browser_network_request`.
2. Call `playwright_open` before all other browser tools.
3. Read the result. Continue only if `ok` is true and `exit_ip` is
   `<PROXY_EXIT_IP>`.
4. Stop if the IP is not correct. Do not use the browser tools then.

## Step 4: Load the timeline and collect four batches

1. Navigate to `https://x.com/home`.
2. Wait 4 seconds.
3. Scroll to the bottom with
   `window.scrollTo(0, document.body.scrollHeight)`.
4. Wait 3 seconds.
5. Do the scroll and the wait two more times (three scrolls in total).
6. Each scroll near the end of a batch causes one more `HomeTimeline`
   request. One load plus three scrolls gives about four batches.

Read only. Do not click, like, follow, or post.

## Step 5: Save the batch responses

1. List the network requests with the filter `HomeTimeline`.
2. You will see about four requests to
   `https://x.com/i/api/graphql/<hash>/HomeTimeline`.
3. Save the response body of each request with `browser_network_request`
   (`part: "response-body"`).
4. Use the file names `<run_dir>/raw_batch_1.json` to
   `<run_dir>/raw_batch_4.json`, in request order.

## Step 6: Close the browser

1. Call `playwright_close`.
2. This sends SIGTERM, so the browser writes the session cookies.

## Step 7: Parse the new posts

1. Run `python3 parse_tweets.py <run_dir>`.
2. The script reads all `raw_batch_*.json` files in the run folder.
3. It removes ads, cursors, and duplicate posts.
4. It removes posts with an id that is already in `news/seen_ids.json`.
5. It writes `<run_dir>/timeline.json` and prints the count of new posts.
6. It adds the new ids to `news/seen_ids.json`.

Caution: the script updates `news/seen_ids.json`. Do not run it two
times on the same run folder. The second run finds 0 new posts and
overwrites `timeline.json` with an empty list.

## Step 8: Get the images

1. Run `python3 fetch_images.py <run_dir>`.
2. The script downloads every image in `<run_dir>/timeline.json` to
   `<run_dir>/images/` and writes each `local_path` back into the JSON.
3. The folder name of each post is its position (3 digits) plus the
   author handle. Files with a `quoted_` prefix belong to the quoted
   post.
4. The script skips files that exist, so a second run is safe.

## Step 9: Make a compact list for review

1. Print one line for each post from `<run_dir>/timeline.json`:
   position, handle, the first 280 characters of the text, the media
   types, and the quoted text if there is one.
2. Use a small inline Python script for this. Do not read the full JSON
   into context.

## Step 10: Select the posts that match the taste

Compare each line with the profile in `taste.md`.

Keep a post when it shows:
- A new AI model launch (open weights is a plus).
- A tool that connects to AI agents (Claude Code, Codex, Cursor,
  harnesses, agent proxies, agent memory).
- A version release of a developer tool or library.
- A product or startup launch with substance.
- An engineering write-up or a learning post with a link.
- A robotics or hardware product with real innovation.
- AI-business content that helps the user's AI factory.
- A free asset collection or build resource.

Drop a post when it shows:
- Funding, valuation, VC, or investment news.
- An anecdote, reaction, or praise without the artifact itself.
- Model hot takes, vendor gossip, or drama.
- Politics, memes, jokes, anime, or personal posts.
- Workflow advice about tools the user already knows.

Rules for edge cases:
- A reaction post that quotes a launch: keep it, and link the quoted
  launch post as the artifact.
- An acquisition that changes tools the user works with: you can add it
  as one separate news item, with a note about why you include it.
- Novelty decides ties. The user's phrase is "I haven't seen it yet".
- Expect about 20 to 30 keepers from 122 posts.

## Step 11: Get the links

1. Print the `url` of each selected post from `<run_dir>/timeline.json`.
2. Print the `quoted` post `url` too when there is one.

## Step 12: Write the report

Group the keepers under these headings, in this order:

1. New AI models
2. Tools that connect to AI agents
3. Releases and developer tools
4. Engineering write-ups and learning content
5. Robotics and hardware
6. AI-business content for the AI factory
7. Update on a story from the last run (optional, for follow-ups to
   posts you reported before)
8. Large news items (optional, with a note about why you include them)

Show each post as a compact summary, not as a verbatim quote. Use this
template for each post:

```markdown
**[@handle](https://x.com/handle/status/<id>)** — the artifact in one
line: what it is and why it matters to the user.
Summary: two or three sentences with the key facts of the post: what is
new, the mechanism, the numbers, and the external links (GitHub,
product site) that the post text contains.
Quote: one line about the quoted post, with its x.com link, when the
quote holds the artifact.
Media: one line about the images or the video.
```

Rules for the template:

1. Keep each post block to five lines or fewer. The goal is a short
   report that can hold many posts.
2. Keep the external links from the post text (GitHub, product site,
   blog) in the summary. These links are the artifact.
3. Read every image at its `local_path` before you write the media
   line. Mention only the images that add information, with their
   paths.
4. When the video or image belongs to the quoted post, link the quoted
   post, not the outer post.
5. Never show raw `video.twimg.com` URLs. The video link is always the
   x.com URL of the post that holds it.
6. Separate posts inside one section with a `---` line.
7. When a post follows up a story from an earlier run, put it under
   "Update on a story from the last run" instead of a normal section.
8. When the user asks for the full text of a post, read it from
   `<run_dir>/timeline.json` and show it verbatim as a block quote.

Show only the posts that pass the filter. Do not add a section for the
borderline posts or for the drops.

Close the report with a short note: the run folder path, the counts
(new posts, keepers), and what types of posts you skipped.

## Step 13: Leave the other data unchanged

- Do not change `taste.md`, `news/taste_pool/`, or the folders of the
  earlier runs.
- Each run only adds one folder and adds ids to `news/seen_ids.json`.
