import sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import *

# chapter 08 -- Forecasting new arrivals
#
# the last 60 business days of new deals, left of "today", the next 15 days
# shaded -> Mondays busy, Fridays quiet -> every bar folds into its weekday
# column and the weekday means settle -> the rule (seasonal naive) -> copies of
# the five means are tiled onto the 15 future days: the blue A_hat(t) bars ->
# what actually arrived, as context -> takeaway, hold on A_hat(t).

H = 15
N_PAST = 60
PAST_BLUE = "#33669A"        # muted blue: raw history
DASH_BLUE = "#6C9BCF"        # folded history ticks
LETTER_BLUE = "#C2E0FF"      # weekday letters over highlighted bars
DOW_LETTER = ["M", "T", "W", "T", "F"]
DOW_NAME = ["Mon", "Tue", "Wed", "Thu", "Fri"]
FS_DAY = 24                  # weekday letters / names

# ---- geometry (scene units) ------------------------------------------------
Y0, YT, YMAX = -1.55, 2.15, 22          # baseline, top of the plot, its value
U = (YT - Y0) / YMAX                    # scene units per deal
X0, XE = -6.1, 6.55                     # y-axis, right end of the x-axis
ROW1, ROW2, ROW3 = -1.80, -2.17, -2.60  # label rows under the axis

# phase A: one timeline, 60 past days | today | 15 future days
SA = (XE - X0) / (N_PAST + H + 0.7)
XA_TODAY = X0 + 60.5 * SA


def xa_past(i):          # i = 0..59 (oldest .. today)
    return X0 + (0.8 + i) * SA


# phase B: five weekday columns | today | 15 wide future slots
COL_X = [-5.3, -4.3, -3.3, -2.3, -1.3]
XB_TODAY = -0.62
SB = (XE - XB_TODAY - 0.12) / H


def xb_fut(t):           # t = 1..15
    return XB_TODAY + 0.12 + (t - 0.5) * SB


def py(v):
    return Y0 + v * U


def rect(w, h, color, opacity=1.0):
    return Rectangle(width=w, height=h, stroke_width=0, fill_color=color, fill_opacity=opacity)


