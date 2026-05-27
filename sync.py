#!/usr/bin/env python3
"""
Discourse Motorola sync — automated version for GitHub Actions.
Reads API credentials from environment variables and writes data.json.
"""

import requests
import json
import time
import os
from datetime import datetime, timezone

BASE = "https://discourse.lilt.com"
CAT_SLUG = "motorola"
CAT_ID = 171
SLA_HOURS = 24

API_KEY = os.environ["DISCOURSE_API_KEY"]
API_USER = os.environ["DISCOURSE_API_USER"]

HEADERS = {
    "Api-Key": API_KEY,
    "Api-Username": API_USER,
    "Content-Type": "application/json",
}


def api_get(path, retries=3):
    url = BASE + path
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code == 429:
                wait = int(r.headers.get("Retry-After", 15))
                print(f"  Rate limited — waiting {wait}s…")
                time.sleep(wait)
                continue
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            if attempt == retries - 1:
                raise
            print(f"  Retry {attempt + 1}: {e}")
            time.sleep(3)


def hours_apart(a, b):
    if not a or not b:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            ta = datetime.strptime(a, fmt).replace(tzinfo=timezone.utc)
            tb = datetime.strptime(b, fmt).replace(tzinfo=timezone.utc)
            return round(max(0, (tb - ta).total_seconds() / 3600), 2)
        except ValueError:
            continue
    return None


print(f"Fetching topics from {BASE}/c/{CAT_SLUG}/{CAT_ID}…")

all_topics = []
page = 0
while True:
    print(f"  Page {page + 1} ({len(all_topics)} topics so far)…")
    data = api_get(f"/c/{CAT_SLUG}/{CAT_ID}.json?page={page}")
    topic_list = data.get("topic_list", {})
    topics = topic_list.get("topics", [])
    if not topics:
        break
    all_topics.extend([t for t in topics if not t.get("pinned_globally")])
    if not topic_list.get("more_topics_url") or len(topics) < 30:
        break
    page += 1
    time.sleep(0.2)

print(f"\nEnriching {len(all_topics)} topics…")
now_iso = datetime.now(timezone.utc).isoformat()
enriched = []

for i, t in enumerate(all_topics):
    print(f"  [{i+1}/{len(all_topics)}] {t['title'][:60]}")
    first_reply = None
    try:
        td = api_get(f"/t/{t['id']}.json")
        posts = td.get("post_stream", {}).get("posts", [])
        if len(posts) > 1:
            first_reply = posts[1].get("created_at")
    except Exception as e:
        print(f"    Warning: {e}")

    created = t.get("created_at")
    response_hours = hours_apart(created, first_reply)
    now_hours = hours_apart(created, now_iso)

    if first_reply:
        status = "answered"
    elif now_hours is not None and now_hours > SLA_HOURS:
        status = "overdue"
    else:
        status = "open"

    enriched.append({
        "id": t["id"],
        "title": t["title"],
        "slug": t.get("slug", ""),
        "created": created,
        "firstReply": first_reply,
        "responseHours": response_hours,
        "replies": max(0, t.get("posts_count", 1) - 1),
        "views": t.get("views", 0),
        "status": status,
    })
    time.sleep(0.1)

output = {
    "synced_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    "topic_count": len(enriched),
    "topics": enriched,
}

with open("data.json", "w") as f:
    json.dump(output, f)

print(f"\nDone — {len(enriched)} topics written to data.json")
