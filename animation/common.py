"""Shared visual language for every chapter of the pipeline-forecast explainer.

Import with ``from common import *`` at the top of a scene file. Everything a
viewer should perceive as "the same thing" across chapters lives here: palette,
type, the data bundle, chapter open/close, captions and teaching devices
(definition cards, callouts, takeaways), 2D chart builders, and the 3D builders
including ``HeatTowers``, the 3D heat-map both 3D chapters share.

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
DATA_PATH = HERE / "data" / "model_data.json"

# --------------------------------------------------------------------------
# Palette: dark theme, six saturated hues, one per concept
# --------------------------------------------------------------------------
BG = "#0E1117"        # frame background
PANEL = "#161C25"     # card / panel fill
PANEL_EDGE = "#2A3340"
INK = "#E6EDF3"       # primary text / neutral marks
MUTED = "#8B949E"     # secondary text, axes, ticks
GRID = "#2A313C"      # grid lines, faint outlines

AMBER = "#F5A524"
ROSE = "#E5637D"
BLUE = "#4FA3F7"
TEAL = "#2DD4BF"
LAVENDER = "#C4B5FD"
SLATE = "#7C8BA1"

KERNEL = AMBER        # the win kernel k(a), win hazard h_w(a), win counts w(a)
WON = AMBER           # a won opportunity (same hue as the kernel on purpose)
LOST = SLATE          # a lost opportunity, loss hazard h_l(a), loss counts l(a)
OPEN = LAVENDER       # still open: survival S(a), at-risk counts r(a)
SURVIVAL = LAVENDER
STOCK = ROSE          # the open pipeline today N(a) and everything derived from it
ARRIVALS = BLUE       # forecast arrivals A_hat(t) and everything derived from it
TOTAL = TEAL          # the combined forecast W_hat(d)

# heat-map colour ramps, dark -> bright (value 0 melts into the background)
STOCK_RAMP = [BG, "#3A1524", "#7A2A40", "#B5475B", "#E5637D", "#FFC2CD"]
ARRIVALS_RAMP = [BG, "#10263F", "#1B4A7C", "#2B6CB0", "#4FA3F7", "#C2E0FF"]
KERNEL_RAMP = [BG, "#3D2A0A", "#7A5210", "#B87A14", "#F5A524", "#FFE0A3"]

# --------------------------------------------------------------------------
# Type: Source Sans Pro for words, Computer Modern for maths
# --------------------------------------------------------------------------
FS_TITLE = 64      # film title only
FS_CHAPTER = 30    # chapter header (top-left)
FS_CARD = 54       # chapter title on the opening card
FS_FORMULA = 44    # hero formulas
FS_CAPTION = 34    # one-line captions at the bottom
FS_BODY = 30       # definition-card bodies, callouts
FS_LABEL = 27      # axis titles, annotations
FS_TICK = 22       # tick numbers: the floor for any text on screen

TEMPLATE = TexTemplate()
TEMPLATE.add_to_preamble(r"\usepackage[T1]{fontenc}")
TEMPLATE.add_to_preamble(r"\usepackage[default,semibold]{sourcesanspro}")
TEMPLATE.add_to_preamble(r"\usepackage{amsmath,amssymb}")

config.background_color = BG
Tex.set_default(color=INK, tex_template=TEMPLATE)
MathTex.set_default(color=INK, tex_template=TEMPLATE)


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
        flat = all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in obj)
        nested = all(isinstance(v, list) and v and all(isinstance(x, (int, float)) for x in v) for v in obj)
        if flat or nested:
            return np.array(obj, dtype=float)
    return obj


@lru_cache(maxsize=1)
def load_data() -> SimpleNamespace:
    """The model's real numbers, written by ``build_data.py`` (see GUIDE.md for
    the schema). Dicts become attribute namespaces, numeric lists numpy arrays,
    lists of records stay lists of dicts. ``D.arrivals.dow_means`` is keyed by
    int weekday (0 = Monday)."""
    raw = json.loads(DATA_PATH.read_text())
    dow = raw["arrivals"].pop("dow_means")
    D = _ns(raw)
    D.arrivals.dow_means = {int(k): float(v) for k, v in dow.items()}
    return D


# --------------------------------------------------------------------------
# Colour helpers
# --------------------------------------------------------------------------
def ramp_color(stops, x: float) -> ManimColor:
    """Colour at position ``x`` in [0, 1] along a list of colour stops."""
    x = float(np.clip(x, 0.0, 1.0))
    n = len(stops) - 1
    i = min(int(x * n), n - 1)
    return interpolate_color(ManimColor(stops[i]), ManimColor(stops[i + 1]), x * n - i)


def shade(color, f: float) -> ManimColor:
    """``color`` darkened towards the background (f = 1 unchanged, 0 = BG)."""
    return interpolate_color(ManimColor(BG), ManimColor(color), f)


# --------------------------------------------------------------------------
# Chapters, captions and teaching devices
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
    if cap.width > 12.4:
        cap.scale_to_fit_width(12.4)
    cap.to_edge(DOWN, buff=0.5)
    return cap


def swap_caption(scene, old, text, **kwargs) -> Tex:
    """Replace the caption: the old line leaves, THEN the new one arrives, so two
    captions are never superimposed. ``old`` may be None; returns the new caption.
    Hold every caption at least 3 s with nothing else demanding attention."""
    new = caption(text, **kwargs) if isinstance(text, str) else text
    fix_in_frame(scene, new)
    if old is not None:
        scene.play(FadeOut(old, shift=UP * 0.12), run_time=0.4)
    scene.play(FadeIn(new, shift=UP * 0.12), run_time=0.6)
    return new


def chapter_header(number: int, title: str, accent=INK) -> VGroup:
    """Small persistent chapter tag for the top-left corner."""
    num = Tex(rf"\textbf{{{number:02d}}}", font_size=FS_CHAPTER, color=accent)
    bar = Line(UP * 0.18, DOWN * 0.18, color=GRID, stroke_width=3)
    name = Tex(title, font_size=FS_CHAPTER, color=INK)
    group = VGroup(num, bar, name).arrange(RIGHT, buff=0.2)
    group.to_corner(UL, buff=0.42)
    return group


def film_title(scene, title: str, subtitle: str, hold: float = 2.6) -> None:
    """Opening card of the film (chapter 01 only): title, subtitle, clear."""
    t = Tex(title, font_size=FS_TITLE)
    rule = Line(LEFT * 2.2, RIGHT * 2.2, color=TEAL, stroke_width=3)
    s = Tex(subtitle, font_size=FS_LABEL + 3, color=MUTED)
    card = VGroup(t, rule, s).arrange(DOWN, buff=0.38)
    fix_in_frame(scene, card)
    scene.play(FadeIn(t, shift=UP * 0.2), run_time=1.1)
    scene.play(Create(rule), FadeIn(s, shift=UP * 0.1), run_time=0.9)
    scene.wait(hold)
    scene.play(FadeOut(card, shift=UP * 0.2), run_time=0.8)


def open_chapter(scene, number: int, title: str, accent=INK, question: str | None = None,
                 part: str | None = None, hold: float = 2.6) -> VGroup:
    """Chapter opening card: part label, number, title and the chapter's guiding
    question; then the title settles into the top-left header and the rest
    fades. Returns the header (on screen, pinned in 3D scenes)."""
    header = chapter_header(number, title, accent)
    num = Tex(rf"\textbf{{{number:02d}}}", font_size=FS_CARD, color=accent)
    name = Tex(title, font_size=FS_CARD, color=INK)
    head = VGroup(num, Line(UP * 0.32, DOWN * 0.32, color=GRID, stroke_width=4), name).arrange(RIGHT, buff=0.3)
    parts = [head]
    rule = Line(LEFT, RIGHT, color=accent, stroke_width=3).stretch_to_fit_width(head.width)
    parts.append(rule)
    q = None
    if question:
        q = Tex(rf"\textit{{{question}}}", font_size=FS_CAPTION + 2, color=MUTED)
        if q.width > 11.5:
            q.scale_to_fit_width(11.5)
        parts.append(q)
    card = VGroup(*parts).arrange(DOWN, buff=0.36).move_to(UP * 0.2)
    p = None
    if part:
        p = Tex(part, font_size=FS_LABEL, color=accent).next_to(card, UP, buff=0.5)
    extras = [m for m in (rule, q, p) if m is not None]
    fix_in_frame(scene, head, *extras)
    scene.play(FadeIn(head, shift=UP * 0.2), Create(rule), *([FadeIn(p)] if p else []), run_time=1.0)
    if q is not None:
        scene.play(FadeIn(q, shift=UP * 0.12), run_time=0.8)
    scene.wait(hold)
    scene.play(Transform(head, header), *[FadeOut(m, shift=UP * 0.15) for m in extras], run_time=1.0)
    return head


def takeaway(scene, text: str, accent=INK, old_caption=None, hold: float = 3.2) -> VGroup:
    """The chapter's one-line takeaway in the caption position: an accent tick and
    the line, held ``hold`` seconds. Replaces ``old_caption`` (sequentially)."""
    line = Tex(text, font_size=FS_CAPTION, color=INK)
    if line.width > 11.6:
        line.scale_to_fit_width(11.6)
    tick = RoundedRectangle(width=0.1, height=line.height + 0.16, corner_radius=0.05,
                            fill_color=accent, fill_opacity=1, stroke_width=0)
    group = VGroup(tick, line).arrange(RIGHT, buff=0.25).to_edge(DOWN, buff=0.5)
    fix_in_frame(scene, group)
    if old_caption is not None:
        scene.play(FadeOut(old_caption, shift=UP * 0.12), run_time=0.4)
    scene.play(GrowFromEdge(tick, DOWN), FadeIn(line, shift=RIGHT * 0.15), run_time=0.7)
    scene.wait(hold)
    return group


def close_chapter(scene, run_time: float = 1.0) -> None:
    """Standard chapter ending: everything fades to the background, so chapters
    concatenate seamlessly."""
    mobs = list(scene.mobjects)
    if mobs:
        scene.play(*[FadeOut(m) for m in mobs], run_time=run_time)
    scene.wait(0.3)


def definition_card(term: str, lines, color=INK, width: float = 4.6, icon: Mobject | None = None) -> VGroup:
    """A small panel that defines one term: coloured term (with an optional icon
    to its left) over one to three short body lines. Returns
    VGroup(panel, title_row, body); position it like any mobject."""
    title = Tex(rf"\textbf{{{term}}}", font_size=FS_BODY + 4, color=color)
    title_row = VGroup(icon.copy().set_z_index(2), title).arrange(RIGHT, buff=0.22) if icon is not None else VGroup(title)
    body = VGroup(*[Tex(s, font_size=FS_BODY - 2, color=INK) for s in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
    inner = VGroup(title_row, body).arrange(DOWN, aligned_edge=LEFT, buff=0.24)
    w = max(width, inner.width + 0.6)
    panel = RoundedRectangle(width=w, height=inner.height + 0.55, corner_radius=0.14,
                             fill_color=PANEL, fill_opacity=0.96, stroke_color=PANEL_EDGE, stroke_width=1.5)
    accent = Line(panel.get_corner(UL) + RIGHT * 0.14, panel.get_corner(UR) + LEFT * 0.14,
                  color=color, stroke_width=3)
    inner.move_to(panel).align_to(panel, LEFT).shift(RIGHT * 0.3)
    return VGroup(panel, accent, title_row, body)


def callout(text: str, point, direction=UR, color=INK, length: float = 0.9, font_size: int = FS_LABEL) -> VGroup:
    """Label with a thin leader line to a small dot at ``point``.
    Returns VGroup(dot, line, label)."""
    point = np.array(point, dtype=float)
    d = np.array(direction, dtype=float)
    d = d / (np.linalg.norm(d) or 1.0)
    end = point + d * length
    dot = Dot(point, radius=0.045, color=color)
    line = Line(point, end, color=color, stroke_width=1.6)
    label = Tex(text, font_size=font_size, color=color)
    label.next_to(end, d if abs(d[0]) < 0.2 else np.sign(d[0]) * RIGHT, buff=0.1)
    return VGroup(dot, line, label)


def cohort_grid(spacing: float = 0.34, radius: float = 0.09, color=OPEN) -> VGroup:
    """The film's cohort of 100 brand-new opportunities: a 10 x 10 grid of dots
    centred at ORIGIN. Dot index = ``slot`` in ``D.cohort.dots`` (row = slot // 10
    from the top, column = slot % 10). Open dots are lavender; recolour a dot WON
    or LOST at the age ``D.cohort.dots[slot]["age"]`` it resolves."""
    g = VGroup()
    for s in range(100):
        r, c = divmod(s, 10)
        g.add(Dot([(c - 4.5) * spacing, (4.5 - r) * spacing, 0], radius=radius, color=color))
    return g


def legend_item(text: str, color, mark: str = "dot") -> VGroup:
    """Legend row: a dot, square or line swatch and a label."""
    if mark == "dot":
        sw = Dot(radius=0.08, color=color)
    elif mark == "line":
        sw = Line(LEFT * 0.18, RIGHT * 0.18, color=color, stroke_width=4)
    else:
        sw = Square(0.2, fill_color=color, fill_opacity=1, stroke_width=0)
    return VGroup(sw, Tex(text, font_size=FS_LABEL, color=INK)).arrange(RIGHT, buff=0.16)


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
    kept as hairlines so indices line up."""
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
    by rows or columns (VGroups of cells), never 700 separate animations.
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
# 3D (Cairo renderer)
# --------------------------------------------------------------------------
CAM_3D = dict(phi=62 * DEGREES, theta=-58 * DEGREES)    # standard perspective view
CAM_TOP = dict(phi=0 * DEGREES, theta=-90 * DEGREES)    # straight down: x right, y up
CAM_FRONT = dict(phi=90 * DEGREES, theta=-90 * DEGREES)  # level, looking along +y: x right, z up


