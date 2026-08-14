"""A restrained local raster renderer for Moodboardbook reference boards."""

from __future__ import annotations

from dataclasses import dataclass

from PIL import Image, ImageDraw, ImageFont, ImageOps

from moodboardbook.service import BoardAssessment, TileFact

BACKGROUND = (32, 33, 36)
CARD = (45, 45, 48)
PAPER = (242, 239, 232)
MUTED = (177, 172, 164)
ACCENT = (185, 154, 106)
IMAGE_BACKDROP = (22, 22, 24)


@dataclass(frozen=True)
class RenderTile:
    """A measured card position calculated before any pixel output is created."""

    fact: TileFact
    x: int
    y: int
    width: int
    height: int
    note_lines: tuple[str, ...]


def font(size: int) -> ImageFont.ImageFont:
    """Load a portable readable font with Pillow's bundled default as a final fallback."""

    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except OSError:
        try:
            return ImageFont.load_default(size=size)
        except TypeError:
            return ImageFont.load_default()


def line_height(draw: ImageDraw.ImageDraw, text_font: ImageFont.ImageFont) -> int:
    """Return a stable full-line text height for deterministic vertical spacing."""

    box = draw.textbbox((0, 0), "Ag", font=text_font)
    return box[3] - box[1]


def wrap_text(
    draw: ImageDraw.ImageDraw, value: str, text_font: ImageFont.ImageFont, max_width: int
) -> tuple[str, ...]:
    """Wrap declared annotations without truncating them or letting them extend outside cards."""

    words = value.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        if draw.textlength(candidate, font=text_font) <= max_width:
            current = candidate
            continue
        if current:
            lines.append(current)
            current = word
            continue
        fragment = ""
        for character in word:
            proposed = fragment + character
            if fragment and draw.textlength(proposed, font=text_font) > max_width:
                lines.append(fragment)
                fragment = character
            else:
                fragment = proposed
        current = fragment
    if current:
        lines.append(current)
    return tuple(lines) or ("",)


