"""Local Moodboardbook documents and manifests for rendered local reference boards."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from moodboardbook.render import render_board
from moodboardbook.service import BoardAssessment


@dataclass(frozen=True)
class MoodboardBundle:
    """Files created by one new local board build without overwriting prior output."""

    output_path: Path
    image_path: Path
    markdown_path: Path
    document_path: Path
    manifest_path: Path


def markdown_cell(value: object) -> str:
    """Keep declared board annotations inside predictable Markdown table cells."""

    return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def render_markdown(assessment: BoardAssessment) -> str:
    """Render declared annotations and observed image facts without rights claims."""

    plan = assessment.plan
    lines = [
        f"# Moodboard — {plan.board.title}",
        "",
        f"**Project (declared):** {plan.board.project}  ",
        f"**Purpose (declared):** {plan.board.purpose}  ",
        "**Output state:** READY TO RENDER — LOCAL IMAGE READABILITY ONLY",
        "",
        "## Declared tiles and observed local image facts",
        "",
        "| # | ID | Image | Label | Note | Observed format | Encoded pixels | SHA-256 |",
        "| ---: | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for fact in assessment.tile_facts:
        tile = fact.tile
        lines.append(
            "| "
            + " | ".join(
                [
                    str(tile.position),
                    f"`{tile.id}`",
                    f"`{markdown_cell(tile.image)}`",
                    markdown_cell(tile.label),
                    markdown_cell(tile.note),
                    fact.format,
                    f"{fact.width_px} × {fact.height_px}",
                    f"`{fact.sha256}`",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Requirements basis",
            "",
            plan.board.requirements_basis,
            "",
            "## Scope boundary",
            "",
            (
                "Moodboardbook reads and composites local files you explicitly declare. "
                "It does not validate image rights, licences, authorship, consent, "
                "provenance, originality, artistic quality, project identity, brand fit, "
                "accessibility, platform use, print suitability, or creative approval. "
                "It does not download, upload, publish, share, or alter source images. "
                "A rendered board is a local review artefact, not permission to use any source."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def document(assessment: BoardAssessment) -> dict[str, object]:
    """Return declared context and observed input facts in a portable structured record."""

    plan = assessment.plan
    return {
        "schema_version": 1,
        "status": assessment.status,
        "board": {
            "title": plan.board.title,
            "project": plan.board.project,
            "purpose": plan.board.purpose,
            "requirements_basis": plan.board.requirements_basis,
        },
        "layout": {
            "columns": plan.layout.columns,
            "board_width_px": plan.layout.board_width_px,
        },
        "tiles": [
            {
                "position": fact.tile.position,
                "id": fact.tile.id,
                "declared_image": fact.tile.image,
                "label": fact.tile.label,
                "note": fact.tile.note,
                "observed_file_name": fact.source_path.name,
                "bytes": fact.file_bytes,
                "sha256": fact.sha256,
                "format": fact.format,
                "mode": fact.mode,
                "width_px": fact.width_px,
                "height_px": fact.height_px,
            }
            for fact in assessment.tile_facts
        ],
        "scope_boundary": (
            "Local image readability and composition only; no image rights, provenance, creative, "
            "identity, accessibility, print, platform, or approval validation."
        ),
    }


def sha256(path: Path) -> str:
    """Return a generated-file digest for the local portable manifest."""

    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_bundle(assessment: BoardAssessment, output_path: Path) -> MoodboardBundle:
    """Write a new annotated local board packet without changing declared source images."""

    if output_path.exists():
        raise FileExistsError(f"output directory already exists: {output_path}")
    output_path.mkdir(parents=True)
    image_path = output_path / "MOODBOARD.png"
    markdown_path = output_path / "MOODBOARD.md"
    document_path = output_path / "moodboard.json"
    manifest_path = output_path / "manifest.json"
    render_board(assessment).save(image_path, format="PNG", optimize=True)
    markdown_path.write_text(render_markdown(assessment), encoding="utf-8")
    document_path.write_text(
        json.dumps(document(assessment), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    generated_files = (image_path, markdown_path, document_path)
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "status": assessment.status,
                "source_plan": {
                    "file_name": assessment.plan.source_path.name,
                    "sha256": sha256(assessment.plan.source_path),
                },
                "generated_files": [
                    {"path": path.name, "bytes": path.stat().st_size, "sha256": sha256(path)}
                    for path in generated_files
                ],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return MoodboardBundle(
        output_path=output_path,
        image_path=image_path,
        markdown_path=markdown_path,
        document_path=document_path,
        manifest_path=manifest_path,
    )
