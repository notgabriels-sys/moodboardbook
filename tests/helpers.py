from __future__ import annotations

from pathlib import Path

from PIL import Image


def make_assets(root: Path) -> Path:
    root.mkdir()
    Image.new("RGB", (1200, 800), color=(29, 28, 27)).save(root / "grain.png", format="PNG")
    Image.new("RGB", (800, 1200), color=(185, 154, 106)).save(root / "light.png", format="PNG")
    return root
