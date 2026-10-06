# hamidbdr.github.io

Personal site of Dr. Hamid Badri, served by GitHub Pages at <https://hamidbdr.github.io>.

| File | Purpose |
| --- | --- |
| `index.html` | The site |
| `assets/style.css` | Site styles (light and dark theme) |
| `assets/photo.jpg`, `assets/favicon.jpg` | Portrait and tab icon |
| `cv.html` | Printable CV, source of the PDF |
| `CV_HamidBadri.pdf` | Downloadable CV |

## Updating the CV PDF

Edit `cv.html`, then from the repo root:

```sh
chrome --headless --no-pdf-header-footer --print-to-pdf=CV_HamidBadri.pdf cv.html
```
