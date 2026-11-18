"""Shared visual language for every chapter of the pipeline-forecast explainer.

Import with ``from common import *`` at the top of a scene file. Everything a
viewer should perceive as "the same thing" across chapters lives here: palette,
type, the data bundle, chapter cards and teaching devices (guiding question,
takeaway, definition card, callout, counter), captions, 2D chart builders, and
the 3D builders, including ``HeatTowers``: a 3D heat-map that flattens into the
flat heat-map and collapses onto a wall into its marginal bar chart.

Only the coordinator edits this file. Authors work around gaps in their own
scene file and report them. Once chapters are approved, add a parameter rather
than change a default: every chapter was reviewed with the defaults it saw.
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

# part labels for open_chapter(part=PART[n])
PART = {
    1: r"Part 1 \textperiodcentered{} The setting",
    2: r"Part 2 \textperiodcentered{} How long deals take to decide",
    3: r"Part 3 \textperiodcentered{} Deals already open",
    4: r"Part 4 \textperiodcentered{} Deals not yet created",
    5: r"Part 5 \textperiodcentered{} Putting it together",
}

# --------------------------------------------------------------------------
# Type: Source Sans Pro for words (if installed), Computer Modern for maths
# --------------------------------------------------------------------------
FS_TITLE = 64      # film title only
FS_CHAPTER = 30    # chapter header (top-left)
FS_CARD = 54       # chapter title on the opening card
FS_FORMULA = 44    # hero formulas
FS_CAPTION = 34    # one-line captions at the bottom
FS_BODY = 30       # definition-card bodies, callouts
FS_LABEL = 27      # axis titles, annotations
FS_TICK = 22       # tick numbers: the floor for any text on screen


TEXT_FONT = "Source Sans Pro"
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


def shade(color, f: float) -> ManimColor:
    """``color`` darkened towards the background (f = 1 unchanged, 0 = BG)."""
    return interpolate_color(ManimColor(BG), ManimColor(color), f)


# --------------------------------------------------------------------------
# Text, captions and chapter structure
# --------------------------------------------------------------------------
_CAMERA = [None]     # the 3D scene's camera, for helpers that create pieces later (TexCounter)


def fix_in_frame(scene, *mobjects) -> None:
    """Pin 2D overlays (text, formulas, legends) to the screen in a 3D scene.
    Call BEFORE animating them in. Harmless in a 2D scene."""
    if isinstance(scene, ThreeDScene):
        _CAMERA[0] = scene.renderer.camera
        scene.add_fixed_in_frame_mobjects(*mobjects)
        scene.remove(*mobjects)


def text_line(text, font_size: int = FS_LABEL, color=INK, colors=()) -> Tex:
    """Tex from a string, or from a list of parts where ``colors[i]`` (or None)
    colours part i: the way to colour a symbol inside a sentence. Parts are
    joined with no space, so put the spaces inside them."""
    parts = [text] if isinstance(text, str) else list(text)
    t = Tex(*parts, font_size=font_size, color=color)
    for i, c in enumerate(colors):
        if c is not None:
            t[i].set_color(c)
    return t


def caption(text, color=INK, font_size: int = FS_CAPTION, colors=()) -> Tex:
    """One-line caption in the standard bottom position. ``text`` is a string or
    a list of parts coloured by ``colors`` (see ``text_line``)."""
    cap = text_line(text, font_size, color, colors)
    if cap.width > 12.4:
        cap.scale_to_fit_width(12.4)
    cap.to_edge(DOWN, buff=0.5)
    return cap


def swap_caption(scene, old, text, *also, **kwargs) -> Tex:
    """Replace the caption: the old line leaves (any ``also`` animations, such as
    dimming or a panel leaving, ride along), THEN the new one arrives, so two
    captions are never superimposed. ``old`` may be None; ``text`` may be a
    ready caption mobject. Returns the new caption. Hold every caption at least
    3 s. To change a caption DURING another animation use ``caption_swap``."""
    new = text if isinstance(text, Mobject) else caption(text, **kwargs)
    fix_in_frame(scene, new)
    out = [FadeOut(old, shift=UP * 0.12, rate_func=delayed(0.0, 0.5 if also else 1.0))] if old is not None else []
    if out or also:
        scene.play(*out, *also, run_time=0.8 if also else 0.4)
    scene.play(FadeIn(new, shift=UP * 0.12), run_time=0.6)
    return new


def caption_swap(scene, old, text, run_time: float, at: float = 0.0, **kwargs):
    """``swap_caption`` as animations that ride inside a longer play (a slide, a
    rescale, a camera move) of ``run_time`` seconds: the old line leaves over
    [at, at + 0.4] s, the new one arrives over [at + 0.5, at + 1.1] s.
    Returns ``(new_caption, animations)``. Leave ``rate_func`` off that play:
    a play-level rate_func overrides these timings."""
    rt = float(run_time)
    assert rt >= at + 1.1, "caption_swap needs run_time >= at + 1.1 s"
    new = text if isinstance(text, Mobject) else caption(text, **kwargs)
    fix_in_frame(scene, new)
    anims = [FadeIn(new, shift=UP * 0.12, rate_func=delayed((at + 0.5) / rt, 0.6 / rt))]
    if old is not None:
        anims.insert(0, FadeOut(old, shift=UP * 0.12, rate_func=delayed(at / rt, 0.4 / rt)))
    return new, anims


def chapter_header(number: int, title: str, accent=INK) -> VGroup:
    """Small persistent chapter tag for the top-left corner."""
    num = Tex(rf"\textbf{{{number:02d}}}", font_size=FS_CHAPTER, color=accent)
    bar = Line(UP * 0.18, DOWN * 0.18, color=GRID, stroke_width=3)
    name = Tex(title, font_size=FS_CHAPTER, color=INK)
    group = VGroup(num, bar, name).arrange(RIGHT, buff=0.2)
    group.to_corner(UL, buff=0.42)
    return group


def film_title(scene, title: str, subtitle: str, accent=TEAL, hold: float = 2.6) -> None:
    """Opening card of the film (first chapter only): title, rule, subtitle, clear."""
    t = Tex(title, font_size=FS_TITLE)
    rule = Line(LEFT * 2.2, RIGHT * 2.2, color=accent, stroke_width=3)
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
    question (the one the takeaway answers); then the title settles into the
    top-left header and the rest fades. Returns the header (on screen, pinned in
    3D scenes)."""
    header = chapter_header(number, title, accent)
    num = Tex(rf"\textbf{{{number:02d}}}", font_size=FS_CARD, color=accent)
    name = Tex(title, font_size=FS_CARD, color=INK)
    head = VGroup(num, Line(UP * 0.32, DOWN * 0.32, color=GRID, stroke_width=4), name).arrange(RIGHT, buff=0.3)
    rule = Line(LEFT, RIGHT, color=accent, stroke_width=3).stretch_to_fit_width(head.width)
    parts = [head, rule]
    q = None
    if question:
        q = Tex(rf"\textit{{{question}}}", font_size=FS_CAPTION + 2, color=MUTED)
        if q.width > 11.5:
            q.scale_to_fit_width(11.5)
        parts.append(q)
    card = VGroup(*parts).arrange(DOWN, buff=0.36).move_to(UP * 0.2)
    p = Tex(part, font_size=FS_LABEL, color=accent).next_to(card, UP, buff=0.5) if part else None
    extras = [m for m in (rule, q, p) if m is not None]
    fix_in_frame(scene, head, *extras)
    scene.play(FadeIn(head, shift=UP * 0.2), Create(rule), *([FadeIn(p)] if p else []), run_time=1.0)
    if q is not None:
        scene.play(FadeIn(q, shift=UP * 0.12), run_time=0.8)
    scene.wait(hold)
    scene.play(Transform(head, header), *[FadeOut(m, shift=UP * 0.15) for m in extras], run_time=1.0)
    return head


