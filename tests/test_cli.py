from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image

from moodboardbook.cli import main

from .helpers import make_assets
from .test_config import write_board


def test_cli_check_reports_local_boundary(tmp_path: Path, capsys) -> None:
    assets = make_assets(tmp_path / "assets")
    source = write_board(tmp_path / "board.toml")

    assert main(["check", str(source), str(assets)]) == 0
    output = capsys.readouterr().out
    assert "READY TO RENDER" in output
    assert "does not validate image rights" in output


def test_cli_build_writes_a_reference_board_and_evidence_files(tmp_path: Path) -> None:
    assets = make_assets(tmp_path / "assets")
    source = write_board(tmp_path / "board.toml")
    output = tmp_path / "packet"

    assert main(["build", str(source), str(assets), "--output", str(output)]) == 0
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "ready_to_render"
    for entry in manifest["generated_files"]:
        file_path = output / entry["path"]
        assert file_path.stat().st_size == entry["bytes"]
        assert hashlib.sha256(file_path.read_bytes()).hexdigest() == entry["sha256"]
    rendered = Image.open(output / "MOODBOARD.png")
    assert rendered.size[0] == 1600
    assert "rights" in (output / "MOODBOARD.md").read_text(encoding="utf-8")


def test_cli_build_refuses_overwrite_and_missing_assets_are_errors(tmp_path: Path) -> None:
    assets = make_assets(tmp_path / "assets")
    source = write_board(tmp_path / "board.toml")
    output = tmp_path / "packet"

    assert main(["build", str(source), str(assets), "--output", str(output)]) == 0
    assert main(["build", str(source), str(assets), "--output", str(output)]) == 1
    assert main(["check", str(source), str(tmp_path / "missing-assets")]) == 1
