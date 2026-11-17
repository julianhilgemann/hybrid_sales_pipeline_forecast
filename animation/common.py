"""Shared visual language for every clip of the pipeline-forecast explainer.

Import with ``from common import *`` at the top of a scene file (scenes are
rendered from the ``animation/`` directory, so this module is importable).

Everything a viewer should perceive as "the same thing" across clips lives
here: palette, type sizes, the data bundle, chapter open/close, and a few
geometry builders for charts, heatmaps and 3D ribbons.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from manim import *  # noqa: F401,F403

HERE = Path(__file__).resolve().parent
DATA_PATH = HERE / "data" / "model_data.json"

# --------------------------------------------------------------------------
# Palette (dark-theme translation of the README chart colours)
# --------------------------------------------------------------------------
BG = "#0E1117"        # frame background
PANEL = "#151B23"     # subtle panel fill
INK = "#E6EDF3"       # primary text / neutral marks
MUTED = "#8B949E"     # secondary text, axes, ticks
GRID = "#2A313C"      # grid lines, faint outlines

KERNEL = "#F5A524"    # the win kernel k(a)  -- and anything that is "a win"
STOCK = "#E5637D"     # existing pipeline stock N(a) and everything derived from it
ARRIVALS = "#4FA3F7"  # forecast arrivals A_hat(t) and everything derived from it
TOTAL = "#2DD4BF"     # the combined forecast W_hat(d)
WON = KERNEL          # a won deal (same hue as the kernel on purpose)
LOST = "#64748B"      # a lost deal
SURVIVAL = "#C4B5FD"  # survival curve S(a) / "still open"

# heat-map colour ramps, dark -> bright (value 0 blends into the background)
STOCK_RAMP = [BG, "#3A1524", "#7A2A40", "#B5475B", "#E5637D", "#FFC2CD"]
ARRIVALS_RAMP = [BG, "#10263F", "#1B4A7C", "#2B6CB0", "#4FA3F7", "#C2E0FF"]
KERNEL_RAMP = [BG, "#3D2A0A", "#7A5210", "#B87A14", "#F5A524", "#FFE0A3"]

# --------------------------------------------------------------------------
# Type scale (font_size values for Tex / MathTex) -- frame is 14.22 x 8 units
# --------------------------------------------------------------------------
FS_TITLE = 60      # film title only
FS_CHAPTER = 34    # chapter header (top-left)
FS_FORMULA = 42    # hero formulas
FS_CAPTION = 32    # one-line captions at the bottom
FS_LABEL = 26      # axis titles, annotations
FS_TICK = 22       # tick numbers (never go below 20)

config.background_color = BG
Tex.set_default(color=INK)
MathTex.set_default(color=INK)


# --------------------------------------------------------------------------
# Data
# --------------------------------------------------------------------------
def _ns(obj):
    if isinstance(obj, dict):
        return SimpleNamespace(**{k: _ns(v) for k, v in obj.items()})
    if isinstance(obj, list) and obj and all(isinstance(v, (int, float)) for v in obj):
        return np.array(obj, dtype=float)
    if (
        isinstance(obj, list)
        and obj
        and all(isinstance(v, list) for v in obj)
        and all(isinstance(x, (int, float)) for v in obj for x in v)
    ):
        return np.array(obj, dtype=float)
    return obj


@lru_cache(maxsize=1)
def load_data() -> SimpleNamespace:
    """The model's real numbers (see build_data.py).

    ``D = load_data()`` then e.g. ``D.kernel.win_mass`` (46,), ``D.stock.surface``
    (46, 15) indexed [age, d-1], ``D.arrivals.surface`` (15, 15) indexed
    [t-1, d-1], ``D.forecast.total`` (15,). Lists of records (``D.lifelines``,
    ``D.monte_carlo.particles``, ``D.arrivals.history``) stay plain lists of dicts.
    """
    raw = json.loads(DATA_PATH.read_text())
    lifelines = raw.pop("lifelines")
    particles = raw["monte_carlo"].pop("particles")
    history = raw["arrivals"].pop("history")
    dow_means = raw["arrivals"].pop("dow_means")
    D = _ns(raw)
    D.lifelines = lifelines
    D.monte_carlo.particles = particles
    D.arrivals.history = history
    D.arrivals.dow_means = {int(k): float(v) for k, v in dow_means.items()}
    return D


# --------------------------------------------------------------------------
# Colour helpers
# --------------------------------------------------------------------------
def ramp_color(stops, x: float) -> ManimColor:
    """Colour at position ``x`` in [0, 1] along a list of hex stops."""
    x = float(np.clip(x, 0.0, 1.0))
    n = len(stops) - 1
    i = min(int(x * n), n - 1)
    return interpolate_color(ManimColor(stops[i]), ManimColor(stops[i + 1]), x * n - i)


# --------------------------------------------------------------------------
# Text helpers
# --------------------------------------------------------------------------
def caption(text: str, color=INK, font_size: int = FS_CAPTION) -> Tex:
    """One-line caption in the standard bottom position. ``text`` is LaTeX text
    (math goes inside ``$...$``)."""
    cap = Tex(text, font_size=font_size, color=color)
    if cap.width > 12.6:
        cap.scale_to_fit_width(12.6)
    cap.to_edge(DOWN, buff=0.45)
    return cap


def chapter_header(number: int, title: str, accent=INK) -> VGroup:
    """Small persistent chapter tag for the top-left corner."""
    num = Tex(rf"\textbf{{{number:02d}}}", font_size=FS_CHAPTER, color=accent)
    bar = Line(UP * 0.2, DOWN * 0.2, color=GRID, stroke_width=3)
    name = Tex(title, font_size=FS_CHAPTER, color=INK)
    group = VGroup(num, bar, name).arrange(RIGHT, buff=0.22)
    group.to_corner(UL, buff=0.45)
    return group


def open_chapter(scene: Scene, number: int, title: str, accent=INK, hold: float = 0.9) -> VGroup:
    """Standard chapter opening: big centred card that settles into the top-left
    header. Returns the header (already on screen). Works in 2D and 3D scenes."""
    header = chapter_header(number, title, accent)
    card = header.copy().scale(1.9).move_to(ORIGIN)
    rule = Line(LEFT, RIGHT, color=accent, stroke_width=3)
    rule.stretch_to_fit_width(card.width)
    rule.next_to(card, DOWN, buff=0.3)
    if isinstance(scene, ThreeDScene):
        fix_in_frame(scene, card, rule)
    scene.play(FadeIn(card, shift=UP * 0.25), Create(rule), run_time=0.9)
    scene.wait(hold)
    scene.play(
        Transform(card, header),
        FadeOut(rule, shift=UP * 0.2),
        run_time=0.9,
        rate_func=smooth,
    )
    return card


def close_chapter(scene: Scene, run_time: float = 0.9) -> None:
    """Standard chapter ending: everything fades to the background colour so the
    clips concatenate seamlessly."""
    mobs = [m for m in scene.mobjects]
    if mobs:
        scene.play(*[FadeOut(m) for m in mobs], run_time=run_time)
    scene.wait(0.25)


# --------------------------------------------------------------------------
# 2D chart builders
# --------------------------------------------------------------------------
AXIS_STYLE = dict(
    include_tip=False,
    stroke_color=MUTED,
    stroke_width=2,
    include_numbers=False,
    tick_size=0.06,
)


def make_axes(x_range, y_range, x_length, y_length, **kwargs) -> Axes:
    """2D axes in the house style (thin muted lines, no tips, no numbers --
    add tick labels with ``tick_labels``)."""
    cfg = dict(AXIS_STYLE)
    cfg.update(kwargs.pop("axis_config", {}))
    return Axes(
        x_range=x_range,
        y_range=y_range,
        x_length=x_length,
        y_length=y_length,
        axis_config=cfg,
        tips=False,
        **kwargs,
    )


def tick_labels(axes: Axes, x_values=(), y_values=(), fmt_x="{:g}", fmt_y="{:g}", font_size=FS_TICK) -> VGroup:
    """Tick numbers placed just outside the axes. Returns VGroup(x_labels, y_labels)."""
    xs = VGroup()
    for v in x_values:
        lab = MathTex(fmt_x.format(v), font_size=font_size, color=MUTED)
        lab.next_to(axes.c2p(v, axes.y_range[0]), DOWN, buff=0.14)
        xs.add(lab)
    ys = VGroup()
    for v in y_values:
        lab = MathTex(fmt_y.format(v), font_size=font_size, color=MUTED)
        lab.next_to(axes.c2p(axes.x_range[0], v), LEFT, buff=0.14)
        ys.add(lab)
    return VGroup(xs, ys)


def bars(axes: Axes, xs, heights, color, width: float = 0.8, fill_opacity: float = 0.9, bottoms=None) -> VGroup:
    """Vertical bars sitting on ``axes`` (one Rectangle per value; ``bottoms``
    stacks them). Zero-height bars are kept (as hairlines) so indices line up."""
    xs = np.asarray(xs, dtype=float)
    heights = np.asarray(heights, dtype=float)
    bottoms = np.zeros_like(heights) if bottoms is None else np.asarray(bottoms, dtype=float)
    unit_x = axes.x_axis.unit_size
    unit_y = axes.y_axis.unit_size
    group = VGroup()
    for x, h, b in zip(xs, heights, bottoms):
        rect = Rectangle(
            width=width * unit_x,
            height=max(h * unit_y, 1e-3),
            stroke_width=0,
            fill_color=color,
            fill_opacity=fill_opacity,
        )
        rect.move_to(axes.c2p(x, b), aligned_edge=DOWN)
        group.add(rect)
    return group


def hbars(axes: Axes, ys, lengths, color, height: float = 0.8, fill_opacity: float = 0.9, to_left: bool = False) -> VGroup:
    """Horizontal bars growing from the y-axis of ``axes`` (rightwards, or
    leftwards if ``to_left`` -- then x on the axes is read as a magnitude)."""
    unit_x = axes.x_axis.unit_size
    unit_y = axes.y_axis.unit_size
    group = VGroup()
    for y, length in zip(np.asarray(ys, dtype=float), np.asarray(lengths, dtype=float)):
        rect = Rectangle(
            width=max(length * unit_x, 1e-3),
            height=height * unit_y,
            stroke_width=0,
            fill_color=color,
            fill_opacity=fill_opacity,
        )
        rect.move_to(axes.c2p(0, y), aligned_edge=RIGHT if to_left else LEFT)
        group.add(rect)
    return group


def curve(axes: Axes, xs, ys, color, stroke_width: float = 4, smooth: bool = True) -> VMobject:
    """Polyline / smooth curve through data points on ``axes``."""
    pts = [axes.c2p(x, y) for x, y in zip(xs, ys)]
    path = VMobject(color=color, stroke_width=stroke_width)
    if smooth:
        path.set_points_smoothly(pts)
    else:
        path.set_points_as_corners(pts)
    return path


def area_under(axes: Axes, xs, ys, color, opacity: float = 0.25, smooth: bool = True) -> VMobject:
    """Filled area between a data curve and the x-axis of ``axes``."""
    top = curve(axes, xs, ys, color, smooth=smooth)
    region = VMobject(stroke_width=0, fill_color=color, fill_opacity=opacity)
    region.set_points(top.points)
    region.add_line_to(axes.c2p(xs[-1], 0))
    region.add_line_to(axes.c2p(xs[0], 0))
    region.add_line_to(axes.c2p(xs[0], ys[0]))
    return region


def heat_grid(matrix, cell_w: float, cell_h: float, ramp, vmax: float | None = None) -> VGroup:
    """Flat heat-map: one filled Rectangle per cell, row 0 at the bottom.

    The lower-left corner of the grid is at ORIGIN; cell (i, j) is
    ``grid[i * n_cols + j]``. ``grid.vmax`` stores the colour-scale maximum.
    """
    M = np.asarray(matrix, dtype=float)
    rows, cols = M.shape
    if vmax is None:
        vmax = float(np.percentile(M, 99)) if np.any(M > 0) else 1.0
    grid = VGroup()
    for i in range(rows):
        for j in range(cols):
            c = ramp_color(ramp, M[i, j] / vmax)
            cell = Rectangle(
                width=cell_w,
                height=cell_h,
                stroke_color=c,
                stroke_width=0.8,   # same-colour hairline hides anti-aliasing seams
                fill_color=c,
                fill_opacity=1.0,
            )
            cell.move_to([(j + 0.5) * cell_w, (i + 0.5) * cell_h, 0.0])
            grid.add(cell)
    grid.n_rows, grid.n_cols, grid.vmax = rows, cols, vmax
    return grid


# --------------------------------------------------------------------------
# 3D builders
# --------------------------------------------------------------------------
CAM_3D = dict(phi=62 * DEGREES, theta=-58 * DEGREES)   # standard perspective view
CAM_TOP = dict(phi=0 * DEGREES, theta=-90 * DEGREES)   # straight down: x right, y up


def fix_in_frame(scene: ThreeDScene, *mobjects) -> None:
    """Pin 2D overlays (text, formulas, legends) to the screen in a 3D scene.
    Call this BEFORE animating them in."""
    scene.add_fixed_in_frame_mobjects(*mobjects)
    scene.remove(*mobjects)
def make_axes_3d(x_range, y_range, z_range, x_length, y_length, z_length, **kwargs) -> ThreeDAxes:
    """3D axes in the house style."""
    cfg = dict(AXIS_STYLE)
    cfg.update(kwargs.pop("axis_config", {}))
    return ThreeDAxes(
        x_range=x_range,
        y_range=y_range,
        z_range=z_range,
        x_length=x_length,
        y_length=y_length,
        z_length=z_length,
        axis_config=cfg,
        tips=False,
        **kwargs,
    )


def ribbon_3d(top_points, floor_points, color, fill_opacity: float = 0.55, stroke_width: float = 2.5) -> VGroup:
    """A vertical "curtain": the filled sheet between a 3D polyline
    (``top_points``) and its shadow on the floor (``floor_points``), plus the
    bright edge line on top. Cheap to render and depth-sorts correctly.

    Returns VGroup(sheet, edge).
    """
    top_points = [np.array(p, dtype=float) for p in top_points]
    floor_points = [np.array(p, dtype=float) for p in floor_points]
    sheet = Polygon(
        *top_points,
        *reversed(floor_points),
        stroke_width=0,
        fill_color=color,
        fill_opacity=fill_opacity,
    )
    sheet.set_shade_in_3d(True)
    edge = VMobject(color=color, stroke_width=stroke_width)
    edge.set_points_as_corners(top_points)
    edge.set_shade_in_3d(True)
    return VGroup(sheet, edge)


def floor_tiles_3d(axes: ThreeDAxes, matrix, x_values, y_values, ramp, vmax: float | None = None, z: float = 0.0) -> VGroup:
    """Heat-map tiles lying on the floor (or any height ``z``) of 3D axes.

    ``matrix[i, j]`` is drawn as a tile centred at (x_values[j], y_values[i]).
    Seen from straight above this is exactly the README heat-map.
    Tile (i, j) is ``tiles[i * n_cols + j]``.
    """
    M = np.asarray(matrix, dtype=float)
    rows, cols = M.shape
    if vmax is None:
        vmax = float(np.percentile(M, 99)) if np.any(M > 0) else 1.0
    dx = (x_values[1] - x_values[0]) / 2 if cols > 1 else 0.5
    dy = (y_values[1] - y_values[0]) / 2 if rows > 1 else 0.5
    tiles = VGroup()
    for i in range(rows):
        for j in range(cols):
            c = ramp_color(ramp, M[i, j] / vmax)
            x, y = x_values[j], y_values[i]
            tile = Polygon(
                axes.c2p(x - dx, y - dy, z),
                axes.c2p(x + dx, y - dy, z),
                axes.c2p(x + dx, y + dy, z),
                axes.c2p(x - dx, y + dy, z),
                stroke_color=c,
                stroke_width=0.8,
                fill_color=c,
                fill_opacity=1.0,
            )
            tiles.add(tile)
    tiles.n_rows, tiles.n_cols, tiles.vmax = rows, cols, vmax
    return tiles