def takeaway(scene, text, accent=INK, old_caption=None, hold: float = 3.2, colors=(), also=()) -> VGroup:
    """The chapter's one-line answer to its guiding question, in the caption
    slot: an accent tick and the line, held ``hold`` seconds. ``text`` may be a
    list of parts coloured by ``colors``; ``also`` animations ride along with
    the old caption's exit."""
    line = text_line(text, FS_CAPTION, INK, colors)
    if line.width > 11.6:
        line.scale_to_fit_width(11.6)
    tick = RoundedRectangle(width=0.1, height=line.height + 0.16, corner_radius=0.05,
                            fill_color=accent, fill_opacity=1, stroke_width=0)
    group = VGroup(tick, line).arrange(RIGHT, buff=0.25).to_edge(DOWN, buff=0.5)
    fix_in_frame(scene, group)
    first = list(also) + ([FadeOut(old_caption, shift=UP * 0.12)] if old_caption is not None else [])
    if first:
        scene.play(*first, run_time=0.8 if also else 0.4)
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


# --------------------------------------------------------------------------
# Teaching devices
# --------------------------------------------------------------------------
def definition_card(term: str, lines, color=INK, width: float = 4.6, icon: Mobject | None = None,
                    aside: str | None = None) -> VGroup:
    """A panel that defines one term: the coloured term (an optional ``icon``
    to its left, an optional muted ``aside`` such as an abbreviation to its
    right) over one to three short body lines; a body line may be a list of
    parts, coloured like ``text_line(parts, colors=...)`` via (parts, colors).
    Returns VGroup(panel, accent, title_row, body). The icon sits above the
    panel in z, so a dot can fly into it in the same play as the panel's FadeIn."""
    title = Tex(rf"\textbf{{{term}}}", font_size=FS_BODY + 4, color=color)
    row = [icon.copy().set_z_index(2)] if icon is not None else []
    row.append(title)
    if aside:
        row.append(Tex(aside, font_size=FS_BODY - 2, color=MUTED))
    title_row = VGroup(*row).arrange(RIGHT, buff=0.22)
    body = VGroup()
    for s in lines:
        body.add(text_line(s[0], FS_BODY - 2, INK, s[1]) if isinstance(s, tuple) else Tex(s, font_size=FS_BODY - 2))
    body.arrange(DOWN, aligned_edge=LEFT, buff=0.14)
    inner = VGroup(title_row, body).arrange(DOWN, aligned_edge=LEFT, buff=0.24)
    w = max(width, inner.width + 0.6)
    panel = RoundedRectangle(width=w, height=inner.height + 0.55, corner_radius=0.14,
                             fill_color=PANEL, fill_opacity=0.96, stroke_color=PANEL_EDGE, stroke_width=1.5)
    accent = Line(panel.get_corner(UL) + RIGHT * 0.14, panel.get_corner(UR) + LEFT * 0.14,
                  color=color, stroke_width=3)
    inner.move_to(panel).align_to(panel, LEFT).shift(RIGHT * 0.3)
    return VGroup(panel, accent, title_row, body)


def callout(text, point, direction=UR, color=INK, length: float = 0.9, font_size: int = FS_LABEL) -> VGroup:
    """Label with a thin leader line to a small dot at ``point``. ``text`` is a
    string or a list of lines. Returns VGroup(dot, line, label)."""
    point = np.array(point, dtype=float)
    d = np.array(direction, dtype=float)
    d = d / (np.linalg.norm(d) or 1.0)
    end = point + d * length
    dot = Dot(point, radius=0.045, color=color)
    line = Line(point, end, color=color, stroke_width=1.6)
    if isinstance(text, str):
        label = Tex(text, font_size=font_size, color=color)
    else:
        label = VGroup(*[Tex(s, font_size=font_size, color=color) for s in text]).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
    label.next_to(end, d if abs(d[0]) < 0.2 else np.sign(d[0]) * RIGHT, buff=0.1)
    return VGroup(dot, line, label)


def legend_item(text: str, color, mark: str = "dot") -> VGroup:
    """Legend row: a dot, square or line swatch and a label."""
    if mark == "dot":
        sw = Dot(radius=0.08, color=color)
    elif mark == "line":
        sw = Line(LEFT * 0.18, RIGHT * 0.18, color=color, stroke_width=4)
    else:
        sw = Square(0.2, fill_color=color, fill_opacity=1, stroke_width=0)
    return VGroup(sw, Tex(text, font_size=FS_LABEL, color=INK)).arrange(RIGHT, buff=0.16)


