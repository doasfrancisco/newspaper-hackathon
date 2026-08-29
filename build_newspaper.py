import base64
import html
import json
import os
import re
import sys

TEMPLATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", "frontpage.html")

ELLIPSIS = "\u2026"

MONTHS = ["JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE", "JULY",
          "AUGUST", "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER"]

MIME = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
        ".gif": "image/gif", ".webp": "image/webp"}

LIMITS = {
    "PAPER_NAME": 24, "DATE_LINE": 40, "CITY": 28, "VOL": 8, "NO": 8,
    "PRICE": 12, "RUN_ID": 24, "POSTS_READ": 8,
    "LEAD_SECTION": 46, "LEAD_HEADLINE": 80, "LEAD_DECK": 260,
    "LEAD_HANDLE": 24, "LEAD_SOURCE": 64, "LEAD_CAPTION": 200,
    "LEAD_DROPCAP": 1,
    "STAT1_LABEL": 22, "STAT2_LABEL": 22, "STAT3_LABEL": 22,
    "STAT1_VALUE": 16, "STAT2_VALUE": 16, "STAT3_VALUE": 16,
    "DIGEST_NOTE": 92,
    "DIGEST1_SECTION": 46, "DIGEST2_SECTION": 46,
    "SEC1_SECTION": 46, "SEC2_SECTION": 46, "SEC3_SECTION": 46,
    "SEC1_HEADLINE": 46, "SEC2_HEADLINE": 46, "SEC3_HEADLINE": 46,
    "DESK_NOTE_1": 320, "DESK_NOTE_2": 320,
}
for _i in range(1, 5):
    LIMITS["DIGEST1_H%d" % _i] = 24
    LIMITS["DIGEST2_H%d" % _i] = 24
    LIMITS["DIGEST1_T%d" % _i] = 160
    LIMITS["DIGEST2_T%d" % _i] = 160
LEAD_BODY_LIMIT = 1950
SEC1_BODY_LIMIT = 560
SEC_BODY_LIMIT = 560
WIRE_NOTE_LIMIT = 130
SPEC_LIMITS = {"lead_headline": 80, "secondary_headline": 46, "body": 700,
               "stat_label": 22, "stat_value": 16, "note": 92}

for _i in range(1, 13):
    LIMITS["WIRE%d_HANDLE" % _i] = 24
    LIMITS["WIRE%d_NOTE" % _i] = WIRE_NOTE_LIMIT

RULE_TAG = re.compile(r'^<div class="(?:hair1-(?:816|370|300)|vrule)"></div>$')
GROUP_HEADS = ('<div class="stat-row">', '<div class="wire-col">',
               '<div class="rule1-370"></div>')


def die(msg):
    sys.stderr.write("build_newspaper: %s\n" % msg)
    sys.exit(1)


def clip(value, limit):
    text = "" if value is None else str(value)
    text = text.replace("\r\n", " ").replace("\n", " ").strip()
    if limit is None or len(text) <= limit:
        return text
    if limit <= 1:
        return text[:limit]
    cut = text[:limit - 1].rstrip()
    space = cut.rfind(" ")
    if space >= int(limit * 0.6):
        cut = cut[:space].rstrip()
    return cut.rstrip(",;:.\u2014-").rstrip() + ELLIPSIS


def split_parts(text, parts):
    words = text.split(" ")
    if len(words) <= parts:
        out = words + [""] * (parts - len(words))
        return out[:parts]
    target = len(text) / float(parts)
    out = []
    buf = []
    size = 0
    for word in words:
        if len(out) < parts - 1 and buf and size + len(word) > target * (len(out) + 1) - sum(len(x) + 1 for x in out):
            out.append(" ".join(buf))
            buf = []
            size = 0
        buf.append(word)
        size += len(word) + 1
    out.append(" ".join(buf))
    while len(out) < parts:
        out.append("")
    return out[:parts]


def as_parts(value, parts, limit):
    if isinstance(value, list):
        items = [clip(v, None) for v in value]
        items = items + [""] * (parts - len(items))
        joined = " ".join(x for x in items[:parts] if x)
        if len(joined) > limit:
            return split_parts(clip(joined, limit), parts)
        return items[:parts]
    return split_parts(clip(value, limit), parts)


