"""Chapter 06 - Already open.

The conditional-probability tangent. Today's 14 open deals aged 8 are not brand
new: they survived to age 8. Their chance to win on forecast day d is therefore
k(8+d) / S(8), the kernel restricted to the survivors and stretched by 1/S(8).
Over 15 days that is 0.25 per deal, 3.5 expected wins for the 14.

Beats: the 14 deals -> the tempting answer k(8+d) -> the cohort shrinks to its
61 survivors (16 of them win) -> the formula -> renormalise on the chart ->
sum 0.25 -> times 14 = E_stock(8, d) -> takeaway.

Layout: two "pages" side by side. The chart page (age axis, later day axis)
pans out to the left while the cohort page pans in, and back again.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import *

D = load_data()
A0 = int(D.conditional.a0)              # 8
H = int(D.meta.horizon)                 # 15
AMAX = int(D.meta.max_age)              # 45 = pooled 45+ bucket
N = D.stock.N.astype(int)
K = D.kernel.win_mass                   # raw kernel k(a): what the model uses
S8 = float(D.conditional.S_a0)          # 0.613
COND = D.conditional.cond_prob          # k(8+d)/S(8), d = 1..15
ROW = D.conditional.row                 # N(8) k(8+d)/S(8)
N8 = int(round(D.conditional.N_a0))     # 14
COND_TOT = float(D.conditional.cond_total)   # 0.251
ROW_TOT = float(D.conditional.row_total)     # 3.52

# ---- one chart frame: an age axis that later becomes a day axis -------------
X0, X1 = -5.45, 5.95
WID = X1 - X0
UA = WID / (AMAX + 1)         # one age bin
UD = WID / H                  # one forecast day
Y0 = -1.62                    # baseline
UK = 87.5                     # scene units per unit of probability
K_TOP0, K_TOP1 = 0.035, 0.04  # the k axis before / after the stretch
N_TOP = 16                    # open-deal axis (the 45+ bar is clipped here)
UN = K_TOP0 * UK / N_TOP      # scene units per open deal
E_TOP = 0.6
UE = K_TOP1 * UK / E_TOP      # scene units per expected win
PAN = 14.6                    # width of a "page" for the pans
BWA, BWD = 0.78 * UA, 0.62 * UD   # bar widths on the age / day axis
GLOW = ManimColor("#FFD27A")      # amber highlight

# ---- cohort page ---------------------------------------------------------------
CO_SP = 0.34
CO_C = np.array([-3.55, 0.3, 0.0])   # cohort centre (left half: the formula takes the right)
F_X = 0.0                            # left edge of the formula on the cohort page
REF_R = 6.45                         # right edge of the formula block on the chart page
REF_Y = 1.72


def ax(a):
    return X0 + (a + 0.5) * UA


def dx(d):
    return X0 + (d - 0.5) * UD


def rect_bar(x, h, w, color, op=0.92, bottom=0.0):
    r = Rectangle(width=w, height=max(h, 1e-3), stroke_width=0, fill_color=color, fill_opacity=op)
    r.move_to([x, Y0 + bottom, 0], aligned_edge=DOWN)
    return r


def words(*parts, colors=(), fs=FS_LABEL):
    """One line of text; part i coloured colors[i] (no xcolor in the template)."""
    t = Tex(*parts, font_size=fs, color=INK)
    for i, c in enumerate(colors):
        if c is not None:
            t[i].set_color(c)
    return t


def xtick(x, s, color=MUTED, fs=FS_TICK):
    mark = Line([x, Y0, 0], [x, Y0 - 0.07, 0], color=MUTED, stroke_width=2)
    lab = MathTex(s, font_size=fs, color=color).next_to([x, Y0 - 0.07, 0], DOWN, buff=0.1)
    return VGroup(mark, lab)


def ytick(v, unit, s):
    y = Y0 + v * unit
    mark = Line([X0, y, 0], [X0 - 0.07, y, 0], color=MUTED, stroke_width=2)
    lab = MathTex(s, font_size=FS_TICK, color=MUTED).next_to([X0 - 0.07, y, 0], LEFT, buff=0.1)
    return VGroup(mark, lab)


def y_title(mob, top):
    """Axis title in the top-left corner of the plot, above the y-axis."""
    mob.next_to([X0, top, 0], UP, buff=0.3)
    mob.align_to([X0 - 0.55, 0, 0], LEFT)
    return mob


def hatched_bar(x0, x1, y0, y1, color, step=0.11):
    """The pooled 45+ bar, drawn as in chapter 02: outline, faint fill, hatching."""
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


def cap_anims(old, text):
    """Caption swap that rides inside a longer animation (a pan or a slide):
    the old line leaves in the first 30%, the new one arrives at 40-75%, so the
    two never overlap. Returns (new caption, animations)."""
    new = caption(text)
    anims = [FadeIn(new, shift=UP * 0.12, rate_func=delayed(0.4, 0.35))]
    if old is not None:
        anims.insert(0, FadeOut(old, shift=UP * 0.12, rate_func=delayed(0.0, 0.3)))
    return new, anims


def swap_text(old, new, run_time_split=0.45):
    """Old label out, then new label in, inside one play (no superimposed text)."""
    return [FadeOut(old, rate_func=delayed(0.0, run_time_split)),
            FadeIn(new, rate_func=delayed(1 - run_time_split, run_time_split))]


class Clip(Scene):
    def construct(self):
        # =====================================================================
        # 1. open
        # =====================================================================
        open_chapter(self, 6, "Already open", STOCK,
                     question="A deal is 8 days old and still open. What are its chances now?",
                     part=PART[3])

        # =====================================================================
        # 2. the 14 deals
        # =====================================================================
        x_axis = Line([X0, Y0, 0], [X1, Y0, 0], color=MUTED, stroke_width=2)
        y_axis = Line([X0, Y0, 0], [X0, Y0 + K_TOP0 * UK, 0], color=MUTED, stroke_width=2)
        age_ticks = VGroup(*[xtick(ax(a), s) for a, s in
                             ((0, "0"), (10, "10"), (20, "20"), (30, "30"), (40, "40"), (AMAX, "45{+}"))])
        x_title = Tex("age (business days)", font_size=FS_LABEL, color=MUTED).move_to([X0 + WID / 2, Y0 - 0.74, 0])
        n_ticks = VGroup(*[ytick(v, UN, f"{v}") for v in (0, 5, 10, 15)])
        n_title = y_title(words(r"$N(a)$", r": deals open today, at each age", colors=(STOCK,)), Y0 + K_TOP0 * UK)

        n_bars = VGroup(*[rect_bar(ax(a), N[a] * UN, BWA, STOCK) for a in range(AMAX)])
        pooled = hatched_bar(ax(AMAX) - BWA / 2, ax(AMAX) + BWA / 2, Y0, Y0 + N_TOP * UN, STOCK, step=0.09)
        pooled_n = MathTex(f"{N[AMAX]}", font_size=FS_TICK, color=STOCK).next_to(pooled, UP, buff=0.08)

        self.play(Create(x_axis), Create(y_axis), FadeIn(age_ticks), FadeIn(n_ticks), FadeIn(x_title),
                  run_time=1.0)
        self.play(LaggedStart(*[GrowFromEdge(b, DOWN) for b in n_bars], GrowFromEdge(pooled, DOWN),
                              lag_ratio=0.03),
                  FadeIn(n_title, shift=UP * 0.1), FadeIn(pooled_n, rate_func=delayed(0.6, 0.4)), run_time=1.5)

        bar8 = n_bars[A0]
        others = VGroup(*[b for i, b in enumerate(n_bars) if i != A0])
        tick8 = xtick(ax(A0), "8", STOCK)
        lab14 = words(r"\textbf{14}", r" deals aged 8", colors=(STOCK,)).next_to(bar8, UP, buff=0.16)
        cap, c_anims = cap_anims(None, "take the 14 open deals aged 8")
        self.play(others.animate.set_fill(opacity=0.25), pooled.animate.set_opacity(0.25),
                  pooled_n.animate.set_opacity(0.3), FadeIn(tick8), FadeIn(lab14, shift=UP * 0.1),
                  *c_anims, run_time=1.6)
        self.wait(1.4)

        # the bar is 14 deals: it breaks into 14 dots that fly up to become the badge
        segs = VGroup(*[Rectangle(width=BWA, height=UN, stroke_width=0, fill_color=STOCK, fill_opacity=0.92)
                        .move_to([ax(A0), Y0 + (j + 0.5) * UN, 0]) for j in range(N8)])
        self.remove(bar8)
        self.add(segs)
        badge_lab = words(r"\textbf{14}", r" open deals, aged 8", colors=(STOCK,))
        badge_lab.to_edge(RIGHT, buff=0.42).set_y(3.4)
        bx = badge_lab.get_left()[0] - 0.26
        badge_pts = [np.array([bx - (6 - (j % 7)) * 0.17, 3.4 + (0.085 if j >= 7 else -0.085), 0]) for j in range(N8)]
        badge_dots = segs
        self.play(LaggedStart(*[Transform(sg, Dot(p, radius=0.062, color=STOCK), path_arc=-0.5)
                                for sg, p in zip(segs, badge_pts)], lag_ratio=0.05),
                  FadeOut(lab14, rate_func=delayed(0, 0.3)), FadeIn(badge_lab, rate_func=delayed(0.65, 0.35)),
                  *[b.animate.stretch_to_fit_height(1e-3, about_edge=DOWN) for b in others],
                  pooled.animate.stretch_to_fit_height(1e-3, about_edge=DOWN).set_opacity(0),
                  FadeOut(pooled_n), FadeOut(n_ticks), FadeOut(n_title), run_time=2.0)
        self.remove(others, pooled)

        # =====================================================================
        # 3. the tempting answer: k(8+d)?
        # =====================================================================
        k_bars = VGroup(*[rect_bar(ax(a), K[a] * UK, BWA, KERNEL) for a in range(AMAX + 1)])
        k_ticks = VGroup(*[ytick(v, UK, s) for v, s in ((0, "0"), (0.01, "0.01"), (0.02, "0.02"), (0.03, "0.03"))])
        k_title = y_title(words(r"$k(a)$", r": chance a new deal wins at exactly age $a$", colors=(KERNEL,)),
                          Y0 + K_TOP0 * UK)
        self.play(LaggedStart(*[GrowFromEdge(b, DOWN) for b in k_bars], lag_ratio=0.03),
                  FadeIn(k_ticks), FadeIn(k_title, shift=UP * 0.1), run_time=1.6)
        self.wait(0.4)

        marker = DashedLine([ax(A0), Y0, 0], [ax(A0), Y0 + 2.15, 0], color=STOCK, stroke_width=2.2,
                            dash_length=0.08)
        win_top = Y0 + K[A0 + 1:A0 + H + 1].max() * UK + 0.2
        brace = BraceBetweenPoints([X0 + (A0 + 1) * UA, win_top, 0], [X0 + (A0 + H + 1) * UA, win_top, 0],
                                   direction=UP, color=INK, buff=0.02)
        brace_lab = words(r"next 15 days, $d = 1, \dots, 15$: ", rf"ages {A0 + 1} to {A0 + H}", colors=(None, MUTED))
        brace_lab.next_to(brace, UP, buff=0.12).align_to(brace, LEFT)
        q = MathTex(r"\text{use }", r"k(8{+}d)", r"\,?", font_size=FS_FORMULA - 4, color=INK)
        q[1].set_color(KERNEL)
        q.next_to(brace_lab, RIGHT, buff=0.35)
        win_bars = VGroup(*k_bars[A0 + 1:A0 + H + 1])
        self.play(Create(marker), GrowFromCenter(brace), FadeIn(brace_lab, shift=UP * 0.1), run_time=1.1)
        self.play(FadeIn(q, shift=LEFT * 0.15), Indicate(win_bars, color=GLOW, scale_factor=1.0), run_time=1.1)
        self.wait(1.5)

        cap, c_anims = cap_anims(cap, r"but $k$ also counts deals decided before age 8")
        early = VGroup(*k_bars[:A0 + 1])
        self.play(early.animate(rate_func=delayed(0.35, 0.65)).set_fill(MUTED, opacity=0.35),
                  q.animate(rate_func=delayed(0.35, 0.65)).set_opacity(0.35), *c_anims, run_time=2.0)
        self.wait(1.9)

        # =====================================================================
        # 4. shrink the world to the survivors (the cohort of 100)
        # =====================================================================
        info = {int(d["slot"]): d for d in D.cohort.dots}
        resolved = [s for s in range(100) if info[s]["outcome"] != "open" and info[s]["age"] < A0]
        survivors = [s for s in range(100) if s not in resolved]
        winners = [s for s in survivors if info[s]["outcome"] == "won" and A0 + 1 <= info[s]["age"] <= A0 + H]
        n_open8 = int(D.cohort.open_at_age[A0])
        assert len(survivors) == n_open8 == 61 and len(winners) == 16, (len(survivors), len(winners))

        grid = cohort_grid(spacing=CO_SP).move_to(CO_C)
        box = SurroundingRectangle(grid, buff=0.2, corner_radius=0.1, stroke_width=2, color=MUTED)
        top_lab = words("100 new deals").next_to(box, UP, buff=0.18)

        # the age clock to the right of the cohort
        clock_word = Tex("age", font_size=FS_LABEL, color=MUTED)
        clock_nums = {v: Tex(f"{v}", font_size=FS_FORMULA + 4, color=INK) for v in range(0, A0 + H + 1)}
        clock_word.move_to(box.get_corner(UR) + np.array([0.62, -0.3, 0]))
        for t in clock_nums.values():
            t.next_to(clock_word, DOWN, buff=0.14)
        clock = clock_nums[0].copy()
        legend = VGroup(legend_item("won", WON), legend_item("lost", LOST), legend_item("still open", OPEN))
        legend.arrange(DOWN, aligned_edge=LEFT, buff=0.16)
        legend.next_to(clock_nums[0], DOWN, buff=0.45).align_to(clock_word, LEFT).shift(LEFT * 0.08)
        cohort_page = VGroup(grid, box, top_lab, clock_word, clock, legend)
        cohort_page.shift(RIGHT * PAN)

        chart_page = VGroup(x_axis, y_axis, age_ticks, tick8, x_title, k_ticks, k_title, k_bars)
        cap, c_anims = cap_anims(cap, "condition on what we know: still open at 8")
        pan = rate_functions.ease_in_out_sine
        self.play(chart_page.animate(rate_func=pan).shift(LEFT * PAN),
                  cohort_page.animate(rate_func=pan).shift(LEFT * PAN),
                  FadeOut(VGroup(marker, brace, brace_lab, q), rate_func=delayed(0, 0.3)), *c_anims,
                  run_time=2.4)
        self.wait(0.2)

        # play the cohort forward from age 0 to 8: dots take their outcome colours
        tk = ValueTracker(0.0)

        def resolver(slot):
            age = info[slot]["age"]
            target = ManimColor(WON if info[slot]["outcome"] == "won" else LOST)
            base = ManimColor(OPEN)

            def upd(m):   # take the outcome colour, then dim: decided, no longer our concern
                f = float(np.clip((tk.get_value() - age) / 0.9, 0, 1))
                g = float(np.clip((tk.get_value() - age - 0.9) / 0.7, 0, 1))
                m.set_color(interpolate_color(base, target, f))
                m.set_opacity(1 - 0.72 * smooth(g))
            return upd

        def clock_upd(m, lo=0, hi=A0):
            v = int(np.clip(np.floor(tk.get_value() + 1e-6), lo, hi))
            if getattr(m, "shown", None) != v:
                m.become(clock_nums[v])
                m.shown = v

        for s in resolved:
            grid[s].add_updater(resolver(s))
        clock.add_updater(clock_upd)
        self.play(tk.animate.set_value(A0 + 0.6), run_time=3.4, rate_func=linear)
        for s in resolved:
            grid[s].clear_updaters()
        clock.clear_updaters()
        self.wait(0.7)

        # the world shrinks: the 39 decided dim and leave, the 61 close ranks, the frame follows
        tl = grid[0].get_center()
        pos = [tl + np.array([(i % 10) * CO_SP, -(i // 10) * CO_SP, 0]) for i in range(len(survivors))]
        ghost = VGroup(*[Dot(p, radius=0.09) for p in pos])
        new_box = SurroundingRectangle(ghost, buff=0.2, corner_radius=0.1, stroke_width=2, color=OPEN)
        top61 = words(f"{len(survivors)}", r" still open at age 8: like our ", f"{N8}", colors=(OPEN, None, STOCK))
        top61.next_to(new_box, UP, buff=0.18)
        tally_v = {v: words(r"won in the next 15 days: ", rf"{v}", f" of {len(survivors)}",
                            colors=(None, KERNEL, OPEN)) for v in range(0, len(winners) + 1)}
        for t in tally_v.values():
            t.next_to(new_box, DOWN, buff=0.25)
        tally0 = tally_v[0].copy()
        self.play(LaggedStart(*[grid[s].animate.move_to(p) for s, p in zip(survivors, pos)], lag_ratio=0.012),
                  *[grid[s].animate.set_opacity(0) for s in resolved],
                  Transform(box, new_box, rate_func=delayed(0.4, 0.6)),
                  FadeOut(top_lab, rate_func=delayed(0.0, 0.4)), FadeIn(top61, rate_func=delayed(0.6, 0.4)),
                  FadeIn(tally0, shift=UP * 0.1, rate_func=delayed(0.7, 0.3)),
                  run_time=2.2)
        for s in resolved:
            self.remove(grid[s])
        self.wait(0.3)

        # the 16 survivors that win in the next 15 days (ages 9..23) flash amber, day by day
        self.remove(tally0)
        tally = tally_v[0].copy()
        self.add(tally)
        tk.set_value(A0 + 0.5)
        win_ages = sorted(info[s]["age"] for s in winners)

        def winner_upd(slot):
            age = info[slot]["age"]
            base = grid[slot].copy()

            def upd(m):
                f = float(np.clip((tk.get_value() - age) / 0.9, 0, 1))
                pulse = 1 + 0.55 * np.sin(np.pi * f)
                m.become(base.copy().set_color(interpolate_color(ManimColor(OPEN), ManimColor(WON), f))
                         .scale(pulse))
            return upd

        # survivors lost by age 23 turn slate on their day too (dimmer, no pulse), so the
        # lavender dots left at age 23 are only the ones really still open. The one lost
        # at age 8 itself (after the count at the start of age 8) turns at the first tick.
        losers = [s for s in survivors if info[s]["outcome"] == "lost" and info[s]["age"] <= A0 + H]
        assert len(survivors) - len(winners) - len(losers) == int(D.cohort.open_at_age[A0 + H + 1])

        def loser_upd(slot):
            start = max(info[slot]["age"], A0 + 0.5)

            def upd(m):
                f = float(np.clip((tk.get_value() - start) / 0.9, 0, 1))
                m.set_color(interpolate_color(ManimColor(OPEN), ManimColor(LOST), f))
                m.set_opacity(1 - 0.4 * f)
            return upd

        def tally_upd(m):
            v = int(sum(1 for a in win_ages if a <= tk.get_value() - 0.25))
            if getattr(m, "shown", None) != v:
                m.become(tally_v[v])
                m.shown = v

        for s in winners:
            grid[s].add_updater(winner_upd(s))
        for s in losers:
            grid[s].add_updater(loser_upd(s))
        tally.add_updater(tally_upd)
        clock.add_updater(lambda m: clock_upd(m, A0 + 1, A0 + H))
        self.play(tk.animate(rate_func=linear).set_value(A0 + H + 1), run_time=3.4)
        for s in winners + losers:
            grid[s].clear_updaters()
        tally.clear_updaters()
        clock.clear_updaters()
        tally.become(tally_v[len(winners)])

        share = words(rf"$\approx {len(winners) / len(survivors):.2f}$", colors=(KERNEL,)).next_to(tally, RIGHT, buff=0.16)
        model = words(r"the model will say ", rf"${COND_TOT:.2f}$", colors=(MUTED, KERNEL))
        model.next_to(VGroup(tally, share), DOWN, buff=0.16)
        self.play(FadeIn(share, shift=LEFT * 0.1), FadeIn(model, shift=UP * 0.1), run_time=0.9)
        self.wait(1.1)

        # =====================================================================
        # 5. the formula
        # =====================================================================
        lhs = MathTex(r"P(", r"\text{win at } 8{+}d", r"\;\mid\;", r"\text{open at } 8", r")",
                      font_size=FS_FORMULA)
        lhs[1].set_color(KERNEL)
        lhs[3].set_color(OPEN)
        lhs.move_to([0, 1.75, 0]).align_to([F_X, 0, 0], LEFT)
        given = VGroup(Tex("chance of", font_size=FS_LABEL - 3, color=MUTED).next_to(lhs[0], DOWN, buff=0.18),
                       Tex("given", font_size=FS_LABEL - 3, color=MUTED).next_to(lhs[2], DOWN, buff=0.18))
        given[0].align_to(lhs, LEFT)
        given[1].align_to(given[0], DOWN)
        self.play(FadeOut(VGroup(clock_word, clock, legend)), Write(lhs), FadeIn(given, rate_func=delayed(0.6, 0.4)),
                  run_time=1.4)
        self.wait(0.5)

        rhs = MathTex(r"=", r"\frac{", r"k(8+d)", r"}{", r"S(8)", r"}", font_size=FS_FORMULA)
        rhs[2].set_color(KERNEL)
        rhs[4].set_color(SURVIVAL)
        rhs.next_to(lhs, DOWN, buff=0.75).align_to(lhs, LEFT).shift(RIGHT * 0.05)
        lab_x = rhs.get_right()[0] + 0.4
        num_lab = VGroup(words(r"chance a new deal wins at $8{+}d$", colors=(KERNEL,)),
                         Tex(r"(such a deal was still open at 8)", font_size=FS_TICK + 2, color=MUTED))
        num_lab.arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        num_lab.move_to([0, rhs[2].get_y() + 0.12, 0]).align_to([lab_x, 0, 0], LEFT)
        den_lab = words(r"chance a new deal is still open at 8", colors=(SURVIVAL,))
        den_lab.move_to([0, rhs[4].get_y() - 0.12, 0]).align_to([lab_x, 0, 0], LEFT)
        den_val = words(rf"$S(8) = {S8:.2f}$", colors=(SURVIVAL,)).next_to(den_lab, DOWN, buff=0.14).align_to(den_lab, LEFT)

        self.play(Write(rhs[0]), Create(rhs[3]), Write(rhs[2]),
                  FadeIn(num_lab, shift=LEFT * 0.12, rate_func=delayed(0.45, 0.55)), run_time=1.5)
        self.wait(1.1)
        self.play(Write(rhs[4], rate_func=delayed(0, 0.45)),
                  FadeIn(den_lab, shift=LEFT * 0.12, rate_func=delayed(0.2, 0.4)),
                  TransformFromCopy(top61[0], den_val, rate_func=delayed(0.45, 0.55)), run_time=1.9)
        self.wait(4.0)

        # =====================================================================
        # 6. payoff: renormalise on the chart
        # =====================================================================
        formula = VGroup(lhs, rhs)
        ref = VGroup(lhs.copy(), rhs.copy())
        ref[1].next_to(ref[0], RIGHT, buff=0.18)
        ref.scale(0.7)
        ref.move_to([0, REF_Y, 0]).align_to([REF_R, 0, 0], RIGHT)
        cohort_now = VGroup(*[grid[s] for s in survivors], box, top61, tally, share, model)
        self.play(chart_page.animate(rate_func=pan).shift(RIGHT * PAN),
                  FadeOut(cohort_now, rate_func=delayed(0, 0.28)),
                  FadeOut(VGroup(given, num_lab, den_lab, den_val), rate_func=delayed(0, 0.28)),
                  Transform(lhs, ref[0], rate_func=pan), Transform(rhs, ref[1], rate_func=pan, path_arc=1.1),
                  run_time=2.5)

        # keep only ages 9..23: for these deals they are forecast days 1..15
        drop = VGroup(*[k_bars[a] for a in range(AMAX + 1) if not (A0 + 1 <= a <= A0 + H)])
        day_ticks = VGroup(*[xtick(dx(d), f"{d}", INK) for d in (1, 5, 10, 15)])
        age_row = VGroup(*[MathTex(f"{A0 + d}", font_size=FS_TICK, color=MUTED)
                           .move_to([dx(d), day_ticks[0][1].get_y() - 0.33, 0]) for d in (1, 5, 10, 15)])
        d_title = words(r"forecast day $d$", r"\quad (age $8{+}d$)", colors=(INK, MUTED))
        d_title.move_to([X0 + WID / 2, age_row.get_y() - 0.4, 0])
        new_bars = [rect_bar(dx(d), K[A0 + d] * UK, BWD, KERNEL) for d in range(1, H + 1)]
        k_title2 = y_title(words(r"$k(8{+}d)$", r": chance a new deal wins at age $8{+}d$", colors=(KERNEL,)),
                           Y0 + K_TOP0 * UK)
        cap, c_anims = cap_anims(cap, r"divide by $S(8)$: chances among the survivors")
        self.play(FadeOut(drop, rate_func=delayed(0, 0.3)), FadeOut(age_ticks, rate_func=delayed(0, 0.3)),
                  FadeOut(tick8, rate_func=delayed(0, 0.3)), FadeOut(x_title, rate_func=delayed(0, 0.3)),
                  *[Transform(k_bars[A0 + d], new_bars[d - 1], rate_func=delayed(0.2, 0.8, rate_functions.ease_in_out_sine))
                    for d in range(1, H + 1)],
                  FadeIn(day_ticks, rate_func=delayed(0.7, 0.3)), FadeIn(age_row, rate_func=delayed(0.7, 0.3)),
                  FadeIn(d_title, rate_func=delayed(0.7, 0.3)),
                  FadeOut(k_title, rate_func=delayed(0.2, 0.3)), FadeIn(k_title2, rate_func=delayed(0.7, 0.3)),
                  *c_anims, run_time=2.7)
        self.wait(1.2)

        win_bars = VGroup(*[k_bars[A0 + d] for d in range(1, H + 1)])
        caps_old = VGroup(*[Line([dx(d) - BWD / 2, Y0 + K[A0 + d] * UK, 0], [dx(d) + BWD / 2, Y0 + K[A0 + d] * UK, 0],
                                 color=INK, stroke_width=2.5, stroke_opacity=0.85) for d in range(1, H + 1)])
        s_box = SurroundingRectangle(formula[1][4], corner_radius=0.08, stroke_width=2, color=SURVIVAL, buff=0.08)
        stretch_lab = words(rf"$\div\, {S8:.2f}$", r"\;=\;", rf"$\times\, {1 / S8:.2f}$", colors=(SURVIVAL, MUTED, KERNEL))
        stretch_lab.next_to(formula, DOWN, buff=0.4).align_to(formula, LEFT).shift(RIGHT * 0.3)
        self.play(Create(s_box), FadeIn(stretch_lab[0], shift=UP * 0.1), FadeIn(caps_old), run_time=0.8)

        y_ext = Line([X0, Y0, 0], [X0, Y0 + K_TOP1 * UK, 0], color=MUTED, stroke_width=2)
        tick04 = ytick(0.04, UK, "0.04")
        tall = [rect_bar(dx(d), COND[d - 1] * UK, BWD, KERNEL) for d in range(1, H + 1)]
        new_title = y_title(words(r"chance to win on day $d$, if open at 8"), Y0 + K_TOP1 * UK)
        self.play(*[Transform(b, t) for b, t in zip(win_bars, tall)],
                  Transform(y_axis, y_ext), FadeIn(tick04, shift=UP * 0.2),
                  FadeIn(VGroup(*stretch_lab[1:]), shift=UP * 0.1),
                  *swap_text(k_title2, new_title),
                  run_time=3.0)
        self.wait(2.5)

        # =====================================================================
        # 7. over the horizon: 0.25 per deal
        # =====================================================================
        sum_row = MathTex(r"\sum_{d=1}^{15}", r"\frac{", r"k(8+d)", r"}{", r"S(8)", r"}", r"=", f"{COND_TOT:.2f}",
                          font_size=FS_FORMULA - 6)
        sum_row[2].set_color(KERNEL)
        sum_row[4].set_color(SURVIVAL)
        sum_row[7].set_color(KERNEL)
        sum_row.next_to(formula, DOWN, buff=0.3).align_to([REF_R, 0, 0], RIGHT)
        sum_words = VGroup(words(r"each deal: a ", rf"{round(100 * COND_TOT)}\%", r" chance", colors=(None, KERNEL, None)),
                           words(r"to win in the next 15 days"))
        sum_words.arrange(DOWN, aligned_edge=RIGHT, buff=0.1)
        sum_words.next_to(sum_row, DOWN, buff=0.2).align_to([REF_R, 0, 0], RIGHT)
        self.play(FadeOut(caps_old), FadeOut(stretch_lab), FadeOut(s_box), run_time=0.7)
        self.play(FadeIn(sum_row[0]), TransformFromCopy(VGroup(*formula[1][1:6]), VGroup(*sum_row[1:6])),
                  run_time=1.1)
        self.play(LaggedStart(*[Indicate(b, color=GLOW, scale_factor=1.0) for b in win_bars], lag_ratio=0.12),
                  FadeIn(VGroup(sum_row[6], sum_row[7]), rate_func=delayed(0.55, 0.3)),
                  FadeIn(sum_words, shift=UP * 0.1, rate_func=delayed(0.7, 0.3)),
                  run_time=2.4)
        self.wait(1.1)

        # =====================================================================
        # 8. times 14: expected wins from the 14 deals
        # =====================================================================
        cap = swap_caption(self, cap, "times 14 deals: expected wins on each day")
        self.wait(1.5)
        e_ticks = VGroup(*[ytick(v, UE, s) for v, s in ((0.2, "0.2"), (0.4, "0.4"), (0.6, "0.6"))])
        e_title = y_title(words(r"expected wins per day"), Y0 + K_TOP1 * UK)
        old_ticks = VGroup(*k_ticks[1:], tick04)
        shrunk = [rect_bar(dx(d), COND[d - 1] * UE, BWD, KERNEL) for d in range(1, H + 1)]
        self.play(FadeOut(VGroup(sum_row, sum_words), rate_func=delayed(0, 0.35)),
                  *[Transform(b, t) for b, t in zip(win_bars, shrunk)],
                  *[t.animate(rate_func=delayed(0, 0.45)).shift(DOWN * (t.get_y() - Y0) * 0.5).set_opacity(0)
                    for t in old_ticks],
                  FadeIn(e_ticks, shift=DOWN * 0.6, rate_func=delayed(0.4, 0.6)), *swap_text(new_title, e_title),
                  badge_dots.animate.set_opacity(0.3),
                  run_time=1.8)
        self.remove(old_ticks)

        layers = [VGroup(*[Rectangle(width=BWD, height=COND[d - 1] * UE, stroke_color=BG, stroke_width=1,
                                     fill_color=STOCK, fill_opacity=0.92)
                           .move_to([dx(d), Y0 + j * COND[d - 1] * UE, 0], aligned_edge=DOWN)
                           for d in range(1, H + 1)]) for j in range(N8)]
        stack = [AnimationGroup(Transform(win_bars, layers[0]), badge_dots[0].animate.set_opacity(1))]
        for j in range(1, N8):
            stack.append(AnimationGroup(FadeIn(layers[j], shift=DOWN * 0.25),
                                        badge_dots[j].animate.set_opacity(1)))
        self.play(LaggedStart(*stack, lag_ratio=0.2), run_time=2.4)
        e_bars = VGroup(*[rect_bar(dx(d), ROW[d - 1] * UE, BWD, STOCK) for d in range(1, H + 1)])

        E = MathTex(r"E_{\text{stock}}(8,d)", r"=", r"N(8)", r"\,", r"\frac{", r"k(8+d)", r"}{", r"S(8)", r"}",
                    font_size=FS_FORMULA - 4)
        E[0].set_color(STOCK)
        E[2].set_color(STOCK)
        E[5].set_color(KERNEL)
        E[7].set_color(SURVIVAL)
        E.move_to([0, REF_Y, 0]).align_to([REF_R, 0, 0], RIGHT)
        e_words = words(r"expected wins on day $d$ from the 14 deals").scale(0.92)
        e_words.next_to(E, DOWN, buff=0.3).align_to(E, LEFT)
        e_total = words(r"in all: ", rf"{ROW_TOT:.1f}", r" expected wins", colors=(MUTED, STOCK, STOCK))
        e_total.next_to(e_words, DOWN, buff=0.2).align_to(E, LEFT)
        self.play(FadeOut(formula[0], rate_func=delayed(0, 0.3)), FadeOut(formula[1][0], rate_func=delayed(0, 0.3)),
                  ReplacementTransform(VGroup(*formula[1][1:6]), VGroup(*E[4:9])),
                  FadeIn(E[0:2], rate_func=delayed(0.35, 0.4)),
                  TransformFromCopy(badge_lab[0], E[2], rate_func=delayed(0.2, 0.6)),
                  FadeIn(e_bars, rate_func=delayed(0, 0.3)),
                  FadeIn(e_words, shift=UP * 0.1, rate_func=delayed(0.45, 0.35)),
                  FadeIn(e_total, shift=UP * 0.1, rate_func=delayed(0.7, 0.3)),
                  run_time=2.4)
        self.remove(win_bars, *layers)
        self.wait(3.0)

        # =====================================================================
        # 9. takeaway
        # =====================================================================
        takeaway(self, "condition on what we know: open at its age", STOCK, old_caption=cap)
        close_chapter(self)
