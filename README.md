# hamidbdr.github.io

Personal site of Dr. Hamid Badri, served by GitHub Pages at <https://hamidbdr.github.io>.

| File | Purpose |
| --- | --- |
| `index.html` | The site |
| `assets/style.css` | Site styles (light and dark theme) |
| `assets/photo.jpg`, `assets/favicon.jpg` | Portrait and tab icon |
| `cv.html` | Printable CV, source of the PDF |
| `CV_HamidBadri.pdf` | Downloadable CV |
| `assets/videos/` | Video thumbnails (`.jpg`) and 4-second silent hover previews (`.mp4`) |
| `assets/stats.json`, `scripts/`, `.github/` | Daily refresh of view counts and citations |

## Updating the CV PDF

Edit `cv.html`, then from the repo root:

```sh
chrome --headless --no-pdf-header-footer --print-to-pdf=CV_HamidBadri.pdf cv.html
```

## Live numbers

`assets/stats.json` holds the TikTok and YouTube view counts and the Google Scholar
citations shown on the page. The **Refresh stats** GitHub Action
(`.github/workflows/stats.yml`) runs `scripts/update_stats.py` every day and commits
the file when a number changes; the page reads it on load. Run it by hand from the
Actions tab (Run workflow) or locally with `python scripts/update_stats.py`.

What works from GitHub's servers:

- **TikTok**: yes.
- **YouTube**: only videos in the channel's 15 latest uploads, unless a
  YouTube Data API key is set. Create a free key in Google Cloud Console
  (APIs & Services → enable *YouTube Data API v3* → Credentials → API key),
  then add it to this repo under Settings → Secrets and variables → Actions
  as `YT_API_KEY`.
- **Google Scholar**: blocked (403). The last value stays on the page; run the
  script on your own computer and push `assets/stats.json` to refresh it.

To track another video, add its ID to `TIKTOK_VIDEOS` or `YOUTUBE_VIDEOS` in the
script and put `data-stat="youtube.<id>"` (or `tiktok.<id>`) on the element that
shows the number.