def source_line(run_id):
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})_(\d{2})(\d{2})$", str(run_id or ""))
    if not m:
        return "HOME TIMELINE"
    y, mo, d, hh, mm = m.groups()
    month = MONTHS[int(mo) - 1] if 1 <= int(mo) <= 12 else mo
    return "HOME TIMELINE  \u00b7  RUN OF %d %s %s, %s:%s" % (int(d), month, y, hh, mm)


def load_keepers(run_dir):
    path = os.path.join(run_dir, "keepers.json")
    if not os.path.isfile(path):
        die("no keepers.json at %s" % path)
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except ValueError as exc:
        die("keepers.json is not valid JSON: %s" % exc)
    if not isinstance(data, dict):
        die("keepers.json must hold a JSON object, found %s" % type(data).__name__)
    for key, kind in (("lead", dict), ("secondary", list), ("digest", list), ("wire", list)):
        if key in data and not isinstance(data[key], kind):
            die("keepers.json field %r must be a %s" % (key, kind.__name__))
    return data


def image_uri(run_dir, value):
    if not value:
        return ""
    candidates = [os.path.join(run_dir, value), value,
                  os.path.join(run_dir, "images", value)]
    for cand in candidates:
        if os.path.isfile(cand):
            ext = os.path.splitext(cand)[1].lower()
            if ext not in MIME:
                die("unsupported image type %r for %s" % (ext, cand))
            with open(cand, "rb") as fh:
                blob = base64.b64encode(fh.read()).decode("ascii")
            return '<img alt="" src="data:%s;base64,%s">' % (MIME[ext], blob)
    die("lead image not found: %r (looked in %s)" % (value, run_dir))


def build_values(data, run_dir):
    values = {}
    values["PAPER_NAME"] = data.get("paper_name", "THE TIMELINE")
    values["DATE_LINE"] = data.get("date_line", "")
    values["CITY"] = data.get("city", "")
    values["VOL"] = data.get("vol", "I")
    values["NO"] = data.get("no", "1")
    values["PRICE"] = data.get("price", "")
    values["RUN_ID"] = data.get("run", "")
    values["POSTS_READ"] = data.get("posts_read", "")
    values["DIGEST_NOTE"] = data.get("digest_note", "")

    lead = data.get("lead") or {}
    values["LEAD_SECTION"] = lead.get("section", "")
    values["LEAD_HEADLINE"] = lead.get("headline", "")
    values["LEAD_DECK"] = lead.get("deck", "")
    values["LEAD_HANDLE"] = lead.get("handle", "")
    values["LEAD_SOURCE"] = data.get("source_line") or source_line(data.get("run"))
    values["LEAD_CAPTION"] = lead.get("stats_caption", "")

    body = as_parts(lead.get("body", ""), 3, LEAD_BODY_LIMIT)
    first = body[0]
    values["LEAD_DROPCAP"] = first[:1]
    values["LEAD_BODY_1"] = first[1:].lstrip() if len(first) > 1 else ""
    values["LEAD_BODY_2"] = body[1]
    values["LEAD_BODY_3"] = body[2]
    if not values["LEAD_DROPCAP"]:
        values["LEAD_BODY_1"] = ""

    stats = lead.get("stats") or []
    if not isinstance(stats, list):
        die("lead.stats must be a list")
    for i in range(3):
        row = stats[i] if i < len(stats) else {}
        if not isinstance(row, dict):
            die("lead.stats[%d] must be an object" % i)
        values["STAT%d_LABEL" % (i + 1)] = row.get("label", "")
        values["STAT%d_VALUE" % (i + 1)] = row.get("value", "")

    groups = data.get("digest") or []
    for g in range(2):
        grp = groups[g] if g < len(groups) else {}
        if not isinstance(grp, dict):
            die("digest[%d] must be an object" % g)
        values["DIGEST%d_SECTION" % (g + 1)] = grp.get("section", "")
        items = grp.get("items")
        if items is None:
            handles = grp.get("handles") or []
            items = [{"handle": h, "note": grp.get("note", "") if i == 0 else ""}
                     for i, h in enumerate(handles)]
        if not isinstance(items, list):
            die("digest[%d].items must be a list" % g)
        for i in range(4):
            row = items[i] if i < len(items) else {}
            if not isinstance(row, dict):
                die("digest[%d].items[%d] must be an object" % (g, i))
            values["DIGEST%d_H%d" % (g + 1, i + 1)] = str(row.get("handle", "")).lstrip("@")
            values["DIGEST%d_T%d" % (g + 1, i + 1)] = row.get("note", "")

    secondary = data.get("secondary") or []
    for s in range(3):
        row = secondary[s] if s < len(secondary) else {}
        if not isinstance(row, dict):
            die("secondary[%d] must be an object" % s)
        values["SEC%d_SECTION" % (s + 1)] = row.get("section", "")
        values["SEC%d_HEADLINE" % (s + 1)] = row.get("headline", "")
        limit = SEC1_BODY_LIMIT if s == 0 else SEC_BODY_LIMIT
        parts = as_parts(row.get("body", ""), 2, limit)
        values["SEC%d_BODY_1" % (s + 1)] = parts[0]
        values["SEC%d_BODY_2" % (s + 1)] = parts[1]

    wire = data.get("wire") or []
    for w in range(12):
        row = wire[w] if w < len(wire) else {}
        if not isinstance(row, dict):
            die("wire[%d] must be an object" % w)
        values["WIRE%d_HANDLE" % (w + 1)] = str(row.get("handle", "")).lstrip("@")
        values["WIRE%d_NOTE" % (w + 1)] = row.get("note", "")

    notes = data.get("desk_note") or []
    if isinstance(notes, str):
        notes = [notes]
    if not isinstance(notes, list):
        die("desk_note must be a string or a list")
    values["DESK_NOTE_1"] = notes[0] if len(notes) > 0 else ""
    values["DESK_NOTE_2"] = notes[1] if len(notes) > 1 else ""

    for key in list(values):
        values[key] = clip(values[key], LIMITS.get(key))

    values["LEAD_IMAGE"] = image_uri(run_dir, (lead.get("image") or "").strip())
    return values


