# Template slots

`templates/frontpage.html` holds 82 tokens and 29 removable blocks.
It holds no run copy. Every word that changes from run to run is a token.

`build_newspaper.py` reads `<run_dir>/keepers.json`, fills the tokens and
writes `<run_dir>/paper/index.html`.

## Two limits differ from get_news_v2.md

The spec gives two limits that the design cannot hold. Both are named
constants at the top of `build_newspaper.py`.

| Field | Spec | Used | Why |
|---|---|---|---|
| `lead.body` | 700 | 1950 | The three-column well holds about 1,950 characters. At 700 the well stays two thirds empty. |
| `wire[].note` | 92 | 130 | The wire slot is 300 px wide and 3 lines deep. It holds about 130 characters. At 92 eight of the twelve notes are cut in the middle of a sentence. |

Set `LEAD_BODY_LIMIT = 700` and `WIRE_NOTE_LIMIT = 92` to follow the spec exactly.
All other limits are the spec values.

## Fields the spec does not give

The design has copy that `keepers.json` in the spec has no field for.
These fields are added. They are optional. An absent field leaves the slot
empty and the builder removes its block.

| Field | Limit | What it is |
|---|---|---|
| `paper_name` | 24 | Masthead wordmark. Default `THE TIMELINE`. |
| `city` | 28 | Folio city. No default. |
| `vol`, `no`, `price` | 8, 8, 12 | Folio furniture. |
| `digest_note` | 92 | The italic line under 'The Digest'. |
| `lead.deck` | 260 | The italic standfirst. |
| `lead.stats_caption` | 200 | The caption under the stat table. |
| `lead.image` | - | Path of the lead photo, relative to `<run_dir>`. |
| `secondary[].body` | 560 | The body of a secondary item. A string, or a list of 2 strings. |
| `digest[].items` | - | A list of 4 `{handle, note}`. The spec gives `handles` and one group `note`; both forms work. |
| `desk_note` | 320 each | A list of 2 strings for the boxed note. |
| `source_line` | 64 | The byline source. Derived from `run` when absent. |

`lead.body` and `secondary[].body` take a string or a list. A string is cut
to the limit and then split on word boundaries, 3 parts for the lead and 2
for a secondary item. A list is used part for part.

## Every token

