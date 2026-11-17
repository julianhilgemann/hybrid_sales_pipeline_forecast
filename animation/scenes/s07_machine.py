import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import *

# ---------------------------------------------------------------------------
# Geometry (frame 14.22 x 8).  A 3-column x 4-row twin of docs/model-overview.png
# ---------------------------------------------------------------------------
CX0, CX1 = -2.60, 2.60          # centre column: kernel, both heat-maps, forecast
LX0, LX1 = -6.20, -4.30         # left column  (N(a), A_hat(t)) -- bars grow leftward from LX1
RX0, RX1 = 4.30, 6.20           # right column (row sums)        -- bars grow rightward from RX0
K_Y0, K_Y1 = 2.50, 3.52         # kernel
S_Y0, S_Y1 = 0.06, 1.82         # existing-pipeline row
A_Y0, A_Y1 = -1.70, -0.55       # future-arrivals row
F_Y0, F_Y1 = -3.30, -2.40       # forecast
CW = CX1 - CX0
SIDE_W = LX1 - LX0
H = 15
NA = 46

SHRINK = 0.75                   # beat 4: machine shrinks about the top centre
SHRINK_ABOUT = np.array([0.0, 3.65, 0.0])
MIN_FS = FS_TICK


def label(tex, fs, anchor, color=INK, math=False):
    m = (MathTex if math else Tex)(tex, font_size=fs, color=color)
    m._fs = fs
    m._anchor = anchor
    return m


def box(x0, x1, y0, y1):
    return Rectangle(width=x1 - x0, height=y1 - y0, stroke_color=GRID, stroke_width=1.6,
                     fill_opacity=0).move_to([(x0 + x1) / 2, (y0 + y1) / 2, 0])


def hbar_rows(values, y0, y1, x_base, scale, color, to_left, fill_opacity=0.9, frac=0.78):
    """One horizontal bar per row of a panel spanning [y0, y1]; row 0 at the bottom."""
    n = len(values)
    ch = (y1 - y0) / n
    g = VGroup()
    for i, v in enumerate(values):
        w = max(float(v) * scale, 1e-3)
        r = Rectangle(width=w, height=ch * frac, stroke_width=0, fill_color=color,
                      fill_opacity=fill_opacity)
        r.move_to([x_base, y0 + (i + 0.5) * ch, 0], aligned_edge=RIGHT if to_left else LEFT)
        g.add(r)
    return g


def heat_rows(matrix, y0, y1, ramp):
    """heat_grid split into row VGroups (row 0 at the bottom), placed in the centre column."""
    M = np.asarray(matrix, dtype=float)
    n, m = M.shape
    grid = heat_grid(M, CW / m, (y1 - y0) / n, ramp)
    grid.shift([CX0, y0, 0])
    return VGroup(*[VGroup(*grid[i * m:(i + 1) * m]) for i in range(n)])