class Clip(Scene):
    def construct(self):
        D = load_data()
        A = D.arrivals
        hist = A.history
        cnt = np.array([r["arrivals"] for r in hist], dtype=float)
        dow = [int(r["dow"]) for r in hist]
        fc = np.asarray(A.forecast, dtype=float)
        fdow = [int(v) for v in A.forecast_dow]
        means = [A.dow_means[k] for k in range(5)]
        born = Counter(int(r["created_rel"]) for r in D.lifelines)
        actual = [born[t] for t in range(1, H + 1)]

        open_chapter(self, 8, "Forecasting new arrivals", ARRIVALS,
                     question="How many new deals will arrive on each coming day?", part=PART[4])

        # ==================================================================
        # 2. history: 60 business days left of today, the next 15 shaded
        # ==================================================================
        x_axis = Line([X0, Y0, 0], [XE, Y0, 0], color=MUTED, stroke_width=2)
        y_axis = Line([X0, Y0, 0], [X0, YT, 0], color=MUTED, stroke_width=2)
        grid = VGroup(*[Line([X0, py(v), 0], [XE, py(v), 0], color=GRID, stroke_width=1)
                        for v in (5, 10, 15, 20)])
        y_ticks = VGroup(*[MathTex(str(v), font_size=FS_TICK, color=MUTED).next_to([X0, py(v), 0], LEFT, buff=0.14)
                           for v in (0, 5, 10, 15, 20)])
        y_title = Tex("new deals per day", font_size=FS_LABEL, color=MUTED)
        y_title.move_to([0, YT + 0.4, 0]).align_to([X0 - 0.5, 0, 0], LEFT)
        x_ticks_a = VGroup(*[MathTex(str(v), font_size=FS_TICK, color=MUTED).move_to([xa_past(59 - v), ROW1, 0])
                             for v in (50, 40, 30, 20, 10, 0)])
        x_title_a = Tex("business days before today", font_size=FS_LABEL, color=MUTED)
        x_title_a.move_to([0.5 * (X0 + XA_TODAY), ROW2 - 0.04, 0])

        zone = rect(XE - XA_TODAY, YT - Y0, ARRIVALS, 0.07).move_to([0.5 * (XA_TODAY + XE), 0.5 * (Y0 + YT), 0])
        zone_lab = Tex("next 15 business days", font_size=FS_TICK, color=MUTED)
        zone_lab.move_to([zone.get_center()[0], YT - 0.26, 0])
        qmark = Tex("?", font_size=72, color=ARRIVALS).move_to([zone.get_center()[0], py(9), 0])
        today_line = DashedLine([XA_TODAY, Y0, 0], [XA_TODAY, YT + 0.08, 0], color=MUTED,
                                stroke_width=2, dash_length=0.08)
        today_lab = Tex("today", font_size=FS_DAY, color=INK).next_to(today_line, UP, buff=0.1)

        past_bars = VGroup(*[rect(0.8 * SA, cnt[i] * U, PAST_BLUE, 1.0).move_to([xa_past(i), Y0, 0], aligned_edge=DOWN)
                             for i in range(N_PAST)])

        self.add(grid, zone)
        grid.set_opacity(0)
        zone.set_opacity(0)
        self.play(Create(x_axis), Create(y_axis), grid.animate.set_stroke(opacity=1),
                  FadeIn(y_ticks), FadeIn(y_title), zone.animate.set_fill(opacity=0.07),
                  Create(today_line), FadeIn(today_lab, shift=DOWN * 0.1), FadeIn(zone_lab),
                  FadeIn(qmark, scale=0.8), run_time=1.2)
        self.play(LaggedStart(*[GrowFromEdge(b, DOWN) for b in past_bars], lag_ratio=0.03),
                  FadeIn(x_ticks_a), FadeIn(x_title_a), run_time=1.8)
        cap = swap_caption(self, None, "new deals per business day, last 60 days")
        self.wait(2.0)

        # ==================================================================
        # 3. the weekly pattern: Mondays busy ... Fridays quiet
        # ==================================================================
        def highlight(k):
            return [b.animate.set_fill(ARRIVALS if dow[i] == k else PAST_BLUE, opacity=1.0 if dow[i] == k else 0.25)
                    for i, b in enumerate(past_bars)]

        def letters(k):
            return VGroup(*[Tex(DOW_LETTER[k], font_size=FS_DAY, color=LETTER_BLUE).next_to(past_bars[i], UP, buff=0.1)
                            for i in range(N_PAST) if dow[i] == k])

        L = letters(0)
        self.play(*highlight(0), FadeIn(L, shift=DOWN * 0.1), run_time=1.0)
        cap = swap_caption(self, cap, "Mondays are busy, Fridays quiet")
        self.wait(1.2)
        for k in (1, 2, 3, 4):
            L2 = letters(k)
            self.play(*highlight(k), FadeOut(L, shift=RIGHT * SA), FadeIn(L2, shift=RIGHT * SA),
                      run_time=0.5)
            L = L2
            self.wait(0.08 if k < 4 else 1.5)

        # ==================================================================
        # 4. fold every day into its weekday column; the means settle
        # ==================================================================
        dashes = VGroup(*[rect(0.12, 0.05, DASH_BLUE).move_to([xa_past(i), py(cnt[i]), 0]) for i in range(N_PAST)])
        self.play(*[ReplacementTransform(past_bars[i], dashes[i]) for i in range(N_PAST)],
                  FadeOut(L), FadeOut(cap, shift=UP * 0.12), FadeOut(x_ticks_a), FadeOut(x_title_a),
                  run_time=1.2)

        tx = np.zeros(N_PAST)
        for k in range(5):
            idx = [i for i in range(N_PAST) if dow[i] == k]
            for o, i in zip(np.linspace(-0.36, 0.36, len(idx)), idx):
                tx[i] = COL_X[k] + o
        col_labs = VGroup(*[Tex(DOW_NAME[k], font_size=FS_DAY, color=INK).move_to([COL_X[k], ROW1, 0]) for k in range(5)])
        flights = [AnimationGroup(*[dashes[i].animate.move_to([tx[i], py(cnt[i]), 0])
                                    for i in range(N_PAST) if dow[i] == k]) for k in range(5)]
        cap = caption("sort the past days by weekday")
        self.play(LaggedStart(*flights, lag_ratio=0.3),
                  LaggedStart(*[FadeIn(c, shift=UP * 0.1) for c in col_labs], lag_ratio=0.3),
                  FadeIn(cap, shift=UP * 0.12, rate_func=delayed(0.0, 0.22)), run_time=2.9)

        mean_lines = VGroup(*[rect(0.86, 0.075, ARRIVALS).move_to([COL_X[k], py(means[k]), 0]) for k in range(5)])
        mean_labs = VGroup(*[MathTex(f"{means[k]:.1f}", font_size=FS_DAY, color=ARRIVALS).move_to([COL_X[k], py(20.3), 0])
                             for k in range(5)])
        self.play(LaggedStart(*[GrowFromCenter(m) for m in mean_lines], lag_ratio=0.15),
                  LaggedStart(*[FadeIn(m, shift=DOWN * 0.1) for m in mean_labs], lag_ratio=0.15),
                  dashes.animate.set_fill(opacity=0.5), run_time=1.3)
        cap = swap_caption(self, cap, "average each weekday over the last 180 days")
        self.wait(1.7)

        # ==================================================================
        # 5. make room for the next 15 days, then the rule
        # ==================================================================
        dx_today = XB_TODAY - XA_TODAY
        zone_b = rect(XE - XB_TODAY, YT - Y0, ARRIVALS, 0.07).move_to([0.5 * (XB_TODAY + XE), 0.5 * (Y0 + YT), 0])
        x_title_b = Tex(r"forecast day $t$, the next 15 business days", font_size=FS_LABEL, color=MUTED)
        x_title_b.move_to([zone_b.get_center()[0], ROW3, 0])
        f_letters = VGroup(*[Tex(DOW_LETTER[fdow[j]], font_size=FS_DAY, color=INK).move_to([xb_fut(j + 1), ROW1, 0])
                             for j in range(H)])
        f_nums = VGroup(*[MathTex(str(j + 1), font_size=FS_TICK, color=MUTED).move_to([xb_fut(j + 1), ROW2, 0])
                          for j in range(H)])
        self.play(Transform(zone, zone_b), today_line.animate.shift(RIGHT * dx_today),
                  today_lab.animate.shift(RIGHT * dx_today), FadeOut(zone_lab), FadeOut(qmark),
                  run_time=1.6)
        self.play(LaggedStart(*[FadeIn(VGroup(f_letters[j], f_nums[j]), shift=UP * 0.08) for j in range(H)],
                              lag_ratio=0.08), FadeIn(x_title_b), run_time=1.1)

        f1 = MathTex(r"\hat{A}(t)", r"=", r"\text{average of recent days}", font_size=40)
        f1[0].set_color(ARRIVALS)
        f2 = MathTex(r"\text{with the same weekday as }", r"t", font_size=40)
        f2.next_to(f1[2], DOWN, buff=0.16, aligned_edge=LEFT)
        rule = VGroup(f1, f2)
        rule.move_to([0, 2.9, 0]).align_to([XE - 0.05, 0, 0], RIGHT)
        self.play(FadeIn(f1[0], shift=DOWN * 0.1), FadeOut(cap, shift=UP * 0.12), run_time=0.8)
        self.play(Write(f1[1:]), run_time=1.0)
        self.play(Write(f2), run_time=1.0)
        card = definition_card("Seasonal naive", ["a deliberately simple baseline:", "repeat the weekly pattern"], ARRIVALS)
        card.move_to([zone_b.get_center()[0], 0.25, 0])
        self.play(FadeIn(card, shift=UP * 0.15), run_time=0.9)
        self.wait(4.0)

        # ==================================================================
        # 6. payoff: copies of the five means tile the next 15 days
        # ==================================================================
        cap = caption("each future day gets its weekday's average")
        self.play(FadeOut(card, shift=DOWN * 0.15), FadeIn(cap, shift=UP * 0.12), run_time=0.8)
        self.wait(0.7)
        f_caps = [rect(0.8 * SB, 0.075, ARRIVALS).move_to([xb_fut(j + 1), py(fc[j]), 0]) for j in range(H)]
        f_bars = VGroup(*[rect(0.8 * SB, fc[j] * U, ARRIVALS, 0.92).move_to([xb_fut(j + 1), Y0, 0], aligned_edge=DOWN)
                          for j in range(H)])
        order = []
        for k in fdow:
            if k not in order:
                order.append(k)
        tiles = [AnimationGroup(*[TransformFromCopy(mean_lines[k], f_caps[j], path_arc=0.5)
                                  for j in range(H) if fdow[j] == k]) for k in order]
        self.play(LaggedStart(*tiles, lag_ratio=0.3), run_time=3.0)
        self.play(*[ReplacementTransform(f_caps[j], f_bars[j]) for j in range(H)], run_time=1.1)
        self.wait(2.5)

        # ==================================================================
        # 7. what really arrived: context, not a verdict
        # ==================================================================
        sw1 = Square(0.22, fill_color=ARRIVALS, fill_opacity=0.92, stroke_width=0)
        lab1 = Tex(r"$\hat{A}(t)$", r" forecast of new deals", font_size=FS_LABEL)
        lab1[0].set_color(ARRIVALS)
        leg1 = VGroup(sw1, lab1).arrange(RIGHT, buff=0.18)
        sw2 = Dot(radius=0.075, color=INK)
        lab2 = Tex("what actually arrived", font_size=FS_LABEL, color=INK)
        leg2 = VGroup(sw2, lab2).arrange(RIGHT, buff=0.18)
        legend = VGroup(leg1, leg2).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        sw2.match_x(sw1)
        legend.move_to([0, 2.85, 0]).align_to([XE - 0.05, 0, 0], RIGHT)

        dots = VGroup(*[Dot([xb_fut(t), py(actual[t - 1]), 0], radius=0.075, color=INK) for t in range(1, H + 1)])
        self.play(ReplacementTransform(f1[0], lab1[0]), FadeOut(f1[1:], rate_func=delayed(0, 0.5)),
                  FadeOut(f2, rate_func=delayed(0, 0.5)),
                  FadeIn(sw1, rate_func=delayed(0.45, 0.55)), FadeIn(lab1[1], rate_func=delayed(0.45, 0.55)),
                  dashes.animate.set_fill(opacity=0.22), mean_lines.animate.set_fill(opacity=0.4),
                  mean_labs.animate.set_opacity(0.4), col_labs.animate.set_opacity(0.45), run_time=1.1)
        self.play(LaggedStart(*[GrowFromCenter(d) for d in dots], lag_ratio=0.08), FadeIn(leg2, shift=LEFT * 0.1),
                  run_time=1.4)
        cap = swap_caption(self, cap, "a forecast of how many, not which ones")
        self.wait(3.0)
        self.play(FadeOut(dots), FadeOut(leg2), run_time=0.8)
        self.wait(1.0)

        takeaway(self, "a forecast of how many new deals arrive each day", ARRIVALS, old_caption=cap)
        close_chapter(self)