def dot_grid(rows: int = 10, cols: int = 10, spacing: float = 0.34, radius: float = 0.09, color=INK) -> VGroup:
    """The motif as a population (a cohort of 100): rows x cols dots centred at
    ORIGIN; dot index = row * cols + col, row 0 on top. Recolour each dot on the
    beat its state changes, never later: a dot keeps telling its state."""
    g = VGroup()
    for s in range(rows * cols):
        r, c = divmod(s, cols)
        g.add(Dot([(c - (cols - 1) / 2) * spacing, ((rows - 1) / 2 - r) * spacing, 0], radius=radius, color=color))
    return g


def cohort_grid(spacing: float = 0.34, radius: float = 0.09, color=OPEN) -> VGroup:
    """The film's cohort of 100 brand-new opportunities: a 10 x 10 grid of dots
    centred at ORIGIN. Dot index = ``slot`` in ``D.cohort.dots`` (row = slot // 10
    from the top, column = slot % 10). Open dots are lavender; recolour a dot WON
    or LOST at the age ``D.cohort.dots[slot]["age"]`` it resolves."""
    return dot_grid(10, 10, spacing, radius, color)


class TexCounter(VGroup):
    """A number that changes on screen, in the film's text font. Use it instead
    of ``Integer(mob_class=Tex)``, which falls back to Computer Modern digits on
    ``set_value``. It swaps whole cached numbers and blanks the old glyphs
    (Cairo keeps drawing the family list captured when a play started), and
    keeps its ``edge`` (LEFT, RIGHT, or ORIGIN for the centre) in place."""

    def __init__(self, value, fmt: str = "{:d}", font_size: int = FS_LABEL, color=INK, edge=LEFT):
        super().__init__()
        self.fmt, self.fs, self.tex_color, self.edge = fmt, font_size, color, np.array(edge, dtype=float)
        self.integer = fmt.endswith("d}")
        self.cache, self.value = {}, value
        self.add(self._make(value))

    def _key(self, v) -> str:
        return self.fmt.format(int(round(v)) if self.integer else v)

    def _make(self, v):
        key = self._key(v)
        if key not in self.cache:
            self.cache[key] = Tex(key, font_size=self.fs, color=self.tex_color)
        return self.cache[key].copy()

    def set_value(self, v):
        same = self._key(v) == self._key(self.value)
        self.value = v
        if same:
            return self
        new = self._make(v)
        anchor = self.get_critical_point(self.edge) if np.any(self.edge) else self.get_center()
        new.move_to(anchor, aligned_edge=self.edge)
        old = list(self.submobjects)
        self.remove(*old)
        self.add(new)
        cam = _CAMERA[0]
        if cam is not None and self in cam.fixed_in_frame_mobjects:
            cam.add_fixed_in_frame_mobjects(new)       # a pinned counter stays pinned
        for m in old:
            for f in m.get_family():
                f.points = np.zeros((0, 3))
        return self

    def count_to(self, v1, rate_func=smooth) -> Animation:
        """Animation: count from the current value to ``v1``."""
        v0 = self.value

        def update(mob, alpha):
            self.set_value(v0 + (v1 - v0) * rate_func(alpha))

        return UpdateFromAlphaFunc(self, update, rate_func=linear)


def hatched_rect(x0: float, x1: float, y0: float, y1: float, color, step: float = 0.11) -> VGroup:
    """Outlined, faintly filled, diagonally hatched rectangle: the look of a
    pooled or special bucket (e.g. "45 days or older"). Returns VGroup(rect, hatch)."""
    rect = Rectangle(width=x1 - x0, height=y1 - y0, stroke_color=color, stroke_width=1.6,
                     fill_color=color, fill_opacity=0.28)
    rect.move_to([(x0 + x1) / 2, (y0 + y1) / 2, 0])
    w = x1 - x0
    hatch = VGroup()
    c = y0 - w
    while c < y1:
        sx, sy, ex, ey = x0, c, x1, c + w
        if sy < y0:
            sx, sy = x0 + (y0 - sy), y0
        if ey > y1:
            ex, ey = x1 - (ey - y1), y1
        if ex - sx > 0.02:
            hatch.add(Line([sx, sy, 0], [ex, ey, 0], color=color, stroke_width=1.6))
        c += step
    return VGroup(rect, hatch)


