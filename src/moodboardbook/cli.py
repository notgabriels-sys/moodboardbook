"""Command-line interface for local Moodboardbook checks and renders."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from moodboardbook.config import BoardPlan, ConfigError, load_board
from moodboardbook.report import document, write_bundle
from moodboardbook.service import AssetError, BoardAssessment, inspect_assets


def build_parser() -> argparse.ArgumentParser:
    """Build the compact local check/build command interface."""

    parser = argparse.ArgumentParser(
        prog="moodboardbook",
        description="Build an annotated local image reference board from a declared plan.",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)
    for command in ("check", "build"):
        subparser = subcommands.add_parser(command)
        subparser.add_argument("plan", type=Path, help="TOML declared moodboard plan")
        subparser.add_argument("asset_directory", type=Path, help="Local image directory")
        subparser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
        if command == "build":
            subparser.add_argument(
                "--output", required=True, type=Path, help="New local output directory"
            )
    return parser


def concise_text(plan: BoardPlan, assessment: BoardAssessment) -> str:
    """Render a short readability result without declaring source, rights, or creative approval."""

    return "\n".join(
        [
            f"Moodboard: {plan.board.title}",
            "Output state: READY TO RENDER",
            f"Readable declared local images: {len(assessment.tile_facts)}",
            (
                "Moodboardbook does not validate image rights, provenance, originality, "
                "creative fit, or approval, and does not alter source images."
            ),
        ]
    )


def run(plan_path: Path, asset_directory: Path) -> tuple[BoardPlan, BoardAssessment]:
    """Load one declared plan and verify only its explicitly named local image inputs."""

    plan = load_board(plan_path)
    return plan, inspect_assets(plan, asset_directory)


def main(argv: Sequence[str] | None = None) -> int:
    """Run a local board check/render and fail only for invalid inputs or output conflicts."""

    args = build_parser().parse_args(argv)
    try:
        plan, assessment = run(args.plan, args.asset_directory)
        if args.command == "build":
            bundle = write_bundle(assessment, args.output)
            payload = document(assessment)
            payload["output_directory"] = str(bundle.output_path)
            if args.json:
                print(json.dumps(payload, indent=2, sort_keys=True))
            else:
                print(f"Wrote local moodboard packet: {bundle.output_path}")
                print(concise_text(plan, assessment))
        elif args.json:
            print(json.dumps(document(assessment), indent=2, sort_keys=True))
        else:
            print(concise_text(plan, assessment))
        return 0
    except (ConfigError, AssetError, FileExistsError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
