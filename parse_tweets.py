import json
import glob
import os
import sys


def load_entries(path):
    with open(path) as f:
        data = json.load(f)
    instructions = data["data"]["home"]["home_timeline_urt"]["instructions"]
    for ins in instructions:
        if ins.get("type") == "TimelineAddEntries":
            return ins.get("entries", [])
    return []


def unwrap(result):
    if result is None:
        return None
    if result.get("__typename") == "TweetWithVisibilityResults":
        return result.get("tweet")
    return result


def best_video(media):
    variants = media.get("video_info", {}).get("variants", [])
    mp4 = [v for v in variants if v.get("content_type") == "video/mp4" and v.get("bitrate") is not None]
    if not mp4:
        return None
    return max(mp4, key=lambda v: v["bitrate"])["url"]


def expand_text(legacy, note=None):
    note_text = note.get("text") if note else None
    text = note_text if note_text else legacy.get("full_text", "")
    entities = legacy.get("entities", {})
    urls = list(entities.get("urls", []))
    if note:
        urls += note.get("entity_set", {}).get("urls", [])
    for u in urls:
        if u.get("url") and u.get("expanded_url"):
            text = text.replace(u["url"], u["expanded_url"])
    media_ents = legacy.get("extended_entities", {}).get("media", []) or entities.get("media", [])
    for m in media_ents:
        if m.get("url"):
            text = text.replace(m["url"], "").strip()
    return text.strip()


def get_media(legacy):
    out = []
    media_ents = legacy.get("extended_entities", {}).get("media", []) or legacy.get("entities", {}).get("media", [])
    for m in media_ents:
        mtype = m.get("type")
        if mtype == "photo":
            out.append({"type": "image", "url": m.get("media_url_https")})
        elif mtype in ("video", "animated_gif"):
            out.append({
                "type": "video" if mtype == "video" else "gif",
                "thumbnail": m.get("media_url_https"),
                "video_url": best_video(m),
            })
    return out


def parse_result(result):
    result = unwrap(result)
    if not result:
        return None
    legacy = result.get("legacy", {})
    core = result.get("core", {}).get("user_results", {}).get("result", {})
    user_core = core.get("core", {})
    handle = user_core.get("screen_name")
    name = user_core.get("name")
    note = result.get("note_tweet", {}).get("note_tweet_results", {}).get("result", {})
    text = expand_text(legacy, note if note.get("text") else None)
    if not handle:
        return None
    tweet_id = result.get("rest_id") or legacy.get("id_str")
    obj = {
        "id": tweet_id,
        "handle": handle,
        "name": name,
        "text": text,
        "created_at": legacy.get("created_at"),
        "likes": legacy.get("favorite_count"),
        "retweets": legacy.get("retweet_count"),
        "replies": legacy.get("reply_count"),
        "url": "https://x.com/{}/status/{}".format(handle, tweet_id),
        "media": get_media(legacy),
    }
    quoted = result.get("quoted_status_result", {}).get("result")
    if quoted:
        obj["quoted"] = parse_result(quoted)
    return obj


def extract(entry):
    entry_id = entry.get("entryId", "")
    if not entry_id.startswith("tweet-"):
        return None
    content = entry.get("content", {})
    item = content.get("itemContent", {})
    if item.get("promotedMetadata"):
        return None
    result = unwrap(item.get("tweet_results", {}).get("result"))
    if not result:
        return None
    legacy = result.get("legacy", {})
    repost = legacy.get("retweeted_status_result", {}).get("result")
    if repost:
        inner = parse_result(repost)
        outer = parse_result(result)
        if not inner or not outer:
            return None
        inner["is_repost"] = True
        inner["reposted_by"] = {"handle": outer["handle"], "name": outer["name"]}
        inner["liked_by_me"] = None
        return inner
    obj = parse_result(result)
    if not obj or not obj.get("text") and not obj.get("media"):
        return None
    obj["is_repost"] = False
    obj["liked_by_me"] = None
    return obj


def main():
    run_dir = sys.argv[1].rstrip("/")
    seen_path = os.path.join("news", "seen_ids.json")
    seen = set()
    if os.path.exists(seen_path):
        with open(seen_path) as f:
            seen = set(json.load(f))
    tweets = []
    for path in sorted(glob.glob(os.path.join(run_dir, "raw_batch_*.json"))):
        for entry in load_entries(path):
            t = extract(entry)
            if not t:
                continue
            if t["id"] in seen:
                continue
            seen.add(t["id"])
            tweets.append(t)
    out = {"count": len(tweets), "tweets": tweets}
    with open(os.path.join(run_dir, "timeline.json"), "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    with open(seen_path, "w") as f:
        json.dump(sorted(seen), f, indent=2)
    print("new unique tweets:", len(tweets))


if __name__ == "__main__":
    main()