# --------------------------------------------------------------------------
# 2D charts
# --------------------------------------------------------------------------
class Chart:
    """A 2D plot frame with explicit linear maps from data to scene coordinates.

    Reach for it where ``Axes`` does not fit: bars centred on integers (with
    ``x_range=(-0.6, n + 0.6)`` bar 0 stands clear of the y-axis), an axis
    that rescales, an axis that changes meaning, or charts sharing a baseline.
    A Chart is geometry, not a mobject: its builders return mobjects.
    ``origin`` is the scene point of the lower-left corner (x_range[0], y_range[0]).

    Rescale: ``new = chart.with_range(y_range=(0, 12))``, then Transform each
    mark into its ``new`` build and swap the tick labels sequentially (old out,
    then new in). Data should fill at least 60% of the plot height.
    """

    def __init__(self, x_range, y_range, width: float, height: float, origin=ORIGIN):
        self.x_range = (float(x_range[0]), float(x_range[1]))
        self.y_range = (float(y_range[0]), float(y_range[1]))
        self.width, self.height = float(width), float(height)
        self.origin = np.array(origin, dtype=float)
        self.ux = self.width / (self.x_range[1] - self.x_range[0])    # scene units per data unit
        self.uy = self.height / (self.y_range[1] - self.y_range[0])

    def with_range(self, x_range=None, y_range=None) -> "Chart":
        """The same frame with a new data range (for an animated rescale)."""
        return Chart(x_range or self.x_range, y_range or self.y_range, self.width, self.height, self.origin)

    def p(self, x, y=None) -> np.ndarray:
        """Scene point of data (x, y); y defaults to the bottom of the range."""
        y = self.y_range[0] if y is None else y
        return self.origin + np.array([(x - self.x_range[0]) * self.ux, (y - self.y_range[0]) * self.uy, 0.0])

    def axes(self, color=MUTED, stroke_width: float = 2) -> VGroup:
        o = self.origin
        return VGroup(Line(o, o + RIGHT * self.width, color=color, stroke_width=stroke_width),
                      Line(o, o + UP * self.height, color=color, stroke_width=stroke_width))

    def x_ticks(self, values, labels=None, fmt: str = "{:g}", font_size: int = FS_TICK, color=MUTED) -> VGroup:
        g = VGroup()
        for i, v in enumerate(values):
            s = labels[i] if labels is not None else fmt.format(v)
            g.add(MathTex(s, font_size=font_size, color=color).next_to(self.p(v), DOWN, buff=0.16))
        return g

    def y_ticks(self, values, labels=None, fmt: str = "{:g}", grid: bool = False,
                font_size: int = FS_TICK, color=MUTED) -> VGroup:
        """VGroup(labels, grid_lines); grid lines are faint and span the frame."""
        labs, lines = VGroup(), VGroup()
        for i, v in enumerate(values):
            s = labels[i] if labels is not None else fmt.format(v)
            labs.add(MathTex(s, font_size=font_size, color=color).next_to(self.p(self.x_range[0], v), LEFT, buff=0.14))
            if grid:
                lines.add(Line(self.p(self.x_range[0], v), self.p(self.x_range[1], v), color=GRID, stroke_width=1))
        return VGroup(labs, lines)

    def x_title(self, text: str, font_size: int = FS_LABEL, color=MUTED) -> Tex:
        """Axis title in words with its unit, under the tick labels."""
        mid = self.p(0.5 * (self.x_range[0] + self.x_range[1]))
        return Tex(text, font_size=font_size, color=color).next_to(mid, DOWN, buff=0.62)

    def y_title(self, text: str, font_size: int = FS_LABEL, color=MUTED) -> Tex:
        """Axis title in words with its unit, above the top of the y-axis."""
        t = Tex(text, font_size=font_size, color=color)
        t.next_to(self.p(self.x_range[0], self.y_range[1]), UP, buff=0.25)
        return t.align_to(self.origin + LEFT * 0.45, LEFT)

    def bars(self, xs, heights, color, width: float = 0.8, bottoms=None, fill_opacity: float = 0.9) -> VGroup:
        """Bars ``width`` data units wide centred on ``xs``; ``bottoms`` stacks
        them. Zero-height bars are hairlines, so indices line up."""
        heights = np.asarray(heights, dtype=float)
        bottoms = np.zeros_like(heights) if bottoms is None else np.asarray(bottoms, dtype=float)
        g = VGroup()
        for x, h, b in zip(np.asarray(xs, dtype=float), heights, bottoms):
            r = Rectangle(width=width * self.ux, height=max(h * self.uy, 1e-3), stroke_width=0,
                          fill_color=color, fill_opacity=fill_opacity)
            g.add(r.move_to(self.p(x, b), aligned_edge=DOWN))
        return g

    def curve(self, xs, ys, color, stroke_width: float = 4, smooth: bool = True) -> VMobject:
        pts = [self.p(x, y) for x, y in zip(xs, ys)]
        path = VMobject(color=color, stroke_width=stroke_width)
        path.set_points_smoothly(pts) if smooth else path.set_points_as_corners(pts)
        return path

    def area(self, xs, ys, color, opacity: float = 0.25, smooth: bool = True) -> VMobject:
        top = self.curve(xs, ys, color, smooth=smooth)
        region = VMobject(stroke_width=0, fill_color=color, fill_opacity=opacity)
        region.set_points(top.points)
        for pt in (self.p(xs[-1], 0), self.p(xs[0], 0), self.p(xs[0], ys[0])):
            region.add_line_to(pt)
        return region

    def dots(self, xs, ys, color, radius: float = 0.06) -> VGroup:
        return VGroup(*[Dot(self.p(x, y), radius=radius, color=color) for x, y in zip(xs, ys)])


AXIS_STYLE = dict(include_tip=False, stroke_color=MUTED, stroke_width=2, include_numbers=False, tick_size=0.06)


def make_axes(x_range, y_range, x_length, y_length, **kwargs) -> Axes:
    """2D ``Axes`` in the house style (thin, muted, no tips; label with
    ``tick_labels``). Manim draws the y-axis at x = 0 whenever 0 lies inside
    ``x_range``; for bars centred on integers or a rescaling axis use ``Chart``."""
    cfg = dict(AXIS_STYLE)
    cfg.update(kwargs.pop("axis_config", {}))
    return Axes(x_range=x_range, y_range=y_range, x_length=x_length, y_length=y_length,
                axis_config=cfg, tips=False, **kwargs)


def tick_labels(axes: Axes, x_values=(), y_values=(), fmt_x="{:g}", fmt_y="{:g}", font_size=FS_TICK) -> VGroup:
    """Tick numbers just outside the axes. Returns VGroup(x_labels, y_labels)."""
    xs = VGroup(*[MathTex(fmt_x.format(v), font_size=font_size, color=MUTED)
                  .next_to(axes.c2p(v, axes.y_range[0]), DOWN, buff=0.14) for v in x_values])
    ys = VGroup(*[MathTex(fmt_y.format(v), font_size=font_size, color=MUTED)
                  .next_to(axes.c2p(axes.x_range[0], v), LEFT, buff=0.14) for v in y_values])
    return VGroup(xs, ys)


def bars(axes: Axes, xs, heights, color, width: float = 0.8, fill_opacity: float = 0.9, bottoms=None) -> VGroup:
    """Vertical bars on ``axes`` (``bottoms`` stacks them). Zero-height bars are
    kept as hairlines so indices line up."""
    heights = np.asarray(heights, dtype=float)
    bottoms = np.zeros_like(heights) if bottoms is None else np.asarray(bottoms, dtype=float)
    ux, uy = axes.x_axis.unit_size, axes.y_axis.unit_size
    group = VGroup()
    for x, h, b in zip(np.asarray(xs, dtype=float), heights, bottoms):
        rect = Rectangle(width=width * ux, height=max(h * uy, 1e-3), stroke_width=0,
                         fill_color=color, fill_opacity=fill_opacity)
        group.add(rect.move_to(axes.c2p(x, b), aligned_edge=DOWN))
    return group


