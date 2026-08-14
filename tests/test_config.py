from __future__ import annotations

from pathlib import Path

import pytest

from moodboardbook.config import ConfigError, load_board


def write_board(path: Path, *, replacements: dict[str, str] | None = None) -> Path:
    content = """
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
image = "grain.png"
label = "Surface"
note = "A fictional note about pressure, material, and negative space."

[[tiles]]
position = 2
id = "light"
image = "light.png"
label = "Signal"
note = "A fictional note about contrast and an isolated accent."
""".strip()
    for old, new in (replacements or {}).items():
        content = content.replace(old, new)
    path.write_text(content + "\n", encoding="utf-8")
    return path


def test_load_board_parses_declared_layout_and_order(tmp_path: Path) -> None:
    board = load_board(write_board(tmp_path / "board.toml"))

    assert board.layout.columns == 2
    assert board.layout.board_width_px == 1600
    assert [tile.id for tile in board.tiles] == ["grain", "light"]


@pytest.mark.parametrize(
    "replacements, expected",
    [
        ({"columns = 2": "columns = 0"}, "at least 1"),
        ({'id = "light"': 'id = "grain"'}, "duplicate"),
        ({'image = "grain.png"': 'image = "../outside.png"'}, "relative"),
        ({"board_width_px = 1600": "board_width_px = 400"}, "at least"),
    ],
)
def test_load_board_rejects_unsafe_or_invalid_declarations(
    tmp_path: Path, replacements: dict[str, str], expected: str
) -> None:
    with pytest.raises(ConfigError, match=expected):
        load_board(write_board(tmp_path / "board.toml", replacements=replacements))


def test_load_board_rejects_unknown_fields(tmp_path: Path) -> None:
    source = write_board(tmp_path / "board.toml")
    source.write_text(source.read_text(encoding="utf-8") + "published = true\n", encoding="utf-8")

    with pytest.raises(ConfigError, match="unknown field"):
        load_board(source)