def flat_shading(scene) -> None:
    """Turn off the camera's automatic lighting so 3D faces keep the colours we
    give them (HeatTowers shade their sides themselves). Call once at the start
    of a ThreeDScene; depth sorting is unaffected."""
    scene.renderer.camera.should_apply_shading = False


def delayed(start: float, length: float, rate_func=smooth):
    """Rate function that runs inside [start, start + length] of an animation.
    Use it to stagger 3D animations without LaggedStart (which re-adds its group
    on top and breaks far-to-near draw order), and to time fades inside
    ``move_camera(added_anims=...)``, which stretches them to the camera's run_time."""
    def f(t):
        return rate_func(float(np.clip((t - start) / length, 0.0, 1.0)))
    return f


def pin_label(scene, mob, point, offset=ORIGIN):
    """Camera-facing label anchored at a 3D point with a fixed screen offset (it
    never drifts into the data during camera moves). Returns ``mob`` (not yet on
    screen: FadeIn it)."""
    A = np.array(point, dtype=float)
    mob.move_to(A + np.array(offset, dtype=float))
    scene.add_fixed_orientation_mobjects(mob, center_func=lambda: A)
    scene.remove(mob)
    return mob


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
    Keep sheets faint and let edges carry the shape; add ribbons far-to-near."""
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
    """Heat-map tiles lying on the floor of a 3D scene (unshaded, so they draw on
    top of every shaded mobject). ``c2p(x, y, z)`` maps data to scene coordinates."""
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


# ---- the 3D heat-map ------------------------------------------------------
_FACE_OFFSETS = {"top": (0.0, 0.0), "front": (0.0, -1.0), "back": (0.0, 1.0),
                 "left": (-1.0, 0.0), "right": (1.0, 0.0)}


class TowerFace(Polygon):
    """One face of a HeatTowers tower. Sorted by its tower's floor position (plus
    a small nudge towards the face's side and a tiny height term), so towers
    paint far-to-near and a stack paints bottom-to-top."""

    def __init__(self, kind, **kwargs):
        super().__init__(ORIGIN, RIGHT * 1e-3, UP * 1e-3, **kwargs)
        self.kind = kind
        self.ref = np.zeros(3)
        self.set_shade_in_3d(True)

    def get_z_index_reference_point(self):
        return self.ref


class HeatTowers(VGroup):
    """A 3D heat-map: one tower per matrix cell, height = value, top colour from
    the ramp, sides shaded darker. From straight above (CAM_TOP) the flattened
    field IS the flat heat-map; ``collapse`` stacks the towers on a wall, where
    each stack IS the sum over one axis (the marginal bar chart).

    Geometry (scene units, floor at ``z0``): column j spans x in
    ``origin[0] + [j, j+1] * cell_w``; row i spans y in ``origin[1] + [r, r+1] * cell_d``
    with r = i (``row_origin="lower"``, row 0 nearest the camera) or rows-1-i
    (``"upper"``, row 0 farthest, like a heat-map with row 0 on top).
    Height = value * ``z_scale``. Cells with value <= ``min_value`` get no tower.

    Only the faces a camera on the -y, +x side can see are built ("top",
    "front", "right"); pass ``sides=("front", "left")`` for a camera on the -x side.
    Towers below ``side_threshold`` * vmax get a top face only. Call
    ``flat_shading(scene)`` first. Position with shift/move_to only (no
    rotate/scale): the class keeps its own geometry state.

    ``towers.tower_list`` holds one VGroup per tower with attributes
    ``i, j, value, k`` (k = index into the state arrays).
    """

    def __init__(self, matrix, cell_w: float, cell_d: float, z_scale: float, ramp, vmax: float | None = None,
                 origin=ORIGIN, z0: float = 0.0, row_origin: str = "lower", gap: float = 0.12,
                 min_value: float = 1e-9, side_threshold: float = 0.03, sides=("front", "right"),
                 side_shade=(0.66, 0.46), stroke_width: float = 0.6):
        super().__init__()
        M = np.asarray(matrix, dtype=float)
        self.M = M
        rows, cols = M.shape
        self.n_rows, self.n_cols = rows, cols
        self.vmax = float(vmax if vmax is not None else M.max())
        self.ramp, self.z_scale, self.cell_w, self.cell_d = ramp, z_scale, cell_w, cell_d
        self.sides, self.side_shade, self.stroke_w = tuple(sides), side_shade, stroke_width
        origin = np.array(origin, dtype=float)
        hw0, hd0 = 0.5 * cell_w * (1 - gap), 0.5 * cell_d * (1 - gap)
        cells = [(i, j) for i in range(rows) for j in range(cols) if M[i, j] > min_value]
        n = len(cells)
        self.cx, self.cy = np.zeros(n), np.zeros(n)
        self.hw, self.hd = np.full(n, hw0), np.full(n, hd0)
        self.zb, self.h = np.full(n, float(z0)), np.zeros(n)
        self.base_h = np.zeros(n)
        self.tower_list = []
        self.ii, self.jj, self.vals = np.zeros(n, int), np.zeros(n, int), np.zeros(n)
        for k, (i, j) in enumerate(cells):
            v = M[i, j]
            r = i if row_origin == "lower" else rows - 1 - i
            self.cx[k] = origin[0] + (j + 0.5) * cell_w
            self.cy[k] = origin[1] + (r + 0.5) * cell_d
            self.h[k] = self.base_h[k] = v * z_scale
            self.ii[k], self.jj[k], self.vals[k] = i, j, v
            top_c = ramp_color(ramp, v / self.vmax)
            kinds = ["top"] if v < side_threshold * self.vmax else [*self.sides, "top"]
            faces = []
            for kind in kinds:
                f = 1.0 if kind == "top" else (side_shade[0] if kind in ("front", "back") else side_shade[1])
                c = shade(top_c, f)
                face = TowerFace(kind, fill_color=c, fill_opacity=1.0, stroke_color=c, stroke_width=stroke_width)
                faces.append(face)
            tower = VGroup(*faces)
            tower.i, tower.j, tower.value, tower.k = int(i), int(j), float(v), k
            self.tower_list.append(tower)
            self.add(tower)
        self._refresh()

    # -- geometry ------------------------------------------------------------
    def _refresh(self, ks=None):
        ks = range(len(self.tower_list)) if ks is None else ks
        for k in ks:
            cx, cy, hw, hd = self.cx[k], self.cy[k], self.hw[k], self.hd[k]
            zb = self.zb[k]
            zt = zb + max(self.h[k], 1e-3)
            x0, x1, y0, y1 = cx - hw, cx + hw, cy - hd, cy + hd
            for face in self.tower_list[k]:
                kind = face.kind
                if kind == "top":
                    pts = [(x0, y0, zt), (x1, y0, zt), (x1, y1, zt), (x0, y1, zt)]
                elif kind == "front":
                    pts = [(x0, y0, zb), (x1, y0, zb), (x1, y0, zt), (x0, y0, zt)]
                elif kind == "back":
                    pts = [(x1, y1, zb), (x0, y1, zb), (x0, y1, zt), (x1, y1, zt)]
                elif kind == "right":
                    pts = [(x1, y0, zb), (x1, y1, zb), (x1, y1, zt), (x1, y0, zt)]
                else:  # left
                    pts = [(x0, y1, zb), (x0, y0, zb), (x0, y0, zt), (x0, y1, zt)]
                face.set_points_as_corners([*pts, pts[0]])
                ox, oy = _FACE_OFFSETS[kind]
                face.ref = np.array([cx + 0.25 * ox * hw, cy + 0.25 * oy * hd,
                                     0.004 * (zb + 0.5 * (zt - zb)) + (0.002 if kind == "top" else 0.0)])

    def shift(self, *vectors):
        v = np.sum([np.array(u, dtype=float) for u in vectors], axis=0) if vectors else np.zeros(3)
        self.cx += v[0]
        self.cy += v[1]
        self.zb += v[2]
        self._refresh()
        return self

    def set_lift(self, f: float):
        """Immediately set every tower to ``f`` times its native height."""
        self.h[:] = self.base_h * f
        self._refresh()
        return self

    def floor_center(self) -> np.ndarray:
        """Centre of the floor rectangle the towers stand on (scene coords)."""
        return np.array([0.5 * (self.cx.min() + self.cx.max()), 0.5 * (self.cy.min() + self.cy.max()), float(self.zb.min())])

    # -- animations ----------------------------------------------------------
    def _stagger(self, order, lag: float):
        """Per-tower (start, length) inside [0, 1] for an animation."""
        n = len(self.tower_list)
        if order is None or lag <= 0:
            return np.zeros(n), np.ones(n)
        key = np.asarray(order(self), dtype=float)
        rank = (key - key.min()) / (np.ptp(key) or 1.0)
        length = 1.0 - lag
        return rank * lag, np.full(n, length)

    def lift(self, f_from: float, f_to: float, order=None, lag: float = 0.0, rate_func=smooth) -> Animation:
        """Animate every tower from ``f_from`` to ``f_to`` times its native height
        (1 -> 0 flattens the field into the heat-map; 0 -> 1 raises it).
        ``order(towers) -> key per tower`` with ``lag`` in [0, 1) staggers it,
        e.g. ``order=lambda T: T.ii`` raises row 0 first."""
        start, length = self._stagger(order, lag)
        base = self.base_h.copy()

        def update(mob, alpha):
            t = np.clip((alpha - start) / length, 0, 1)
            t = np.array([rate_func(x) for x in t])
            self.h[:] = base * (f_from + (f_to - f_from) * t)
            self._refresh()

        return UpdateFromAlphaFunc(self, update)

    def collapse(self, axis: str = "y", wall: float | None = None, z_scale_wall: float | None = None,
                 wall_depth: float | None = None, lag: float = 0.55, rate_func=smooth) -> Animation:
        """Slide every tower onto a wall and stack it there: the stack in each
        column (axis="y", wall at the far y edge) or row (axis="x", wall at the
        +x edge) is the sum of that column/row - the marginal bar chart.

        Towers nearest the wall go first and land at the bottom of their stack;
        each slides, then rises into its slot, its height rescaled to
        ``value * z_scale_wall`` (default: unchanged). Faces keep their colours;
        ``recolor`` them afterwards to merge each stack into one bar.
        After the animation ``self.stack_tops`` maps column j (or row i) to the
        stack's top z, and ``self.wall`` holds the wall coordinate."""
        n = len(self.tower_list)
        zsw = self.z_scale if z_scale_wall is None else z_scale_wall
        if axis == "y":
            wall = (self.cy.max() + self.hd.max()) if wall is None else wall
            dist = wall - self.cy
            group_of = self.jj
        else:
            wall = (self.cx.max() + self.hw.max()) if wall is None else wall
            dist = wall - self.cx
            group_of = self.ii
        dep = (self.hd.max() if axis == "y" else self.hw.max()) if wall_depth is None else wall_depth / 2
        tgt_c = np.full(n, wall - dep)
        tgt_zb = np.zeros(n)
        tgt_h = self.vals * zsw
        z_floor = float(self.zb.min())
        tops = {}
        for g in np.unique(group_of):
            ks = np.where(group_of == g)[0]
            ks = ks[np.argsort(dist[ks])]          # nearest the wall first -> bottom
            z = z_floor
            for k in ks:
                tgt_zb[k] = z
                z += tgt_h[k]
            tops[int(g)] = z
        start = (dist - dist.min()) / (np.ptp(dist) or 1.0) * lag
        length = 1.0 - lag
        c0 = (self.cy if axis == "y" else self.cx).copy()
        d0 = (self.hd if axis == "y" else self.hw).copy()
        zb0, h0 = self.zb.copy(), self.h.copy()

        def seg(t, a, b):
            return np.array([rate_func(x) for x in np.clip((t - a) / (b - a), 0, 1)])

        def update(mob, alpha):
            t = np.clip((alpha - start) / length, 0, 1)
            slide, rise, size = seg(t, 0.0, 0.7), seg(t, 0.35, 1.0), seg(t, 0.1, 0.8)
            c = c0 + (tgt_c - c0) * slide
            d = d0 + (dep - d0) * size
            if axis == "y":
                self.cy[:], self.hd[:] = c, d
            else:
                self.cx[:], self.hw[:] = c, d
            self.zb[:] = zb0 + (tgt_zb - zb0) * rise
            self.h[:] = h0 + (tgt_h - h0) * size
            self._refresh()

        self.stack_tops, self.wall, self.collapse_axis = tops, wall, axis
        return UpdateFromAlphaFunc(self, update)

    def as_bars(self, color) -> "HeatTowers":
        """After ``collapse``: one solid box per stack, exactly where the stack
        stands (same footprint, same total height), all faces in ``color``. Use
        ``merge`` to swap it in."""
        axis = self.collapse_axis
        groups = sorted(self.stack_tops)
        z_floor = float(self.zb.min())
        sums = np.array([self.stack_tops[g] - z_floor for g in groups])
        dep = (self.hd if axis == "y" else self.hw).max()
        ramp = [color, color]
        if axis == "y":
            first = groups[0]
            ox = float(self.cx[self.jj == first][0] - (first + 0.5) * self.cell_w)
            cols = max(groups) + 1
            M = np.zeros((1, cols))
            M[0, groups] = sums
            bars = HeatTowers(M, self.cell_w, 2 * dep, 1.0, ramp, vmax=1.0, origin=(ox, self.wall - 2 * dep, z_floor),
                              gap=1 - 2 * float(self.hw.max()) / self.cell_w, min_value=1e-6, side_threshold=0.0,
                              sides=self.sides, side_shade=self.side_shade, stroke_width=self.stroke_w)
            bars.hd[:] = dep
        else:
            first = groups[0]
            r0 = float(self.cy[self.ii == first][0])
            rows = max(groups) + 1
            M = np.zeros((rows, 1))
            M[groups, 0] = sums
            bars = HeatTowers(M, 2 * dep, self.cell_d, 1.0, ramp, vmax=1.0, origin=(self.wall - 2 * dep, 0, z_floor),
                              gap=1 - 2 * float(self.hd.max()) / self.cell_d, min_value=1e-6, side_threshold=0.0,
                              sides=self.sides, side_shade=self.side_shade, stroke_width=self.stroke_w)
            for t in bars.tower_list:
                g = t.i
                bars.cy[t.k] = float(self.cy[self.ii == g][0])
            bars.hw[:] = dep
        for t in bars.tower_list:
            for f in t:
                c = ManimColor(color) if f.kind == "top" else shade(color, self.side_shade[0] if f.kind in ("front", "back") else self.side_shade[1])
                f.set_fill(c, 1.0)
                f.set_stroke(c, self.stroke_w)
        bars._refresh()
        return bars

    def merge(self, scene, color, run_time: float = 1.2) -> "HeatTowers":
        """After ``collapse``: recolour the stacks to ``color``, then swap them for
        solid bars (``as_bars``) so no seams remain. Plays the animation and
        returns the bars (a HeatTowers with one tower per stack, ``.value`` =
        the stack's sum in scene units)."""
        scene.play(self.recolor(color), run_time=run_time)
        bars = self.as_bars(color)
        scene.add(bars)
        scene.remove(self)
        return bars

    def recolor(self, color, side_shade=None) -> Animation:
        """Animate every face to one hue (top) with shaded sides: merges the
        colourful stacks into solid bars after ``collapse``."""
        ss = self.side_shade if side_shade is None else side_shade
        faces = [f for t in self.tower_list for f in t]
        c_from = [f.get_fill_color() for f in faces]
        c_to = [ManimColor(color) if f.kind == "top" else shade(color, ss[0] if f.kind in ("front", "back") else ss[1])
                for f in faces]

        def update(mob, alpha):
            a = smooth(alpha)
            for f, c0, c1 in zip(faces, c_from, c_to):
                c = interpolate_color(c0, c1, a)
                f.set_fill(c, 1.0)
                f.set_stroke(c, self.stroke_w)

        return UpdateFromAlphaFunc(self, update)


