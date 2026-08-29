import json
import os
import re
import sys
import urllib.request


def ext_of(url):
    m = re.search(r"\.(jpg|jpeg|png|gif|webp)$", url.split("?")[0], re.I)
    return m.group(1).lower() if m else "jpg"


def download(url, path):
    if os.path.exists(path):
        return True
    req = urllib.request.Request(url + "?name=medium", headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r, open(path, "wb") as f:
            f.write(r.read())
        return True
    except Exception as e:
        print("FAIL", url, e)
        return False


def save_images(t, folder, prefix, counter):
    for m in t.get("media", []):
        if m.get("type") != "image" or not m.get("url"):
            continue
        counter[0] += 1
        name = "{}{}.{}".format(prefix, counter[0], ext_of(m["url"]))
        path = os.path.join(folder, name)
        os.makedirs(folder, exist_ok=True)
        if download(m["url"], path):
            m["local_path"] = os.path.relpath(path)
    if t.get("quoted"):
        save_images(t["quoted"], folder, "quoted_", [0])


def main():
    run_dir = sys.argv[1].rstrip("/")
    timeline_path = os.path.join(run_dir, "timeline.json")
    images_dir = os.path.join(run_dir, "images")
    d = json.load(open(timeline_path))
    for i, t in enumerate(d["tweets"], 1):
        folder = os.path.join(images_dir, "{:03d}_{}".format(i, t["handle"]))
        save_images(t, folder, "", [0])
    json.dump(d, open(timeline_path, "w"), ensure_ascii=False, indent=2)
    total = sum(1 for root, _, files in os.walk(images_dir) for f in files)
    print("images on disk:", total)


if __name__ == "__main__":
    main()
