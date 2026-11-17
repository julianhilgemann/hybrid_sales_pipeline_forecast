import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import *

# ---------------------------------------------------------------------------
# Chapter 01 -- The stream of opportunities
#
# A Lexis diagram: calendar time (business days relative to as-of) to the
# right, age (business days) upwards. One unit of time and one unit of age
# share the same screen length U, so every lifeline rises at exactly 45 deg.
# ---------------------------------------------------------------------------

U = 0.12                      # screen units per business day (both axes)
X_MIN, X_MAX = -40, 15        # calendar window (business days rel. to as-of)
A_MAX = 45                    # top of the age axis
ORIGIN_PT = np.array([1.0, -2.55, 0.0])   # screen position of (as-of, age 0)
H = 15

LINE_W = 1.3
DOT_R = 0.036


def P(x, a):
    """Lexis coordinates (calendar day x, age a) -> screen point."""
    return ORIGIN_PT + np.array([x * U, a * U, 0.0])


class Life:
    """One opportunity's lifeline, revealed by the calendar cursor T."""

    def __init__(self, rec):
        self.s = rec["created_rel"]
        self.e = rec["closed_rel"]                    # None if censored
        self.outcome = rec["outcome"]
        self.x0 = max(self.s, X_MIN)                  # enters at the left edge if older
        self.xtop = self.s + A_MAX                    # leaves the chart at age 45
        self.open_at_asof = self.e is None or self.e > 0
        self.line = Line(P(self.x0, self.x0 - self.s), P(self.x0, self.x0 - self.s) + 1e-4 * RIGHT,
                         stroke_width=LINE_W, color=INK)
        self.line.set_stroke(opacity=0)
        self.dot = Dot(P(self.x0, self.x0 - self.s), radius=DOT_R, color=SURVIVAL)
        self.dot.set_fill(opacity=0)
        self.state = None

    def end_x(self, T):
        xe = min(T, self.xtop)
        if self.e is not None:
            xe = min(xe, self.e)
        return xe

    def update(self, T):
        if T <= self.x0 or self.x0 > self.xtop:
            if self.state != "hidden":
                self.line.set_stroke(opacity=0)
                self.dot.set_fill(opacity=0)
                self.state = "hidden"
            return
        xe = self.end_x(T)
        a0 = self.x0 - self.s
        p0, p1 = P(self.x0, a0), P(xe, xe - self.s)
        if np.linalg.norm(p1 - p0) < 1e-4:
            p1 = p0 + 1e-4 * RIGHT
        self.line.put_start_and_end_on(p0, p1)
        self.dot.move_to(p1)
        fade = min(1.0, (T - self.x0) / 0.6)
        closed = self.e is not None and T >= self.e and self.e <= self.xtop
        if closed:
            state = self.outcome
            since = T - self.e
            if state == "won":
                # brief amber flash: grows then settles
                k = 1.0 + 1.3 * max(0.0, 1.0 - since / 1.2)
                self.dot.set(width=2 * DOT_R * 1.15 * k)
                if self.state != "won":
                    self.dot.set_fill(WON, opacity=1)
                    self.line.set_stroke(INK, opacity=0.32)
            else:
                if self.state != "lost":
                    self.dot.set_fill(LOST, opacity=0.9)
                    self.dot.set(width=2 * DOT_R)
                # the line dims over about a day
                self.line.set_stroke(LOST, opacity=0.18 + 0.2 * max(0.0, 1 - since / 1.5))
            self.state = state
        elif T >= self.xtop:
            if self.state != "gone":
                self.dot.set_fill(opacity=0)
                self.line.set_stroke(INK, opacity=0.26)
                self.state = "gone"
        else:
            self.dot.set_fill(SURVIVAL, opacity=fade)
            self.line.set_stroke(INK, opacity=0.3 * fade)
            self.state = "open"


