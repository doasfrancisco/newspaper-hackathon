# Read the X Home Timeline through the browser API

This document explains how many posts you can read from the X Home Timeline
without a scroll, and how the posts are read from the timeline API through
the residential proxy.

## Result

One page load gives you about **35 posts** with no scroll.

- The API batch for one load held **35 posts**: 31 organic posts and 4 ads.
- The response also held 2 pagination cursors (top and bottom).
- The page shows only about **5 posts** at one time. The list is virtualized.
- All 35 posts are in browser memory. A scroll only draws more of them. A new
  network request starts when you come near the end of the batch.

## The setup

The browser is a Chromium that already runs on this machine. It has a
logged-in x.com session. Playwright attaches to it through CDP at
`127.0.0.1:9222`. The browser sends all its traffic through a SOCKS5 proxy
chain.

You do not send API requests yourself. The X web app sends them. You read the
response that the browser already received.

## The residential proxy

All traffic goes out through the SOCKS5 chain. The chain must exit at IP
`<PROXY_EXIT_IP>` (your residential proxy exit).

The check is a navigation to `https://ipinfo.io/json`. The browser makes the
request, so the result shows the proxy exit IP, not the machine IP.

```json
{ "ip": "<PROXY_EXIT_IP>", "city": "<CITY>", "region": "<REGION>",
  "country": "<CC>", "org": "<ISP>",
  "timezone": "<TZ>" }
```

The IP is correct. Every x.com request in this work went through the same
browser, so every request used the proxy.

Note: an in-page `fetch()` to `ipinfo.io` from the x.com origin fails with a
CORS error. Use a navigation to `ipinfo.io`, not a fetch from the x.com page.

## Steps to read the posts

1. Confirm the proxy exit IP first.
   - Navigate to `https://ipinfo.io/json`.
   - Take a snapshot and read the `ip` field.
   - Stop if the IP is not `<PROXY_EXIT_IP>`.

2. Load the timeline.
   - Navigate to `https://x.com/home`.
   - Wait about 4 seconds for the page to load.
   - This one load causes one `HomeTimeline` GraphQL request.

3. Find the timeline request in the network log.
   - List network requests and filter for `HomeTimeline`.
   - The endpoint is a POST to
     `https://x.com/i/api/graphql/<hash>/HomeTimeline`.
   - The `<hash>` part changes between app versions.

4. Read the response body.
   - Get the response body of that request.
   - Save it to a file. The body is about 290 KB.

5. Parse the posts from the JSON.
   - Path to the entries:
     `data.home.home_timeline_urt.instructions`.
   - Find the instruction with `type == "TimelineAddEntries"`.
   - Read its `entries` list.
   - Entry ids that start with `tweet-` are posts.
   - Entry ids that start with `promoted-` are ads.
   - Entry ids that start with `cursor-` are pagination cursors.

6. Read each post.
   - For a post entry, go to
     `content.itemContent.tweet_results.result`.
   - A quote or ad can nest the post under a `tweet` key. Use `tweet` if it
     is present.
   - The handle is at `core.user_results.result.core.screen_name`.
   - The text is at `legacy.full_text`.
   - A key `promotedMetadata` in `itemContent` marks an ad.

## How to read more posts

- The 35 posts come from one batch. To get the next batch, use the bottom
  cursor value in a new `HomeTimeline` request, or scroll to the end of the
  batch and let the app fetch more.
- Read only. Do not click, like, follow, or post.

## Tools used

The work used the Playwright MCP tools against the CDP browser:

- `browser_navigate` — go to a URL.
- `browser_snapshot` — read the page as an accessibility tree.
- `browser_wait_for` — wait for the load.
- `browser_network_requests` — list and filter the network log.
- `browser_network_request` — read one request, headers or body.
- `browser_evaluate` — run JavaScript in the page (for the DOM count).

## How to collect about 100 tweets

One page load gives one batch of about 35 posts. To get more batches:

1. Load `https://x.com/home` and wait about 4 seconds.
2. Scroll to the bottom of the page with
   `window.scrollTo(0, document.body.scrollHeight)` and wait about 3 seconds.
3. Do the scroll 3 times. Each scroll near the end of a batch causes one more
   `HomeTimeline` request.
4. Save the response body of each `HomeTimeline` request to a
   `<run_dir>/raw_batch_N.json` file.
5. Run `parse_tweets.py <run_dir>`. It reads all `raw_batch_*.json` files in
   the run folder, removes ads and duplicate posts, and writes
   `<run_dir>/timeline.json`.

Four batches gave 122 unique posts.

## The file tree (`news/`)

Each timeline read is one run. Each run has its own folder:

```
news/
  seen_ids.json          <- all tweet ids from all runs
  taste_pool/            <- the old pool that trained taste.md
    raw_batch_1..4.json
    timeline.json
    images/
  2026-08-14_2221/       <- one folder per run: date + time (local, HHMM)
    raw_batch_1..4.json
    timeline.json
    images/
```

`news/seen_ids.json` is a JSON list of tweet ids. The parser reads it to
remove posts that an earlier run already saw, and writes the new ids back.

## The parser (`parse_tweets.py`)

Usage: `python3 parse_tweets.py <run_dir>`.

The parser applies these rules:

- It removes ads (`promotedMetadata`) and pagination cursors.
- It removes duplicate posts across batches (same tweet id).
- It removes posts with an id in `news/seen_ids.json`, and it adds the new
  ids to that file. Do not run it two times on the same run folder: the
  second run writes an empty `timeline.json`.
- It expands each `t.co` link to the real URL. This includes links inside
  long-form (note) tweets, which keep their URL entities in
  `note_tweet.note_tweet_results.result.entity_set.urls`.
- For a repost, it unwraps the inner tweet and records `reposted_by`.
- For a quote, it stores the full quoted tweet under `quoted`.
- For long-form tweets, it reads the full text from
  `note_tweet.note_tweet_results.result.text`.
- For each image, it stores the `pbs.twimg.com` URL.
- For each video or GIF, it stores the best-bitrate MP4 URL and the thumbnail.

Each tweet object also has `liked_by_me` (true / false / null) for the taste
review, and each video has `x_link` — the x.com URL of the tweet that holds
the video.

## Images on disk (`fetch_images.py`)

Usage: `python3 fetch_images.py <run_dir>`.

`fetch_images.py` downloads every image in `<run_dir>/timeline.json` to
`<run_dir>/images/` and writes the `local_path` back into the JSON:

```
news/2026-08-14_2221/images/
  003_thdxr/
    1.jpg             <- image 1 of the tweet itself
  010_dok2001/
    quoted_1.jpg      <- image 1 of the quoted tweet
  023_IntCyberDigest/
    1.jpg
    2.jpg
```

- The folder name is the tweet position in the JSON (3 digits) plus the
  author handle. The position is the same number used in the review batches.
- Files named `1.jpg`, `2.png`, ... are the tweet's own images.
- Files named `quoted_1.jpg`, ... are images of the quoted tweet.
- The script skips files that already exist, so a second run is safe.

## How to show tweets to the user

Follow these presentation rules (the full report template is in
`get_news.md`, step 12):

1. Make the handle a link to the tweet:
   `**[@bykahlil](https://x.com/bykahlil/status/<id>)**`.
2. Show the full tweet text verbatim as a block quote. Do not summarize
   it. Keep the expanded links inside the text.
3. For a quote or repost, show the full inner tweet text too, nested
   one level deeper, with the inner author as a link.
4. Do not show raw `video.twimg.com` URLs. For a video, link the x.com
   URL of the tweet that holds it.
5. For an image, read the file at `local_path`, describe the content, and
   show the local path so the user can find the file.
6. If the tweet points to long-form content (an essay, a blog post), show the
   expanded link.
