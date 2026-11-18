import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import *

"""Chapter 10 -- The forecast and its uncertainty.

One 2D chart for the whole chapter: forecast days 1..15 on x, wins per day on y.
The y scale starts tight (0..4, the expected bars) and is rescaled once (0..10)
when the first simulated future arrives. Every data object is drawn through
``P(day, value, top)`` so the rescale is a transform between two builds.
"""

H = 15
X0, Y0 = -5.2, -2.0       # scene position of (day 0, value 0)
UX = 0.65                 # scene units per forecast day
PH = 4.2                  # plot height (scene units)
TOP_A, TOP_B = 4, 10      # y range: expected bars only, then simulated futures
N_DRAWN = 40              # simulated futures drawn as lines (of 400)
ROW_Y = 2.68              # text row between the header/formula and the plot
DAYS = np.arange(1, H + 1)


def P(d, v, top):
    """Scene point of forecast day ``d`` and value ``v`` on a 0..``top`` y scale."""
    return np.array([X0 + d * UX, Y0 + v * PH / top, 0.0])


def bar_rects(xs, heights, bottoms, top, color, width, opacity=0.9):
    g = VGroup()
    for x, h, b in zip(xs, heights, bottoms):
        r = Rectangle(width=width * UX, height=max(h * PH / top, 1e-3), stroke_width=0,
                      fill_color=color, fill_opacity=opacity)
        r.move_to(P(x, b, top), aligned_edge=DOWN)
        g.add(r)
    return g


def polyline(values, top, color, width, opacity=1.0):
    ln = VMobject(stroke_color=color, stroke_width=width, stroke_opacity=opacity)
    ln.set_points_as_corners([P(d, v, top) for d, v in zip(DAYS, values)])
    return ln


def mean_poly(values, halo=8.0):
    """The running mean: a bright line with a dark halo that lifts it off the futures."""
    ln = polyline(values, TOP_B, INK, 4)
    ln.set_stroke(BG, width=halo, opacity=0.85 if halo else 0.0, background=True)
    return ln.set_z_index(4)


def value_dots(values, top, color, radius=0.06, opacity=1.0):
    return VGroup(*[Dot(P(d, v, top), radius=radius, color=color, fill_opacity=opacity)
                    for d, v in zip(DAYS, values)])


def y_ticks(values, top):
    """Grid line + tick number for each value on a 0..``top`` scale."""
    g = VGroup()
    for v in values:
        lab = MathTex(f"{v:g}", font_size=FS_TICK, color=MUTED).next_to(P(0, v, top), LEFT, buff=0.14)
        if v == 0:
            g.add(VGroup(lab))
            continue
        grid = Line(P(0, v, top), P(16, v, top), color=GRID, stroke_width=1.2)
        g.add(VGroup(grid, lab))
    return g


def band_polygon(lo, hi, top):
    pts = [P(d, v, top) for d, v in zip(DAYS, hi)] + [P(d, v, top) for d, v in zip(DAYS[::-1], lo[::-1])]
    return Polygon(*pts, stroke_color=TOTAL, stroke_width=1.4, stroke_opacity=0.55,
                   fill_color=TOTAL, fill_opacity=0.2)