def layout_tiles(assessment: BoardAssessment) -> tuple[tuple[RenderTile, ...], int]:
    """Measure a non-overlapping card grid before rendering images, labels, or notes."""

    board_width = assessment.plan.layout.board_width_px
    columns = assessment.plan.layout.columns
    margin = max(56, board_width // 24)
    gap = max(28, board_width // 48)
    title_font = font(max(42, board_width // 26))
    project_font = font(max(22, board_width // 55))
    body_font = font(max(20, board_width // 75))
    note_font = font(max(18, board_width // 88))
    probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    purpose_lines = wrap_text(
        probe, assessment.plan.board.purpose, body_font, board_width - (2 * margin)
    )
    header_height = (
        margin
        + line_height(probe, title_font)
        + max(20, board_width // 80)
        + line_height(probe, project_font)
        + max(28, board_width // 52)
        + len(purpose_lines) * line_height(probe, body_font)
        + max(48, board_width // 32)
    )
    card_width = (board_width - (2 * margin) - ((columns - 1) * gap)) // columns
    card_padding = max(20, board_width // 80)
    image_height = max(200, int(card_width * 0.62))
    label_font = font(max(22, board_width // 62))
    label_height = line_height(probe, label_font)
    note_height = line_height(probe, note_font)
    measured: list[tuple[TileFact, tuple[str, ...], int]] = []
    for fact in assessment.tile_facts:
        note_lines = wrap_text(probe, fact.tile.note, note_font, card_width - (2 * card_padding))
        card_height = (
            card_padding
            + image_height
            + card_padding
            + label_height
            + max(12, card_padding // 2)
            + len(note_lines) * note_height
            + card_padding
        )
        measured.append((fact, note_lines, card_height))
    rendered: list[RenderTile] = []
    y = header_height
    for row_start in range(0, len(measured), columns):
        row = measured[row_start : row_start + columns]
        row_height = max(card_height for _, _, card_height in row)
        for column, (fact, note_lines, card_height) in enumerate(row):
            x = margin + column * (card_width + gap)
            rendered.append(
                RenderTile(
                    fact=fact,
                    x=x,
                    y=y,
                    width=card_width,
                    height=card_height,
                    note_lines=note_lines,
                )
            )
        y += row_height + gap
    footer_height = max(110, board_width // 12)
    return tuple(rendered), y + footer_height + margin


def paste_contained_image(
    canvas: Image.Image, fact: TileFact, x: int, y: int, width: int, height: int
) -> None:
    """Place a source image proportionally inside a card viewport without changing the source."""

    with Image.open(fact.source_path) as source:
        prepared = ImageOps.exif_transpose(source).convert("RGB")
        thumbnail = ImageOps.contain(prepared, (width, height), method=Image.Resampling.LANCZOS)
    backdrop = Image.new("RGB", (width, height), color=IMAGE_BACKDROP)
    offset = ((width - thumbnail.width) // 2, (height - thumbnail.height) // 2)
    backdrop.paste(thumbnail, offset)
    canvas.paste(backdrop, (x, y))


def render_board(assessment: BoardAssessment) -> Image.Image:
    """Render declared annotations alongside readable local image inputs."""

    plan = assessment.plan
    tiles, board_height = layout_tiles(assessment)
    board_width = plan.layout.board_width_px
    margin = max(56, board_width // 24)
    card_padding = max(20, board_width // 80)
    canvas = Image.new("RGB", (board_width, board_height), color=BACKGROUND)
    draw = ImageDraw.Draw(canvas)
    title_font = font(max(42, board_width // 26))
    project_font = font(max(22, board_width // 55))
    body_font = font(max(20, board_width // 75))
    note_font = font(max(18, board_width // 88))
    label_font = font(max(22, board_width // 62))
    y = margin
    draw.text((margin, y), plan.board.title.upper(), font=title_font, fill=PAPER)
    y += line_height(draw, title_font) + max(20, board_width // 80)
    draw.text((margin, y), plan.board.project, font=project_font, fill=ACCENT)
    y += line_height(draw, project_font) + max(28, board_width // 52)
    for line in wrap_text(draw, plan.board.purpose, body_font, board_width - (2 * margin)):
        draw.text((margin, y), line, font=body_font, fill=MUTED)
        y += line_height(draw, body_font)
    for render_tile in tiles:
        draw.rounded_rectangle(
            (
                render_tile.x,
                render_tile.y,
                render_tile.x + render_tile.width,
                render_tile.y + render_tile.height,
            ),
            radius=max(12, board_width // 120),
            fill=CARD,
        )
        draw.rectangle(
            (
                render_tile.x,
                render_tile.y,
                render_tile.x + max(8, board_width // 200),
                render_tile.y + render_tile.height,
            ),
            fill=ACCENT,
        )
        image_x = render_tile.x + card_padding
        image_y = render_tile.y + card_padding
        image_width = render_tile.width - (2 * card_padding)
        image_height = max(200, int(render_tile.width * 0.62))
        paste_contained_image(canvas, render_tile.fact, image_x, image_y, image_width, image_height)
        text_y = image_y + image_height + card_padding
        draw.text((image_x, text_y), render_tile.fact.tile.label, font=label_font, fill=PAPER)
        text_y += line_height(draw, label_font) + max(12, card_padding // 2)
        for line in render_tile.note_lines:
            draw.text((image_x, text_y), line, font=note_font, fill=MUTED)
            text_y += line_height(draw, note_font)
    footer = "LOCAL REFERENCE BOARD · IMAGE SOURCE, RIGHTS, AND CREATIVE FIT UNVERIFIED"
    footer_font = font(max(16, board_width // 100))
    footer_y = board_height - margin - line_height(draw, footer_font)
    draw.line(
        (
            margin,
            footer_y - max(20, board_width // 90),
            board_width - margin,
            footer_y - max(20, board_width // 90),
        ),
        fill=ACCENT,
        width=2,
    )
    draw.text((margin, footer_y), footer, font=footer_font, fill=MUTED)
    return canvas