def hbars(axes: Axes, ys, lengths, color, height: float = 0.8, fill_opacity: float = 0.9, to_left: bool = False) -> VGroup:
    """Horizontal bars growing from the y-axis of ``axes`` (leftwards if ``to_left``)."""
    ux, uy = axes.x_axis.unit_size, axes.y_axis.unit_size
    group = VGroup()
    for y, length in zip(np.asarray(ys, dtype=float), np.asarray(lengths, dtype=float)):
        rect = Rectangle(width=max(length * ux, 1e-3), height=height * uy, stroke_width=0,
                         fill_color=color, fill_opacity=fill_opacity)
        group.add(rect.move_to(axes.c2p(0, y), aligned_edge=RIGHT if to_left else LEFT))
    return group


def curve(axes: Axes, xs, ys, color, stroke_width: float = 4, smooth: bool = True) -> VMobject:
    """Smooth curve (or polyline) through data points on ``axes``."""
    pts = [axes.c2p(x, y) for x, y in zip(xs, ys)]
    path = VMobject(color=color, stroke_width=stroke_width)
    path.set_points_smoothly(pts) if smooth else path.set_points_as_corners(pts)
    return path


def area_under(axes: Axes, xs, ys, color, opacity: float = 0.25, smooth: bool = True) -> VMobject:
    """Filled area between a data curve and the x-axis of ``axes``."""
    top = curve(axes, xs, ys, color, smooth=smooth)
    region = VMobject(stroke_width=0, fill_color=color, fill_opacity=opacity)
    region.set_points(top.points)
    for pt in (axes.c2p(xs[-1], 0), axes.c2p(xs[0], 0), axes.c2p(xs[0], ys[0])):
        region.add_line_to(pt)
    return region


def heat_grid(matrix, cell_w: float, cell_h: float, ramp, vmax: float | None = None, origin: str = "lower") -> VGroup:
    """Flat heat-map, one filled Rectangle per cell, lower-left corner at ORIGIN.

    ``origin="lower"`` draws matrix row 0 at the bottom, ``"upper"`` at the top.
    Cell (i, j) is ``grid[i * n_cols + j]`` either way; animate it by rows or
    columns (VGroups of cells), never hundreds of separate animations.
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
CAM_3D = dict(phi=62 * DEGREES, theta=-58 * DEGREES)     # standard perspective view
CAM_TOP = dict(phi=0 * DEGREES, theta=-90 * DEGREES)     # straight down: x right, y up
CAM_FRONT = dict(phi=90 * DEGREES, theta=-90 * DEGREES)  # level, looking along +y: x right, z up


def delayed(start: float, length: float, rate_func=smooth):
    """Rate function that runs inside [start, start + length] of an animation
    (fractions of its run_time). Staggers 3D animations without LaggedStart
    (which re-adds its group on top and breaks far-to-near order) and times
    fades inside ``move_camera`` / ``cam_to``. A play-level ``rate_func``
    replaces it silently: set rate functions per animation."""
    def f(t):
        return rate_func(float(np.clip((t - start) / length, 0.0, 1.0)))
    return f


def setup_3d(scene, flat: bool = True) -> Mobject:
    """First line of every ThreeDScene's ``construct()``.

    - adds ``scene.host``, an empty mobject with a do-nothing updater, as the
      FIRST mobject. Every custom 3D animation here drives it, and because it
      always moves, every frame redraws and depth-sorts the whole scene. Without
      it a play that animates only a caption freezes the towers into Cairo's
      static background (they pop at the end, and lines added later paint on top).
    - registers the camera for ``FloorLine`` / ``FloorPoly``.
    - with ``flat``, turns off automatic lighting so faces keep their colours
      (``HeatTowers`` shades its own sides).

    Leave ``frame_center`` at ORIGIN until the first frame is rendered (after
    ``open_chapter``): Cairo keeps the frame centre of the first frame for
    every pinned overlay, so header, captions and formulas would stay shifted.
    """
    cam = scene.renderer.camera
    if flat:
        cam.should_apply_shading = False
    FloorLine.cam = cam
    host = VMobject()
    host.add_updater(lambda m, dt: None)
    scene.add(host)
    scene.host = host
    return host


def flat_shading(scene) -> None:
    """Only the lighting part of ``setup_3d``."""
    scene.renderer.camera.should_apply_shading = False


def _host(scene) -> Mobject:
    host = getattr(scene, "host", None)
    if host is None:
        raise RuntimeError("call setup_3d(self) at the start of construct()")
    return host


def view(phi: float, theta: float, zoom: float = 1.0, frame_center=ORIGIN) -> dict:
    """A camera framing in degrees, for ``cam_to``."""
    return dict(phi=phi * DEGREES, theta=theta * DEGREES, zoom=zoom, frame_center=np.array(frame_center, dtype=float))


def cam_to(scene, v: dict, run_time: float, added_anims=(), rate_func=smooth,
           zoom_dip: float = 0.0, fc_lead: float = 1.0) -> None:
    """Play a camera move to framing ``v`` (keys phi, theta, zoom, frame_center;
    missing keys stay as they are). ``zoom_dip`` lowers the zoom mid-move so
    nothing swings off-frame or through the formula; ``fc_lead`` < 1 makes the
    frame centre arrive early. Time ``added_anims`` with ``delayed``."""
    cam = scene.renderer.camera
    p0, t0, z0, f0 = cam.get_phi(), cam.get_theta(), cam.get_zoom(), np.array(cam.frame_center, dtype=float)
    p1, t1, z1 = v.get("phi", p0), v.get("theta", t0), v.get("zoom", z0)
    f1 = np.array(v.get("frame_center", f0), dtype=float)

    def update(_, alpha):
        s = rate_func(alpha)
        cam.set_phi(p0 + (p1 - p0) * s)
        cam.set_theta(t0 + (t1 - t0) * s)
        cam.set_zoom(z0 + (z1 - z0) * s - zoom_dip * np.sin(np.pi * alpha))
        cam.frame_center = f0 + (f1 - f0) * rate_func(min(1.0, alpha / fc_lead))

    scene.play(UpdateFromAlphaFunc(_host(scene), update, rate_func=linear), *added_anims, run_time=run_time)


def drift(scene, dtheta_deg: float, run_time: float, dphi_deg: float = 0.0) -> None:
    """A slow camera drift with eased ends: keeps a long 3D hold alive."""
    cam = scene.renderer.camera
    cam_to(scene, dict(phi=cam.get_phi() + dphi_deg * DEGREES, theta=cam.get_theta() + dtheta_deg * DEGREES),
           run_time, rate_func=rate_functions.ease_in_out_sine)


def pin_label(scene, mob, point, offset=ORIGIN):
    """Camera-facing label anchored at a 3D point with a fixed screen offset (it
    never drifts into the data during camera moves). Anchor and offset can be
    animated later with ``move_pins``. Returns ``mob``, not yet on screen."""
    mob.anchor = np.array(point, dtype=float)
    mob.offset = np.array(offset, dtype=float)
    mob.move_to(mob.anchor + mob.offset)
    scene.add_fixed_orientation_mobjects(mob, center_func=lambda m=mob: m.anchor)
    scene.remove(mob)
    return mob


def place_pin(mob, point=None, offset=None):
    """Move a pinned label instantly (while it is off screen)."""
    a = mob.anchor if point is None else np.array(point, dtype=float)
    o = mob.offset if offset is None else np.array(offset, dtype=float)
    mob.shift((a + o) - (mob.anchor + mob.offset))
    mob.anchor, mob.offset = a, o
    return mob


def move_pins(scene, items, rate_func=smooth) -> Animation:
    """Animation: slide pinned labels, so tick labels ride along when an axis
    slides or rescales. ``items`` are (mob, new_point or None, new_offset or None)."""
    data = []
    for mob, a1, o1 in items:
        a0, off0 = mob.anchor.copy(), mob.offset.copy()
        data.append((mob, a0, a0 if a1 is None else np.array(a1, dtype=float),
                     off0, off0 if o1 is None else np.array(o1, dtype=float)))

    def update(_, alpha):
        s = rate_func(alpha)
        for mob, a0, a1, off0, o1 in data:
            a, o = a0 + (a1 - a0) * s, off0 + (o1 - off0) * s
            mob.shift((a + o) - (mob.anchor + mob.offset))
            mob.anchor, mob.offset = a, o

    return UpdateFromAlphaFunc(_host(scene), update, rate_func=linear)


def slide(scene, mobs, delta, rate_func=smooth) -> Animation:
    """Animation: translate 3D mobjects (floor lines, axes) by ``delta`` without
    the copies ``.animate`` makes."""
    delta = np.array(delta, dtype=float)
    state = {"s": 0.0}

    def update(_, alpha):
        s = rate_func(alpha)
        for m in mobs:
            m.shift(delta * (s - state["s"]))
        state["s"] = s

    return UpdateFromAlphaFunc(_host(scene), update, rate_func=linear)


def hide_during(scene, mobs, a: float = 0.25, b: float = 0.75) -> Animation:
    """Animation for a camera move's ``added_anims``: fade ``mobs`` out over
    [0, a] of the move and back in over [b, 1] (labels that would sweep
    through a formula mid-move)."""
    def update(_, alpha):
        o = 1 - smooth(min(1.0, alpha / a)) if alpha < 0.5 else smooth(max(0.0, (alpha - b) / (1 - b)))
        for m in mobs:
            m.set_opacity(o)

    return UpdateFromAlphaFunc(_host(scene), update, rate_func=linear)


def pinned(scene, anim: Animation) -> Animation:
    """Wrap a Transform of pinned (fix_in_frame) text in a 3D scene: the pieces
    the animation creates are pinned as it starts, so no ghost copies float in
    3D. Where a symbol's glyph count changes, cross-fade instead."""
    orig = anim.begin
    cam = scene.renderer.camera

    def begin():
        orig()
        cam.add_fixed_in_frame_mobjects(anim.mobject)

    anim.begin = begin
    return anim


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
    edges instead (near: bright and thick, far: dim and thin)."""
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
    (CAM_TOP) this IS the flat heat-map. ``c2p(x, y, z)`` maps data to scene
    coordinates; ``matrix[i, j]`` is centred at (x_values[j], y_values[i]) and is
    ``tiles[i * n_cols + j]``. Tiles are unshaded, so they draw on top of shaded
    ribbons: fade ribbons out (or flatten them) as tiles come in."""
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


