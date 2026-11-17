"""Shared visual language for every chapter of the explainer film.

Import with ``from common import *`` at the top of a scene file. Everything a
viewer should perceive as "the same thing" across chapters lives here: palette,
type scale, the data bundle, chapter open/close, captions, and geometry
builders for charts, heat-maps and 3D ribbons.

Only the coordinator edits this file. Authors work around gaps in their own
scene file and report them.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from manim import *  # noqa: F401,F403

HERE = Path(__file__).resolve().parent
DATA_PATH = HERE / "data" / "bundle.json"

# --------------------------------------------------------------------------
# Palette: dark theme, a few saturated hues
# --------------------------------------------------------------------------
BG = "#0E1117"        # frame background
PANEL = "#151B23"     # subtle panel fill
INK = "#E6EDF3"       # primary text / neutral marks
MUTED = "#8B949E"     # secondary text, axes, ticks
GRID = "#2A313C"      # grid lines, faint outlines

AMBER = "#F5A524"
ROSE = "#E5637D"
BLUE = "#4FA3F7"
TEAL = "#2DD4BF"
LAVENDER = "#C4B5FD"
SLATE = "#64748B"

# >>> PROJECT: alias every concept of the film to exactly ONE hue, and use only
# >>> the aliases in scenes (formulas are coloured like the objects they denote).
# e.g.  KERNEL = AMBER ; STOCK = ROSE ; ARRIVALS = BLUE ; TOTAL = TEAL

# --------------------------------------------------------------------------
# Type scale (font_size for Tex / MathTex); the frame is 14.22 x 8 units
# --------------------------------------------------------------------------
FS_TITLE = 60      # film title only
FS_CHAPTER = 34    # chapter header (top-left)
FS_FORMULA = 42    # hero formulas
FS_CAPTION = 32    # one-line captions at the bottom
FS_LABEL = 26      # axis titles, annotations
FS_TICK = 22       # tick numbers: the floor for any text on screen

config.background_color = BG
Tex.set_default(color=INK)
MathTex.set_default(color=INK)


# --------------------------------------------------------------------------
# Data bundle
# --------------------------------------------------------------------------
def _ns(obj):
    if isinstance(obj, dict):
        converted = {k: _ns(v) for k, v in obj.items()}
        if all(str(k).isidentifier() for k in obj):
            return SimpleNamespace(**converted)
        return converted
    if isinstance(obj, list) and obj:
        flat = all(isinstance(v, (int, float)) for v in obj)
        nested = all(isinstance(v, list) and v and all(isinstance(x, (int, float)) for x in v) for v in obj)
        if flat or nested:
            return np.array(obj, dtype=float)
    return obj


@lru_cache(maxsize=1)
def load_data() -> SimpleNamespace:
    """The project's real numbers, written by ``build_data.py``.

    Dicts become attribute namespaces, numeric lists become numpy arrays, lists
    of records stay lists of dicts.
    """
    return _ns(json.loads(DATA_PATH.read_text()))


# --------------------------------------------------------------------------
# Colour helpers
# --------------------------------------------------------------------------
def ramp_for(color, highlight: float = 0.55) -> list:
    """Heat-map ramp for one hue: background -> hue -> pale highlight, so value 0
    disappears into the frame."""
    base = ManimColor(color)
    stops = [interpolate_color(ManimColor(BG), base, s) for s in (0.0, 0.22, 0.48, 0.74, 1.0)]
    stops.append(interpolate_color(base, ManimColor("#FFFFFF"), highlight))
    return stops


def ramp_color(stops, x: float) -> ManimColor:
    """Colour at position ``x`` in [0, 1] along a list of colour stops."""
    x = float(np.clip(x, 0.0, 1.0))
    n = len(stops) - 1
    i = min(int(x * n), n - 1)
    return interpolate_color(ManimColor(stops[i]), ManimColor(stops[i + 1]), x * n - i)


# --------------------------------------------------------------------------
# Chapters and captions
# --------------------------------------------------------------------------
def fix_in_frame(scene, *mobjects) -> None:
    """Pin 2D overlays (text, formulas, legends) to the screen in a 3D scene.
    Call BEFORE animating them in. Harmless in a 2D scene."""
    if isinstance(scene, ThreeDScene):
        scene.add_fixed_in_frame_mobjects(*mobjects)
        scene.remove(*mobjects)


def caption(text: str, color=INK, font_size: int = FS_CAPTION) -> Tex:
    """One-line caption in the standard bottom position (LaTeX text; math in $...$)."""
    cap = Tex(text, font_size=font_size, color=color)
    if cap.width > 12.6:
        cap.scale_to_fit_width(12.6)
    cap.to_edge(DOWN, buff=0.45)
    return cap


def swap_caption(scene, old, text, **kwargs) -> Tex:
    """Replace the caption: the old line leaves, THEN the new one arrives, so two
    captions are never superimposed. ``old`` may be None; returns the new caption."""
    new = caption(text, **kwargs) if isinstance(text, str) else text
    fix_in_frame(scene, new)
    if old is not None:
        scene.play(FadeOut(old, shift=UP * 0.15), run_time=0.3)
    scene.play(FadeIn(new, shift=UP * 0.15), run_time=0.45)
    return new


def chapter_header(number: int, title: str, accent=INK) -> VGroup:
    """Small persistent chapter tag for the top-left corner."""
    num = Tex(rf"\textbf{{{number:02d}}}", font_size=FS_CHAPTER, color=accent)
    bar = Line(UP * 0.2, DOWN * 0.2, color=GRID, stroke_width=3)
    name = Tex(title, font_size=FS_CHAPTER, color=INK)
    group = VGroup(num, bar, name).arrange(RIGHT, buff=0.22)
    group.to_corner(UL, buff=0.45)
    return group


def film_title(scene, title: str, subtitle: str, hold: float = 1.8) -> None:
    """Opening card of the film (first chapter only): title, subtitle, clear."""
    t = Tex(title, font_size=FS_TITLE)
    s = Tex(subtitle, font_size=FS_LABEL, color=MUTED)
    card = VGroup(t, s).arrange(DOWN, buff=0.4)
    fix_in_frame(scene, card)
    scene.play(FadeIn(t, shift=UP * 0.2), run_time=0.9)
    scene.play(FadeIn(s), run_time=0.6)
    scene.wait(hold)
    scene.play(FadeOut(card), run_time=0.7)


def open_chapter(scene, number: int, title: str, accent=INK, hold: float = 0.9) -> VGroup:
    """Standard chapter opening: centred card that settles into the top-left
    header. Returns the header (on screen, pinned in 3D scenes)."""
    header = chapter_header(number, title, accent)
    card = header.copy().scale(1.9).move_to(ORIGIN)
    rule = Line(LEFT, RIGHT, color=accent, stroke_width=3)
    rule.stretch_to_fit_width(card.width)
    rule.next_to(card, DOWN, buff=0.3)
    fix_in_frame(scene, card, rule)
    scene.play(FadeIn(card, shift=UP * 0.25), Create(rule), run_time=0.9)
    scene.wait(hold)
    scene.play(Transform(card, header), FadeOut(rule, shift=UP * 0.2), run_time=0.9)
    return card


def close_chapter(scene, run_time: float = 0.9) -> None:
    """Standard chapter ending: everything fades to the background, so chapters
    concatenate seamlessly."""
    mobs = list(scene.mobjects)
    if mobs:
        scene.play(*[FadeOut(m) for m in mobs], run_time=run_time)
    scene.wait(0.25)


# --------------------------------------------------------------------------
# 2D chart builders
# --------------------------------------------------------------------------
AXIS_STYLE = dict(include_tip=False, stroke_color=MUTED, stroke_width=2, include_numbers=False, tick_size=0.06)


def make_axes(x_range, y_range, x_length, y_length, **kwargs) -> Axes:
    """2D axes in the house style (thin, muted, no tips; label with ``tick_labels``).

    Manim draws the y-axis at x = 0 whenever 0 lies inside ``x_range``. For data
    with negative x that should have its axis on the left edge, plot against
    ``x - x_min`` and write the tick labels by hand.
    """
    cfg = dict(AXIS_STYLE)
    cfg.update(kwargs.pop("axis_config", {}))
    return Axes(x_range=x_range, y_range=y_range, x_length=x_length, y_length=y_length,
                axis_config=cfg, tips=False, **kwargs)


def tick_labels(axes: Axes, x_values=(), y_values=(), fmt_x="{:g}", fmt_y="{:g}", font_size=FS_TICK) -> VGroup:
    """Tick numbers just outside the axes. Returns VGroup(x_labels, y_labels)."""
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
    """Vertical bars on ``axes`` (``bottoms`` stacks them). Zero-height bars are
    kept as hairlines so indices line up. Build before rotating axes into 3D."""
    xs = np.asarray(xs, dtype=float)
    heights = np.asarray(heights, dtype=float)
    bottoms = np.zeros_like(heights) if bottoms is None else np.asarray(bottoms, dtype=float)
    ux, uy = axes.x_axis.unit_size, axes.y_axis.unit_size
    group = VGroup()
    for x, h, b in zip(xs, heights, bottoms):
        rect = Rectangle(width=width * ux, height=max(h * uy, 1e-3), stroke_width=0,
                         fill_color=color, fill_opacity=fill_opacity)
        rect.move_to(axes.c2p(x, b), aligned_edge=DOWN)
        group.add(rect)
    return group


def hbars(axes: Axes, ys, lengths, color, height: float = 0.8, fill_opacity: float = 0.9, to_left: bool = False) -> VGroup:
    """Horizontal bars growing from the y-axis of ``axes`` (leftwards if ``to_left``)."""
    ux, uy = axes.x_axis.unit_size, axes.y_axis.unit_size
    group = VGroup()
    for y, length in zip(np.asarray(ys, dtype=float), np.asarray(lengths, dtype=float)):
        rect = Rectangle(width=max(length * ux, 1e-3), height=height * uy, stroke_width=0,
                         fill_color=color, fill_opacity=fill_opacity)
        rect.move_to(axes.c2p(0, y), aligned_edge=RIGHT if to_left else LEFT)
        group.add(rect)
    return group


def curve(axes: Axes, xs, ys, color, stroke_width: float = 4, smooth: bool = True) -> VMobject:
    """Smooth curve (or polyline) through data points on ``axes``."""
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


def heat_grid(matrix, cell_w: float, cell_h: float, ramp, vmax: float | None = None, origin: str = "lower") -> VGroup:
    """Flat heat-map, one filled Rectangle per cell, lower-left corner at ORIGIN.

    ``origin="lower"`` draws matrix row 0 at the bottom, ``"upper"`` at the top.
    Cell (i, j) of the matrix is ``grid[i * n_cols + j]`` either way; animate it
    by rows or columns (VGroups of cells), never 900 separate animations.
    """
    M = np.asarray(matrix, dtype=float)
    rows, cols = M.shape
    if vmax is None:
        vmax = float(np.percentile(M, 99)) if np.any(M > 0) else 1.0
    grid = VGroup()
    for i in range(rows):
        row_y = i if origin == "lower" else rows - 1 - i
        for j in range(cols):
            c = ramp_color(ramp, M[i, j] / vmax)
            cell = Rectangle(width=cell_w, height=cell_h, stroke_color=c, stroke_width=0.8,
                             fill_color=c, fill_opacity=1.0)   # same-colour hairline hides seams
            cell.move_to([(j + 0.5) * cell_w, (row_y + 0.5) * cell_h, 0.0])
            grid.add(cell)
    grid.n_rows, grid.n_cols, grid.vmax = rows, cols, vmax
    return grid


# --------------------------------------------------------------------------
# 3D builders (Cairo renderer)
# --------------------------------------------------------------------------
CAM_3D = dict(phi=62 * DEGREES, theta=-58 * DEGREES)   # standard perspective view
CAM_TOP = dict(phi=0 * DEGREES, theta=-90 * DEGREES)   # straight down: x right, y up


def delayed(start: float, length: float, rate_func=smooth):
    """Rate function that runs inside [start, start + length] of an animation.
    Use it to stagger 3D animations without LaggedStart (which re-adds its group
    on top and breaks far-to-near draw order), and to time fades inside
    ``move_camera(added_anims=...)``, which stretches them to the camera's run_time."""
    def f(t):
        return rate_func(float(np.clip((t - start) / length, 0.0, 1.0)))
    return f