class Clip(Scene):
    def construct(self):
        D = load_data()
        F, MC = D.forecast, D.monte_carlo
        T = MC.total                       # 400 simulated futures x 15 days
        zeros = np.zeros(H)

        open_chapter(self, 10, "The forecast and its uncertainty", TOTAL,
                     question=r"What does ``3.4 expected wins'' actually mean?", part=PART[5])

        # ------------------------------------------------------------ the chart
        ax = make_axes([0, 16, 1], [0, TOP_A, 1], 16 * UX, PH, y_axis_config={"include_ticks": False})
        ax.shift(P(0, 0, TOP_A) - ax.c2p(0, 0))
        xlabs = VGroup(*[MathTex(f"{v}", font_size=FS_TICK, color=MUTED).next_to(P(v, 0, TOP_A), DOWN, buff=0.14)
                         for v in (1, 5, 10, 15)])
        xt = Tex(r"forecast day $d$", font_size=FS_LABEL, color=MUTED)
        xt.next_to(P(16, 0, TOP_A), DOWN, buff=0.5).align_to(P(16, 0, TOP_A), RIGHT)
        yt = Tex("expected wins per day", font_size=FS_LABEL, color=MUTED).rotate(PI / 2)
        yt.move_to([X0 - 0.78, Y0 + PH / 2, 0])
        yt_sim = Tex("wins per day", font_size=FS_LABEL, color=MUTED).rotate(PI / 2).move_to(yt)
        ticks_a = y_ticks([0, 1, 2, 3, 4], TOP_A)
        ticks_b = y_ticks([0, 2, 4, 6, 8, 10], TOP_B)

        # ------------------------------------------- beat 2: the two streams
        rose_side = bar_rects(DAYS - 0.19, F.stock, zeros, TOP_A, STOCK, 0.36)
        blue_side = bar_rects(DAYS + 0.19, F.arrivals, zeros, TOP_A, ARRIVALS, 0.36)
        lab_s = VGroup(MathTex(r"W_{\text{stock}}(d)", font_size=FS_FORMULA - 6, color=STOCK),
                       Tex("open pipeline", font_size=FS_LABEL, color=STOCK)).arrange(DOWN, buff=0.12)
        lab_s.move_to(P(6.7, 0, TOP_A)[0] * RIGHT).set_y(1.0, direction=DOWN)
        lab_a = VGroup(MathTex(r"W_{\text{arr}}(d)", font_size=FS_FORMULA - 6, color=ARRIVALS),
                       Tex("new deals", font_size=FS_LABEL, color=ARRIVALS)).arrange(DOWN, buff=0.12)
        lab_a.move_to(P(12.6, 0, TOP_A)[0] * RIGHT).set_y(1.05, direction=DOWN)

        self.play(Create(ax), FadeIn(xlabs), FadeIn(ticks_a), FadeIn(xt), FadeIn(yt), run_time=0.9)
        self.play(LaggedStart(*[GrowFromEdge(b, DOWN) for b in rose_side], lag_ratio=0.06),
                  FadeIn(lab_s, shift=UP * 0.15), run_time=1.0)
        self.play(LaggedStart(*[GrowFromEdge(b, DOWN) for b in blue_side], lag_ratio=0.06),
                  FadeIn(lab_a, shift=UP * 0.15), run_time=1.0)
        cap = swap_caption(self, None, "one stream drains, the other ripens")
        self.wait(3.0)

        # ------------------------------------------------- beat 3: add them
        formula = MathTex(r"\hat{W}(d)", "=", r"W_{\text{stock}}(d)", "+", r"W_{\text{arr}}(d)",
                          font_size=FS_FORMULA)
        for part, col in zip(formula, (TOTAL, INK, STOCK, INK, ARRIVALS)):
            part.set_color(col)
        formula.to_edge(RIGHT, buff=0.45).set_y(3.32)
        w_hat = Tex("forecast", font_size=FS_LABEL, color=TOTAL).move_to([formula[0].get_x(), ROW_Y, 0])
        w_s_pos = np.array([formula[2].get_x(), ROW_Y, 0])
        w_a_pos = np.array([formula[4].get_x(), ROW_Y, 0])

        # the two symbols fly up and become the right-hand side
        self.play(ReplacementTransform(lab_s[0], formula[2]), lab_s[1].animate.move_to(w_s_pos),
                  ReplacementTransform(lab_a[0], formula[4]), lab_a[1].animate.move_to(w_a_pos),
                  FadeIn(formula[3], scale=0.6, rate_func=delayed(0.55, 0.45)),
                  run_time=1.7)
        words = VGroup(w_hat, lab_s[1], lab_a[1])

        # the blue bars lift onto the rose bars
        rose_stack = bar_rects(DAYS, F.stock, zeros, TOP_A, STOCK, 0.72)
        blue_stack = bar_rects(DAYS, F.arrivals, F.stock, TOP_A, ARRIVALS, 0.72)
        blue_lift = bar_rects(DAYS + 0.19, F.arrivals, F.stock, TOP_A, ARRIVALS, 0.36)
        self.play(LaggedStart(*[Transform(a, b) for a, b in zip(blue_side, blue_lift)], lag_ratio=0.05),
                  run_time=1.3)
        self.play(*[Transform(a, b) for a, b in zip(rose_side, rose_stack)],
                  *[Transform(a, b) for a, b in zip(blue_side, blue_stack)],
                  run_time=1.1)
        rose, blue = rose_side, blue_side

        # their sum: the forecast, marked by a teal line over the stacks
        model_line = polyline(F.total, TOP_A, TOTAL, 4.5)
        model_dots = value_dots(F.total, TOP_A, TOTAL)
        model = VGroup(model_line, model_dots).set_z_index(3)
        wtag = MathTex(r"\hat{W}(d)", font_size=FS_LABEL + 3, color=TOTAL)
        wtag.next_to(P(15, F.total[-1], TOP_A), RIGHT, buff=0.42)
        self.play(Write(formula[0]), FadeIn(formula[1]), FadeIn(w_hat, shift=UP * 0.1),
                  Create(model_line), FadeIn(model_dots, lag_ratio=0.1), FadeIn(wtag),
                  run_time=1.6)
        self.remove(*formula)
        self.add(formula)
        self.wait(3.2)

        # the words become the 15-day totals
        nums = VGroup(
            MathTex(f"{F.total.sum():.1f}", font_size=FS_LABEL + 5, color=TOTAL),
            MathTex("=", font_size=FS_LABEL + 5, color=INK),
            MathTex(f"{F.stock.sum():.1f}", font_size=FS_LABEL + 5, color=STOCK),
            MathTex("+", font_size=FS_LABEL + 5, color=INK),
            MathTex(f"{F.arrivals.sum():.1f}", font_size=FS_LABEL + 5, color=ARRIVALS),
        )
        for n, term in zip(nums, formula):
            n.move_to([term.get_x(), ROW_Y, 0])
        sum_lab = Tex("expected wins over 15 days:", font_size=FS_LABEL, color=MUTED)
        sum_lab.next_to(nums[0], LEFT, buff=0.35)
        self.play(FadeTransform(words[0], nums[0]), FadeTransform(words[1], nums[2]),
                  FadeTransform(words[2], nums[4]), FadeIn(nums[1]), FadeIn(nums[3]),
                  FadeIn(sum_lab, shift=RIGHT * 0.15), run_time=1.3)
        self.wait(2.1)

        # --------------------------------------------- beat 4: what is 3.4?
        k8 = 7   # day 8: 3.4 expected wins
        box = SurroundingRectangle(VGroup(rose[k8], blue[k8]), color=TOTAL, corner_radius=0.08,
                                   stroke_width=2.2, buff=0.07)
        box_lab = Tex(f"day {k8 + 1}: {F.total[k8]:.1f} expected wins", font_size=FS_LABEL, color=TOTAL)
        box_lab.next_to(box, UP, buff=0.14)
        self.play(Create(box), FadeIn(box_lab, shift=DOWN * 0.1),
                  *[m.animate.set_fill(opacity=0.35) for i, m in enumerate([*rose, *blue]) if i % H != k8],
                  run_time=1.0)
        cap = swap_caption(self, cap, r"no deal is 0.4 won: this is an average")
        self.wait(2.7)

        # rescale for the simulated futures: 0..4 -> 0..10
        rose_b = bar_rects(DAYS, F.stock, zeros, TOP_B, STOCK, 0.72, opacity=0.28)
        blue_b = bar_rects(DAYS, F.arrivals, F.stock, TOP_B, ARRIVALS, 0.72, opacity=0.28)
        model_b = VGroup(polyline(F.total, TOP_B, TOTAL, 4.5, opacity=0.55),
                         value_dots(F.total, TOP_B, TOTAL, opacity=0.55))
        ticks_a_out = ticks_a.copy()
        for v, item in zip([0, 1, 2, 3, 4], ticks_a_out):
            item.shift(DOWN * v * PH * (1 / TOP_A - 1 / TOP_B)).set_opacity(0)
        ticks_b.shift(UP * 0.35).set_opacity(0)
        ticks_b_tgt = y_ticks([0, 2, 4, 6, 8, 10], TOP_B)
        self.play(FadeOut(cap, shift=UP * 0.12), run_time=0.4)
        self.play(*[Transform(a, b) for a, b in zip([*rose, *blue], [*rose_b, *blue_b])],
                  Transform(model, model_b),
                  wtag.animate.next_to(P(15, F.total[-1], TOP_B), RIGHT, buff=0.42),
                  Transform(ticks_a, ticks_a_out), Transform(ticks_b, ticks_b_tgt),
                  FadeTransform(yt, yt_sim),
                  FadeOut(box), FadeOut(box_lab), FadeOut(nums), FadeOut(sum_lab),
                  formula.animate.set_opacity(0.4),
                  run_time=2.0)
        self.remove(ticks_a)

        # one possible future: every deal's dice rolled once; one dot per win
        cap = swap_caption(self, None, r"roll the dice for every deal: one possible future")
        self.wait(1.5)
        s0, a0 = MC.stock[0].astype(int), MC.arrivals[0].astype(int)
        columns = []
        for d in DAYS:
            col = VGroup()
            for k in range(s0[d - 1] + a0[d - 1]):
                c = STOCK if k < s0[d - 1] else ARRIVALS
                col.add(Dot(P(d, k + 0.5, TOP_B), radius=0.15, color=c))
            columns.append(col)
        dots = VGroup(*columns).set_z_index(5)
        legend = VGroup(Dot(radius=0.11, color=STOCK), Dot(radius=0.11, color=ARRIVALS),
                        Tex("one dot = one win", font_size=FS_LABEL, color=INK))
        legend.arrange(RIGHT, buff=0.1)
        legend[2].shift(RIGHT * 0.08)
        legend.move_to([0, ROW_Y, 0]).align_to(P(0, 0, TOP_B), LEFT)
        self.play(LaggedStart(*[LaggedStart(*[FadeIn(dt, shift=DOWN * 0.3) for dt in col], lag_ratio=0.25)
                                if len(col) else Wait() for col in columns], lag_ratio=0.12),
                  FadeIn(legend, rate_func=delayed(0.0, 0.3)),
                  run_time=3.0)
        self.wait(1.4)

        # ---------------------------------------------- beat 5: many futures
        rng = np.random.default_rng(10)
        depth = rng.uniform(0.0, 1.0, N_DRAWN)
        rest = [dict(color=interpolate_color(ManimColor(TOTAL), ManimColor(INK), 0.35 * f),
                     width=0.9 + 0.9 * f, opacity=0.13 + 0.24 * f) for f in depth]
        lines = [polyline(T[j], TOP_B, INK, 2.2, opacity=0.0).set_z_index(2) for j in range(N_DRAWN)]
        cum_mean = np.cumsum(T, axis=0) / np.arange(1, T.shape[0] + 1)[:, None]

        def rest_anim(j):
            r = rest[j]
            return lines[j].animate.set_stroke(color=r["color"], width=r["width"], opacity=r["opacity"])

        # the dots become a line: this future
        self.play(Create(lines[0].set_stroke(opacity=0.95)), FadeOut(dots), FadeOut(legend), run_time=1.3)
        self.wait(0.4)

        # a second future, then the average of the two
        self.play(Create(lines[1].set_stroke(opacity=0.95)), rest_anim(0), run_time=1.0)
        mean_line = mean_poly(T[0], halo=0.0)
        mean_line.set_stroke(INK, width=2.2, opacity=0.95)
        sw = Line(LEFT * 0.2, RIGHT * 0.2, color=INK, stroke_width=4)
        w_mean = Tex("average of", font_size=FS_LABEL, color=INK)
        counter = DecimalNumber(2, num_decimal_places=0, mob_class=Tex, font_size=FS_LABEL, color=INK)
        w_fut = Tex("simulated futures", font_size=FS_LABEL, color=INK)
        crow = VGroup(sw, w_mean, counter, w_fut).arrange(RIGHT, buff=0.12)
        crow[1:].shift(RIGHT * 0.06)
        crow.move_to([0, ROW_Y, 0]).align_to(P(0, 0, TOP_B), LEFT)
        base_y = w_mean[0][0].get_bottom()[1]          # text baseline (the "a")

        def sit(m):
            return m.shift(UP * (base_y - m.get_bottom()[1]))

        sit(counter)
        sit(w_fut)
        anchor_l = counter.get_left().copy()
        self.play(Transform(mean_line, mean_poly(cum_mean[1])), FadeIn(crow), run_time=1.2)
        self.wait(0.4)

        # futures 3..40 drawn, then the remaining 360 counted only
        TB, TC = 3.6, 3.2                       # seconds of each phase
        total_t = TB + TC
        t_app = {j: (j - 2) / (N_DRAWN - 2) * (TB - 0.5) for j in range(2, N_DRAWN)}
        t_app[1] = -0.6                         # future 2 settles at the start
        FADE_IN, DECAY, PEAK = 0.4, 0.7, 0.55
        NEW = interpolate_color(ManimColor(TOTAL), ManimColor(INK), 0.6)   # a fresh future

        def n_at(t):
            if t <= TB:
                return 2 + (N_DRAWN - 2) * min(1.0, t / (TB - 0.5 + 1e-9) + 1 / (N_DRAWN - 2))
            s = (t - TB) / TC
            return N_DRAWN + (T.shape[0] - N_DRAWN) * (0.12 * s + 0.88 * smooth(s))

        def style(j, t):
            u = t - t_app[j]
            r = rest[j]
            if u < 0:
                return None
            if u < FADE_IN:
                return NEW, 1.8, PEAK * smooth(u / FADE_IN)
            b = smooth(min(1.0, (u - FADE_IN) / DECAY))
            col = interpolate_color(NEW, ManimColor(r["color"]), b)
            return col, 1.8 + (r["width"] - 1.8) * b, PEAK + (r["opacity"] - PEAK) * b

        def update(mob, alpha):
            t = alpha * total_t
            n = max(2, min(T.shape[0], int(n_at(t))))
            mean_line.set_points_as_corners([P(d, v, TOP_B) for d, v in zip(DAYS, cum_mean[n - 1])])
            if int(counter.get_value()) != n:
                counter.set_value(n)
                sit(counter.move_to(anchor_l, aligned_edge=LEFT))
                sit(w_fut.next_to(counter, RIGHT, buff=0.12))
            for j in range(1, N_DRAWN):
                st = style(j, t)
                if st is not None:
                    lines[j].set_stroke(color=st[0], width=st[1], opacity=st[2])

        for j in range(2, N_DRAWN):
            self.add(lines[j])
        w400 = DecimalNumber(T.shape[0], num_decimal_places=0, mob_class=Tex, font_size=FS_LABEL).width
        drawn_note = Tex(f"({N_DRAWN} drawn)", font_size=FS_TICK, color=MUTED)
        drawn_note.move_to([anchor_l[0] + w400 + 0.12 + w_fut.width + 0.22, w_fut.get_y(), 0], aligned_edge=LEFT)
        self.play(UpdateFromAlphaFunc(VGroup(model, mean_line, counter, w_fut, *lines[1:]), update,
                                      rate_func=linear),
                  FadeIn(drawn_note, rate_func=delayed(TB / total_t, 0.6 / total_t)),
                  run_time=total_t)

        # payoff: the average lands on the model
        self.play(*[lines[j].animate.set_stroke(opacity=rest[j]["opacity"] * 0.55) for j in range(N_DRAWN)],
                  model[0].animate.set_stroke(width=7, opacity=1.0), model[1].animate.set_fill(opacity=1.0),
                  mean_line.animate.set_stroke(width=2.6).set_stroke(BG, width=0, opacity=0, background=True),
                  formula[0].animate.set_opacity(1.0),
                  run_time=1.0)
        cap = swap_caption(self, cap, "average many futures: the forecast")
        self.wait(1.6)
        sim_total = T.sum(axis=1).mean()
        note = Tex(r"15 days: simulated mean ", f"{sim_total:.1f}", r" vs ", f"model {F.total.sum():.1f}",
                   font_size=FS_LABEL, color=INK)
        note[0].set_color(MUTED)
        note[2].set_color(MUTED)
        note[3].set_color(TOTAL)
        note.to_edge(RIGHT, buff=0.45)
        note.shift(UP * (base_y - note[0][0].get_bottom()[1]))
        self.play(FadeIn(note, shift=UP * 0.1), run_time=0.9)
        self.wait(2.3)

        # ------------------------------------------------- beat 6: the spread
        band = band_polygon(MC.q05_total, MC.q95_total, TOP_B).set_z_index(1)
        band_start = band_polygon(MC.mean_total, MC.mean_total, TOP_B).set_z_index(1)
        band_start.set_fill(opacity=0.0)
        self.play(Transform(band_start, band),
                  *[FadeOut(ln) for ln in lines], FadeOut(mean_line),
                  FadeOut(crow), FadeOut(drawn_note), FadeOut(note),
                  model[0].animate.set_stroke(width=4.5),
                  *[b.animate.set_fill(opacity=0.12) for b in [*rose, *blue]],
                  run_time=2.2)
        band_lab = Tex(r"90\% of simulated futures", font_size=FS_LABEL, color=TOTAL)
        band_lab.move_to([P(12.4, 0, TOP_B)[0], P(0, 8.3, TOP_B)[1], 0])
        self.play(FadeIn(band_lab, shift=DOWN * 0.1), run_time=0.8)
        cap = swap_caption(self, cap, "a typical day: between 1 and 6 wins")
        self.wait(3.0)

        # --------------------------------------- beat 7: what actually happened
        cap = swap_caption(self, cap, "what actually happened: all 15 days within the band")
        self.wait(1.5)
        actual = VGroup(*[Dot(P(d, v, TOP_B), radius=0.1, color=INK) for d, v in zip(DAYS, F.actual)])
        actual.set_z_index(6)
        self.play(LaggedStart(*[FadeIn(a, scale=0.3) for a in actual], lag_ratio=0.14), run_time=2.8)
        self.wait(2.0)

        # ------------------------------------------------------------- takeaway
        takeaway(self, "the forecast is the average of possible futures", TOTAL, old_caption=cap)
        close_chapter(self)