class Clip(Scene):
    def construct(self):
        D = load_data()

        # ------------------------------------------------------------ 0. title
        title = Tex("Pipeline Forecast", font_size=FS_TITLE)
        sub = Tex("how a stream of opportunities becomes a forecast of wins",
                  font_size=FS_CAPTION, color=MUTED)
        VGroup(title, sub).arrange(DOWN, buff=0.4).move_to(UP * 0.2)
        self.play(FadeIn(title, shift=UP * 0.2), run_time=0.9)
        self.play(FadeIn(sub, shift=UP * 0.1), run_time=0.6)
        self.wait(1.4)
        self.play(FadeOut(title), FadeOut(sub), run_time=0.6)

        header = open_chapter(self, 1, "The stream of opportunities", INK)

        # ------------------------------------------------------------ 1. axes
        x_axis = Line(P(X_MIN, 0), P(X_MAX, 0), stroke_color=MUTED, stroke_width=2)
        y_axis = Line(P(X_MIN, 0), P(X_MIN, A_MAX), stroke_color=MUTED, stroke_width=2)
        x_ticks = VGroup(*[Line(P(x, 0), P(x, 0) + DOWN * 0.07, stroke_color=MUTED, stroke_width=2)
                           for x in range(X_MIN, X_MAX + 1, 5)])
        y_ticks = VGroup(*[Line(P(X_MIN, a), P(X_MIN, a) + LEFT * 0.07, stroke_color=MUTED, stroke_width=2)
                           for a in range(0, A_MAX + 1, 5)])
        x_nums = VGroup()
        for x in (-40, -30, -20, -10, 0, 10):
            s = rf"{x}" if x >= 0 else rf"{x}"
            m = MathTex(s, font_size=FS_TICK, color=MUTED).next_to(P(x, 0), DOWN, buff=0.14)
            x_nums.add(m)
        y_nums = VGroup(*[MathTex(str(a), font_size=FS_TICK, color=MUTED).next_to(P(X_MIN, a), LEFT, buff=0.16)
                          for a in (0, 10, 20, 30, 40)])
        x_title = Tex("time (business days)", font_size=FS_LABEL, color=MUTED)
        x_title.next_to(P(X_MAX, 0), RIGHT, buff=0.25)
        y_title = Tex("age (business days)", font_size=FS_LABEL, color=MUTED).rotate(PI / 2)
        y_title.next_to(y_nums, LEFT, buff=0.22).set_y(P(0, A_MAX / 2)[1])
        top_rule = DashedLine(P(X_MIN, A_MAX), P(X_MAX, A_MAX), stroke_color=GRID, stroke_width=1.5,
                              dash_length=0.06)
        axes_grp = VGroup(x_axis, y_axis, x_ticks, y_ticks, x_nums, y_nums, x_title, y_title, top_rule)

        self.play(Create(x_axis), Create(y_axis), run_time=0.9)
        self.play(FadeIn(x_ticks), FadeIn(y_ticks), FadeIn(x_nums), FadeIn(y_nums),
                  FadeIn(x_title), FadeIn(y_title), FadeIn(top_rule), run_time=0.7)

        # ------------------------------------------------------------ lifelines
        recs = [l for l in D.lifelines
                if l["created_rel"] <= 0 and (l["closed_rel"] is None or l["closed_rel"] >= X_MIN)]
        open_recs = [l for l in recs if l["closed_rel"] is None or l["closed_rel"] > 0]
        closed_recs = [l for l in recs if not (l["closed_rel"] is None or l["closed_rel"] > 0)]
        rng = np.random.default_rng(7)
        keep = rng.choice(len(closed_recs), size=int(round(0.5 * len(closed_recs))), replace=False)
        keep_o = rng.choice(len(open_recs), size=int(round(0.6 * len(open_recs))), replace=False)
        chosen = [open_recs[i] for i in sorted(keep_o)] + [closed_recs[i] for i in sorted(keep)]
        chosen.sort(key=lambda r: r["created_rel"])
        lives = [Life(r) for r in chosen]
        lines = VGroup(*[lf.line for lf in lives])
        dots = VGroup(*[lf.dot for lf in lives])

        T = ValueTracker(X_MIN)
        cursor = Line(P(X_MIN, 0), P(X_MIN, A_MAX), stroke_color=INK, stroke_width=2)
        cursor.set_stroke(opacity=0.55)
        cursor.add_updater(lambda m: m.put_start_and_end_on(P(T.get_value(), 0),
                                                            P(T.get_value(), A_MAX)))

        def upd(_m):
            t = T.get_value()
            for lf in lives:
                lf.update(t)

        lines.add_updater(upd)
        self.add(lines, dots, cursor)
        upd(None)

        cap1 = caption("each opportunity ages one business day per day")
        self.play(FadeIn(cursor), FadeIn(cap1, shift=UP * 0.2), run_time=0.6)
        self.play(T.animate.set_value(-29), run_time=3.8, rate_func=smooth)

        # slope triangle on one long-lived lifeline: one day of time = one day of age
        cands = [lf for lf in lives if -58 <= lf.s <= -50 and (lf.e is None or lf.e > -29)]
        ex = min(cands, key=lambda lf: abs(lf.s + 54))
        xa = -39
        aa = xa - ex.s
        tri_pts = [P(xa, aa), P(xa + 5, aa), P(xa + 5, aa + 5)]
        hl = Line(P(ex.x0, ex.x0 - ex.s), P(-29, -29 - ex.s), stroke_color=INK, stroke_width=3)
        tri = VGroup(Line(tri_pts[0], tri_pts[1]), Line(tri_pts[1], tri_pts[2])).set_stroke(INK, 2.5)
        dt = MathTex(r"\Delta t", font_size=FS_TICK, color=INK).next_to(tri[0], DOWN, buff=0.08)
        da = MathTex(r"\Delta a", font_size=FS_TICK, color=INK).next_to(tri[1], RIGHT, buff=0.08)
        for lab in (dt, da):
            lab.add_background_rectangle(color=BG, opacity=0.85, buff=0.03)
        eq = MathTex(r"\Delta a = \Delta t", font_size=FS_LABEL, color=INK)
        eq.next_to(P(-29, aa + 3), RIGHT, buff=0.35)
        self.play(Create(hl), run_time=0.5)
        self.play(Create(tri), FadeIn(dt), FadeIn(da), Write(eq), run_time=0.9)
        self.wait(1.5)
        self.play(FadeOut(VGroup(tri, dt, da, eq)), hl.animate.set_stroke(opacity=0), run_time=0.5)
        self.remove(hl)

        # legend (top right)
        def leg_row(color, label, opacity=1.0):
            d = Dot(radius=DOT_R * 1.5, color=color).set_fill(opacity=opacity)
            t = Tex(label, font_size=FS_LABEL, color=INK)
            return VGroup(d, t).arrange(RIGHT, buff=0.18)
        legend = VGroup(leg_row(WON, "won"), leg_row(LOST, "lost"), leg_row(SURVIVAL, "still open"))
        legend.arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        legend.move_to([3.55, 2.35, 0], aligned_edge=UL)

        cap2 = caption(r"until it is won --- or lost")
        self.play(FadeOut(cap1, shift=UP * 0.2), FadeIn(cap2, shift=UP * 0.2), FadeIn(legend, lag_ratio=0.2), run_time=0.8)
        self.play(T.animate.set_value(0), run_time=8.5, rate_func=rate_functions.ease_out_sine)
        lines.clear_updaters()
        for lf in lives:                      # settle any win flash still in progress
            if lf.state == "won":
                lf.dot.set(width=2 * DOT_R * 1.15)
        cursor.clear_updaters()

        # ------------------------------------------------------------ 2. as-of
        asof = Line(P(0, 0), P(0, A_MAX + 1.5), stroke_color=INK, stroke_width=3)
        asof_lab = Tex("as-of", font_size=FS_LABEL, color=INK).next_to(P(0, A_MAX + 1.5), UP, buff=0.1)
        open_lives = [lf for lf in lives if lf.open_at_asof]
        closed_lives = [lf for lf in lives if not lf.open_at_asof]
        heads = [lf for lf in open_lives if -lf.s <= A_MAX]
        n_open = int(D.stock.total_active)
        counter = Tex(rf"{n_open} open opportunities", font_size=FS_LABEL, color=STOCK)
        counter.move_to([3.55, 0.2, 0], aligned_edge=LEFT)
        cap3 = caption("the as-of date cuts known past from unknown future")

        anims = [ReplacementTransform(cursor, asof), FadeIn(asof_lab, shift=DOWN * 0.1),
                 FadeOut(cap2, shift=UP * 0.2), FadeIn(cap3, shift=UP * 0.2)]
        anims += [lf.line.animate.set_stroke(STOCK, opacity=0.6) for lf in open_lives]
        anims += [lf.dot.animate.set_fill(STOCK, opacity=1) for lf in heads]
        anims += [lf.line.animate.set_stroke(opacity=0.1) for lf in closed_lives]
        anims += [lf.dot.animate.set_fill(opacity=0.35) for lf in closed_lives if lf.state in ("won", "lost")]
        self.play(*anims, run_time=1.6)
        self.play(FadeIn(counter, shift=LEFT * 0.15), run_time=0.7)
        self.wait(1.5)

        # ------------------------------------------------------------ 3. stock by age
        N = np.array(D.stock.N, dtype=float)
        n_max = float(N[:A_MAX].max())
        CU = 3.0 / n_max                                    # screen units per opportunity
        bar_h = 0.8 * U
        bars_g = VGroup()
        for a in range(A_MAX + 1):
            length = min(N[a], n_max) * CU
            r = Rectangle(width=max(length, 1e-3), height=bar_h, stroke_width=0,
                          fill_color=STOCK, fill_opacity=0.9)
            r.move_to(P(0, a), aligned_edge=RIGHT)
            bars_g.add(r)
        top_bar = bars_g[A_MAX]
        # pooled 45+ bucket: drawn at the common maximum, hatched to show it is clipped
        hatch = VGroup(*[Line(ORIGIN, UR * 0.11, stroke_color=BG, stroke_width=2)
                         .move_to(top_bar.get_left() + RIGHT * (0.12 + 0.16 * i))
                         for i in range(3)])
        pooled = int(N[A_MAX])
        lab45 = Tex(rf"45+: {pooled}", font_size=FS_TICK, color=STOCK)
        lab45.next_to(top_bar, LEFT, buff=0.12)
        n_lab = MathTex(r"N(a)", font_size=FS_FORMULA, color=STOCK)
        n_lab.move_to(P(-22, 30))

        dim = [lf.line.animate.set_stroke(opacity=0.06) for lf in closed_lives]
        dim += [lf.dot.animate.set_fill(opacity=0.12) for lf in closed_lives if lf.state in ("won", "lost")]
        dim += [lf.line.animate.set_stroke(opacity=0.13) for lf in open_lives]
        cap4 = caption("the open pipeline, by age", color=INK)
        self.play(*dim, FadeOut(cap3, shift=UP * 0.2), FadeIn(cap4, shift=UP * 0.2), run_time=0.8)

        by_age = {}
        for lf in heads:
            by_age.setdefault(-lf.s, []).append(lf.dot)
        grow = []
        for a in range(A_MAX + 1):
            g = [GrowFromEdge(bars_g[a], RIGHT)]
            if a in by_age:
                g.append(FadeOut(VGroup(*by_age[a]), shift=LEFT * 0.05, scale=0.6))
            grow.append(AnimationGroup(*g))
        self.play(LaggedStart(*grow, lag_ratio=0.06), run_time=2.4)
        self.play(FadeIn(hatch), FadeIn(lab45), ReplacementTransform(counter, n_lab), run_time=0.9)
        self.wait(1.6)

        # ------------------------------------------------------------ 4. the future
        region = Rectangle(width=H * U, height=A_MAX * U, stroke_width=0, fill_color=INK, fill_opacity=0.06)
        region.move_to(P(0, 0), aligned_edge=DL)
        reg_lab = Tex(r"next 15 business days", font_size=FS_LABEL, color=INK)
        reg_lab.next_to(asof_lab, RIGHT, buff=0.35)
        cap5 = caption("future wins come from two sources")

        self.play(FadeIn(region), FadeIn(reg_lab), FadeOut(cap4, shift=UP * 0.2), FadeIn(cap5, shift=UP * 0.2), run_time=1.0)

        # (i) existing stock continuing (real outcomes inside the horizon)
        def dashed(p0, p1, color):
            return DashedLine(p0, p1, dash_length=0.05, dashed_ratio=0.55,
                              stroke_width=2.2, color=color)

        stock_pick = [lf for lf in heads if -lf.s <= 30]
        rng2 = np.random.default_rng(11)
        won_in_h = [lf for lf in stock_pick if lf.e is not None and lf.e <= H and lf.outcome == "won"]
        other = [lf for lf in stock_pick if lf not in won_in_h]
        sel = list(rng2.choice(len(won_in_h), size=min(4, len(won_in_h)), replace=False))
        sel_o = list(rng2.choice(len(other), size=5, replace=False))
        stock_future = VGroup()
        stock_wins = VGroup()
        for lf in [won_in_h[i] for i in sel] + [other[i] for i in sel_o]:
            a0 = -lf.s
            end = H if lf.e is None else min(lf.e, H)
            end = min(end, A_MAX - a0)
            stock_future.add(dashed(P(0, a0), P(end, a0 + end), STOCK))
            if lf.e is not None and lf.e <= H and lf.outcome == "won":
                stock_wins.add(Dot(P(end, a0 + end), radius=DOT_R * 1.3, color=WON))

        fut = [l for l in D.lifelines if 1 <= l["created_rel"] <= H - 2]
        fw = [l for l in fut if l["outcome"] == "won" and l["closed_rel"] <= H]
        fo = [l for l in fut if l not in fw]
        rng3 = np.random.default_rng(5)
        pick = [fw[i] for i in rng3.choice(len(fw), size=min(4, len(fw)), replace=False)]
        pick += [fo[i] for i in rng3.choice(len(fo), size=5, replace=False)]
        arr_future = VGroup()
        arr_wins = VGroup()
        arr_starts = VGroup()
        for l in sorted(pick, key=lambda r: r["created_rel"]):
            s = l["created_rel"]
            end = H if l["closed_rel"] is None else min(l["closed_rel"], H)
            end = max(end, s + 0.4)
            arr_starts.add(Dot(P(s, 0), radius=DOT_R, color=ARRIVALS))
            arr_future.add(dashed(P(s, 0), P(end, end - s), ARRIVALS))
            if l["outcome"] == "won" and l["closed_rel"] <= H:
                arr_wins.add(Dot(P(end, end - s), radius=DOT_R * 1.3, color=WON))

        def leg_dash(color, label):
            d = DashedLine(ORIGIN, RIGHT * 0.45, dash_length=0.06, stroke_width=2.6, color=color)
            t = Tex(label, font_size=FS_LABEL, color=color)
            return VGroup(d, t).arrange(RIGHT, buff=0.18)
        fam = VGroup(leg_dash(STOCK, "existing stock"), leg_dash(ARRIVALS, "future arrivals"))
        fam.arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        fam.move_to([3.5, 0.75, 0], aligned_edge=UL)

        self.play(LaggedStart(*[Create(l) for l in stock_future], lag_ratio=0.12),
                  FadeIn(fam[0], shift=LEFT * 0.1), run_time=1.4)
        self.play(LaggedStart(*[FadeIn(d, scale=2.2) for d in stock_wins], lag_ratio=0.2),
                  LaggedStart(*[FadeIn(d, scale=0.5) for d in arr_starts], lag_ratio=0.1),
                  FadeIn(fam[1], shift=LEFT * 0.1), run_time=0.9)
        self.play(LaggedStart(*[Create(l) for l in arr_future], lag_ratio=0.12), run_time=1.3)
        self.play(LaggedStart(*[FadeIn(d, scale=2.2) for d in arr_wins], lag_ratio=0.2), run_time=0.6)
        self.wait(1.3)

        # ------------------------------------------------------------ 5. the question
        GX0, GY0 = 3.75, -2.55
        gw = 2.85 / H
        g_axis = Line([GX0, GY0, 0], [GX0 + H * gw + 0.1, GY0, 0], stroke_color=MUTED, stroke_width=2)
        ghosts = VGroup()
        cols = VGroup()
        for d in range(1, H + 1):
            gb = Rectangle(width=0.62 * gw, height=1.4, stroke_color=TOTAL, stroke_width=1.4,
                           fill_color=TOTAL, fill_opacity=0.05)
            gb.set_stroke(opacity=0.6)
            gb.move_to([GX0 + (d - 0.5) * gw + 0.05, GY0, 0], aligned_edge=DOWN)
            ghosts.add(gb)
            col = Rectangle(width=0.8 * U, height=A_MAX * U, stroke_width=0,
                            fill_color=TOTAL, fill_opacity=0.07)
            col.move_to(P(d - 0.5, 0), aligned_edge=DOWN)
            cols.add(col)
        g_nums = VGroup(*[MathTex(str(d), font_size=FS_TICK, color=MUTED)
                          .next_to(ghosts[d - 1], DOWN, buff=0.14) for d in (1, 5, 10, 15)])
        g_d = MathTex("d", font_size=FS_LABEL, color=MUTED).next_to(g_axis, RIGHT, buff=0.15)
        q = MathTex(r"\hat{W}(d) = \;?", font_size=FS_FORMULA, color=TOTAL)
        q.next_to(ghosts, UP, buff=0.35)
        cap6 = caption("how many wins on each of the next 15 days?")

        self.play(FadeOut(cap5, shift=UP * 0.2), FadeIn(cap6, shift=UP * 0.2), FadeIn(cols, lag_ratio=0.05), FadeOut(x_title), run_time=1.0)
        self.play(Create(g_axis), *[ReplacementTransform(cols[i], ghosts[i]) for i in range(H)],
                  run_time=1.6)
        self.play(FadeIn(g_nums), FadeIn(g_d), Write(q), run_time=1.0)
        self.wait(3.0)

        close_chapter(self)