| Token | Limit | keepers.json field | Where it prints |
|---|---|---|---|
| `{{CITY}}` | 28 | `city` | Folio, third cell. |
| `{{DATE_LINE}}` | 40 | `date_line` | Folio, centre. Also the page title. |
| `{{DESK_NOTE_1}}` | 320 | `desk_note[0]` | Desk note, left column. |
| `{{DESK_NOTE_2}}` | 320 | `desk_note[1]` | Desk note, right column. |
| `{{DIGEST1_H1}}` | 24 | `digest[0].items[0].handle` | Digest handle. The template adds `@`. |
| `{{DIGEST1_H2}}` | 24 | `digest[0].items[1].handle` | Digest handle. The template adds `@`. |
| `{{DIGEST1_H3}}` | 24 | `digest[0].items[2].handle` | Digest handle. The template adds `@`. |
| `{{DIGEST1_H4}}` | 24 | `digest[0].items[3].handle` | Digest handle. The template adds `@`. |
| `{{DIGEST1_SECTION}}` | 46 | `digest[0].section` | Digest group 1 kicker. |
| `{{DIGEST1_T1}}` | 160 | `digest[0].items[0].note` | Digest note, 370 px, 2 lines. |
| `{{DIGEST1_T2}}` | 160 | `digest[0].items[1].note` | Digest note, 370 px, 2 lines. |
| `{{DIGEST1_T3}}` | 160 | `digest[0].items[2].note` | Digest note, 370 px, 2 lines. |
| `{{DIGEST1_T4}}` | 160 | `digest[0].items[3].note` | Digest note, 370 px, 2 lines. |
| `{{DIGEST2_H1}}` | 24 | `digest[1].items[0].handle` | Digest handle. The template adds `@`. |
| `{{DIGEST2_H2}}` | 24 | `digest[1].items[1].handle` | Digest handle. The template adds `@`. |
| `{{DIGEST2_H3}}` | 24 | `digest[1].items[2].handle` | Digest handle. The template adds `@`. |
| `{{DIGEST2_H4}}` | 24 | `digest[1].items[3].handle` | Digest handle. The template adds `@`. |
| `{{DIGEST2_SECTION}}` | 46 | `digest[1].section` | Digest group 2 kicker. |
| `{{DIGEST2_T1}}` | 160 | `digest[1].items[0].note` | Digest note, 370 px, 2 lines. |
| `{{DIGEST2_T2}}` | 160 | `digest[1].items[1].note` | Digest note, 370 px, 2 lines. |
| `{{DIGEST2_T3}}` | 160 | `digest[1].items[2].note` | Digest note, 370 px, 2 lines. |
| `{{DIGEST2_T4}}` | 160 | `digest[1].items[3].note` | Digest note, 370 px, 2 lines. |
| `{{DIGEST_NOTE}}` | 92 | `digest_note` | Italic line under 'The Digest'. |
| `{{LEAD_BODY_1}}` | 1950 shared | `lead.body` part 1, less the drop cap | Body column 1, 219 px. |
| `{{LEAD_BODY_2}}` | 1950 shared | `lead.body` part 2 | Body column 2, 258 px. |
| `{{LEAD_BODY_3}}` | 1950 shared | `lead.body` part 3 | Body column 3, 258 px. |
| `{{LEAD_CAPTION}}` | 200 | `lead.stats_caption` | Italic caption under the stat table. |
| `{{LEAD_DECK}}` | 260 | `lead.deck` | Italic standfirst under the lead headline. |
| `{{LEAD_DROPCAP}}` | 1 | first character of `lead.body` | The drop cap. The builder splits it off. |
| `{{LEAD_HANDLE}}` | 24 | `lead.handle` | Byline. The template adds `BY @`. |
| `{{LEAD_HEADLINE}}` | 80 | `lead.headline` | Lead headline, 68 px. |
| `{{LEAD_IMAGE}}` | no limit (binary) | `lead.image` | Lead photo. Base64 data URI. Fills the space left under the jump line. |
| `{{LEAD_SECTION}}` | 46 | `lead.section` | Red kicker over the lead headline. |
| `{{LEAD_SOURCE}}` | 64 | `source_line`, else derived from `run` | Byline, right side. |
| `{{NO}}` | 8 | `no` | Folio, first cell. |
| `{{PAPER_NAME}}` | 24 | `paper_name` | Masthead wordmark, both plates, and the left footer. |
| `{{POSTS_READ}}` | 8 | `posts_read` | Footer, centre. |
| `{{PRICE}}` | 12 | `price` | Folio, right cell. |
| `{{RUN_ID}}` | 24 | `run` | Footer, centre. |
| `{{SEC1_BODY_1}}` | 560 shared | `secondary[0].body` part 1 | Sidebar paragraph 1, 408 px. |
| `{{SEC1_BODY_2}}` | 560 shared | `secondary[0].body` part 2 | Sidebar paragraph 2, 408 px. |
| `{{SEC1_HEADLINE}}` | 46 | `secondary[0].headline` | Sidebar headline, 30 px. |
| `{{SEC1_SECTION}}` | 46 | `secondary[0].section` | Sidebar item kicker. |
| `{{SEC2_BODY_1}}` | 560 shared | `secondary[1].body` part 1 | Bottom column 1, 300 px. |
| `{{SEC2_BODY_2}}` | 560 shared | `secondary[1].body` part 2 | Bottom column 2, 300 px. |
| `{{SEC2_HEADLINE}}` | 46 | `secondary[1].headline` | Bottom headline, 38 px. |
| `{{SEC2_SECTION}}` | 46 | `secondary[1].section` | Bottom item 1 kicker. |
| `{{SEC3_BODY_1}}` | 560 shared | `secondary[2].body` part 1 | Bottom column 1, 300 px. |
| `{{SEC3_BODY_2}}` | 560 shared | `secondary[2].body` part 2 | Bottom column 2, 300 px. |
| `{{SEC3_HEADLINE}}` | 46 | `secondary[2].headline` | Bottom headline, 38 px. |
| `{{SEC3_SECTION}}` | 46 | `secondary[2].section` | Bottom item 2 kicker. |
| `{{STAT1_LABEL}}` | 22 | `lead.stats[0].label` | Stat table, small red or grey label. |
| `{{STAT1_VALUE}}` | 16 | `lead.stats[0].value` | Stat table, 52 px figure. |
| `{{STAT2_LABEL}}` | 22 | `lead.stats[1].label` | Stat table, small red or grey label. |
| `{{STAT2_VALUE}}` | 16 | `lead.stats[1].value` | Stat table, 52 px figure. |
| `{{STAT3_LABEL}}` | 22 | `lead.stats[2].label` | Stat table, small red or grey label. |
| `{{STAT3_VALUE}}` | 16 | `lead.stats[2].value` | Stat table, 52 px figure. |
| `{{VOL}}` | 8 | `vol` | Folio, first cell: `VOL. {VOL} — NO. {NO}`. |
| `{{WIRE10_HANDLE}}` | 24 | `wire[9].handle` | Wire handle. The template adds `@`. |
| `{{WIRE10_NOTE}}` | 130 | `wire[9].note` | Wire note, 300 px, 3 lines. |
| `{{WIRE11_HANDLE}}` | 24 | `wire[10].handle` | Wire handle. The template adds `@`. |
| `{{WIRE11_NOTE}}` | 130 | `wire[10].note` | Wire note, 300 px, 3 lines. |
| `{{WIRE12_HANDLE}}` | 24 | `wire[11].handle` | Wire handle. The template adds `@`. |
| `{{WIRE12_NOTE}}` | 130 | `wire[11].note` | Wire note, 300 px, 3 lines. |
| `{{WIRE1_HANDLE}}` | 24 | `wire[0].handle` | Wire handle. The template adds `@`. |
| `{{WIRE1_NOTE}}` | 130 | `wire[0].note` | Wire note, 300 px, 3 lines. |
| `{{WIRE2_HANDLE}}` | 24 | `wire[1].handle` | Wire handle. The template adds `@`. |
| `{{WIRE2_NOTE}}` | 130 | `wire[1].note` | Wire note, 300 px, 3 lines. |
| `{{WIRE3_HANDLE}}` | 24 | `wire[2].handle` | Wire handle. The template adds `@`. |
| `{{WIRE3_NOTE}}` | 130 | `wire[2].note` | Wire note, 300 px, 3 lines. |
| `{{WIRE4_HANDLE}}` | 24 | `wire[3].handle` | Wire handle. The template adds `@`. |
| `{{WIRE4_NOTE}}` | 130 | `wire[3].note` | Wire note, 300 px, 3 lines. |
| `{{WIRE5_HANDLE}}` | 24 | `wire[4].handle` | Wire handle. The template adds `@`. |
| `{{WIRE5_NOTE}}` | 130 | `wire[4].note` | Wire note, 300 px, 3 lines. |
| `{{WIRE6_HANDLE}}` | 24 | `wire[5].handle` | Wire handle. The template adds `@`. |
| `{{WIRE6_NOTE}}` | 130 | `wire[5].note` | Wire note, 300 px, 3 lines. |
| `{{WIRE7_HANDLE}}` | 24 | `wire[6].handle` | Wire handle. The template adds `@`. |
| `{{WIRE7_NOTE}}` | 130 | `wire[6].note` | Wire note, 300 px, 3 lines. |
| `{{WIRE8_HANDLE}}` | 24 | `wire[7].handle` | Wire handle. The template adds `@`. |
| `{{WIRE8_NOTE}}` | 130 | `wire[7].note` | Wire note, 300 px, 3 lines. |
| `{{WIRE9_HANDLE}}` | 24 | `wire[8].handle` | Wire handle. The template adds `@`. |
| `{{WIRE9_NOTE}}` | 130 | `wire[8].note` | Wire note, 300 px, 3 lines. |

## Removable blocks

A block is removed when every token inside it is empty. The builder then
drops a rule that would be left hanging at the head of a group.

| Block | Removed when |
|---|---|
| STAT1..STAT3 | the stat has no label and no value; the leading hairline goes with it |
| DIGEST1_ITEM1..4 | the digest item has no handle and no note |
| DIGEST2_ITEM1..4 | the digest item has no handle and no note |
| DIGEST1_GROUP, DIGEST2_GROUP | the whole group is empty, section included |
| SEC1 | the sidebar item is empty |
| SEC2, SEC3 | the bottom item is empty; the ink column rule goes with SEC3 |
| WIRE1..WIRE12 | the wire item has no handle and no note |
| LEAD_IMAGE | `lead.image` is absent |

## Escaping

Every value is HTML-escaped. `LEAD_IMAGE` is the one exception: the builder
makes that markup itself from a file it read, so there is no user text in it.
