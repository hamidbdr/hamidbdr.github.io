"""Refresh assets/stats.json with live view counts and citation metrics.

Run daily by .github/workflows/stats.yml. Uses only the standard library.
Every source is fetched independently: if one fails or its page layout
changes, the previous value is kept so the site never shows a blank.
"""

import html
import json
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
YOUTUBE_VIDEOS = ["1_WKkzb5Dd4", "xMZ7kFXE5Jc", "X-8d8J09OTA", "zabBqJazzWg"]
SCHOLAR_USER = "9fMwc-wAAAAJ"
# Key used in the page -> start of the paper title on Google Scholar.
SCHOLAR_PAPERS = {
    "adjoint2017": "A comparison of discrete versus continuous adjoint states",
    "conductivity2019": "Heterogeneous hydraulic conductivity and porosity fields",
    "thesis2018": "Identification des paramètres de l'écoulement",
    "thomasfermi2015": "Self-consistent approach to solving the 1D Thomas-Fermi",
}


def get(url, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en", **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def tiktok_views(video_id):
    page = get(f"https://www.tiktok.com/@{TIKTOK_USER}/video/{video_id}")
    return int(re.search(r'"playCount":(\d+)', page).group(1))


def youtube_views(video_id):
    page = get(f"https://www.youtube.com/watch?v={video_id}", {"Cookie": "SOCS=CAI"})
    return int(re.search(r'"viewCount":"(\d+)"', page).group(1))


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
    for vid in YOUTUBE_VIDEOS:
        n = attempt(f"youtube {vid}", lambda: youtube_views(vid))
        if n:
            stats.setdefault("youtube", {})[vid] = n
    s = attempt("scholar", scholar)
    if s:
        stats.setdefault("scholar", {}).update(s)

    after = json.dumps({k: v for k, v in stats.items() if k != "updated"}, sort_keys=True)
    if after != before:
        stats["updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    STATS.write_text(json.dumps(stats, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps(stats, indent=2, ensure_ascii=False))
    for f in failures:
        print("warning:", f, file=sys.stderr)


if __name__ == "__main__":
    main()
