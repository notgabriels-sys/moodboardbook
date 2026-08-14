from __future__ import annotations

from pathlib import Path

import pytest

from moodboardbook.config import load_board
from moodboardbook.service import AssetError, inspect_assets

from .helpers import make_assets
from .test_config import write_board


def test_inspect_assets_records_readable_local_image_facts(tmp_path: Path) -> None:
    assets = make_assets(tmp_path / "assets")
    assessment = inspect_assets(load_board(write_board(tmp_path / "board.toml")), assets)

    assert assessment.status == "ready_to_render"
    assert [fact.width_px for fact in assessment.tile_facts] == [1200, 800]
    assert [fact.format for fact in assessment.tile_facts] == ["PNG", "PNG"]


def test_inspect_assets_rejects_missing_or_unreadable_declared_image(tmp_path: Path) -> None:
    assets = make_assets(tmp_path / "assets")
    board = load_board(
        write_board(
            tmp_path / "board.toml",
            replacements={'image = "light.png"': 'image = "missing.png"'},
        )
    )

    with pytest.raises(AssetError, match="does not exist"):
        inspect_assets(board, assets)


def test_rendered_board_has_declared_width_and_a_visual_canvas(tmp_path: Path) -> None:
    from moodboardbook.render import render_board

    assets = make_assets(tmp_path / "assets")
    assessment = inspect_assets(load_board(write_board(tmp_path / "board.toml")), assets)
    image = render_board(assessment)

    assert image.size[0] == 1600
    assert image.size[1] > 500
    assert image.mode == "RGB"
