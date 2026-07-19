# Textured Noise CAPTCHA — Work Plan

## Goal

Add a noise-texture rendering mode to the animated GIF CAPTCHA generator.
Instead of solid grey fills, every layer is rendered with white noise baked in
at init time, so the noise pattern rides rigidly with its layer across all
36 frames. The human visual system separates the layers by motion; OCR cannot.

---

## Background: how the current compositor works

`VISCHA._nextImage()` builds each frame by compositing three layers onto a
solid base:

```
canvas (solid bgColor)
  └─ background words  (rolled up/down each frame, pasted as solid bgwColor)
  └─ the word          (moves in a circle, pasted as solid fgColor)
  └─ foreground grating (shifted each frame, pasted as solid screenColor)
```

`pastmask(base, mask, xy, colour)` is the compositor primitive — it creates a
same-size solid-colour image and pastes it through `mask` at `xy`.

---

## What changes

### New primitive: `pastmask_texture`

```python
def pastmask_texture(base, mask, xy, texture):
    base.paste(texture, tuple(xy), mask=mask)
```

Instead of a solid colour, paste a pre-generated noise image through the mask.
The texture must match the mask's size at call time.

### Noise images (created once in `VISCHA.__init__`)

| Attribute | Size | Moves with |
|---|---|---|
| `self.word_noise` | `self.word.size` | the word (same position/rotation) |
| `self.bg_noise` | `(width, height)` | the background (same roll/scroll) |
| `self.fg_noise` | `(width, height)` | the foreground grating (same shift) |

`_make_noise(size)` — one helper, returns a random `'L'` mode PIL Image.

### `_nextImage` changes

Apply the same transform to the noise layer as to its corresponding mask layer,
then call `pastmask_texture` instead of `pastmask`.

```
canvas (solid bgColor)                            ← unchanged
  └─ bg_noise    rolled/scrolled same as background
  └─ word_noise  at same position as word (rotation is 0 so no-op)
  └─ fg_noise    shifted same as foreground grating
```

### Config / presets

Add a boolean `texture` field to each preset in `default_conf.py`:
- Existing presets 0, 1, 2 get `'texture': False` — no behaviour change.
- Add new preset 3 with `'texture': True` and tuned values.

`VISCHA` checks `self.CONF.texture` to decide whether to use
`pastmask` or `pastmask_texture`. Backwards-compatible.

---

## Open questions (decide before coding)

- [ ] **Noise brightness range**: pure 0–255 vs centred around the existing
  colour values (e.g. noise in `[fgColor-64, fgColor+64]`). Pure noise makes
  a stronger CAPTCHA; bounded noise keeps the grey-level feel closer to the
  original.
- [ ] **Background canvas**: keep `bgColor` solid, or also noise-fill it?
  Solid base gives the eye a resting point and is probably better for legibility.
- [ ] **Word noise size after rotation**: `wSH[2]` is always 0 in the current
  code so the word never rotates mid-animation — word_noise stays fixed-size.
  If rotation is ever enabled later, the noise crop/expand logic needs updating.

---

## Task list

### Phase 1 — core generator changes (`modules/imagesH.py`)

- [ ] **T1** Add `_make_noise(size)` static helper using `numpy.random` (re-add
  numpy import, or use `os.urandom` + `frombuffer` if we want to drop numpy)
- [ ] **T2** Add `pastmask_texture(base, mask, xy, texture)` utility function
- [ ] **T3** In `VISCHA.__init__`, generate `self.word_noise`, `self.bg_noise`,
  `self.fg_noise` when `self.CONF.texture` is True
- [ ] **T4** In `VISCHA._nextImage`, apply matching transforms to noise images
  and call `pastmask_texture` instead of `pastmask` when texture mode is on
- [ ] **T5** Keep `pastmask` / solid-colour path untouched — texture is opt-in

### Phase 2 — config (`modules/default_conf.py`)

- [ ] **T6** Add `'texture': False` to existing presets 0–2
- [ ] **T7** Add preset 3: texture=True, tuned params (start from preset 0 values,
  adjust wordCount/speed/colours for readability with noise)

### Phase 3 — web layer (`main.py`)

- [ ] **T8** Confirm `c=3` routes through correctly (it does — no change needed,
  just verify the clamp added from the review allows `c` up to
  `len(preconf)-1` dynamically)

### Phase 4 — review fixes (from the code review, bundle these in)

- [ ] **T9**  Clamp `c` param: `max(0, min(int(c), len(CONF.preconf)-1))`
- [ ] **T10** Raise at startup if `CAPTCHA_SECRET` is not set (or is the default)
- [ ] **T11** Fix `open(..., 'w')` → `'wb'` in `imagesH.py` `main()`
- [ ] **T12** Remove unused `import numpy as np` from current code (T1 will
  re-add it only inside `_make_noise`)

### Phase 5 — test & docs

- [ ] **T13** Local smoke test: generate a texture-mode GIF with `c=3`, visually
  inspect that noise moves with each layer
- [ ] **T14** Update `README.md` — add preset 3 to the parameters table, note
  texture mode
- [ ] **T15** Commit on this branch, push, update PR

---

## File map

| File | Touches |
|---|---|
| `modules/imagesH.py` | T1 T2 T3 T4 T5 T11 T12 |
| `modules/default_conf.py` | T6 T7 |
| `main.py` | T8 T9 T10 |
| `README.md` | T14 |

---

## What this does NOT change

- The token / HMAC URL scheme
- The existing three presets or any existing API behaviour
- `muove.py` (historical reference, untouched)
- Frame count (36), GIF encoding, or the circular word motion path