def strip_blocks(text, values):
    while True:
        m = re.search(r"<!--B:([A-Z0-9_]+)-->\n(.*?)<!--/B:\1-->\n", text, re.S)
        if not m:
            break
        name, inner = m.group(1), m.group(2)
        toks = re.findall(r"\{\{([A-Z0-9_]+)\}\}", inner)
        keep = any(values.get(t, "") for t in toks)
        text = text[:m.start()] + (inner if keep else "") + text[m.end():]
    return text


def tidy_rules(text):
    lines = text.split("\n")
    out = []
    for line in lines:
        s = line.strip()
        if RULE_TAG.match(s):
            prev = ""
            for cand in reversed(out):
                if cand.strip():
                    prev = cand.strip()
                    break
            if prev in GROUP_HEADS or RULE_TAG.match(prev):
                continue
        out.append(line)
    return "\n".join(out)


def main():
    if len(sys.argv) != 2:
        die("usage: python3 build_newspaper.py <run_dir>")
    run_dir = sys.argv[1].rstrip("/")
    if not os.path.isdir(run_dir):
        die("no such run folder: %s" % run_dir)
    if not os.path.isfile(TEMPLATE):
        die("no template at %s" % TEMPLATE)

    data = load_keepers(run_dir)
    values = build_values(data, run_dir)

    with open(TEMPLATE, encoding="utf-8") as fh:
        page = fh.read()

    page = strip_blocks(page, values)

    def swap(m):
        name = m.group(1)
        if name == "LEAD_IMAGE":
            return values.get(name, "")
        return html.escape(values.get(name, ""), quote=False)

    page = re.sub(r"\{\{([A-Z0-9_]+)\}\}", swap, page)
    page = tidy_rules(page)

    out_dir = os.path.join(run_dir, "paper")
    try:
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "index.html")
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(page)
    except OSError as exc:
        die("cannot write the page: %s" % exc)

    filled = sum(1 for k, v in values.items() if v)
    sys.stdout.write("%s\n%d of %d slots filled\n" % (out_path, filled, len(values)))


if __name__ == "__main__":
    main()
