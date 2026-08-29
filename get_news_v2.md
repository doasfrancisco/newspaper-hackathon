# Get the news from X and print it as a newspaper (v2)

v1 (`get_news.md`) ends with a written report in the chat. v2 ends with a
one-page HTML newspaper on a URL. The steps that collect the posts do not
change. Only the last part changes.

The rule of v2: **the model chooses the posts, a script draws the page.**
The model writes one small JSON file. Everything after that is deterministic.
The same JSON always gives the same HTML, and it takes less than a second.

## The file tree

```
news/
  seen_ids.json
  2026-08-19_2224/
    raw_batch_1..4.json
    timeline.json
    images/
    keepers.json        <- NEW, written by the model
    paper/
      index.html        <- NEW, written by the script
templates/
  frontpage.html        <- the 1980s design, with {{SLOT}} tokens
build_newspaper.py      <- NEW, the deterministic builder
serve_paper.sh          <- NEW, the tailnet host
send_paper.py           <- NEW, the Resend mailer
```

## Steps 1 to 8: no change

Do steps 1 to 8 of `get_news.md` exactly as they are:

1. Read `taste.md`.
2. Make the run folder: `mkdir -p news/$(date +%Y-%m-%d_%H%M)`.
3. Open the proxy browser with `playwright_open`. Stop if the exit IP is
   wrong. See `residential_proxy.md`.
4. Load `https://x.com/home`, wait 4 s, then scroll to the bottom and wait
   3 s, three times.
5. Save the four `HomeTimeline` response bodies as
   `<run_dir>/raw_batch_1..4.json`.
6. Call `playwright_close`.
7. Run `python3 parse_tweets.py <run_dir>`. Run it one time only.
8. Run `python3 fetch_images.py <run_dir>`.

## Step 9: make the compact list

Print one line for each post from `<run_dir>/timeline.json`: position,
handle, the first 280 characters, and the media types. Use a small inline
Python script. Do not read the full JSON into context.

## Step 10: choose the keepers

Use the LIKE and SKIP lists of `taste.md`, the same as v1 step 10. A post
stays only when it shows a new, concrete artifact.

The page holds **24 posts**. Choose 24. If the run gives fewer, the empty
slots are removed. If it gives more, keep the best 24 and drop the rest.

## Step 11: write `keepers.json`

This is the only file the model writes. Put it at `<run_dir>/keepers.json`.

```json
{
  "run": "2026-08-19_2224",
  "date_line": "WEDNESDAY, AUGUST 19, 2026",
  "posts_read": 127,
  "lead": {
    "position": 119,
    "handle": "pbshgthm",
    "section": "ENGINEERING WRITE-UPS AND LEARNING",
    "headline": "A Single Skill Took Claude Code to a Perfect Score on the ARC-AGI-3 Benchmark",
    "body": "Two or three sentences of real facts from the post.",
    "stats": [
      {"label": "GAMES FINISHED", "value": "25 of 25"},
      {"label": "LEVELS FINISHED", "value": "183 of 183"},
      {"label": "RHAE, THE TOP SCORE", "value": "100.00 of 100"}
    ]
  },
  "secondary": [
    {"position": 105, "handle": "cjc", "section": "AI-BUSINESS CONTENT",
     "headline": "Stripe Is Buying OpenRouter"},
    {"position": 126, "handle": "superwhisper", "section": "NEW AI MODELS",
     "headline": "Superwhisper Opens the Weights on S1-Mini"},
    {"position": 116, "handle": "GeneralistAI", "section": "ROBOTICS AND HARDWARE",
     "headline": "A One-Shot Learner for the Physical World"}
  ],
  "digest": [
    {"section": "TOOLS THAT CONNECT TO AI AGENTS",
     "handles": ["Benioff", "ClaudeDevs", "jasonzhou1993", "charlieholtz"],
     "note": "One line about the strongest item in this group."},
    {"section": "RELEASES AND DEVELOPER TOOLS",
     "handles": ["RobKnight__", "rauchg", "VictorTaelin", "nutlope"],
     "note": "One line about the strongest item in this group."}
  ],
  "wire": [
    {"handle": "cursor_ai", "note": ""},
    {"handle": "linear", "note": ""},
    {"handle": "notrab", "note": "One line, or an empty string."}
  ]
}
```

Rules for the fields:

| Field | Limit | Note |
|---|---|---|
| `headline` (lead) | 80 characters | The layout is fixed. Longer text is cut. |
| `headline` (secondary) | 46 characters | |
| `body` | 700 characters | |
| `stats` | exactly 3 | Label 22 characters, value 16. |
| `note` | 92 characters | An empty string is allowed. |
| `section` | Use the six names of `get_news.md` step 12, in capitals. |
| `handle` | No `@`. The script adds it. |

Counts: 1 lead, 3 secondary, 2 digest groups of 4 handles, 12 wire items.
1 + 3 + 8 + 12 = 24.

Take every fact from `<run_dir>/timeline.json`. Do not invent a product, a
number, or a link.

## Step 12: build the page

```
python3 build_newspaper.py <run_dir>
```

The script:

1. Reads `<run_dir>/keepers.json` and `templates/frontpage.html`.
2. Replaces each `{{SLOT}}` token with its value, escaped for HTML.
3. Cuts any string that is longer than its limit and adds an ellipsis.
4. Removes the block of a slot that has no value.
5. Embeds the lead image from `<run_dir>/images/` as a base64 data URI, so
   the page is one file with no external assets.
6. Writes `<run_dir>/paper/index.html`.

The script calls no model and reaches no network. It always gives the same
output for the same input.

## Step 13: host it on the tailnet

```
./serve_paper.sh <run_dir>
```

It copies `<run_dir>/paper/index.html` to the served folder and starts
`python3 -m http.server 8899 --bind 0.0.0.0` in the background.

Read the tailnet address of this machine with `tailscale ip -4`. The URL is
`http://<tailnet-ip>:8899/`.

The port is open on the tailnet only. The VPS firewall blocks it from the
internet. Every device with the VPN on can open the URL.

## Step 14: report

Report these lines only. **Do not write the news in the chat.**

```
Run:      news/2026-08-19_2224
Read:     127 posts, 24 kept
Page:     news/2026-08-19_2224/paper/index.html
URL:      http://<tailnet-ip>:8899/
Mail:     sent to <recipient>
Skipped:  funding and VC, hot takes, memes, personal posts
```

If the user asks for a post in full, read it from `<run_dir>/timeline.json`
and show it as a block quote.

## Step 15: email the front page

```
python3 send_paper.py <run_dir>
```

The script reads `<run_dir>/keepers.json`, makes
`<run_dir>/paper/frontpage.pdf` from the page if it is not there yet, and
sends it through Resend as an attachment. The body of the mail holds the
lead, the three secondary headlines, and the counts. Add `--dry-run` to
print the payload and send nothing.

`.env` holds the settings. `.gitignore` excludes that file.

| Key | Note |
|---|---|
| `RESEND` | The API key. |
| `MAIL_TO` | The recipient. |
| `MAIL_FROM` | `onboarding@resend.dev` until a domain is verified. |
| `PAPER_URL` | Optional. A link in the mail body. |

A Resend account with no verified domain sends only from
`onboarding@resend.dev` and only to the address that owns the account. To
mail any other address, verify a domain first.

## Optional: a PDF

```
chromium --headless --disable-gpu --no-pdf-header-footer \
  --print-to-pdf=<run_dir>/paper/frontpage.pdf \
  <run_dir>/paper/index.html
```

The template has an `@page` rule of 1400 x 2120 px with no margin, thus the
PDF is one page at the size of the design.

## Optional: Convex

Convex gives the page a permanent public URL, so you do not need the VPN.

Three files, and no change to the Python:

```
convex/schema.ts      one table, editions, indexed by runId
convex/editions.ts    publish (upsert), byRun, latest
convex/http.ts        GET /paper/:runId and GET /paper/latest
```

Deploy one time:

```
CONVEX_DEPLOY_KEY=... npx convex deploy
```

Publish after step 12:

```
npx convex run editions:publish --push "$(python3 - "$RUN_DIR" <<'PY'
import json, sys, pathlib
d = pathlib.Path(sys.argv[1])
k = json.loads((d / "keepers.json").read_text())
print(json.dumps({
    "runId": k["run"],
    "dateLine": k["date_line"],
    "postsRead": k["posts_read"],
    "keptCount": 24,
    "html": (d / "paper" / "index.html").read_text(),
}))
PY
)"
```

The page is then at `https://<deployment>.convex.site/paper/<runId>`, and the
newest one is always at `/paper/latest`.

Keep the deploy key in `.env.local`. `.gitignore` excludes that file.

Convex cannot do steps 3 to 6. Its functions run in a datacentre, thus their
IP has the `hosting` class that X rejects. The browser stays on the VPS.
