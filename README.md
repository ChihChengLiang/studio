# Studio

Explorations in images, 3D, music, video and games, published as a static site on GitHub Pages.

## Layout

```
index.html                  landing page; lists every exploration
<category>/<slug>/index.html   one self-contained page per exploration
```

Categories: `images`, `3d`, `music`, `video`, `games`.

## Adding an exploration

1. Create `<category>/<slug>/index.html` (plus any assets next to it, using relative paths).
2. Add an entry to `EXPLORATIONS` in the root `index.html`.
3. Optionally add a 960×540 `cover.webp` next to the page; the landing card shows it.

## Preview locally

```bash
python3 -m http.server 8000
```

## Publishing

Settings → Pages → Deploy from a branch → `main` / root. `.nojekyll` disables Jekyll processing.