class DepthPoly(Polygon):
    """Polygon depth-sorted by where it stands on the floor, not by its bounding-box
    centre, so a tall ribbon never pops in front of a short one nearer the camera."""
    depth_bias = 0.0

    def get_z_index_reference_point(self):
        if not len(self.points):
            return ORIGIN
        p = self.points.mean(axis=0)
        return np.array([p[0], p[1] - self.depth_bias, 0.0])


class DepthPath(VMobject):
    """Stroke that sorts with (and just in front of) the DepthPoly it outlines.
    The bias assumes the camera sits on the -y side, as in CAM_3D."""
    depth_bias = 1e-3

    def get_z_index_reference_point(self):
        if not len(self.points):
            return ORIGIN
        p = self.points.mean(axis=0)
        return np.array([p[0], p[1] - self.depth_bias, 0.0])


def ribbon_3d(top_points, floor_points, color, fill_opacity: float = 0.3, stroke_width: float = 2.5) -> VGroup:
    """A vertical curtain: the sheet between a 3D polyline and its shadow on the
    floor, plus the bright edge on top. Returns VGroup(sheet, edge).

    Keep sheets faint and let edges carry the shape; add ribbons far-to-near.
    For dozens of crossing paths drop the sheet (opacity 0) and depth-grade the
    edges instead (near: bright and thick, far: dim and thin).
    """
    top_points = [np.array(p, dtype=float) for p in top_points]
    floor_points = [np.array(p, dtype=float) for p in floor_points]
    sheet = DepthPoly(*top_points, *reversed(floor_points), stroke_width=0,
                      fill_color=color, fill_opacity=fill_opacity)
    edge = DepthPath(color=color, stroke_width=stroke_width)
    edge.set_points_as_corners(top_points)
    group = VGroup(sheet, edge)
    group.set_shade_in_3d(True)
    return group


