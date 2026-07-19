# Eppur si muove — animated CAPTCHA / text-to-GIF generator

A small Google App Engine (Python 2.7) app that renders text as an **animated GIF**,
with moving obstructions and background noise, so the result can be used as a
dynamic CAPTCHA or for e-mail address obfuscation.

The name is Galileo's "and yet it moves" — the text drifts and wobbles behind an
animated grating, which makes it much harder for OCR to read while staying legible
to a human. Demo was hosted at `eppur-si.appspot.com` (see `eppur.html` for the
landing page).

## How it works

Each frame composites three layers (see `modules/imagesH.py`):

1. **Background** — a canvas scattered with random decoy words (`wordCount` of them),
   scrolled up/down between frames.
2. **The word** — the actual text to display, rendered in a randomly-sized,
   slightly rotated font, moving along a circular path frame to frame.
3. **Foreground "screen"** — a grating of ellipses or rectangles (`shape`) that
   partially hides the word; it can shift (`dx`/`dy`) and jitter (`wobble`)
   between frames.

36 frames are generated and encoded into a GIF with a bundled, trimmed-down copy
of the `images2gif` module (from the visvis package, BSD-licensed —
`modules/images2gif.py` + `modules/images2gif_extension.py`).

## Web API (`muove.py`)

The app supports two modes:

### Non-secure (one step)

```
GET /direct_gif?word=Hello&c=1&dx=4&shape=1
```

Returns the GIF directly. The word is visible in the URL, so this is for image
generation / e-mail obfuscation, not for CAPTCHA use.

### Secure (two steps)

1. `GET /get_code?word=Hello&...` — stores the request parameters in the
   datastore and returns a URL of the form `/gif/XXXXnn.gif`, where `XXXX` is a
   4-letter verification code and `nn` the record id. The word never appears in
   the served URL.
2. `GET /gif/XXXXnn.gif` — looks up the stored record, verifies the code, and
   serves the animated GIF.

Other routes:

| Route | Purpose |
|---|---|
| `/decode/XXXXnn.gif` | Reverse a code back into its `/direct_gif` URL |
| `/vars` | Debug: echo request arguments |
| `/robots` | Serves `robots.txt` |
| anything else | Serves the `eppur.html` landing page |

## Parameters

All parameters are passed as GET variables (or via the `settings` dict when using
the library directly). `c` selects one of the preset configurations in
`modules/default_conf.py`; individual values can then be overridden:

| Parameter | Default | Meaning |
|---|---|---|
| `font` | 0 | Font index: 0 = Bradley Hand ITC, 1 = Arial |
| `font_size` | 36 | Base font size (a random 0–20 is added) |
| `width` / `height` | 300 / 120 | Image size in pixels |
| `wordCount` | 10 | Number of random decoy words in the background |
| `shape` | 0 | Grating shape: 0 = ellipses, 1 = rectangles, 2 = thin rectangles |
| `screen_r` / `screen_d` | 16 / 14 | Grating spacing / element size |
| `dx` / `dy` | 0 / 0 | Per-frame shift of the grating |
| `wobble` | 0 | Random rotation jitter of the grating per frame |
| `duration` | 10 | Frame duration in hundredths of a second |
| `bgColor` | 255 | Background grey level (0–255) |
| `bgwColor` | 100 | Decoy-word grey level |
| `fgColor` | 100 | Main word grey level |
| `screenColor` | 155 | Grating grey level |

## Using the generator as a library

`modules/imagesH.py` also runs standalone (Python 2, needs PIL and numpy):

```python
from modules.imagesH import VISCHA

v = VISCHA('Example 32', confn=1, settings={'dx': 4, 'shape': 1})
with open('example.gif', 'wb') as fp:
    v.writeImage_fp(fp)
```

`writeImage_fp` accepts any file-like object, so it can write to disk or straight
into an HTTP response (as `muove.py` does with `StringIO`).

## Repository layout

| Path | Contents |
|---|---|
| `muove.py` | App Engine request handlers and datastore model |
| `app.yaml`, `index.yaml` | App Engine configuration |
| `modules/imagesH.py` | `VISCHA` GIF generator and `CONF` configuration class |
| `modules/default_conf.py` | Preset configurations (selected with `c`) |
| `modules/images2gif*.py` | Bundled GIF encoder (from visvis, BSD license) |
| `eppur.html` | Landing/demo page |
| `fonts/`, `*.ttf` | Fonts used for rendering |
| `images/` | Sample output GIFs and page assets |

## Deploying

The app runs on App Engine Python 3.12 with Flask. Deploy with:

```
gcloud app deploy
```

Set a real secret before deploying to production — either in `app.yaml`:

```yaml
env_variables:
  CAPTCHA_SECRET: "your-random-secret"
```

or via `gcloud app deploy --set-env-vars CAPTCHA_SECRET=your-secret`.

### Running locally

```bash
pip install -r requirements.txt
python main.py
```

Then open `http://localhost:5000/direct_gif?word=Hello&c=1` to see a GIF.

## Changes from the original Python 2 version

The original was a Python 2.7 / `webapp2` / App Engine Datastore app (circa
2012) that no longer ran after Google retired the Python 2.7 runtime. The
revival makes the following changes:

- **Runtime**: Python 2.7 + `webapp2` → Python 3.12 + Flask (`main.py`)
- **GIF encoding**: removed the bundled `images2gif` module; now uses Pillow's
  native `save(save_all=True, append_images=...)` GIF writer
- **Two-step secure flow**: replaced App Engine Datastore records with
  **stateless HMAC-SHA256 signed tokens** embedded in the GIF URL. No database
  dependency; tokens are verified on the fly. Set `CAPTCHA_SECRET` to make
  tokens non-forgeable.
- **Python 3 fixes** in `modules/imagesH.py`: `getsize` → `getbbox`, integer
  division, removed `numpy` from the GIF path, `raw_input` → `input`

Note: `muove.py` is the original Python 2 source kept for reference; `main.py`
is the live entry point.

Note: `serve_request` and `decode` in `muove.py` use `eval()` on stored request
content — fine for a demo, but it should be replaced with `json` if this is ever
revived.

## Author and license

Written by vish (avishalom@gmail.com). Use freely, but please attribute
authorship where applicable. Provided as is. The bundled `images2gif` code is
BSD-licensed by its original authors (Almar Klein, Ant1, Marius van Voorden).