class Clip(Scene):
    def construct(self):
        D = load_data()
        header = open_chapter(self, 7, "The whole machine", INK)

        texts = []          # every label of the machine (counter-scaled on shrink)

        def T(*a, **k):
            m = label(*a, **k)
            texts.append(m)
            return m

        def title_above(tex, x0, y1, color=INK):
            t = T(tex, FS_LABEL, DL, color=color)
            t.move_to([x0, y1 + 0.1, 0], aligned_edge=DL)
            return t

        # ---------------- row 1: kernel ----------------------------------
        ages = D.kernel.age
        ks = D.kernel.win_mass_smooth
        kmax = ks.max() * 1.1

        def kp(a, v):
            return np.array([CX0 + a / 45 * CW, K_Y0 + v / kmax * (K_Y1 - K_Y0), 0])

        k_box = box(CX0, CX1, K_Y0, K_Y1)
        k_pts = [kp(a, v) for a, v in zip(ages, ks)]
        k_curve = VMobject(color=KERNEL, stroke_width=4).set_points_smoothly(k_pts)
        k_fill = VMobject(stroke_width=0, fill_color=KERNEL, fill_opacity=0.22)
        k_fill.set_points(k_curve.points)
        k_fill.add_line_to(kp(45, 0)).add_line_to(kp(0, 0)).add_line_to(k_pts[0])
        k_title = T(r"kernel $k(a)$", FS_LABEL, LEFT)
        k_title.move_to([CX1 + 0.75, (K_Y0 + K_Y1) / 2 + 0.05, 0], aligned_edge=LEFT)
        k_t0 = T("0", FS_TICK, RIGHT, color=MUTED, math=True).next_to(kp(0, 0), LEFT, buff=0.12)
        k_t45 = T("45", FS_TICK, UP, color=MUTED, math=True).next_to(kp(45, 0), DOWN, buff=0.08)
        kernel = VGroup(k_box, k_fill, k_curve, k_title, k_t0, k_t45)

        # ---------------- row 2: existing pipeline -----------------------
        N = D.stock.N.copy()
        n_scale = SIDE_W * 0.9 / N[:45].max()
        N_disp = N.copy()
        N_disp[45] = SIDE_W * 0.97 / n_scale          # pooled 45+ bucket: clipped bar
        n_box = box(LX0, LX1, S_Y0, S_Y1)
        n_bars = hbar_rows(N_disp, S_Y0, S_Y1, LX1, n_scale, STOCK, to_left=True)
        n_bars[45].set_fill(opacity=0.35)
        n_title = title_above(r"open stock $N(a)$", LX0, S_Y1)
        ch_s = (S_Y1 - S_Y0) / NA
        n_ticks = VGroup()
        for a, s in [(0, "0"), (15, "15"), (30, "30"), (45, "45{+}")]:
            t = T(s, FS_TICK, RIGHT, color=MUTED, math=True)
            t.next_to([LX0, S_Y0 + (a + 0.5) * ch_s, 0], LEFT, buff=0.12)
            n_ticks.add(t)
        stock_N = VGroup(n_box, n_bars, n_title, n_ticks)

        s_box = box(CX0, CX1, S_Y0, S_Y1)
        s_rows = heat_rows(D.stock.surface_smooth, S_Y0, S_Y1, STOCK_RAMP)
        s_title = title_above(r"existing pipeline", CX0, S_Y1)
        stock_hm = VGroup(s_rows, s_box, s_title)

        by_age = D.stock.by_age
        wa_scale = SIDE_W * 0.9 / by_age.max()
        wa_box = box(RX0, RX1, S_Y0, S_Y1)
        wa_bars = hbar_rows(by_age, S_Y0, S_Y1, RX0, wa_scale, STOCK, to_left=False)
        wa_title = title_above(r"wins per age", RX0, S_Y1)
        wins_age = VGroup(wa_box, wa_bars, wa_title)

        # ---------------- row 3: future arrivals -------------------------
        Ahat = D.arrivals.forecast
        a_scale = SIDE_W * 0.9 / Ahat.max()
        ah_box = box(LX0, LX1, A_Y0, A_Y1)
        ah_bars = hbar_rows(Ahat[::-1], A_Y0, A_Y1, LX1, a_scale, ARRIVALS, to_left=True)
        ah_bars = VGroup(*reversed(ah_bars.submobjects))       # index t-1, t = 1 at the top
        ah_title = title_above(r"arrivals $\hat{A}(t)$", LX0, A_Y1)
        ch_a = (A_Y1 - A_Y0) / H
        ah_ticks = VGroup()
        for t_ in (1, 5, 10, 15):
            t = T(str(t_), FS_TICK, RIGHT, color=MUTED, math=True)
            t.next_to([LX0, A_Y1 - (t_ - 0.5) * ch_a, 0], LEFT, buff=0.12)
            ah_ticks.add(t)
        arr_A = VGroup(ah_box, ah_bars, ah_title, ah_ticks)

        a_box = box(CX0, CX1, A_Y0, A_Y1)
        a_rows = heat_rows(D.arrivals.surface_smooth[::-1], A_Y0, A_Y1, ARRIVALS_RAMP)
        a_rows = VGroup(*reversed(a_rows.submobjects))           # index t-1, top row first
        a_title = title_above(r"future arrivals", CX0, A_Y1)
        arr_hm = VGroup(a_rows, a_box, a_title)

        by_or = D.arrivals.by_origin
        wc_scale = SIDE_W * 0.9 / by_or.max()
        wc_box = box(RX0, RX1, A_Y0, A_Y1)
        wc_bars = hbar_rows(by_or[::-1], A_Y0, A_Y1, RX0, wc_scale, ARRIVALS, to_left=False)
        wc_bars = VGroup(*reversed(wc_bars.submobjects))
        wc_title = title_above(r"wins per cohort", RX0, A_Y1)
        wins_coh = VGroup(wc_box, wc_bars, wc_title)

        # ---------------- row 4: forecast --------------------------------
        fs_, fa_ = D.forecast.stock, D.forecast.arrivals
        fmax = max((fs_ + fa_).max(), D.forecast.total_smooth.max()) * 1.12
        cw = CW / H
        f_unit = (F_Y1 - F_Y0) / fmax

        def fx(d):
            return CX0 + (d - 0.5) * cw

        f_box = box(CX0, CX1, F_Y0, F_Y1)
        f_rose, f_blue = VGroup(), VGroup()
        for i in range(H):
            r = Rectangle(width=cw * 0.72, height=max(fs_[i] * f_unit, 1e-3), stroke_width=0,
                          fill_color=STOCK, fill_opacity=0.9)
            r.move_to([fx(i + 1), F_Y0, 0], aligned_edge=DOWN)
            b = Rectangle(width=cw * 0.72, height=max(fa_[i] * f_unit, 1e-3), stroke_width=0,
                          fill_color=ARRIVALS, fill_opacity=0.9)
            b.move_to([fx(i + 1), F_Y0 + fs_[i] * f_unit, 0], aligned_edge=DOWN)
            f_rose.add(r)
            f_blue.add(b)
        f_line = VMobject(color=TOTAL, stroke_width=4).set_points_smoothly(
            [[fx(d), F_Y0 + v * f_unit, 0] for d, v in zip(D.forecast.day, D.forecast.total_smooth)])
        f_title = T(r"forecast $\hat{W}(d)$", FS_LABEL, RIGHT)
        f_title.move_to([CX0 - 0.3, (F_Y0 + F_Y1) / 2, 0], aligned_edge=RIGHT)
        f_ticks = VGroup()
        for d in (1, 5, 10, 15):
            t = T(str(d), FS_TICK, UP, color=MUTED, math=True)
            t.next_to([fx(d), F_Y0, 0], DOWN, buff=0.1)
            f_ticks.add(t)
        forecast = VGroup(f_box, f_rose, f_blue, f_line, f_title, f_ticks)

        # ---------------- connectors and glyphs (flow beat) --------------
        CONN = dict(color=MUTED, stroke_width=2)
        TIP = dict(tip_length=0.13, max_tip_length_to_length_ratio=0.5)
        bus_x = CX1 + 0.3
        k_out_y = K_Y0 + 0.28
        bus = VMobject(**CONN).set_points_as_corners(
            [[CX1, k_out_y, 0], [bus_x, k_out_y, 0], [bus_x, A_Y1 - 0.12, 0]])
        stub_s = Arrow([bus_x, S_Y1 - 0.12, 0], [CX1, S_Y1 - 0.12, 0], buff=0, **CONN, **TIP)
        stub_a = Arrow([bus_x, A_Y1 - 0.12, 0], [CX1, A_Y1 - 0.12, 0], buff=0, **CONN, **TIP)
        k_conn = VGroup(bus, stub_s, stub_a)

        sm, am = (S_Y0 + S_Y1) / 2, (A_Y0 + A_Y1) / 2
        gx = (LX1 + CX0) / 2
        n_arrow = Arrow([LX1 + 0.08, sm, 0], [CX0 - 0.06, sm, 0], buff=0, **CONN, **TIP)
        n_glyph = T(r"\times\,\frac{k(a+d)}{S(a)}", 24, ORIGIN, math=True).move_to([gx, sm + 0.45, 0])
        n_glyph[0][1:7].set_color(KERNEL)
        n_glyph[0][8:].set_color(SURVIVAL)
        a_arrow = Arrow([LX1 + 0.08, am, 0], [CX0 - 0.06, am, 0], buff=0, **CONN, **TIP)
        a_glyph = T(r"\times\,k(d-t)", 24, ORIGIN, math=True).move_to([gx, am + 0.3, 0])
        a_glyph[0][1:].set_color(KERNEL)

        rx = (bus_x + RX0) / 2 + 0.08
        r_s_arrow = Arrow([bus_x + 0.2, sm, 0], [RX0 - 0.06, sm, 0], buff=0, **CONN, **TIP)
        r_s_glyph = T(r"\sum_d", 24, ORIGIN, math=True).move_to([rx, sm + 0.42, 0])
        r_a_arrow = Arrow([bus_x + 0.2, am, 0], [RX0 - 0.06, am, 0], buff=0, **CONN, **TIP)
        r_a_glyph = T(r"\sum_d", 24, ORIGIN, math=True).move_to([rx, am + 0.42, 0])

        gy = (A_Y0 + F_Y1) / 2
        p_sa = T(r"\sum_a", 24, ORIGIN, color=STOCK, math=True).move_to([-1.1, gy, 0])
        p_plus = T(r"+", 24, ORIGIN, math=True).move_to([0, gy, 0])
        p_st = T(r"\sum_t", 24, ORIGIN, color=ARRIVALS, math=True).move_to([1.1, gy, 0])
        pour = VGroup(p_sa, p_plus, p_st)

        machine = VGroup(stock_N, kernel, stock_hm, wins_age, arr_A, arr_hm, wins_coh, forecast,
                         k_conn, n_arrow, n_glyph, a_arrow, a_glyph,
                         r_s_arrow, r_s_glyph, r_a_arrow, r_a_glyph, pour)

        # =================================================================
        # Beat 2 -- assemble, in the order the film taught it
        # =================================================================
        def grow_left(bars_, lag=0.03):
            return LaggedStart(*[GrowFromEdge(b, RIGHT) for b in bars_], lag_ratio=lag)

        def grow_right(bars_, lag=0.03):
            return LaggedStart(*[GrowFromEdge(b, LEFT) for b in bars_], lag_ratio=lag)

        # N(a)
        self.play(Create(n_box), FadeIn(n_title, shift=0.15 * UP), run_time=0.6)
        self.play(grow_left(n_bars, 0.02), FadeIn(n_ticks), run_time=1.0)
        # kernel
        self.play(Create(k_box), FadeIn(k_title, shift=0.15 * RIGHT), FadeIn(k_t0), FadeIn(k_t45),
                  run_time=0.5)
        self.play(Create(k_curve), FadeIn(k_fill), run_time=1.1)
        # existing-pipeline heat-map: rows sweep in from age 0 upward
        self.play(Create(s_box), FadeIn(s_title, shift=0.15 * UP), run_time=0.4)
        self.play(LaggedStart(*[FadeIn(r, shift=0.25 * RIGHT) for r in s_rows], lag_ratio=0.06),
                  run_time=1.4)
        # wins per age
        self.play(Create(wa_box), FadeIn(wa_title, shift=0.15 * UP), grow_right(wa_bars, 0.02),
                  run_time=1.1)
        # arrivals A_hat(t), t = 1 at the top
        self.play(Create(ah_box), FadeIn(ah_title, shift=0.15 * UP), run_time=0.4)
        self.play(grow_left(ah_bars, 0.06), FadeIn(ah_ticks), run_time=0.9)
        # future-arrivals heat-map: rows sweep in from t = 1 downward
        self.play(Create(a_box), FadeIn(a_title, shift=0.15 * UP), run_time=0.4)
        self.play(LaggedStart(*[FadeIn(r, shift=0.25 * RIGHT) for r in a_rows], lag_ratio=0.12),
                  run_time=1.2)
        # wins per cohort
        self.play(Create(wc_box), FadeIn(wc_title, shift=0.15 * UP), grow_right(wc_bars, 0.05),
                  run_time=1.0)
        # forecast
        self.play(Create(f_box), FadeIn(f_title, shift=0.15 * RIGHT), FadeIn(f_ticks), run_time=0.5)
        self.play(LaggedStart(*[GrowFromEdge(b, DOWN) for b in f_rose], lag_ratio=0.05), run_time=0.8)
        self.play(LaggedStart(*[GrowFromEdge(b, DOWN) for b in f_blue], lag_ratio=0.05), run_time=0.8)
        self.play(Create(f_line), run_time=0.8)
        self.wait(0.4)

        # =================================================================
        # Beat 3 -- flow, one path at a time
        # =================================================================
        def flash_box(b, color):
            return Succession(b.animate(run_time=0.3).set_stroke(color=color, width=3),
                              b.animate(run_time=0.6).set_stroke(color=GRID, width=1.6))

        # (a) the kernel feeds both engines
        self.play(Create(bus), GrowArrow(stub_s), GrowArrow(stub_a),
                  k_curve.animate.set_stroke(width=6), run_time=0.7)
        dot1 = Dot(radius=0.07, color=KERNEL)
        dot2 = Dot(radius=0.07, color=KERNEL)
        path1 = VMobject().set_points_as_corners(
            [[CX1, k_out_y, 0], [bus_x, k_out_y, 0], [bus_x, S_Y1 - 0.12, 0], [CX1, S_Y1 - 0.12, 0]])
        path2 = VMobject().set_points_as_corners(
            [[CX1, k_out_y, 0], [bus_x, k_out_y, 0], [bus_x, A_Y1 - 0.12, 0], [CX1, A_Y1 - 0.12, 0]])
        self.add(dot1, dot2)
        self.play(MoveAlongPath(dot1, path1, run_time=0.9, rate_func=smooth),
                  MoveAlongPath(dot2, path2, run_time=1.5, rate_func=smooth),
                  k_curve.animate(run_time=1.5).set_stroke(width=4))
        self.play(FadeOut(dot1), FadeOut(dot2), flash_box(s_box, KERNEL), flash_box(a_box, KERNEL),
                  run_time=0.7)

        # (b) N(a) pushes into its heat-map, row by row
        self.play(GrowArrow(n_arrow), Write(n_glyph), run_time=0.7)
        push = n_bars[:45].copy().set_fill(color="#FFC2CD", opacity=0.75)
        self.play(push.animate.shift(RIGHT * (CX1 - LX1 + 0.4)).set_fill(opacity=0),
                  Indicate(n_glyph, color=None, scale_factor=1.12),
                  run_time=1.6, rate_func=smooth)
        self.remove(push)

        # (c) A_hat(t) pushes into its heat-map, cohort by cohort
        self.play(GrowArrow(a_arrow), Write(a_glyph), run_time=0.7)
        push = ah_bars.copy().set_fill(color="#C2E0FF", opacity=0.75)
        self.play(push.animate.shift(RIGHT * (CX1 - LX1 + 0.4)).set_fill(opacity=0),
                  Indicate(a_glyph, color=None, scale_factor=1.12),
                  run_time=1.6, rate_func=smooth)
        self.remove(push)

        # (d) each heat-map pours down its columns into the forecast
        self.play(Write(pour), run_time=0.6)
        s_strips = VGroup(*[Rectangle(width=cw * 0.72, height=S_Y1 - S_Y0, stroke_width=0,
                                      fill_color=STOCK, fill_opacity=0.25)
                            .move_to([fx(d), (S_Y0 + S_Y1) / 2, 0]) for d in range(1, H + 1)])
        a_strips = VGroup(*[Rectangle(width=cw * 0.72, height=A_Y1 - A_Y0, stroke_width=0,
                                      fill_color=ARRIVALS, fill_opacity=0.25)
                            .move_to([fx(d), (A_Y0 + A_Y1) / 2, 0]) for d in range(1, H + 1)])
        # column sums appear in place: each column copy squashes to a chip at its map's bottom edge
        def chips(bars_, y_bottom):
            g = VGroup()
            for bar in bars_:
                c = bar.copy().set_fill(opacity=1.0)
                c.move_to([bar.get_x(), y_bottom, 0], aligned_edge=DOWN)
                g.add(c)
            return g

        s_chips = chips(f_rose, S_Y0)
        a_chips = chips(f_blue, A_Y0)
        self.play(LaggedStart(*[FadeIn(x) for x in s_strips], lag_ratio=0.03),
                  LaggedStart(*[FadeIn(x) for x in a_strips], lag_ratio=0.03), run_time=0.5)
        self.play(*[ReplacementTransform(x, c) for x, c in zip(s_strips, s_chips)],
                  *[ReplacementTransform(x, c) for x, c in zip(a_strips, a_chips)],
                  Indicate(pour, color=None, scale_factor=1.1),
                  run_time=1.0, rate_func=smooth)
        self.wait(0.3)
        # then the small chips drop into the stacked forecast bars, left to right
        self.play(LaggedStart(*[c.animate(rate_func=smooth).move_to(bar) for c, bar in zip(a_chips, f_blue)],
                              lag_ratio=0.05),
                  LaggedStart(*[c.animate(rate_func=smooth).move_to(bar) for c, bar in zip(s_chips, f_rose)],
                              lag_ratio=0.05),
                  run_time=1.4)
        self.remove(s_chips, a_chips)
        self.play(flash_box(f_box, TOTAL), run_time=0.7)
        # (e) the side panels are the row sums
        self.play(GrowArrow(r_s_arrow), GrowArrow(r_a_arrow), Write(r_s_glyph), Write(r_a_glyph),
                  run_time=0.7)
        s_rstrips = VGroup(*[Rectangle(width=CW, height=ch_s * 0.78, stroke_width=0, fill_color=STOCK,
                                       fill_opacity=0.3).move_to([0, S_Y0 + (i + 0.5) * ch_s, 0])
                             for i in range(NA)])
        a_rstrips = VGroup(*[Rectangle(width=CW, height=ch_a * 0.78, stroke_width=0, fill_color=ARRIVALS,
                                       fill_opacity=0.3).move_to([0, A_Y1 - (i + 0.5) * ch_a, 0])
                             for i in range(H)])
        self.play(LaggedStart(*[ReplacementTransform(s, b.copy())
                                for s, b in zip(s_rstrips, wa_bars)], lag_ratio=0.015),
                  LaggedStart(*[ReplacementTransform(s, b.copy())
                                for s, b in zip(a_rstrips, wc_bars)], lag_ratio=0.04),
                  Indicate(VGroup(r_s_glyph, r_a_glyph), color=None, scale_factor=1.12),
                  run_time=1.6)
        self.play(flash_box(wa_box, STOCK), flash_box(wc_box, ARRIVALS), run_time=0.7)

        # clean up every transient helper so only the machine and header remain
        self.clear()
        self.add(header, machine)

        # =================================================================
        # Beat 4 -- one line
        # =================================================================
        machine.generate_target()
        tgt = machine.target
        tgt.scale(SHRINK, about_point=SHRINK_ABOUT)
        # keep every label legible: never below FS_TICK on screen
        src_texts = texts
        tgt_texts = [m for m in tgt.get_family() if hasattr(m, "_fs")]
        for m in tgt_texts:
            shown = m._fs * SHRINK
            if shown < MIN_FS:
                m.scale(MIN_FS / shown, about_edge=m._anchor)

        formula = MathTex(r"\hat{W}(d)", r"\;=\;", r"\sum_a", r"N(a)", r"\,", r"\frac{k(a+d)}{S(a)}",
                          r"\;+\;", r"\sum_{t\le d}", r"\hat{A}(t)", r"\,", r"k(d-t)",
                          font_size=38)
        formula[0].set_color(TOTAL)
        formula[3].set_color(STOCK)
        frac = formula[5]
        frac[0:6].set_color(KERNEL)
        frac[7:].set_color(SURVIVAL)
        formula[8].set_color(ARRIVALS)
        formula[10].set_color(KERNEL)
        formula.move_to([0, -2.55, 0])

        self.play(MoveToTarget(machine), run_time=1.4)
        # terms fly out of the panel titles that name them
        self.play(TransformFromCopy(f_title[0][8:], formula[0]),
                  TransformFromCopy(n_title[0][9:], formula[3]),
                  TransformFromCopy(ah_title[0][8:], formula[8]),
                  TransformFromCopy(k_title[0][6:], formula[10]),
                  FadeIn(formula[1]), FadeIn(formula[2]), FadeIn(formula[4]), FadeIn(formula[5]),
                  FadeIn(formula[6]), FadeIn(formula[7]), FadeIn(formula[9]),
                  run_time=1.6)

        # dim the machine, then let each term relight its panel
        machine.save_state()
        self.play(machine.animate.fade(0.72), run_time=0.6)
        links = [
            (VGroup(formula[3]), [stock_N]),
            (VGroup(formula[5]), [kernel]),
            (VGroup(formula[2]), [stock_hm, wins_age, n_arrow, n_glyph, r_s_arrow, r_s_glyph]),
            (VGroup(formula[8]), [arr_A]),
            (VGroup(formula[7], formula[10]), [arr_hm, wins_coh, a_arrow, a_glyph, r_a_arrow, r_a_glyph]),
            (VGroup(formula[0]), [forecast, pour, k_conn]),
        ]
        for term, panels in links:
            anims = []
            for p in panels:
                idx = list(machine.submobjects).index(p)
                anims.append(Transform(p, machine.saved_state.submobjects[idx].copy()))
            self.play(*anims, Indicate(term, color=None, scale_factor=1.18), run_time=0.8)

        cap = caption(r"arrive, age, convert --- on average", color=INK).shift(0.08 * DOWN)
        self.play(FadeIn(cap, shift=0.15 * UP), run_time=0.8)
        self.wait(3.0)
        close_chapter(self)
