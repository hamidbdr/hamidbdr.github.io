"""Refresh assets/stats.json with live view counts and citation metrics.

Run daily by .github/workflows/stats.yml. Uses only the standard library.
Every source is fetched independently: if one fails or its page layout
changes, the previous value is kept so the site never shows a blank.
"""

import html
import http.client
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATS = ROOT / "assets" / "stats.json"

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0 Safari/537.36"
)

TIKTOK_USER = "hd.brr"
TIKTOK_VIDEOS = ["7497985056653249814"]
YOUTUBE_CHANNEL = "UChnlG7TStIlgv1EcdSZBHVg"
YOUTUBE_VIDEOS = ["1_WKkzb5Dd4", "xMZ7kFXE5Jc", "X-8d8J09OTA", "zabBqJazzWg"]
SCHOLAR_USER = "9fMwc-wAAAAJ"
# Key used in the page -> start of the paper title on Google Scholar.
SCHOLAR_PAPERS = {
    "adjoint2017": "A comparison of discrete versus continuous adjoint states",
    "conductivity2019": "Heterogeneous hydraulic conductivity and porosity fields",
    "thesis2018": "Identification des paramètres de l'écoulement",
    "thomasfermi2015": "Self-consistent approach to solving the 1D Thomas-Fermi",
}


def get(url, headers=None, data=None):
    req = urllib.request.Request(url, data=data, headers={"User-Agent": UA, "Accept-Language": "en", **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        try:
            body = r.read()
        except http.client.IncompleteRead as exc:  # TikTok sometimes cuts the stream short
            body = exc.partial
    return body.decode("utf-8", "replace")


def tiktok_views(video_id):
    page = get(f"https://www.tiktok.com/@{TIKTOK_USER}/video/{video_id}")
    return int(re.search(r'"playCount":(\d+)', page).group(1))


def youtube_api_views(video_ids):
    """Official YouTube Data API; needs a free key in the YT_API_KEY secret."""
    key = os.environ.get("YT_API_KEY")
    if not key:
        return {}
    data = json.loads(get("https://www.googleapis.com/youtube/v3/videos?part=statistics&id=%s&key=%s"
                          % (",".join(video_ids), key)))
    return {item["id"]: int(item["statistics"]["viewCount"]) for item in data.get("items", [])}


def youtube_views(video_id, feed=None):
    """Try several public sources; YouTube blocks some of them from cloud servers."""
    player_request = json.dumps({
        "videoId": video_id,
        "context": {"client": {"clientName": "WEB", "clientVersion": "2.20240101.00.00", "hl": "en"}},
    }).encode()
    sources = [
        lambda: get(f"https://www.youtube.com/watch?v={video_id}", {"Cookie": "SOCS=CAI"}),
        lambda: get("https://www.youtube.com/youtubei/v1/player?prettyPrint=false",
                    {"Content-Type": "application/json"}, player_request),
    ]
    for fetch in sources:
        try:
            m = re.search(r'"viewCount":"(\d+)"', fetch())
            if m:
                return int(m.group(1))
        except Exception:
            pass
    # The channel RSS feed lists only the 15 latest uploads, with their views.
    if feed:
        pattern = r"<yt:videoId>%s</yt:videoId>.*?<media:statistics views=\"(\d+)\"" % re.escape(video_id)
        m = re.search(pattern, feed, re.S)
        if m:
            return int(m.group(1))
    raise LookupError("no source returned a view count")


def scholar():
    page = get(f"https://scholar.google.com/citations?user={SCHOLAR_USER}&hl=en")
    std = [int(x) for x in re.findall(r'class="gsc_rsb_std">(\d+)', page)]
    out = {"citations": std[0], "hindex": std[2]}
    rows = re.findall(r'class="gsc_a_at"[^>]*>([^<]+)<.*?class="gsc_a_ac gs_ibl"[^>]*>(\d*)<', page, re.S)
    for key, prefix in SCHOLAR_PAPERS.items():
        counts = [int(c) for t, c in rows if html.unescape(t).startswith(prefix) and c]
        if counts:
            out[key] = max(counts)
    return out


def main():
    stats = json.loads(STATS.read_text(encoding="utf-8")) if STATS.exists() else {}
    before = json.dumps({k: v for k, v in stats.items() if k != "updated"}, sort_keys=True)
    failures = []

    def attempt(label, fn):
        try:
            return fn()
        except Exception as exc:  # keep the old value, report and move on
            failures.append(f"{label}: {exc!r}")
            return None

    for vid in TIKTOK_VIDEOS:
        n = attempt(f"tiktok {vid}", lambda: tiktok_views(vid))
        if n:
            stats.setdefault("tiktok", {})[vid] = n
    feed = attempt("youtube feed", lambda: get(f"https://www.youtube.com/feeds/videos.xml?channel_id={YOUTUBE_CHANNEL}"))
    api = attempt("youtube api", lambda: youtube_api_views(YOUTUBE_VIDEOS)) or {}
    for vid in YOUTUBE_VIDEOS:
        n = api.get(vid) or attempt(f"youtube {vid}", lambda: youtube_views(vid, feed))
        if n:
            stats.setdefault("youtube", {})[vid] = n
    s = attempt("scholar", scholar)
    if s:
        stats.setdefault("scholar", {}).update(s)

    after = json.dumps({k: v for k, v in stats.items() if k != "updated"}, sort_keys=True)
    if after != before:
        stats["updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with open(STATS, "w", encoding="utf-8", newline="\n") as f:  # LF on every OS, so local runs make no diff
        f.write(json.dumps(stats, indent=2, ensure_ascii=False) + "\n")

    print(json.dumps(stats, indent=2, ensure_ascii=False))
    for f in failures:
        print("warning:", f, file=sys.stderr)


if __name__ == "__main__":
    main()