def _to_camera(cam) -> np.ndarray:
    phi, theta = cam.get_phi(), cam.get_theta()
    return np.array([np.sin(phi) * np.cos(theta), np.sin(phi) * np.sin(theta), np.cos(phi)])


class FloorLine(Line):
    """A line on the floor of a 3D scene that paints before (under) every shaded
    mobject at any camera angle: floor outlines, grid lines, a diagonal, a wall
    axis behind towers. Needs ``setup_3d(scene)``. The camera is held on the
    class, since an instance reference would be deep-copied by every fade."""
    cam = None

    def __init__(self, start, end, **kwargs):
        kwargs.setdefault("color", GRID)
        kwargs.setdefault("stroke_width", 1.5)
        super().__init__(start, end, **kwargs)
        self.set_shade_in_3d(True)

    def get_z_index_reference_point(self):
        if FloorLine.cam is None:
            raise RuntimeError("call setup_3d(self) before building FloorLines")
        return -1e3 * _to_camera(FloorLine.cam)


class FloorPoly(Polygon):
    """A filled polygon on the floor that paints under every shaded mobject (a
    highlighted region, an empty triangle). Needs ``setup_3d(scene)``."""

    def __init__(self, *points, **kwargs):
        super().__init__(*points, **kwargs)
        self.set_shade_in_3d(True)

    def get_z_index_reference_point(self):
        return -1e3 * _to_camera(FloorLine.cam)


def floor_grid(x0: float, x1: float, y0: float, y1: float, z: float = 0.0, nx: int = 0, ny: int = 0,
               color=GRID, stroke_width: float = 1.5) -> VGroup:
    """Floor outline (plus ``nx``/``ny`` interior grid lines) that paints under the
    towers. Returns a VGroup of FloorLines."""
    g = VGroup()
    corners = [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)]
    for a, b in zip(corners, corners[1:] + corners[:1]):
        g.add(FloorLine(a, b, color=color, stroke_width=stroke_width))
    for k in range(1, nx):
        x = x0 + (x1 - x0) * k / nx
        g.add(FloorLine((x, y0, z), (x, y1, z), color=color, stroke_width=stroke_width * 0.6))
    for k in range(1, ny):
        y = y0 + (y1 - y0) * k / ny
        g.add(FloorLine((x0, y, z), (x1, y, z), color=color, stroke_width=stroke_width * 0.6))
    return g