class FloorLine(Line):
    """A line on the floor of a 3D scene that always paints before (under) every
    shaded mobject, whatever the camera angle: floor outlines, grid lines, the
    diagonal a + d = const. Build with ``FloorLine(scene, start, end, ...)``."""

    def __init__(self, scene, start, end, **kwargs):
        kwargs.setdefault("color", GRID)
        kwargs.setdefault("stroke_width", 1.5)
        super().__init__(start, end, **kwargs)
        self._cam = scene.renderer.camera
        self.set_shade_in_3d(True)

    def get_z_index_reference_point(self):
        phi, theta = self._cam.get_phi(), self._cam.get_theta()
        to_cam = np.array([np.sin(phi) * np.cos(theta), np.sin(phi) * np.sin(theta), np.cos(phi)])
        return -1e3 * to_cam


def floor_grid(scene, x0: float, x1: float, y0: float, y1: float, z: float = 0.0, nx: int = 0, ny: int = 0,
               color=GRID, stroke_width: float = 1.5) -> VGroup:
    """Floor outline (plus ``nx``/``ny`` interior grid lines) that paints under the
    towers. Returns VGroup of FloorLines."""
    g = VGroup()
    corners = [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)]
    for a, b in zip(corners, corners[1:] + corners[:1]):
        g.add(FloorLine(scene, a, b, color=color, stroke_width=stroke_width))
    for k in range(1, nx):
        x = x0 + (x1 - x0) * k / nx
        g.add(FloorLine(scene, (x, y0, z), (x, y1, z), color=color, stroke_width=stroke_width * 0.6))
    for k in range(1, ny):
        y = y0 + (y1 - y0) * k / ny
        g.add(FloorLine(scene, (x0, y, z), (x1, y, z), color=color, stroke_width=stroke_width * 0.6))
    return g


# --------------------------------------------------------------------------
# Film structure: part labels for open_chapter(part=...)
# --------------------------------------------------------------------------
PART = {
    1: r"Part 1 \textperiodcentered{} The setting",
    2: r"Part 2 \textperiodcentered{} How long deals take to decide",
    3: r"Part 3 \textperiodcentered{} Deals already open",
    4: r"Part 4 \textperiodcentered{} Deals not yet created",
    5: r"Part 5 \textperiodcentered{} Putting it together",
}
