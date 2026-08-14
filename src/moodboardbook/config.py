"""Strict parsing for local declared art-direction reference boards."""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ConfigError(ValueError):
    """Raised when a local reference-board declaration is incomplete or unsafe."""


TILE_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


@dataclass(frozen=True)
class Board:
    """Declared context for one local art-direction board, not a rights or identity claim."""

    title: str
    project: str
    purpose: str
    requirements_basis: str


@dataclass(frozen=True)
class Layout:
    """Safe output-grid dimensions for a deterministic local raster board."""

    columns: int
    board_width_px: int


@dataclass(frozen=True)
class Tile:
    """A declared local image and annotation, not verified source or creative evidence."""

    position: int
    id: str
    image: str
    label: str
    note: str


@dataclass(frozen=True)
class BoardPlan:
    """A parsed reference-board plan that contains declarations only, not image data."""

    board: Board
    layout: Layout
    tiles: tuple[Tile, ...]
    source_path: Path


def load_toml(path: Path) -> dict[str, Any]:
    """Load TOML with useful local input errors instead of raw parser tracebacks."""

    try:
        with path.open("rb") as handle:
            payload = tomllib.load(handle)
    except FileNotFoundError as error:
        raise ConfigError(f"board plan does not exist: {path}") from error
    except IsADirectoryError as error:
        raise ConfigError(f"board plan path is a directory, not TOML: {path}") from error
    except tomllib.TOMLDecodeError as error:
        raise ConfigError(f"invalid TOML in {path}: {error}") from error
    if not isinstance(payload, dict):
        raise ConfigError("board plan root must be a TOML table")
    return payload


def require_table(payload: dict[str, Any], key: str) -> dict[str, Any]:
    """Return one required TOML table with a contextual error."""

    value = payload.get(key)
    if not isinstance(value, dict):
        raise ConfigError(f"{key} must be a TOML table")
    return value


def reject_unknown_keys(payload: dict[str, Any], allowed: set[str], section: str) -> None:
    """Reject typo fields so a visual declaration cannot silently be lost."""

    unknown = sorted(set(payload) - allowed)
    if unknown:
        raise ConfigError(f"{section} contains unknown field(s): {', '.join(unknown)}")


def require_text(payload: dict[str, Any], key: str, section: str) -> str:
    """Return nonblank declared text without evaluating its truth, quality, or rights status."""

    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{section}.{key} must be nonblank text")
    return value.strip()


def require_positive_int(payload: dict[str, Any], key: str, section: str, *, minimum: int) -> int:
    """Return a bounded integral local layout value."""

    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ConfigError(f"{section}.{key} must be at least {minimum}")
    return value


def parse_tile(payload: Any, index: int) -> Tile:
    """Validate one declared image tile without reading the image itself."""

    section = f"tiles[{index}]"
    if not isinstance(payload, dict):
        raise ConfigError(f"{section} must be a TOML table")
    reject_unknown_keys(payload, {"position", "id", "image", "label", "note"}, section)
    tile_id = require_text(payload, "id", section)
    if not TILE_ID_PATTERN.fullmatch(tile_id):
        raise ConfigError(f"{section}.id must be lowercase kebab-case")
    image = require_text(payload, "image", section)
    image_path = Path(image)
    if image_path.is_absolute() or ".." in image_path.parts:
        raise ConfigError(
            f"{section}.image must be a relative path inside the supplied asset directory"
        )
    if image_path.name in {"", "."}:
        raise ConfigError(f"{section}.image must name a file")
    return Tile(
        position=require_positive_int(payload, "position", section, minimum=1),
        id=tile_id,
        image=image,
        label=require_text(payload, "label", section),
        note=require_text(payload, "note", section),
    )


def load_board(path: Path) -> BoardPlan:
    """Parse a declared board plan without reading, copying, or changing local image assets."""

    payload = load_toml(path)
    reject_unknown_keys(payload, {"board", "layout", "tiles"}, "root")
    board_payload = require_table(payload, "board")
    layout_payload = require_table(payload, "layout")
    reject_unknown_keys(
        board_payload,
        {"title", "project", "purpose", "requirements_basis"},
        "board",
    )
    reject_unknown_keys(layout_payload, {"columns", "board_width_px"}, "layout")
    raw_tiles = payload.get("tiles")
    if not isinstance(raw_tiles, list) or not raw_tiles:
        raise ConfigError("tiles must be a nonempty array of TOML tables")
    tiles = tuple(parse_tile(tile, index) for index, tile in enumerate(raw_tiles, start=1))
    ids = [tile.id for tile in tiles]
    if len(set(ids)) != len(ids):
        raise ConfigError("tiles contains duplicate IDs")
    positions = [tile.position for tile in tiles]
    if len(set(positions)) != len(positions):
        raise ConfigError("tiles contains duplicate position values")
    columns = require_positive_int(layout_payload, "columns", "layout", minimum=1)
    if columns > 4:
        raise ConfigError("layout.columns must not exceed 4")
    return BoardPlan(
        board=Board(
            title=require_text(board_payload, "title", "board"),
            project=require_text(board_payload, "project", "board"),
            purpose=require_text(board_payload, "purpose", "board"),
            requirements_basis=require_text(board_payload, "requirements_basis", "board"),
        ),
        layout=Layout(
            columns=columns,
            board_width_px=require_positive_int(
                layout_payload, "board_width_px", "layout", minimum=800
            ),
        ),
        tiles=tuple(sorted(tiles, key=lambda tile: tile.position)),
        source_path=path,
    )
