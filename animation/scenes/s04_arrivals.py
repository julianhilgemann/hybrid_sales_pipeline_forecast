import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import *

# chapter 04 -- Forecasting arrivals
#
# history bars (last 40 business days) -> tinted by weekday -> folded into five
# weekday columns with their 180-day means -> the rule -> means tiled onto the
# 15 future slots as A_hat(t) -> Poisson draws hint that this is "how many".

N_PAST = 40
H = 15
PAST_BLUE = "#2F5F8F"                       # muted blue for raw history
DOW_TINT = ["#2A6BBA", "#3A87DC", "#5AAAF8", "#8CC5FA", "#BCDDFD"]   # Mon..Fri
DOW_NAME = ["Mon", "Tue", "Wed", "Thu", "Fri"]
DOW_INIT = ["M", "T", "W", "T", "F"]
DRAW_COLOR = "#C2E0FF"
COL_X = [2, 5, 8, 11, 14]                   # data-x of the five weekday columns


class Clip(Scene):
    def construct(self):
        D = load_data()
        A = D.arrivals
        hist = A.history[-N_PAST:]
        rel = np.array([r["rel"] for r in hist], dtype=float)
        cnt = np.array([r["arrivals"] for r in hist], dtype=float)
        dow = [int(r["dow"]) for r in hist]
        fc = np.asarray(A.forecast, dtype=float)
        fdow = [int(v) for v in A.forecast_dow]
        means = [A.dow_means[i] for i in range(5)]
        t_days = np.arange(1, H + 1)

        open_chapter(self, 4, "Forecasting arrivals", ARRIVALS)

        # ------------------------------------------------------------------
        # 2. history
        # ------------------------------------------------------------------
        # data x runs 0 .. N_PAST + H + 1 so the y-axis sits at the left edge;
        # P(x, y) takes x in business days relative to as-of
        axes = make_axes([0, N_PAST + H + 1, 5], [0, 20, 5], 12.6, 3.75)
        axes.shift(np.array([-6.15, -2.05, 0]) - axes.c2p(0, 0))

        def P(x, y):
            return axes.c2p(x + N_PAST, y)
        unit = axes.x_axis.unit_size

        future_panel = Rectangle(
            width=(H) * unit, height=axes.y_axis.length,
            stroke_width=0, fill_color=PANEL, fill_opacity=1.0,
        ).move_to(P(0.5, 0), aligned_edge=DL)
        stubs = VGroup(*[
            Rectangle(width=0.8 * unit, height=0.07, stroke_width=0,
                      fill_color=GRID, fill_opacity=1.0).move_to(P(t, 0), aligned_edge=DOWN)
            for t in t_days
        ])
        asof_line = DashedLine(P(0.5, 0), P(0.5, 20.6), color=MUTED,
                               stroke_width=2, dash_length=0.08)
        asof_lab = Tex("as-of", font_size=FS_TICK, color=MUTED).next_to(asof_line, UP, buff=0.08)

        ticks = VGroup(
            *[MathTex(f"{v:g}", font_size=FS_TICK, color=MUTED).next_to(P(v, 0), DOWN, buff=0.14)
              for v in (-30, -20, -10, 0)],
            *[MathTex(f"{v:g}", font_size=FS_TICK, color=MUTED).next_to(P(-N_PAST, v), LEFT, buff=0.14)
              for v in (0, 10, 20)],
        )
        y_title = Tex("new opportunities per day", font_size=FS_LABEL, color=MUTED)
        y_title.next_to(P(-N_PAST, 20), UP, buff=0.22).align_to(P(-N_PAST - 1.6, 0), LEFT)
        past_title = Tex("business days, relative to as-of", font_size=FS_LABEL, color=MUTED)
        past_title.move_to([P(-19.5, 0)[0], -2.78, 0])
        fut_title = Tex(r"forecast day $t$", font_size=FS_LABEL, color=MUTED)
        fut_title.move_to([P(8, 0)[0], -2.78, 0])

        past_bars = bars(axes, rel + N_PAST, cnt, PAST_BLUE, width=0.8, fill_opacity=0.95)

        self.play(
            Create(axes), FadeIn(future_panel), FadeIn(ticks), FadeIn(y_title),
            run_time=1.0,
        )
        self.play(
            Create(asof_line), FadeIn(asof_lab, shift=DOWN * 0.1),
            LaggedStart(*[GrowFromEdge(s, DOWN) for s in stubs], lag_ratio=0.05),
            FadeIn(past_title), FadeIn(fut_title),
            run_time=1.1,
        )
        cap = caption("new opportunities keep arriving")
        self.play(
            LaggedStart(*[GrowFromEdge(b, DOWN) for b in past_bars], lag_ratio=0.04),
            FadeIn(cap, shift=UP * 0.1),
            run_time=1.9,
        )
        self.wait(0.7)

        # ------------------------------------------------------------------
        # 3. a weekly rhythm: tint by weekday, then fold into five columns
        # ------------------------------------------------------------------
        cap2 = caption("the same weekdays look alike")
        legend = VGroup(*[
            Tex(DOW_NAME[i], font_size=FS_TICK, color=DOW_TINT[i]) for i in range(5)
        ]).arrange(RIGHT, buff=0.3)
        legend.move_to([P(-20, 0)[0], P(0, 19.5)[1], 0])
        self.play(
            LaggedStart(*[
                b.animate.set_fill(DOW_TINT[dw]) for b, dw in
                sorted(zip(past_bars, dow), key=lambda p: p[1])
            ], lag_ratio=0.02),
            FadeIn(legend, lag_ratio=0.2),
            FadeOut(cap, shift=DOWN * 0.1), FadeIn(cap2, shift=UP * 0.1),
            run_time=1.8,
        )
        self.wait(1.0)

        # fold: copies of the bars fly into five weekday columns in the future panel
        rng = np.random.default_rng(4)
        dots = VGroup()
        for r, c, dw in zip(rel, cnt, dow):
            jitter = rng.uniform(-0.6, 0.6)
            d = Rectangle(width=0.15, height=0.055, stroke_width=0,
                          fill_color=DOW_TINT[dw], fill_opacity=0.9)
            d.move_to(P(COL_X[dw] + jitter, c))
            dots.add(d)
        col_labels = VGroup(*[
            Tex(DOW_NAME[i], font_size=FS_TICK, color=DOW_TINT[i]).move_to([P(COL_X[i], 0)[0], -2.33, 0])
            for i in range(5)
        ])
        order = sorted(range(N_PAST), key=lambda k: (dow[k], k))
        # (a) each bar lifts off its top as a short dash, the bars dim behind it
        dashes = VGroup()
        for k in range(N_PAST):
            d = dots[k].copy().move_to(past_bars[k].get_top() + DOWN * 0.03)
            dashes.add(d)
        copies = VGroup(*[past_bars[k].copy() for k in range(N_PAST)])
        self.play(
            *[ReplacementTransform(copies[k], dashes[k]) for k in range(N_PAST)],
            past_bars.animate.set_fill(PAST_BLUE, opacity=0.55),
            FadeOut(legend), FadeOut(stubs), FadeOut(fut_title),
            run_time=0.8,
        )
        # (b) the dashes fly, weekday by weekday, into their columns
        self.play(
            LaggedStart(*[
                ReplacementTransform(dashes[k], dots[k], path_arc=-0.5) for k in order
            ], lag_ratio=0.025),
            LaggedStart(*[FadeIn(l, shift=UP * 0.08) for l in col_labels], lag_ratio=0.25),
            run_time=2.2,
        )

        markers = VGroup(*[
            Rectangle(width=2.2 * unit, height=0.07, stroke_width=0,
                      fill_color=ARRIVALS, fill_opacity=1.0).move_to(P(COL_X[i], means[i]))
            for i in range(5)
        ])
        cap3 = caption("mean by weekday, last 180 days")
        self.play(
            LaggedStart(*[GrowFromCenter(m) for m in markers], lag_ratio=0.15),
            dots.animate.set_fill(opacity=0.45),
            FadeOut(cap2, shift=DOWN * 0.1), FadeIn(cap3, shift=UP * 0.1),
            run_time=1.4,
        )
        self.wait(1.6)

        # ------------------------------------------------------------------
        # 4. the rule
        # ------------------------------------------------------------------
        formula = MathTex(
            r"\hat{A}(t)", r"=", r"\operatorname{mean}",
            r"\{\, A(s) : \operatorname{weekday}(s) = \operatorname{weekday}(t) \,\}",
            font_size=FS_FORMULA,
        )
        formula[0].set_color(ARRIVALS)
        formula.move_to([0, 2.78, 0]).to_edge(RIGHT, buff=0.5)
        tag = Tex("seasonal-naive", font_size=FS_LABEL, color=MUTED)
        tag.next_to(formula, DOWN, buff=0.14, aligned_edge=LEFT)
        self.play(
            TransformFromCopy(markers, formula[0]),
            Write(formula[1:]),
            FadeOut(cap3, shift=DOWN * 0.1),
            run_time=1.8,
        )
        self.play(FadeIn(tag, shift=UP * 0.08), run_time=0.6)
        self.wait(2.0)

        # ------------------------------------------------------------------
        # 5. tile it forward
        # ------------------------------------------------------------------
        fbars = bars(axes, t_days + N_PAST, fc, ARRIVALS, width=0.8, fill_opacity=0.95)
        inits = VGroup(*[
            Tex(DOW_INIT[fdow[j]], font_size=FS_TICK, color=INK).move_to([P(t_days[j], 0)[0], -2.33, 0])
            for j in range(H)
        ])
        seps = VGroup(*[
            Line(UP * 0.13, DOWN * 0.13, color=GRID, stroke_width=2).move_to([P(t_days[j] + 0.5, 0)[0], -2.33, 0])
            for j in range(H - 1) if fdow[j] == 4
        ])
        fut_title2 = Tex(r"forecast day $t$", font_size=FS_LABEL, color=MUTED).move_to(fut_title)
        a_lab = MathTex(r"\hat{A}(t)", font_size=FS_FORMULA, color=ARRIVALS)
        a_lab.move_to([P(10.5, 0)[0], 2.12, 0])
        cap4 = caption("repeat the weekly pattern forward")

        # the dots drain away, each weekday marker stamps onto its slots
        self.play(FadeOut(dots), FadeOut(col_labels), FadeIn(cap4, shift=UP * 0.1), run_time=0.7)
        lines = VGroup(*[
            Rectangle(width=0.8 * unit, height=0.07, stroke_width=0,
                      fill_color=ARRIVALS, fill_opacity=1.0).move_to(P(t_days[j], fc[j]))
            for j in range(H)
        ])
        self.play(
            LaggedStart(*[
                TransformFromCopy(markers[fdow[j]], lines[j], path_arc=-0.4) for j in range(H)
            ], lag_ratio=0.07),
            FadeOut(markers),
            LaggedStart(*[FadeIn(inits[j], shift=UP * 0.08) for j in range(H)], lag_ratio=0.07),
            FadeIn(seps),
            run_time=2.2,
        )
        self.play(
            *[ReplacementTransform(lines[j], fbars[j]) for j in range(H)],
            run_time=1.0,
        )
        self.play(
            FadeIn(fut_title2, shift=UP * 0.08),
            FadeIn(a_lab, shift=DOWN * 0.1),
            run_time=0.8,
        )
        self.wait(0.8)

        # ------------------------------------------------------------------
        # 6. stochastic hint: Poisson draws scatter around A_hat(t)
        # ------------------------------------------------------------------
        prng = np.random.default_rng(404)
        n_draws = 4
        draws = prng.poisson(fc, size=(n_draws, H))
        cap5 = caption(r"a forecast of how many --- not which ones")

        def draw_dots(k, opacity):
            return VGroup(*[
                Dot(P(t_days[j], draws[k, j]), radius=0.06, color=DRAW_COLOR).set_fill(opacity=opacity)
                for j in range(H)
            ])

        cur = draw_dots(0, 0.95)
        self.play(
            FadeOut(cap4, shift=DOWN * 0.1), FadeIn(cap5, shift=UP * 0.1),
            FadeIn(cur, lag_ratio=0.05),
            run_time=0.9,
        )
        ghosts = VGroup()
        for k in range(1, n_draws):
            nxt = draw_dots(k, 0.95)
            ghost = cur.copy().set_fill(ARRIVALS, opacity=0.45)
            ghosts.add(ghost)
            self.add(ghost)
            self.play(Transform(cur, nxt), run_time=0.65, rate_func=smooth)
            self.wait(0.15)
        self.wait(0.7)

        # ------------------------------------------------------------------
        # 7. hero: past dimmed, the 15 blue bars
        # ------------------------------------------------------------------
        self.play(
            FadeOut(cur), FadeOut(ghosts), FadeOut(cap5),
            past_bars.animate.set_fill(PAST_BLUE, opacity=0.3),
            FadeOut(formula), FadeOut(tag),
            run_time=1.0,
        )
        self.wait(2.5)
        close_chapter(self)
