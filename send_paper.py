import base64
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request

API = "https://api.resend.com/emails"
ROOT = os.path.dirname(os.path.abspath(__file__))
CHROMIUM = ["chromium", "chromium-browser", "google-chrome", "google-chrome-stable"]
KEYS = ("RESEND", "RESEND_API_KEY", "MAIL_TO", "MAIL_FROM", "PAPER_URL")


def die(msg):
    sys.stderr.write("send_paper: %s\n" % msg)
    raise SystemExit(1)


def load_env():
    env = {}
    path = os.path.join(ROOT, ".env")
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    for k in KEYS:
        if os.environ.get(k):
            env[k] = os.environ[k]
    return env


def make_pdf(run_dir):
    pdf = os.path.join(run_dir, "paper", "frontpage.pdf")
    if os.path.exists(pdf):
        return pdf
    page = os.path.join(run_dir, "paper", "index.html")
    if not os.path.exists(page):
        die("no page at %s (run build_newspaper.py first)" % page)
    binary = next((b for b in CHROMIUM if shutil.which(b)), None)
    if not binary:
        die("no chromium binary; tried %s" % ", ".join(CHROMIUM))
    subprocess.run([binary, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                    "--print-to-pdf=" + pdf, page], check=True, capture_output=True)
    if not os.path.exists(pdf):
        die("chromium did not write %s" % pdf)
    return pdf


def load_keepers(run_dir):
    path = os.path.join(run_dir, "keepers.json")
    if not os.path.exists(path):
        die("no keepers.json in %s" % run_dir)
    with open(path) as f:
        return json.load(f)


def kept_count(k):
    n = 1 if k.get("lead") else 0
    n += len(k.get("secondary", []))
    n += sum(len(g.get("items") or g.get("handles") or []) for g in k.get("digest", []))
    n += len(k.get("wire", []))
    return n


def esc(value):
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def body_html(k, url):
    lead = k.get("lead") or {}
    paper = k.get("paper_name", "THE TIMELINE")
    out = [
        '<div style="max-width:620px;margin:0 auto;padding:24px;',
        'font-family:Georgia,\'Times New Roman\',serif;color:#111">',
        '<div style="border-bottom:3px double #111;padding-bottom:10px;margin-bottom:18px">',
        '<div style="font-size:26px;letter-spacing:3px;font-weight:bold">%s</div>' % esc(paper),
        '<div style="font-size:11px;letter-spacing:2px;color:#555;margin-top:4px">%s</div>'
        % esc(k.get("date_line", "")),
        '</div>',
    ]
    if lead:
        out.append('<div style="font-size:10px;letter-spacing:2px;color:#777">%s</div>'
                   % esc(lead.get("section", "")))
        out.append('<div style="font-size:21px;font-weight:bold;line-height:1.25;margin:6px 0 8px">%s</div>'
                   % esc(lead.get("headline", "")))
        out.append('<div style="font-size:14px;line-height:1.5;color:#333">%s</div>'
                   % esc(lead.get("body", "")))
        out.append('<div style="font-size:12px;color:#777;margin-top:6px">@%s</div>'
                   % esc(lead.get("handle", "")))
    secondary = k.get("secondary", [])
    if secondary:
        out.append('<div style="border-top:1px solid #ccc;margin:20px 0 12px"></div>')
        out.append('<ul style="padding-left:18px;margin:0;font-size:14px;line-height:1.5">')
        for s in secondary:
            out.append('<li style="margin-bottom:6px"><b>%s</b> <span style="color:#777">@%s</span></li>'
                       % (esc(s.get("headline", "")), esc(s.get("handle", ""))))
        out.append('</ul>')
    out.append('<div style="border-top:1px solid #ccc;margin:20px 0 12px"></div>')
    out.append('<div style="font-size:13px;color:#555">Read %s posts, kept %s. '
               'The full front page is attached as a PDF.</div>'
               % (esc(k.get("posts_read", "?")), kept_count(k)))
    if url:
        out.append('<div style="font-size:13px;margin-top:10px">'
                   '<a href="%s" style="color:#111">Open the front page</a></div>' % esc(url))
    out.append('</div>')
    return "".join(out)


def send(env, k, pdf, dry_run):
    key = env.get("RESEND") or env.get("RESEND_API_KEY")
    if not key:
        die("no RESEND key in .env")
    to = env.get("MAIL_TO")
    if not to:
        die("no MAIL_TO in .env")
    sender = env.get("MAIL_FROM", "onboarding@resend.dev")
    date_line = k.get("date_line", k.get("run", ""))
    payload = {
        "from": sender,
        "to": [to],
        "subject": "%s - %s" % (k.get("paper_name", "THE TIMELINE"), date_line),
        "html": body_html(k, env.get("PAPER_URL", "")),
        "attachments": [{
            "filename": "frontpage.pdf",
            "content": base64.b64encode(open(pdf, "rb").read()).decode(),
        }],
    }
    if dry_run:
        print("from:    %s" % sender)
        print("to:      %s" % to)
        print("subject: %s" % payload["subject"])
        print("pdf:     %s (%d KB)" % (pdf, os.path.getsize(pdf) // 1024))
        print("body:    %d bytes of html" % len(payload["html"]))
        print("dry run, nothing sent")
        return
    req = urllib.request.Request(
        API,
        data=json.dumps(payload).encode(),
        headers={"Authorization": "Bearer " + key,
                 "Content-Type": "application/json",
                 "User-Agent": "Mozilla/5.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print("sent:", json.load(r).get("id", ""))
    except urllib.error.HTTPError as e:
        die("resend %s: %s" % (e.code, e.read().decode()[:400]))


def main():
    args = [a for a in sys.argv[1:] if a != "--dry-run"]
    if len(args) != 1:
        die("usage: python3 send_paper.py <run_dir> [--dry-run]")
    run_dir = args[0].rstrip("/")
    k = load_keepers(run_dir)
    send(load_env(), k, make_pdf(run_dir), "--dry-run" in sys.argv)


if __name__ == "__main__":
    main()