# ---- the 3D heat-map ------------------------------------------------------
_FACE_OFFSETS = {"top": (0.0, 0.0), "front": (0.0, -1.0), "back": (0.0, 1.0),
                 "left": (-1.0, 0.0), "right": (1.0, 0.0)}


class TowerFace(Polygon):
    """One face of a HeatTowers tower. Sorted by its tower's floor position (plus
    a small nudge towards the face's side and a tiny height term), so towers
    paint far-to-near and a stack paints bottom-to-top. ``heat_c`` is its own
    heat colour, which ``tint`` returns to."""

    def __init__(self, kind, **kwargs):
        super().__init__(ORIGIN, RIGHT * 1e-3, UP * 1e-3, **kwargs)
        self.kind = kind
        self.ref = np.zeros(3)
        self.heat_c = ManimColor(kwargs.get("fill_color", INK))
        self.set_shade_in_3d(True)

    def get_z_index_reference_point(self):
        return self.ref


class HeatTowers(VGroup):
    """A 3D heat-map: one tower per matrix cell, height = value, top colour from
    the ramp, sides shaded darker. From straight above (CAM_TOP) the flattened
    field IS the flat heat-map; ``collapse`` stacks the towers on a wall, where
    each stack IS the sum over one axis (the marginal bar chart); ``merge``
    turns the stacks into solid bars. In CAM_FRONT one raised row looks exactly
    like a 2D bar chart: start there and tilt for the cleanest 2D-to-3D hand-off.

    Geometry (scene units, floor at ``z0``): column j spans x in
    ``origin[0] + [j, j+1] * cell_w``; row i spans y in ``origin[1] + [r, r+1] * cell_d``
    with r = i (``row_origin="lower"``, row 0 nearest the camera) or rows-1-i
    (``"upper"``, row 0 farthest, like a heat-map with row 0 on top).
    Height = value * ``z_scale``. Cells with value <= ``min_value`` get no tower.
    Colour = ramp((value / vmax) ** gamma): a gamma of about 0.6 keeps mid-sized
    cells visible when a few cells dominate (use the same mapping on any colour bar).

    Only the faces a camera on the -y, +x side can see are built ("top",
    "front", "right"); pass ``sides=("front", "left")`` for a camera on the -x side.
    Towers below ``side_threshold`` * vmax get a top face only. Call
    ``setup_3d(scene)`` first. Position with shift/move_to only (no rotate or
    scale): the class keeps its own geometry state. Stays under about 1000
    faces on screen.

    ``towers.tower_list`` holds one VGroup of faces per tower with attributes
    ``i, j, value, k`` (k = index into the state arrays ``cx, cy, hw, hd, zb, h,
    base_h, ii, jj, vals``); select towers with numpy on ``ii`` / ``jj``.
    """

    def __init__(self, matrix, cell_w: float, cell_d: float, z_scale: float, ramp, vmax: float | None = None,
                 origin=ORIGIN, z0: float = 0.0, row_origin: str = "lower", gap: float = 0.12,
                 min_value: float = 1e-9, side_threshold: float = 0.03, sides=("front", "right"),
                 side_shade=(0.66, 0.46), stroke_width: float = 0.6, gamma: float = 1.0):
        super().__init__()
        M = np.asarray(matrix, dtype=float)
        self.M = M
        rows, cols = M.shape
        self.n_rows, self.n_cols = rows, cols
        self.vmax = float(vmax if vmax is not None else M.max())
        self.ramp, self.z_scale, self.cell_w, self.cell_d, self.gamma = ramp, z_scale, cell_w, cell_d, gamma
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
            top_c = ramp_color(ramp, (v / self.vmax) ** gamma)
            kinds = ["top"] if v < side_threshold * self.vmax else [*self.sides, "top"]
            faces = []
            for kind in kinds:
                c = self._face_color(top_c, kind)
                faces.append(TowerFace(kind, fill_color=c, fill_opacity=1.0, stroke_color=c, stroke_width=stroke_width))
            tower = VGroup(*faces)
            tower.i, tower.j, tower.value, tower.k = int(i), int(j), float(v), k
            self.tower_list.append(tower)
            self.add(tower)
        self._refresh()

    def _face_color(self, hue, kind, side_shade=None) -> ManimColor:
        ss = self.side_shade if side_shade is None else side_shade
        if kind == "top":
            return ManimColor(hue)
        return shade(hue, ss[0] if kind in ("front", "back") else ss[1])

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

    def set_lift(self, f: float, ks=None):
        """Immediately set towers ``ks`` (default all) to ``f`` times their native height."""
        ks = np.arange(len(self.tower_list)) if ks is None else np.asarray(ks, dtype=int)
        self.h[ks] = self.base_h[ks] * f
        self._refresh(ks)
        return self

    def set_tower_opacity(self, o: float, ks=None):
        """Immediately set the opacity of towers ``ks`` (default all)."""
        ks = range(len(self.tower_list)) if ks is None else ks
        for k in ks:
            for f in self.tower_list[k]:
                f.set_fill(opacity=o)
                f.set_stroke(opacity=o)
        return self

    def floor_center(self) -> np.ndarray:
        """Centre of the floor rectangle the towers stand on (scene coords)."""
        return np.array([0.5 * (self.cx.min() + self.cx.max()), 0.5 * (self.cy.min() + self.cy.max()), float(self.zb.min())])

    # -- animations ----------------------------------------------------------
    def _stagger(self, ks, order, lag: float):
        """Per-tower (start, length) inside [0, 1] for towers ``ks``."""
        n = len(ks)
        if order is None or lag <= 0:
            return np.zeros(n), np.ones(n)
        key = np.asarray(order(self), dtype=float)[ks]
        rank = (key - key.min()) / (np.ptp(key) or 1.0)
        return rank * lag, np.full(n, 1.0 - lag)

    def lift(self, f_from: float, f_to: float, order=None, lag: float = 0.0, rate_func=smooth,
             ks=None, fade_in: bool = False) -> Animation:
        """Animate towers ``ks`` (default all) from ``f_from`` to ``f_to`` times
        their native height: 1 -> 0 flattens the field into the heat-map, 0 -> 1
        raises it, 1 -> s rescales it. ``order(towers) -> key per tower`` with
        ``lag`` in [0, 1) staggers it (``order=lambda T: T.ii`` raises row 0
        first); ``fade_in`` raises each tower's opacity from 0 over the first
        30% of its rise."""
        ks = np.arange(len(self.tower_list)) if ks is None else np.asarray(ks, dtype=int)
        start, length = self._stagger(ks, order, lag)
        base = self.base_h[ks].copy()

        def update(mob, alpha):
            t = np.clip((alpha - start) / length, 0, 1)
            s = np.array([rate_func(x) for x in t])
            self.h[ks] = base * (f_from + (f_to - f_from) * s)
            self._refresh(ks)
            if fade_in:
                for k, o in zip(ks, np.clip(t / 0.3, 0, 1)):
                    self.set_tower_opacity(o, [k])

        return UpdateFromAlphaFunc(self, update)   # the play's default rate func eases it once more

    def tint(self, color_of, mix: float = 0.85, rate_func=smooth) -> Animation:
        """Animate a highlight. ``color_of(tower)`` returns a hue (the tower takes
        it, mixed ``mix`` into its heat colour, sides shaded), or None (back to
        its heat colour). ``BG`` with ``mix=0.75`` dims a tower. Light one row
        and dim the rest, or show which cells a formula sums:
        ``T.tint(lambda t: None if t.i == 8 else BG, mix=0.75)``; ``T.tint(lambda t: None)`` undoes it."""
        faces, c0, c1 = [], [], []
        for t in self.tower_list:
            hue = color_of(t)
            for f in t:
                faces.append(f)
                c0.append(f.get_fill_color())
                c1.append(f.heat_c if hue is None else interpolate_color(f.heat_c, self._face_color(hue, f.kind), mix))

        def update(mob, alpha):
            a = rate_func(alpha)
            for f, a0, a1 in zip(faces, c0, c1):
                c = interpolate_color(a0, a1, a)
                f.set_fill(c)
                f.set_stroke(c)

        return UpdateFromAlphaFunc(self, update, rate_func=linear)

    def collapse(self, axis: str = "y", wall: float | None = None, z_scale_wall: float | None = None,
                 wall_depth: float | None = None, lag: float = 0.55, rate_func=smooth) -> Animation:
        """Slide every tower onto a wall and stack it there: the stack in each
        column (axis="y", wall at the far y edge) or row (axis="x", wall at the
        +x edge) is the sum of that column/row - the marginal bar chart.
        The defaults ease twice and squeeze the visible slide into about a
        second (chapter 09 was approved that way); for a slide the eye can
        follow, play it with ``lag=0.35`` and ``rate_func=linear`` over 4-5 s,
        as chapter 07 does.

        Towers nearest the wall go first and land at the bottom of their stack;
        each slides, then rises into its slot, its height rescaled to
        ``value * z_scale_wall`` (default: unchanged). Then ``merge``.
        After the animation ``self.stack_tops`` maps column j (or row i) to the
        stack's top z, and ``self.wall`` holds the wall coordinate."""
        n = len(self.tower_list)
        zsw = self.z_scale if z_scale_wall is None else z_scale_wall
        if axis == "y":
            wall = (self.cy.max() + self.hd.max()) if wall is None else wall
            dist, group_of = wall - self.cy, self.jj
        else:
            wall = (self.cx.max() + self.hw.max()) if wall is None else wall
            dist, group_of = wall - self.cx, self.ii
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
            slide_, rise, size = seg(t, 0.0, 0.7), seg(t, 0.35, 1.0), seg(t, 0.1, 0.8)
            c = c0 + (tgt_c - c0) * slide_
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
        common = dict(min_value=1e-6, side_threshold=0.0, sides=self.sides, side_shade=self.side_shade,
                      stroke_width=self.stroke_w)
        if axis == "y":
            first = groups[0]
            ox = float(self.cx[self.jj == first][0] - (first + 0.5) * self.cell_w)
            M = np.zeros((1, max(groups) + 1))
            M[0, groups] = sums
            bars_ = HeatTowers(M, self.cell_w, 2 * dep, 1.0, ramp, vmax=1.0, origin=(ox, self.wall - 2 * dep, z_floor),
                               gap=1 - 2 * float(self.hw.max()) / self.cell_w, **common)
            bars_.hd[:] = dep
        else:
            M = np.zeros((max(groups) + 1, 1))
            M[groups, 0] = sums
            bars_ = HeatTowers(M, 2 * dep, self.cell_d, 1.0, ramp, vmax=1.0, origin=(self.wall - 2 * dep, 0, z_floor),
                               gap=1 - 2 * float(self.hd.max()) / self.cell_d, **common)
            for t in bars_.tower_list:
                bars_.cy[t.k] = float(self.cy[self.ii == t.i][0])
            bars_.hw[:] = dep
        for t in bars_.tower_list:
            for f in t:
                c = self._face_color(color, f.kind)
                f.set_fill(c, 1.0)
                f.set_stroke(c, self.stroke_w)
                f.heat_c = c
        bars_._refresh()
        return bars_

    def merge(self, scene, color, run_time: float = 1.2) -> "HeatTowers":
        """After ``collapse``: recolour the stacks to ``color``, then swap them for
        solid bars (``as_bars``) so no seams remain (the smallest towers have only
        a top face and would leave a bright rim at a stack's foot). Plays the
        animation and returns the bars (a HeatTowers with one tower per stack,
        ``.value`` = the stack's sum in scene units)."""
        scene.play(self.recolor(color), run_time=run_time)
        bars_ = self.as_bars(color)
        scene.add(bars_)
        scene.remove(self)
        return bars_

    def recolor(self, color, side_shade=None) -> Animation:
        """Animate every face to one hue (top) with shaded sides."""
        faces = [f for t in self.tower_list for f in t]
        c_from = [f.get_fill_color() for f in faces]
        c_to = [self._face_color(color, f.kind, side_shade) for f in faces]

        def update(mob, alpha):
            a = smooth(alpha)
            for f, c0, c1 in zip(faces, c_from, c_to):
                c = interpolate_color(c0, c1, a)
                f.set_fill(c, 1.0)
                f.set_stroke(c, self.stroke_w)

        return UpdateFromAlphaFunc(self, update)
