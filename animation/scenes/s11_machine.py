"""Chapter 11 - The whole machine (finale).

Rebuilds docs/model-overview.png panel by panel in the order the film taught
it, runs the flow through it one path at a time, then shrinks the figure and
writes the one-line formula underneath, each term lighting up its panels.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import *

# ---------------------------------------------------------------------------
# Geometry (frame 14.22 x 8): a 3-column x 4-row twin of the README figure
# ---------------------------------------------------------------------------
H, NA = 15, 46
LX0, LX1 = -5.95, -4.30          # left column: N(a), A_hat(t)  (bars grow leftwards from LX1)
CX0, CX1 = -2.75, 2.75           # centre column: kernel, both heat-maps, forecast
RX0, RX1 = 4.30, 5.95            # right column: per-age / per-cohort totals (bars grow rightwards)
CW, SW = CX1 - CX0, LX1 - LX0
DAY_W = CW / H                   # one forecast day = one heat-map column = one forecast bar
BAR_W = DAY_W * 0.72

K_Y0, K_Y1 = 2.62, 3.50          # kernel
S_Y0, S_Y1 = 0.36, 2.00          # open-pipeline row
A_Y0, A_Y1 = -1.42, -0.24        # arrivals row
F_Y0, F_Y1 = -2.50, -1.66        # forecast
S_MID, A_MID = (S_Y0 + S_Y1) / 2, (A_Y0 + A_Y1) / 2
CH_S, CH_A = (S_Y1 - S_Y0) / NA, (A_Y1 - A_Y0) / H
GX = (LX1 + CX0) / 2             # centre of the left gap (operation glyphs)
BX = 3.30                        # kernel bus (right gap)
BUS_Y = K_Y0 + 0.55

SHRINK = 0.76                    # beat 4: the figure shrinks about its top centre
SHRINK_ABOUT = np.array([0.0, 3.50, 0.0])

PALE_ROSE, PALE_BLUE = "#FFC2CD", "#C2E0FF"
DIM = 0.70                       # fade() darkness for panels not being talked about


def fx(d):
    """x of forecast day d (1..15): centre of heat-map column d-1."""
    return CX0 + (d - 0.5) * DAY_W


def words(*parts, fs=FS_LABEL, color=INK, colors=None, anchor=ORIGIN):
    m = Tex(*parts, font_size=fs, color=color)
    for i, c in (colors or {}).items():
        m[i].set_color(c)
    m._fs, m._anchor = fs, anchor
    return m


def num(s, fs=FS_TICK, anchor=ORIGIN, color=MUTED):
    m = MathTex(s, font_size=fs, color=color)
    m._fs, m._anchor = fs, anchor
    return m


def box(x0, x1, y0, y1):
    return Rectangle(width=x1 - x0, height=y1 - y0, stroke_color=PANEL_EDGE, stroke_width=2,
                     fill_opacity=0).move_to([(x0 + x1) / 2, (y0 + y1) / 2, 0])


def thin_arrow(start, end, color=MUTED):
    return Arrow(start, end, buff=0, color=color, stroke_width=2.5, tip_length=0.14,
                 max_tip_length_to_length_ratio=0.5)


def make_pulse(color, w=0.26, h=0.16):
    """A small glowing chip: VGroup(glow, core)."""
    core = RoundedRectangle(width=w, height=h, corner_radius=h * 0.45, stroke_width=0,
                            fill_color=color, fill_opacity=1)
    glow = RoundedRectangle(width=w + 0.24, height=h + 0.24, corner_radius=(h + 0.24) * 0.45,
                            stroke_width=0, fill_color=color, fill_opacity=0.0)
    return VGroup(glow, core)


def style_pulse(p, color, vis):
    p[1].set_fill(color, opacity=vis)
    p[0].set_fill(color, opacity=0.24 * vis)


def path_length(pts):
    pts = [np.array(p, dtype=float) for p in pts]
    return sum(np.linalg.norm(b - a) for a, b in zip(pts, pts[1:]))


def soft_rect(mob, color, buff=0.07):
    return SurroundingRectangle(mob, buff=buff, corner_radius=0.1, stroke_width=2, color=color)


class Clip(Scene):
    def construct(self):
        D = load_data()
        header = open_chapter(self, 11, "The whole machine", TOTAL,
                              question="How do all the pieces fit together?", part=PART[5])

        # ===================================================================
        # Build every panel (off screen for now)
        # ===================================================================
        # ---- (a) win kernel ------------------------------------------------
        ks = D.kernel.win_mass_smooth
        kmax = ks.max() * 1.12

        def kp(a, v):
            return np.array([CX0 + a / 45 * CW, K_Y0 + v / kmax * (K_Y1 - K_Y0), 0])

        k_box = box(CX0, CX1, K_Y0, K_Y1)
        k_pts = [kp(a, v) for a, v in enumerate(ks)]
        k_curve = VMobject(color=KERNEL, stroke_width=3.5).set_points_smoothly(k_pts)
        k_fill = VMobject(stroke_width=0, fill_color=KERNEL, fill_opacity=0.2)
        k_fill.set_points(k_curve.points)
        k_fill.add_line_to(kp(45, 0)).add_line_to(kp(0, 0)).add_line_to(k_pts[0])
        k_t0 = num("0", anchor=RIGHT).next_to(kp(0, 0), LEFT, buff=0.1)
        k_t45 = num("45", anchor=LEFT).next_to(kp(45, 0), RIGHT, buff=0.1)
        k_title = words("win kernel ", "$k(a)$", colors={1: KERNEL}, anchor=LEFT)
        k_title.move_to([BX + 0.3, K_Y1 - 0.24, 0], aligned_edge=LEFT)
        k_sub = words("chance a new deal wins at age $a$", fs=FS_TICK, color=MUTED, anchor=LEFT)
        k_sub.next_to(k_title, DOWN, buff=0.12, aligned_edge=LEFT)
        G_K = VGroup(k_fill, k_curve, k_box, k_t0, k_t45, k_title, k_sub)

        # ---- (b) open pipeline: N(a) | heat-map | per-age totals -----------
        N = D.stock.N
        n_scale = SW * 0.9 / N[:45].max()
        n_box = box(LX0, LX1, S_Y0, S_Y1)
        n_bars = VGroup()
        for a in range(NA):
            pooled = a == NA - 1          # 45+ bucket: 58 deals, clipped, no wins projected
            L = SW * 0.97 if pooled else max(N[a] * n_scale, 1e-3)
            r = Rectangle(width=L, height=CH_S * 0.78, stroke_width=0, fill_color=STOCK,
                          fill_opacity=0.32 if pooled else 0.9)
            r.move_to([LX1, S_Y0 + (a + 0.5) * CH_S, 0], aligned_edge=RIGHT)
            n_bars.add(r)
        n_title = words("open deals ", "$N(a)$", ", by age", colors={1: STOCK}, anchor=DL)
        n_title.move_to([LX0, S_Y1 + 0.1, 0], aligned_edge=DL)
        n_ticks = VGroup()
        for a, s in [(0, "0"), (15, "15"), (30, "30"), (45, "45{+}")]:
            n_ticks.add(num(s, anchor=RIGHT).next_to([LX0, S_Y0 + (a + 0.5) * CH_S, 0], LEFT, buff=0.12))
        G_N = VGroup(n_box, n_bars, n_title, n_ticks)

        S = D.stock.surface
        s_grid = heat_grid(S, DAY_W, CH_S, STOCK_RAMP, origin="lower").shift([CX0, S_Y0, 0])
        s_rows = [VGroup(*s_grid[i * H:(i + 1) * H]) for i in range(NA)]
        s_box = box(CX0, CX1, S_Y0, S_Y1)
        s_title = words("expected wins from open deals", anchor=DOWN)
        s_title.move_to([0, S_Y1 + 0.1, 0], aligned_edge=DOWN)
        G_S = VGroup(s_grid, s_box, s_title)

        by_age = D.stock.by_age
        wa_scale = SW * 0.9 / by_age.max()
        wa_box = box(RX0, RX1, S_Y0, S_Y1)
        wa_bars = VGroup()
        for a in range(NA):
            r = Rectangle(width=max(by_age[a] * wa_scale, 1e-3), height=CH_S * 0.78, stroke_width=0,
                          fill_color=STOCK, fill_opacity=0.9)
            r.move_to([RX0, S_Y0 + (a + 0.5) * CH_S, 0], aligned_edge=LEFT)
            wa_bars.add(r)
        wa_title = words("wins per age", anchor=DL)
        wa_title.move_to([RX0, S_Y1 + 0.1, 0], aligned_edge=DL)
        G_WA = VGroup(wa_box, wa_bars, wa_title)

        # ---- (c) arrivals: A_hat(t) | heat-map | per-cohort totals ---------
        Ahat = D.arrivals.forecast
        a_scale = SW * 0.9 / Ahat.max()

        def row_y(t):            # t = 1 on top
            return A_Y1 - (t - 0.5) * CH_A

        ah_box = box(LX0, LX1, A_Y0, A_Y1)
        ah_bars = VGroup()
        for t in range(1, H + 1):
            r = Rectangle(width=Ahat[t - 1] * a_scale, height=CH_A * 0.74, stroke_width=0,
                          fill_color=ARRIVALS, fill_opacity=0.9)
            r.move_to([LX1, row_y(t), 0], aligned_edge=RIGHT)
            ah_bars.add(r)
        ah_title = words("new deals ", r"$\hat{A}(t)$", ", by day", colors={1: ARRIVALS}, anchor=DL)
        ah_title.move_to([LX0, A_Y1 + 0.1, 0], aligned_edge=DL)
        ah_ticks = VGroup(*[num(str(t), anchor=RIGHT).next_to([LX0, row_y(t), 0], LEFT, buff=0.12)
                            for t in (1, 5, 10, 15)])
        G_A = VGroup(ah_box, ah_bars, ah_title, ah_ticks)

        AS = D.arrivals.surface
        a_grid = heat_grid(AS, DAY_W, CH_A, ARRIVALS_RAMP, origin="upper").shift([CX0, A_Y0, 0])
        a_rows = [VGroup(*a_grid[i * H:(i + 1) * H]) for i in range(H)]      # index t-1, top first
        a_box = box(CX0, CX1, A_Y0, A_Y1)
        a_title = words("expected wins from new deals", anchor=DOWN)
        a_title.move_to([0, A_Y1 + 0.1, 0], aligned_edge=DOWN)
        G_AH = VGroup(a_grid, a_box, a_title)

        by_or = D.arrivals.by_origin
        wc_scale = SW * 0.9 / by_or.max()
        wc_box = box(RX0, RX1, A_Y0, A_Y1)
        wc_bars = VGroup()
        for t in range(1, H + 1):
            r = Rectangle(width=max(by_or[t - 1] * wc_scale, 1e-3), height=CH_A * 0.74, stroke_width=0,
                          fill_color=ARRIVALS, fill_opacity=0.9)
            r.move_to([RX0, row_y(t), 0], aligned_edge=LEFT)
            wc_bars.add(r)
        wc_title = words("wins per cohort", anchor=DL)
        wc_title.move_to([RX0, A_Y1 + 0.1, 0], aligned_edge=DL)
        G_WC = VGroup(wc_box, wc_bars, wc_title)

        # ---- (d) forecast ---------------------------------------------------
        fs_, fa_ = D.forecast.stock, D.forecast.arrivals
        fmax = max((fs_ + fa_).max(), D.forecast.total_smooth.max()) * 1.1
        f_unit = (F_Y1 - F_Y0) / fmax
        f_box = box(CX0, CX1, F_Y0, F_Y1)
        f_rose, f_blue = VGroup(), VGroup()
        for i in range(H):
            r = Rectangle(width=BAR_W, height=max(fs_[i] * f_unit, 1e-3), stroke_width=0,
                          fill_color=STOCK, fill_opacity=1.0)
            r.move_to([fx(i + 1), F_Y0, 0], aligned_edge=DOWN)
            b = Rectangle(width=BAR_W, height=max(fa_[i] * f_unit, 1e-3), stroke_width=0,
                          fill_color=ARRIVALS, fill_opacity=1.0)
            b.move_to([fx(i + 1), F_Y0 + fs_[i] * f_unit, 0], aligned_edge=DOWN)
            f_rose.add(r)
            f_blue.add(b)
        f_line = VMobject(color=TOTAL, stroke_width=4).set_points_smoothly(
            [[fx(d), F_Y0 + v * f_unit, 0] for d, v in zip(D.forecast.day, D.forecast.total_smooth)])
        f_title = words("forecast ", r"$\hat{W}(d)$", colors={1: TOTAL}, anchor=RIGHT)
        f_title.move_to([CX0 - 0.42, (F_Y0 + F_Y1) / 2 + 0.17, 0], aligned_edge=RIGHT)
        f_sub = words("expected wins per day", fs=FS_TICK, color=MUTED, anchor=RIGHT)
        f_sub.next_to(f_title, DOWN, buff=0.1, aligned_edge=RIGHT)
        f_ticks = VGroup(*[num(str(d), anchor=UP).next_to([fx(d), F_Y0, 0], DOWN, buff=0.1)
                           for d in (1, 5, 10, 15)])
        f_day = words("day $d$", fs=FS_TICK, color=MUTED, anchor=LEFT)
        f_day.next_to(f_ticks[-1], RIGHT, buff=0.3)
        f_y = VGroup(num("0", anchor=RIGHT).next_to([CX0, F_Y0, 0], LEFT, buff=0.1),
                     num("3", anchor=RIGHT).next_to([CX0, F_Y0 + 3 * f_unit, 0], LEFT, buff=0.1))
        G_F = VGroup(f_box, f_rose, f_blue, f_line, f_title, f_sub, f_ticks, f_day, f_y)

        # ---- flow connectors and operation glyphs ---------------------------
        n_arrow = thin_arrow([LX1 + 0.08, S_MID, 0], [CX0 - 0.08, S_MID, 0])
        n_glyph = MathTex(r"\times", r"\frac{k(a+d)}{S(a)}", font_size=28)
        n_glyph[1][0:6].set_color(KERNEL)
        n_glyph[1][7:].set_color(SURVIVAL)
        n_glyph.move_to([GX, S_MID + 0.46, 0])
        n_glyph._fs, n_glyph._anchor = 28, ORIGIN
        G_NP = VGroup(n_arrow, n_glyph)

        a_arrow = thin_arrow([LX1 + 0.08, A_MID, 0], [CX0 - 0.08, A_MID, 0])
        a_glyph = MathTex(r"\times", r"k(d-t)", font_size=28)
        a_glyph[1].set_color(KERNEL)
        a_glyph.move_to([GX, A_MID + 0.3, 0])
        a_glyph._fs, a_glyph._anchor = 28, ORIGIN
        G_AP = VGroup(a_arrow, a_glyph)

        bus_pts = [[CX1, BUS_Y, 0], [BX, BUS_Y, 0], [BX, A_MID, 0]]
        bus = VMobject(color=KERNEL, stroke_width=2.5, stroke_opacity=0.75).set_points_as_corners(bus_pts)
        stub_s = thin_arrow([BX, S_MID, 0], [CX1 + 0.06, S_MID, 0], color=KERNEL)
        stub_a = thin_arrow([BX, A_MID, 0], [CX1 + 0.06, A_MID, 0], color=KERNEL)
        G_BUS = VGroup(bus, stub_s, stub_a)

        sc_glyph = words(r"$\sum$", " over cohorts", fs=26, color=ARRIVALS, anchor=LEFT)
        sc_glyph.move_to([CX1 + 0.3, F_Y1 - 0.2, 0], aligned_edge=LEFT)
        sa_glyph = words(r"$\sum$", " over ages", fs=26, color=STOCK, anchor=LEFT)
        sa_glyph.move_to([CX1 + 0.3, F_Y1 - 0.6, 0], aligned_edge=LEFT)

        figure = VGroup(G_K, G_N, G_S, G_WA, G_A, G_AH, G_WC, G_F, G_NP, G_AP, G_BUS, sa_glyph, sc_glyph)

        # full-brightness copies for the column "pours" of beat 3 (taken before any dimming)
        s_cols = [VGroup(*[s_grid[i * H + j] for i in range(NA)]).copy() for j in range(H)]
        a_cols = [VGroup(*[a_grid[i * H + j] for i in range(H)]).copy() for j in range(H)]

        # ===================================================================
        # Beat 2 - rebuild the figure panel by panel, in the order the film taught it
        # ===================================================================
        def grow_rows(bars_, edge, lag):
            return LaggedStart(*[GrowFromEdge(b, edge) for b in bars_], lag_ratio=lag)

        def enter(frame, *labels):
            return [Create(frame)] + [FadeIn(m, shift=0.12 * UP) for m in labels]

        def row_pour(rows, surf, scale, y_of, height, color):
            """Each heat-map row (a copy) pours rightwards into its total bar: its
            cells shrink to their values' share of the bar, so the bar IS the row sum."""
            anims, copies = [], []
            for i, row in enumerate(rows):
                rc = row.copy()
                copies.append(rc)
                x = RX0
                tgt = VGroup()
                for j in range(H):
                    w = surf[i, j] * scale
                    sl = Rectangle(width=max(w, 1e-4), height=height, stroke_width=0,
                                   fill_color=color, fill_opacity=0.9)
                    sl.move_to([x, y_of(i), 0], aligned_edge=LEFT)
                    x += w
                    tgt.add(sl)
                anims.append(Transform(rc, tgt))
            self.add(*copies)
            return anims, copies

        # (a) the win kernel across the top
        self.play(*enter(k_box, k_title, k_sub, k_t0, k_t45), run_time=0.9)
        self.play(Create(k_curve), FadeIn(k_fill), run_time=1.5)
        self.wait(0.3)

        # (b) today's open deals N(a), age up
        self.play(LaggedStart(AnimationGroup(*enter(n_box, n_title, n_ticks)),
                              grow_rows(n_bars, RIGHT, 0.02), lag_ratio=0.45), run_time=1.7)
        # ... their expected wins, by age (up) and forecast day (right)
        self.play(LaggedStart(AnimationGroup(*enter(s_box, s_title)),
                              LaggedStart(*[FadeIn(r, shift=0.2 * RIGHT) for r in s_rows], lag_ratio=0.04),
                              lag_ratio=0.4), run_time=2.2)
        # ... and each row's total over the 15 days pours into "wins per age"
        self.play(*enter(wa_box, wa_title), run_time=0.8)
        anims, copies = row_pour(s_rows, S, wa_scale, lambda a: S_Y0 + (a + 0.5) * CH_S, CH_S * 0.78, STOCK)
        self.play(LaggedStart(*anims, lag_ratio=0.03), run_time=1.8)
        self.remove(*copies)
        self.add(wa_bars)
        self.wait(0.3)

        # (c) forecast new deals A_hat(t), t = 1 on top
        self.play(LaggedStart(AnimationGroup(*enter(ah_box, ah_title, ah_ticks)),
                              grow_rows(ah_bars, RIGHT, 0.06), lag_ratio=0.45), run_time=1.6)
        self.play(LaggedStart(AnimationGroup(*enter(a_box, a_title)),
                              LaggedStart(*[FadeIn(r, shift=0.2 * RIGHT) for r in a_rows], lag_ratio=0.1),
                              lag_ratio=0.4), run_time=2.0)
        self.play(*enter(wc_box, wc_title), run_time=0.8)
        anims, copies = row_pour(a_rows, AS, wc_scale, lambda i: row_y(i + 1), CH_A * 0.74, ARRIVALS)
        self.play(LaggedStart(*anims, lag_ratio=0.06), run_time=1.5)
        self.remove(*copies)
        self.add(wc_bars)
        self.wait(0.3)

        # (d) the forecast: open-deal wins, new-deal wins stacked on top, the total line
        self.play(Create(f_box), FadeIn(f_title, shift=0.12 * RIGHT), FadeIn(f_sub, shift=0.12 * RIGHT),
                  FadeIn(f_ticks), FadeIn(f_day), FadeIn(f_y), run_time=0.9)
        self.play(grow_rows(f_rose, DOWN, 0.05), run_time=1.0)
        self.play(grow_rows(f_blue, DOWN, 0.05), run_time=1.0)
        self.play(Create(f_line), run_time=0.9)
        # canonical draw order (frames over cells, the total line over its bars), so
        # animating a sub-group later never re-adds it on top of the travelling chips
        self.clear()
        self.add(header, G_K, G_N, G_S, G_WA, G_A, G_AH, G_WC, G_F)
        cap = swap_caption(self, None, r"deal counts times win chances fill both heat-maps")
        self.wait(1.6)

        # ===================================================================
        # Beat 3 - the flow, one path at a time
        # ===================================================================
        def side_path(arrow, glyph, color_from, color_to, target_box, accent, extra=()):
            """Arrow + glyph appear, a chip runs along the arrow (changing colour as
            it passes the operation), then sinks into the heat-map, which lights up.
            Returns the light-up rectangle (still on screen)."""
            self.play(GrowArrow(arrow), FadeIn(glyph, shift=0.1 * UP), *extra, run_time=0.9)
            p0, p1 = arrow.get_start() + RIGHT * 0.05, arrow.get_end() + LEFT * 0.12
            pulse = make_pulse(color_from, 0.3, 0.18)
            pulse.move_to(p0)
            style_pulse(pulse, color_from, 0)
            self.add(pulse)

            def upd(m, a):
                t = smooth(a)
                m.move_to(p0 + (p1 - p0) * t)
                c = interpolate_color(ManimColor(color_from), ManimColor(color_to),
                                      smooth(float(np.clip((t - 0.3) / 0.4, 0, 1))))
                style_pulse(m, c, float(np.clip(a / 0.2, 0, 1)))

            def bump(t):
                return there_and_back(float(np.clip((t - 0.3) / 0.45, 0, 1)))

            self.play(UpdateFromAlphaFunc(pulse, upd),
                      Indicate(glyph, scale_factor=1.1, color=None, rate_func=bump),
                      run_time=1.4)
            rect = soft_rect(target_box, accent, buff=0.05)
            self.play(FadeOut(pulse, scale=0.3), FadeIn(rect), run_time=0.6)
            return rect

        # (1) today's open deals into their heat-map, times the conditional win chance
        rect = side_path(n_arrow, n_glyph, STOCK, PALE_ROSE, s_box, STOCK)

        # (2) the win kernel feeds both heat-maps
        self.play(Create(bus), GrowArrow(stub_s), GrowArrow(stub_a), FadeOut(rect),
                  k_curve.animate.set_stroke(width=5.5), run_time=0.9)
        start = np.array([CX1 + 0.12, BUS_Y, 0])
        q1 = [start, [BX, BUS_Y, 0], [BX, S_MID, 0], [CX1 + 0.14, S_MID, 0]]
        q2 = [start, [BX, BUS_Y, 0], [BX, A_MID, 0], [CX1 + 0.14, A_MID, 0]]
        path1 = VMobject().set_points_as_corners(q1)
        path2 = VMobject().set_points_as_corners(q2)
        L1, L2 = path_length(q1), path_length(q2)
        c1, c2 = make_pulse(KERNEL, 0.22, 0.22), make_pulse(KERNEL, 0.22, 0.22)
        for c in (c1, c2):
            c.move_to(start)
            style_pulse(c, KERNEL, 0)
        r_s, r_a = soft_rect(s_box, KERNEL, buff=0.05), soft_rect(a_box, KERNEL, buff=0.05)
        r_s.set_stroke(opacity=0)
        self.add(c1, c2, r_s)

        def kupd(m, a):
            s = smooth(a) * L2
            vis_in = float(np.clip(a / 0.12, 0, 1))
            c1.move_to(path1.point_from_proportion(min(1.0, s / L1)))
            c2.move_to(path2.point_from_proportion(min(1.0, s / L2)))
            style_pulse(c1, KERNEL, vis_in * (1 - float(np.clip((s - L1 + 0.05) / 0.35, 0, 1))))
            style_pulse(c2, KERNEL, vis_in)
            r_s.set_stroke(opacity=float(np.clip((s - L1 + 0.1) / 0.3, 0, 1)))

        self.play(UpdateFromAlphaFunc(c2, kupd), k_curve.animate.set_stroke(width=3.5), run_time=1.9)
        self.remove(c1)
        self.play(FadeOut(c2, scale=0.3), FadeIn(r_a), run_time=0.6)

        # (3) new deals into their heat-map, times the kernel from their arrival day
        rect = side_path(a_arrow, a_glyph, ARRIVALS, PALE_BLUE, a_box, ARRIVALS,
                         extra=(FadeOut(r_s), FadeOut(r_a)))
        self.play(FadeOut(rect), FadeOut(cap, shift=UP * 0.12), run_time=0.6)
        cap = caption(r"add each day's column: that is the forecast")
        self.play(FadeIn(cap, shift=UP * 0.12), run_time=0.6)
        self.wait(1.5)

        # (4)-(5) each heat-map, summed down its columns, becomes its forecast bars
        def pour_down(cols, grid_, dims, bars_, src_y0, surf, rows_up, base, glyph, extra=()):
            """Each column copy sinks into a chip the size of its forecast bar at the
            bottom of its heat-map, then the chips drop, staggered, onto the bars."""
            n_rows = surf.shape[0]
            color = bars_[0].get_fill_color()
            self.add(*cols)
            self.play(bars_.animate.set_fill(opacity=0.15), grid_.animate.fade(DIM),
                      *[g.animate.fade(DIM) for g in dims], run_time=0.6)
            squash = []
            for j, col in enumerate(cols):
                y = src_y0
                pieces = [None] * n_rows
                for i in (range(n_rows) if rows_up else range(n_rows - 1, -1, -1)):
                    h = surf[i, j] * f_unit
                    sl = Rectangle(width=BAR_W, height=max(h, 1e-4), stroke_width=0.8, stroke_color=color,
                                   fill_color=color, fill_opacity=1.0)
                    sl.move_to([fx(j + 1), y, 0], aligned_edge=DOWN)
                    y += h
                    pieces[i] = sl
                squash.append(Transform(col, VGroup(*pieces)))
            self.play(LaggedStart(*squash, lag_ratio=0.05), run_time=1.3)
            # one solid chip per column (no seams) for the drop
            chips = VGroup()
            for j, col in enumerate(cols):
                ch = Rectangle(width=BAR_W, height=max(surf[:, j].sum() * f_unit, 1e-3), stroke_width=0,
                               fill_color=color, fill_opacity=1.0)
                ch.move_to([fx(j + 1), src_y0, 0], aligned_edge=DOWN)
                chips.add(ch)
            self.remove(*cols)
            self.add(chips)
            self.play(LaggedStart(*[ch.animate.shift(UP * (base[j] - src_y0)) for j, ch in enumerate(chips)],
                                  lag_ratio=0.04), run_time=1.8, rate_func=rate_functions.ease_in_out_sine)
            self.remove(chips)
            bars_.set_fill(opacity=1.0)
            self.play(FadeIn(glyph, shift=0.12 * LEFT), Restore(grid_), *[Restore(g) for g in dims], *extra,
                      run_time=0.9)

        self.add(G_NP, G_AP, G_BUS)          # as groups, so dimming them never re-adds them
        for g in (s_grid, a_grid, G_A, G_AP, G_WC, G_AH):
            g.save_state()
        pour_down(s_cols, s_grid, [G_A, G_AP, G_WC, G_AH], f_rose, S_Y0, S,
                  True, [F_Y0] * H, sa_glyph)
        r_f = soft_rect(VGroup(f_box), TOTAL, buff=0.06)
        pour_down(a_cols, a_grid, [], f_blue, A_Y0, AS, False, [F_Y0 + fs_[j] * f_unit for j in range(H)],
                  sc_glyph, extra=(FadeIn(r_f),))
        self.wait(0.6)

        # ===================================================================
        # Beat 4 - make room, then the formula term by term
        # ===================================================================
        self.play(FadeOut(cap, shift=UP * 0.12), FadeOut(r_f), run_time=0.5)
        self.clear()
        self.add(header, figure)
        figure.generate_target()
        tgt = figure.target
        tgt.scale(SHRINK, about_point=SHRINK_ABOUT)
        for m in tgt.get_family():          # keep every label at or above the size floor
            if hasattr(m, "_fs") and m._fs * SHRINK < FS_TICK:
                m.scale(FS_TICK / (m._fs * SHRINK), about_edge=m._anchor)
        self.play(MoveToTarget(figure), run_time=2.2, rate_func=rate_functions.ease_in_out_sine)

        formula = MathTex(r"\hat{W}(d)", r"\;=\;", r"\sum_a", r"N(a)", r"\,", r"\frac{k(a+d)}{S(a)}",
                          r"\;+\;", r"\sum_{t \le d}", r"\hat{A}(t)", r"\,", r"k(d-t)",
                          font_size=FS_FORMULA)
        formula[0].set_color(TOTAL)
        formula[2].set_color(STOCK)
        formula[3].set_color(STOCK)
        formula[5][0:6].set_color(KERNEL)
        formula[5][7:].set_color(SURVIVAL)
        formula[7].set_color(ARRIVALS)
        formula[8].set_color(ARRIVALS)
        formula[10].set_color(KERNEL)
        formula.move_to([0, (figure.get_bottom()[1] - 3.05) / 2, 0])

        groups = {"K": G_K, "BUS": G_BUS, "N": G_N, "S": G_S, "WA": G_WA, "A": G_A, "AH": G_AH,
                  "WC": G_WC, "F": G_F, "NP": G_NP, "AP": G_AP, "SA": sa_glyph, "SC": sc_glyph}
        for g in groups.values():
            g.save_state()
        lit = {k: True for k in groups}

        def focus(keys):
            """Restore the panels in ``keys``, dim the rest (each change once)."""
            anims = []
            for k, g in groups.items():
                if k in keys and not lit[k]:
                    anims.append(Restore(g))
                    lit[k] = True
                elif k not in keys and lit[k]:
                    anims.append(g.animate.fade(DIM))
                    lit[k] = False
            return anims

        # term 1: the forecast
        rect_f = soft_rect(VGroup(f_box, f_title, f_sub), TOTAL, buff=0.1)
        self.play(*focus({"F", "SA", "SC"}), Create(rect_f), run_time=0.9)
        self.play(TransformFromCopy(f_title[1], formula[0]), run_time=1.3)
        self.wait(0.3)

        # term 2: today's open deals, through the conditional win chance
        rect_s = soft_rect(VGroup(n_box, n_title, n_ticks, s_box, s_title), STOCK, buff=0.06)
        self.play(*focus({"N", "S", "NP", "K", "BUS", "SA"}), ReplacementTransform(rect_f, rect_s), run_time=0.9)
        self.play(FadeIn(formula[1]),
                  TransformFromCopy(sa_glyph[0], formula[2]),
                  TransformFromCopy(n_title[1], formula[3]),
                  TransformFromCopy(n_glyph[1], formula[5]), run_time=1.5)
        self.wait(0.7)

        # term 3: the new deals, through the kernel from their arrival day
        rect_a = soft_rect(VGroup(ah_box, ah_title, ah_ticks, a_box, a_title), ARRIVALS, buff=0.06)
        self.play(*focus({"A", "AH", "AP", "K", "BUS", "SC"}), ReplacementTransform(rect_s, rect_a), run_time=0.9)
        self.play(FadeIn(formula[6]),
                  TransformFromCopy(sc_glyph[0], formula[7]),
                  TransformFromCopy(ah_title[1], formula[8]),
                  TransformFromCopy(a_glyph[1], formula[10]), run_time=1.5)
        self.wait(0.7)

        # the complete picture: every panel back, held through the takeaway
        self.play(*focus(set(groups)), FadeOut(rect_a), run_time=1.0)
        self.wait(1.6)
        takeaway(self, "open deals plus new deals, through one kernel", TOTAL, old_caption=None)
        self.wait(0.6)
        close_chapter(self)
