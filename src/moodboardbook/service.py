"""Read-only local image facts for declared Moodboardbook tiles."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from moodboardbook.config import BoardPlan, Tile


class AssetError(ValueError):
    """Raised when a required local reference image cannot safely be read from the asset root."""


@dataclass(frozen=True)
class TileFact:
    """Observed local image facts; they do not establish source rights, relevance, or quality."""

    tile: Tile
    source_path: Path
    file_bytes: int
    sha256: str
    format: str
    mode: str
    width_px: int
    height_px: int


@dataclass(frozen=True)
class BoardAssessment:
    """A ready-to-render image set, not an art-direction, rights, or creative approval."""

    plan: BoardPlan
    asset_root: Path
    tile_facts: tuple[TileFact, ...]
    status: str


def sha256_file(path: Path) -> str:
    """Return an image-file fingerprint without copying, retaining, or changing its contents."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def resolve_asset(asset_root: Path, tile: Tile) -> Path:
    """Resolve a declared tile path and reject escapes from the asset root."""

    candidate = (asset_root / tile.image).resolve()
    try:
        candidate.relative_to(asset_root)
    except ValueError as error:
        raise AssetError(f"tile {tile.id} resolves outside the supplied asset directory") from error
    return candidate


def inspect_image(tile: Tile, path: Path) -> TileFact:
    """Read safely decodable image facts while preserving the original source file untouched."""

    if not path.is_file():
        raise AssetError(f"declared image for tile {tile.id} does not exist: {path}")
    try:
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            image.load()
            image_format = image.format
            mode = image.mode
            width_px, height_px = image.size
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as error:
        raise AssetError(f"declared image for tile {tile.id} is not readable: {path}") from error
    if not image_format or width_px <= 0 or height_px <= 0:
        raise AssetError(f"declared image for tile {tile.id} has invalid dimensions: {path}")
    stat = path.stat()
    return TileFact(
        tile=tile,
        source_path=path,
        file_bytes=stat.st_size,
        sha256=sha256_file(path),
        format=image_format.upper(),
        mode=mode,
        width_px=width_px,
        height_px=height_px,
    )


def inspect_assets(plan: BoardPlan, asset_root: Path) -> BoardAssessment:
    """Verify local image readability and containment; no source, rights, or creative validation."""

    if not asset_root.is_dir():
        raise AssetError(f"asset directory does not exist or is not a directory: {asset_root}")
    resolved_root = asset_root.resolve()
    facts = tuple(inspect_image(tile, resolve_asset(resolved_root, tile)) for tile in plan.tiles)
    return BoardAssessment(
        plan=plan,
        asset_root=resolved_root,
        tile_facts=facts,
        status="ready_to_render",
    )
