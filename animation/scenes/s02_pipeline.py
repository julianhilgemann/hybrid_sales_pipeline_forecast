"""Chapter 02 - The pipeline today.

Many real deals over the last 60 business days (a Gantt chart drawn by a clock
sweeping up to today) -> today splits the known past from the unknown future ->
the deals open today, each with its own age -> they fly into the open pipeline
by age N(a) (the sample, then all 229 deals) -> new deals keep arriving after
today -> the forecast question W_hat(d) = W_stock(d) + W_arr(d) -> the plan of
the film.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import *

D = load_data()
H = int(D.meta.horizon)            # 15 forecast days
A_MAX = int(D.meta.max_age)        # 45 = pooled 45+ bucket
N = D.stock.N.astype(int)          # open pipeline by age (index 45 pools 45+)
N_TOTAL = int(D.stock.total_active)

# ---------------------------------------------------------------- geometry
BASE_Y = -2.05                     # shared baseline: Gantt axis, N(a) histogram, arrivals
DAY0, DAY1 = -59.5, 15.5           # Gantt time range (business days relative to today)
GX0, GX1 = -6.4, 6.55
UDAY = (GX1 - GX0) / (DAY1 - DAY0)
X_TODAY = GX0 + (0 - DAY0) * UDAY
ROW_TOP, ROW_BOT = 2.72, -1.80     # Gantt rows
TOP_Y = 3.14                       # top of the today line / future shading

HX0, HX1 = -5.9, 3.15              # N(a) histogram: x extent of the 46 age bins
BW = (HX1 - HX0) / (A_MAX + 1)
UN = 0.172                         # scene units per open deal
Y_CLIP = 16                        # y-axis top (the 45+ bar is clipped here)

ARR_DY, ARR_R = 0.125, 0.045       # arrivals: dot spacing / radius

TRAIL_OPEN = ManimColor(shade(LAVENDER, 0.62))
TRAIL_DONE = ManimColor("#384150")
SQUARE_C = ManimColor("#F59AAE")   # sample squares: a lighter rose than the bars
SEED, N_SAMPLE = 2, 64
A_EX = 8                           # the example age (chapter 06 uses the same bucket)


def gx(day):
    return GX0 + (day - DAY0) * UDAY


def hx(a):
    return HX0 + (a + 0.5) * BW


def hy(n):
    return BASE_Y + n * UN


def lab(tex, fs=FS_TICK, color=MUTED):
    return MathTex(tex, font_size=fs, color=color)


def sample_deals():
    """64 real deals created on or before today (fixed seed), in creation order.
    Deals decided exactly on the as-of day are left out so every dot on the
    today line is an open deal."""
    pool = [l for l in D.lifelines if l["created_rel"] <= 0 and l["closed_rel"] != 0]
    rng = np.random.default_rng(SEED)
    idx = rng.choice(len(pool), size=N_SAMPLE, replace=False)
    deals = []
    for i in idx:
        l = pool[i]
        closed = l["closed_rel"] is not None and l["closed_rel"] < 0
        deals.append(dict(s=int(l["created_rel"]), e=int(l["closed_rel"]) if closed else 0,
                          state=l["outcome"] if closed else "open"))
    deals.sort(key=lambda d: (d["s"], d["e"]))
    return deals


def hatched_bar(x0, x1, y0, y1, color, step=0.11):
    """The pooled 45+ bar: outline, faint fill and diagonal hatching."""
    rect = Rectangle(width=x1 - x0, height=y1 - y0, stroke_color=color, stroke_width=1.6,
                     fill_color=color, fill_opacity=0.28)
    rect.move_to([(x0 + x1) / 2, (y0 + y1) / 2, 0])
    w = x1 - x0
    hatch = VGroup()
    c = y0 - w
    while c < y1:
        sx, sy = x0, c
        ex, ey = x1, c + w
        if sy < y0:
            sx, sy = x0 + (y0 - sy), y0
        if ey > y1:
            ex, ey = x1 - (ey - y1), y1
        if ex - sx > 0.02:
            hatch.add(Line([sx, sy, 0], [ex, ey, 0], color=color, stroke_width=1.6))
        c += step
    return VGroup(rect, hatch)


class Clip(Scene):
    def relayout_caption(self, old, text, anims, run_time=1.2):
        """swap_caption with a re-layout: the old caption leaves during the first
        part of the move, the new one arrives after it (never superimposed)."""
        self.play(*anims, FadeOut(old, shift=UP * 0.12, rate_func=delayed(0, 0.4 / run_time)),
                  run_time=run_time)
        new = caption(text)
        self.play(FadeIn(new, shift=UP * 0.12), run_time=0.6)
        return new

    def construct(self):
        deals = sample_deals()
        n = len(deals)
        dy = (ROW_TOP - ROW_BOT) / (n - 1)
        for i, d in enumerate(deals):
            d["y"] = ROW_TOP - i * dy
            d["trail"] = VMobject(stroke_color=TRAIL_OPEN, stroke_width=2.4, stroke_opacity=0)
            d["trail"].set_points_as_corners([[gx(d["s"]), d["y"], 0], [gx(d["s"]) + 1e-3, d["y"], 0]])
            d["dot"] = Dot([gx(d["s"]), d["y"], 0], radius=0.036, color=LAVENDER, fill_opacity=0)
            d["out_c"] = ManimColor(WON if d["state"] == "won" else LOST)
        open_deals = [d for d in deals if d["state"] == "open"]
        closed_deals = [d for d in deals if d["state"] != "open"]
        ex = [d for d in open_deals if d["s"] == -A_EX][0]

        # =====================================================================
        # 1. open
        # =====================================================================
        open_chapter(self, 2, "The pipeline today", STOCK,
                     question="Which deals are open right now, and which are still to come?",
                     part=PART[1])

        # =====================================================================
        # 2. many deals over time: a clock sweeps the last 60 business days
        # =====================================================================
        g_axis = Line([GX0, BASE_Y, 0], [X_TODAY, BASE_Y, 0], color=MUTED, stroke_width=2)
        g_ticks = VGroup()
        for v in (50, 40, 30, 20, 10, 0):
            mark = Line([gx(-v), BASE_Y, 0], [gx(-v), BASE_Y - 0.07, 0], color=MUTED, stroke_width=2)
            g_ticks.add(VGroup(mark, lab(f"{v}").next_to([gx(-v), BASE_Y, 0], DOWN, buff=0.14)))
        g_title = Tex("business days before today", font_size=FS_LABEL, color=MUTED)
        g_title.move_to([(GX0 + X_TODAY) / 2, BASE_Y - 0.66, 0])

        trails = VGroup(*[d["trail"] for d in deals])
        dots = VGroup(*[d["dot"] for d in deals])
        self.add(trails, dots)

        clock = ValueTracker(DAY0)
        cursor = Line([gx(DAY0), BASE_Y, 0], [gx(DAY0), ROW_TOP + 0.16, 0], color=MUTED,
                      stroke_width=1.6, stroke_opacity=0.6)

        def apply_clock(t):
            for d in deals:
                s, e, y = d["s"], d["e"], d["y"]
                a_in = float(np.clip((t - s) / 2.5, 0, 1))
                head = float(np.clip(t, s, e))
                p0 = np.array([gx(s), y, 0.0])
                p1 = np.array([gx(head) + 1e-3, y, 0.0])
                d["trail"].set_points_as_corners([p0, p1])
                f = float(np.clip((t - e) / 2.0, 0, 1)) if d["state"] != "open" else 0.0
                d["trail"].set_stroke(interpolate_color(TRAIL_OPEN, TRAIL_DONE, f), opacity=a_in)
                d["dot"].move_to(p1)
                d["dot"].set_fill(interpolate_color(ManimColor(LAVENDER), d["out_c"], f), opacity=a_in)

        def tick_clock(m):
            t = clock.get_value()
            apply_clock(t)
            cursor.put_start_and_end_on([gx(t), BASE_Y, 0], [gx(t), ROW_TOP + 0.16, 0])

        # the dot motif from chapter 01, re-established in the empty corner of the chart
        leg_won, leg_lost, leg_open = (legend_item("won", WON), legend_item("lost", LOST),
                                       legend_item("still open", OPEN))
        legend = VGroup(leg_won, leg_lost, leg_open).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        legend.move_to([0, -0.95, 0]).align_to([-5.95, 0, 0], LEFT)
        cap = caption("deals are created, worked on, then decided")
        self.play(Create(g_axis), FadeIn(g_ticks), FadeIn(g_title), FadeIn(cursor), FadeIn(legend),
                  FadeIn(cap, shift=UP * 0.12), run_time=1.0)
        self.wait(0.7)
        trails.add_updater(tick_clock)
        self.play(clock.animate.set_value(0), run_time=6.6, rate_func=linear)
        trails.remove_updater(tick_clock)
        apply_clock(0)
        self.wait(1.0)

        # =====================================================================
        # 3. today splits the known past from the unknown future
        # =====================================================================
        today = Line([X_TODAY, BASE_Y, 0], [X_TODAY, TOP_Y, 0], color=INK, stroke_width=2.6)
        today_lab = Tex("today: 1 May 2025", font_size=FS_BODY, color=INK).next_to(today, UP, buff=0.1)
        fut_shade = Rectangle(width=GX1 + 0.12 - X_TODAY, height=TOP_Y - BASE_Y, stroke_width=0,
                              fill_color=INK, fill_opacity=0.05)
        fut_shade.move_to([(X_TODAY + GX1 + 0.12) / 2, (TOP_Y + BASE_Y) / 2, 0])
        fut_shade.set_z_index(-2)
        fut_axis = Line([X_TODAY, BASE_Y, 0], [GX1, BASE_Y, 0], color=MUTED, stroke_width=2)
        past_lab = Tex("known past", font_size=FS_LABEL, color=MUTED)
        past_lab.next_to([X_TODAY, ROW_TOP + 0.26, 0], LEFT, buff=0.18)
        fut_lab = Tex("unknown future", font_size=FS_LABEL, color=MUTED)
        fut_lab.next_to([X_TODAY, ROW_TOP + 0.26, 0], RIGHT, buff=0.18)

        self.play(ReplacementTransform(cursor, today), FadeIn(today_lab, shift=DOWN * 0.1),
                  FadeIn(fut_shade), Create(fut_axis), FadeIn(past_lab, shift=LEFT * 0.1),
                  FadeIn(fut_lab, shift=RIGHT * 0.1), run_time=1.2)
        cap = swap_caption(self, cap, "today splits what we know from what we don't")
        self.wait(1.8)

        # =====================================================================
        # 4. open today, each with its own age
        # =====================================================================
        closed_g = VGroup(*[m for d in closed_deals for m in (d["trail"], d["dot"])])
        o_trails = VGroup(*[d["trail"] for d in open_deals])
        open_today_lab = Tex("open today", font_size=FS_LABEL, color=INK).move_to(leg_open[1], aligned_edge=LEFT)
        self.play(closed_g.animate.set_opacity(0.22), VGroup(leg_won, leg_lost).animate.set_opacity(0.3),
                  leg_open[0].animate.set_color(STOCK), ReplacementTransform(leg_open[1], open_today_lab),
                  o_trails.animate.set_stroke(STOCK, width=2.6, opacity=1),
                  *[d["dot"].animate.set_fill(STOCK, opacity=1).scale(1.25) for d in open_deals],
                  run_time=1.3)
        cap = swap_caption(self, cap, "open today, each with its own age")
        self.wait(1.5)

        others = VGroup(*[d["trail"] for d in open_deals if d is not ex])
        brace = BraceBetweenPoints([gx(-A_EX), ex["y"] + 0.05, 0], [X_TODAY, ex["y"] + 0.05, 0],
                                   direction=UP, buff=0.02, color=INK)
        age_lab = Tex(f"age {A_EX}", font_size=FS_LABEL, color=INK).next_to(brace, UP, buff=0.06)
        age_bg = BackgroundRectangle(age_lab, color=BG, fill_opacity=0.85, buff=0.05)
        self.play(others.animate.set_stroke(opacity=0.4), ex["trail"].animate.set_stroke(width=4),
                  FadeIn(age_bg), GrowFromCenter(brace), FadeIn(age_lab, shift=UP * 0.08), run_time=1.0)
        self.wait(1.6)

        # =====================================================================
        # 5. payoff: the open pipeline by age, N(a)
        # =====================================================================
        h_axis = Line([HX0, BASE_Y, 0], [HX1 + 0.05, BASE_Y, 0], color=MUTED, stroke_width=2)
        y_axis = Line([HX0, BASE_Y, 0], [HX0, hy(Y_CLIP), 0], color=MUTED, stroke_width=2)
        y_ticks = VGroup(*[lab(f"{v}").next_to([HX0, hy(v), 0], LEFT, buff=0.14) for v in (0, 5, 10, 15)])
        a_ticks = VGroup()
        for v in (0, 10, 20, 30, 40):
            mark = Line([hx(v), BASE_Y, 0], [hx(v), BASE_Y - 0.07, 0], color=MUTED, stroke_width=2)
            a_ticks.add(VGroup(mark, lab(f"{v}").next_to([hx(v), BASE_Y, 0], DOWN, buff=0.14)))
        a_ticks.add(lab(r"45{+}").next_to([hx(A_MAX), BASE_Y, 0], DOWN, buff=0.14))
        a_title = Tex("age today (business days)", font_size=FS_LABEL, color=MUTED)
        a_title.move_to([(HX0 + HX1) / 2, BASE_Y - 0.66, 0])
        y_title = Tex("open deals", font_size=FS_LABEL, color=MUTED)
        y_title.next_to([HX0, hy(Y_CLIP), 0], UP, buff=0.16).align_to([HX0 - 0.3, 0, 0], LEFT)

        # the decided deals leave; the open lines step back; the time axis becomes an age axis
        self.play(FadeOut(closed_g), FadeOut(VGroup(age_bg, brace, age_lab)), FadeOut(past_lab),
                  FadeOut(VGroup(leg_won, leg_lost, leg_open[0], open_today_lab)),
                  others.animate.set_stroke(opacity=0.35), ex["trail"].animate.set_stroke(width=2.6, opacity=0.35),
                  run_time=0.9)
        self.play(ReplacementTransform(g_axis, h_axis), FadeOut(g_ticks), FadeIn(a_ticks),
                  FadeTransform(g_title, a_title), Create(y_axis), FadeIn(y_ticks),
                  FadeIn(y_title), run_time=1.2)
        cap = swap_caption(self, cap, "count today's open deals by age")
        self.wait(0.9)

        # the rose dots leave the today line and stack as unit squares by age
        stack = {}
        flights = []
        for d in sorted(open_deals, key=lambda d: -d["s"]):
            a = min(-d["s"], A_MAX)
            k = stack.get(a, 0)
            stack[a] = k + 1
            sq = Rectangle(width=BW * 0.8, height=UN * 0.84, stroke_width=0, fill_color=SQUARE_C, fill_opacity=1)
            sq.move_to([hx(a), hy(k + 0.5), 0])
            flights.append(AnimationGroup(Transform(d["dot"], sq, path_arc=-0.6),
                                          FadeOut(d["trail"], run_time=0.6)))
        note = Tex(f"our sample: {len(open_deals)} open deals", font_size=FS_BODY, color=SQUARE_C)
        note.move_to([0.75, -0.05, 0])
        self.play(LaggedStart(*flights, lag_ratio=0.12),
                  FadeIn(note, shift=UP * 0.1, rate_func=delayed(0.72, 0.28)), run_time=3.2)
        squares = VGroup(*[d["dot"] for d in sorted(open_deals, key=lambda d: -d["s"])])
        squares.set_z_index(2)
        self.wait(1.1)

        # complete to the real N(a): all 229 open deals
        n_bars = VGroup()
        for a in range(A_MAX):
            r = Rectangle(width=BW * 0.8, height=max(N[a] * UN, 1e-3), stroke_width=0,
                          fill_color=STOCK, fill_opacity=0.9)
            r.move_to([hx(a), BASE_Y, 0], aligned_edge=DOWN)
            n_bars.add(r)
        pooled = hatched_bar(hx(A_MAX) - BW * 0.4, hx(A_MAX) + BW * 0.4, BASE_Y, hy(Y_CLIP), STOCK)
        brk = VGroup(*[Line(LEFT * 0.13 + DOWN * 0.04, RIGHT * 0.13 + UP * 0.04, color=BG, stroke_width=4)
                       .move_to([hx(A_MAX), hy(Y_CLIP - 1.6 - 0.9 * i), 0]) for i in range(2)])
        pooled_n = lab(f"{N[A_MAX]}", FS_LABEL, STOCK).next_to(pooled, UP, buff=0.1)
        note2 = Tex(f"all open deals: {N_TOTAL}", font_size=FS_BODY, color=STOCK).move_to(note)
        note_old = Tex(f"{N[A_MAX]} of them aged 45 or more", font_size=FS_LABEL, color=MUTED)
        note_old.next_to(note2, DOWN, buff=0.14)
        sq_young = VGroup(*[d["dot"] for d in open_deals if -d["s"] < A_MAX])
        sq_old = VGroup(*[d["dot"] for d in open_deals if -d["s"] >= A_MAX])
        self.play(LaggedStart(*[GrowFromEdge(b, DOWN) for b in n_bars], GrowFromEdge(pooled, DOWN),
                              lag_ratio=0.03),
                  sq_young.animate.set_fill(STOCK, opacity=0.9), sq_old.animate.set_fill(opacity=0),
                  FadeTransform(note, note2),
                  FadeIn(brk, rate_func=delayed(0.75, 0.25)),
                  FadeIn(pooled_n, shift=UP * 0.1, rate_func=delayed(0.75, 0.25)),
                  FadeIn(note_old, shift=UP * 0.1, rate_func=delayed(0.75, 0.25)), run_time=2.6)
        dots.remove(*squares)
        self.remove(*squares)
        self.wait(0.3)

        # name it: N(a)
        sym = MathTex(r"N(a)", font_size=FS_FORMULA, color=STOCK)
        words = Tex(r"open deals", r" aged $a$ today", font_size=FS_BODY, color=INK)
        name = VGroup(sym, words).arrange(RIGHT, buff=0.3)
        name.next_to([HX0, hy(Y_CLIP), 0], UP, buff=0.32).align_to([HX0 - 0.3, 0, 0], LEFT)
        ex_lab = callout(rf"{N[A_EX]} deals aged {A_EX}", n_bars[A_EX].get_top() + UP * 0.04,
                         RIGHT + UP * 0.45, INK, length=0.6, font_size=FS_LABEL)
        self.play(ReplacementTransform(y_title, words[0], rate_func=delayed(0, 0.5)),
                  FadeIn(words[1], rate_func=delayed(0.3, 0.4)),
                  Write(sym, rate_func=delayed(0.5, 0.5)), FadeIn(ex_lab, rate_func=delayed(0.55, 0.45)),
                  run_time=1.8)
        self.wait(2.5)

        # =====================================================================
        # 6. new deals keep arriving
        # =====================================================================
        f_ticks = VGroup()
        for v in (1, 5, 10, 15):
            mark = Line([gx(v), BASE_Y, 0], [gx(v), BASE_Y - 0.07, 0], color=MUTED, stroke_width=2)
            f_ticks.add(VGroup(mark, lab(f"{v}").next_to([gx(v), BASE_Y, 0], DOWN, buff=0.14)))
        f_title = Tex("business days after today", font_size=FS_LABEL, color=MUTED)
        f_title.move_to([5.05, BASE_Y - 0.66, 0])
        future = [l for l in D.lifelines if 1 <= l["created_rel"] <= H]
        per_day = [sum(1 for l in future if l["created_rel"] == t) for t in range(1, H + 1)]
        cols = VGroup()
        for t, c in zip(range(1, H + 1), per_day):
            cols.add(VGroup(*[Dot([gx(t), BASE_Y + 0.1 + k * ARR_DY, 0], radius=ARR_R, color=ARRIVALS)
                              for k in range(c)]))
        arr_lab = Tex("new deals per day", font_size=FS_LABEL, color=ARRIVALS)
        arr_lab.move_to([(X_TODAY + GX1) / 2 + 0.05, BASE_Y + 0.1 + max(per_day) * ARR_DY + 0.22, 0])
        cap = swap_caption(self, cap, "and new deals keep arriving")
        self.wait(0.9)
        self.play(FadeIn(f_ticks, rate_func=delayed(0, 0.25)), FadeIn(f_title, rate_func=delayed(0, 0.25)),
                  FadeIn(arr_lab, rate_func=delayed(0, 0.25)),
                  LaggedStart(*[LaggedStart(*[FadeIn(dt, scale=0.4) for dt in col], lag_ratio=0.08)
                                for col in cols], lag_ratio=0.22), run_time=3.2)
        self.wait(1.2)

        # =====================================================================
        # 7. the question: W_hat(d) and its two sources
        # =====================================================================
        line_top = 0.86
        cap = self.relayout_caption(cap, "what will the next 15 days bring", [
            FadeOut(ex_lab), FadeOut(note2), FadeOut(note_old), FadeOut(fut_lab), FadeOut(today_lab),
            today.animate.put_start_and_end_on([X_TODAY, BASE_Y, 0], [X_TODAY, line_top, 0]),
            fut_shade.animate.stretch_to_fit_height(line_top - BASE_Y).move_to(
                [fut_shade.get_x(), (line_top + BASE_Y) / 2, 0])])

        F = MathTex(r"\hat{W}(d)", "=", r"W_{\text{stock}}(d)", "+", r"W_{\text{arr}}(d)", font_size=FS_FORMULA)
        F[0].set_color(TOTAL)
        F[2].set_color(STOCK)
        F[4].set_color(ARRIVALS)
        F.move_to([2.4, 2.74, 0])
        Q = MathTex(r"\hat{W}(d)", "=", "?", font_size=FS_FORMULA)
        Q[0].set_color(TOTAL)
        Q[0].move_to(F[0])
        Q[1].move_to(F[1])
        Q[2].next_to(Q[1], RIGHT, buff=0.3)

        def brace_label(term, lines, color):
            b = Brace(term, DOWN, buff=0.1, color=color)
            t = VGroup(*[Tex(s, font_size=FS_LABEL, color=color) for s in lines]).arrange(DOWN, buff=0.1)
            t.next_to(b, DOWN, buff=0.1)
            return VGroup(b, t)

        bW = brace_label(F[0], ["expected wins on", r"forecast day $d$"], TOTAL)
        d_range = MathTex(r"d = 1, \dots, 15", font_size=FS_LABEL, color=MUTED).next_to(bW, DOWN, buff=0.1)
        bW[1].add(d_range)
        bS = brace_label(F[2], ["from today's", "open deals"], STOCK)
        bA = brace_label(F[4], ["from deals", "not yet created"], ARRIVALS)

        self.wait(0.9)
        self.play(Write(Q), run_time=1.0)
        self.play(GrowFromCenter(bW[0]), FadeIn(bW[1], shift=DOWN * 0.08), run_time=1.0)
        self.wait(1.5)
        self.play(FadeOut(Q[2], shift=UP * 0.15, rate_func=delayed(0, 0.4)), Write(F[2], rate_func=delayed(0.1, 0.6)),
                  GrowFromCenter(bS[0], rate_func=delayed(0.55, 0.45)),
                  FadeIn(bS[1], shift=DOWN * 0.08, rate_func=delayed(0.6, 0.4)), run_time=1.6)
        self.wait(0.3)
        self.play(Write(F[3], rate_func=delayed(0, 0.4)), Write(F[4], rate_func=delayed(0.1, 0.6)),
                  GrowFromCenter(bA[0], rate_func=delayed(0.55, 0.45)),
                  FadeIn(bA[1], shift=DOWN * 0.08, rate_func=delayed(0.6, 0.4)), run_time=1.6)
        self.remove(Q[0], Q[1])
        self.add(F[0], F[1])
        self.wait(4.0)

        # =====================================================================
        # 8. the plan
        # =====================================================================
        panels = VGroup(h_axis, y_axis, y_ticks, a_ticks, a_title, n_bars, pooled, brk, pooled_n, name,
                        f_ticks, f_title, arr_lab, cols, fut_axis, fut_shade, today)
        F_target = F.copy().move_to([0, 2.3, 0])
        shift = F_target.get_center() - F.get_center()
        cap = self.relayout_caption(cap, "the plan", [FadeOut(panels), Transform(F, F_target),
                                                      FadeOut(VGroup(bW, bS, bA), shift=shift)], run_time=1.3)

        def plan_row(text, ref, colors):
            if len(colors) == 1:
                mark = Dot(radius=0.1, color=colors[0])
            else:
                mark = VGroup(Dot(radius=0.1, color=colors[0]), Dot(radius=0.1, color=colors[1])).arrange(RIGHT, buff=0.06)
            t = Tex(text, font_size=FS_BODY + 4, color=colors[-1])
            r = Tex(ref, font_size=FS_BODY, color=MUTED)
            return VGroup(mark, t, r)

        rows = [plan_row("How long deals take to decide", r"ch.~03--05", [LAVENDER, AMBER]),
                plan_row("Deals already open", r"ch.~06--07", [STOCK]),
                plan_row("Deals not yet created", r"ch.~08--09", [ARRIVALS]),
                plan_row("Putting it together", r"ch.~10--11", [TOTAL])]
        mark_x, text_x, ref_x = -4.2, -3.45, 3.0
        for i, (mk, t, r) in enumerate(rows):
            y = 1.05 - i * 0.86
            mk.move_to([mark_x, y, 0])
            t.move_to([text_x, y, 0], aligned_edge=LEFT)
            r.move_to([ref_x, y, 0], aligned_edge=LEFT)
            r.align_to(t, UP)
        plan = VGroup(*[VGroup(*row) for row in rows])
        plan.move_to([0, plan.get_y(), 0])
        self.wait(0.6)
        for row in plan:
            self.play(FadeIn(row, shift=RIGHT * 0.15), run_time=0.7)
            self.wait(0.3)
        self.wait(3.0)

        # =====================================================================
        # 9. takeaway
        # =====================================================================
        takeaway(self, "future wins come from open deals and new deals", STOCK, old_caption=cap)
        close_chapter(self)