def floor_tiles_3d(c2p, matrix, x_values, y_values, ramp, vmax: float | None = None, z: float = 0.0) -> VGroup:
    """Heat-map tiles lying on the floor of a 3D scene; from straight above
    (CAM_TOP) this IS the flat heat-map.

    ``c2p(x, y, z)`` maps data to scene coordinates: pass ``axes.c2p`` or your own
    function. ``matrix[i, j]`` is centred at (x_values[j], y_values[i]); tile
    (i, j) is ``tiles[i * n_cols + j]``. Tiles are unshaded, so they draw on top
    of shaded ribbons: fade ribbons out (or flatten them) as tiles come in.
    """
    M = np.asarray(matrix, dtype=float)
    rows, cols = M.shape
    if vmax is None:
        vmax = float(np.percentile(M, 99)) if np.any(M > 0) else 1.0
    dx = abs(x_values[1] - x_values[0]) / 2 if cols > 1 else 0.5
    dy = abs(y_values[1] - y_values[0]) / 2 if rows > 1 else 0.5
    tiles = VGroup()
    for i in range(rows):
        for j in range(cols):
            c = ramp_color(ramp, M[i, j] / vmax)
            x, y = x_values[j], y_values[i]
            tiles.add(Polygon(c2p(x - dx, y - dy, z), c2p(x + dx, y - dy, z),
                              c2p(x + dx, y + dy, z), c2p(x - dx, y + dy, z),
                              stroke_color=c, stroke_width=0.8, fill_color=c, fill_opacity=1.0))
    tiles.n_rows, tiles.n_cols, tiles.vmax = rows, cols, vmax
    return tiles
