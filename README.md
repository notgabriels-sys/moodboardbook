# Moodboardbook

Moodboardbook is a local, annotated image-reference-board builder for art-direction review. You declare a title, purpose, visual notes, and the relative paths of local image tiles; it verifies that those files are readable **inside the asset directory you supply**, then creates a restrained PNG board plus Markdown/JSON evidence records.

It complements a variant contact sheet: use a contact sheet to compare versions of one design direction; use Moodboardbook to hold the visual references and short reasons behind a direction before or during that work.

## What it checks and creates

- Declared project context, purpose, and source/requirements basis.
- One or more ordered image tiles with safe relative paths, labels, and notes.
- Safe containment of each image inside the supplied asset directory, including rejection of path/symlink escapes.
- Readability, encoded pixels, format, mode, byte count, and SHA-256 fingerprint for every declared local image.
- A proportion-preserving, warm-neutral PNG board with non-overlapping cards, annotations, and a clearly unverified footer.

```text
moodboard-packet/
├── MOODBOARD.png
├── MOODBOARD.md
├── moodboard.json
└── manifest.json
```

## What it does not establish

Moodboardbook does **not** validate image rights, licences, authorship, consent, provenance, originality, artistic quality, project identity, brand fit, accessibility, platform use, print suitability, or creative approval. It does not download, upload, publish, share, or alter the source images.

A rendered board is a local review artefact—not permission to use any image. Check the actual source and rights context directly before using a reference in public, commercial, or final work.

## Install

Requires Python 3.11 or later.

```sh
uv tool install .
```

For development:

```sh
uv venv .venv
uv pip install --python .venv/bin/python -e '.[dev]'
```

## Use

Start with the fictional TOML example, place your local references in one directory, and replace every value with the current human-authored context.

```sh
moodboardbook check examples/moodboard-example.toml ./reference-images
moodboardbook check examples/moodboard-example.toml ./reference-images --json
moodboardbook build examples/moodboard-example.toml ./reference-images --output ./delivery/moodboard-v01
```

`check` is read-only. `build` refuses to replace an existing output directory and returns:

- `0` — every declared local image is readable and safely contained; this is not rights or creative approval.
- `1` — invalid/missing TOML, missing/unreadable/escaped source image, or output-directory conflict.

The input images remain untouched; only the composed board is newly written. The manifest hashes generated files and fingerprints the plan; `moodboard.json` records facts about the referenced image files without copying them into the packet.

## Input format

```toml
[board]
title = "Example visual direction"
project = "Example Artist"
purpose = "Fictional creative-reference review."
requirements_basis = "Fictional local sources; check rights and context directly."

[layout]
columns = 2
board_width_px = 1600

[[tiles]]
position = 1
id = "grain"
image = "grain.png" # relative to the supplied asset directory
label = "Surface"
note = "A fictional note about pressure, material, and negative space."
```

The default board design follows the included [Quiet Systems visual philosophy](docs/quiet-systems.md): warm charcoal, off-white, muted bronze, precise card geometry, and generous breathing room. It is a generic interface style, not a claim about any artist identity or source artwork.

## Development

```sh
.venv/bin/python -m pytest -q
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
```

The only runtime dependency is [Pillow](https://python-pillow.org/) for local image decoding and raster rendering. Moodboardbook itself makes no network request and has no browser, shell-command, upload, or destructive-file operation.
