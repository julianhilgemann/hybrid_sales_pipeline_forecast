import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import *

# --------------------------------------------------------------------------
# Chapter 05 -- The win kernel
#
#   k(a) = S(a) h_w(a): survive to age a, then win at age a.
#   One age (13) first, then every age, then the cohort of 100 confirms it,
#   then its shape (two humps) and its area (0.30).
# --------------------------------------------------------------------------
D = load_data()
K = D.kernel
AGES = np.arange(46)

# phase A: two aligned charts in the left column, a calculation panel on the right
XA, UA = -5.85, 0.155            # age a -> x = XA + UA * a
S_BASE, S_H = 0.55, 1.65         # survival chart (top)
H_BASE, H_H = -2.2, 1.75         # win-hazard chart (bottom)
H_TOP = 0.07
PANEL_X = 1.95                   # left edge of the panel text
F_POS = np.array([4.25, 2.95, 0.0])   # the formula, top right

# phase B: the kernel chart, full width
XB, UB = -5.6, 0.25
K_BASE, K_H, K_TOP = -2.2, 2.75, 0.035
U1 = 0.01 * K_H / K_TOP          # scene height of one deal (0.01) on the kernel chart

GRID_C = np.array([-3.3, 2.02, 0.0])   # cohort grid centre (phase B)
GRID_SP, GRID_R = 0.19, 0.064

LOST_TXT = interpolate_color(ManimColor(LOST), ManimColor(INK), 0.35)


def place(ax, x0, y0):
    ax.shift(np.array([x0, y0, 0.0]) - ax.c2p(0, 0))
    return ax


def label_line(*parts, colors=(), font_size=FS_LABEL):
    """One line of words (one baseline); colour part i with colors[i]."""
    t = Tex(*parts, font_size=font_size, color=INK)
    for i, c in enumerate(colors):
        if c is not None:
            t[i].set_color(c)
    return t


def smoothstep(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def pill(width, height, color, center):
    p = RoundedRectangle(width=width, height=height, corner_radius=width * 0.49,
                         fill_color=color, fill_opacity=1.0, stroke_width=0)
    p.move_to(center)
    return p


def cap_swap(old, text, run_time):
    """swap_caption as animations, to play alongside the visual the caption
    describes: the old line leaves in the first 0.4 s, then the new one arrives
    (never superimposed). Returns (new caption, [animations])."""
    new = caption(text)
    if old is None:
        return new, [FadeIn(new, shift=UP * 0.12, rate_func=delayed(0, 0.6 / run_time))]
    return new, [FadeOut(old, shift=UP * 0.12, rate_func=delayed(0, 0.4 / run_time)),
                 FadeIn(new, shift=UP * 0.12, rate_func=delayed(0.4 / run_time, 0.6 / run_time))]


def takeaway_k(scene, parts, colors, accent, old_caption=None, hold=3.2, also=()):
    """common.takeaway with coloured maths (the shared helper takes one plain
    string, and the TeX template has no xcolor). Same geometry and timing;
    ``also`` are animations played with the old caption's exit."""
    line = Tex(*parts, font_size=FS_CAPTION, color=INK)
    for i, c in enumerate(colors):
        if c is not None:
            line[i].set_color(c)
    if line.width > 11.6:
        line.scale_to_fit_width(11.6)
    tick = RoundedRectangle(width=0.1, height=line.height + 0.16, corner_radius=0.05,
                            fill_color=accent, fill_opacity=1, stroke_width=0)
    group = VGroup(tick, line).arrange(RIGHT, buff=0.25).to_edge(DOWN, buff=0.5)
    first = list(also)
    if old_caption is not None:
        first.append(FadeOut(old_caption, shift=UP * 0.12))
    if first:
        scene.play(*first, run_time=0.8 if also else 0.4)
    scene.play(GrowFromEdge(tick, DOWN), FadeIn(line, shift=RIGHT * 0.15), run_time=0.7)
    scene.wait(hold)
    return group


def regroup(scene, group):
    """After a LaggedStart that added the members one by one, put the group
    itself in the scene (so its updaters run)."""
    scene.remove(*group)
    scene.add(group)


class Clip(Scene):
    def construct(self):
        S, hw, k, ks = K.survival, K.win_hazard, K.win_mass, K.win_mass_smooth
        a0 = 13
        s13, h13, k13 = float(S[a0]), float(hw[a0]), float(k[a0])

        open_chapter(self, 5, "The win kernel", KERNEL,
                     question="When does a brand-new deal win, if it wins at all?", part=PART[2])

        # ==================================================================
        # Beat 2 -- re-establish S(a) and h_w(a) on one age axis
        # ==================================================================
        axS = place(make_axes([0, 45, 5], [0, 1, 0.5], 45 * UA, S_H), XA, S_BASE)
        axH = place(make_axes([0, 45, 5], [0, H_TOP, 0.02], 45 * UA, H_H), XA, H_BASE)
        s_yt = tick_labels(axS, y_values=[0.5, 1])[1]
        h_yt = tick_labels(axH, y_values=[0.02, 0.04, 0.06], fmt_y="{:.2f}")[1]
        xa_vals = list(range(0, 46, 10))
        h_xt = tick_labels(axH, x_values=xa_vals)[0]
        x_title = Tex("age (business days)", font_size=FS_LABEL, color=MUTED)
        x_title.next_to(h_xt, DOWN, buff=0.14).set_x(axH.c2p(22.5, 0)[0])

        s_curve = curve(axS, AGES, S, SURVIVAL, stroke_width=4)
        h_bars = bars(axH, AGES, hw, KERNEL, width=0.8, fill_opacity=0.95)

        s_title = label_line(r"survival $S(a)$:", r" still open at age $a$", colors=(SURVIVAL,))
        s_title.next_to(axS.c2p(0, 1), UP, buff=0.28).align_to(axS.c2p(0, 0), LEFT)
        h_title = label_line(r"win hazard $h_w(a)$:", r" chance to win that day, if still open", colors=(KERNEL,))
        h_title.next_to(axH.c2p(0, H_TOP), UP, buff=0.28).align_to(axH.c2p(0, 0), LEFT)

        self.play(Create(axS), Create(axH), FadeIn(s_title), FadeIn(h_title), run_time=0.9)
        self.play(Create(s_curve),
                  LaggedStart(*[GrowFromEdge(b, DOWN) for b in h_bars], lag_ratio=0.02),
                  FadeIn(s_yt), FadeIn(h_yt), FadeIn(h_xt), FadeIn(x_title),
                  run_time=1.4)
        regroup(self, h_bars)
        self.wait(0.5)

        # ==================================================================
        # Beat 3 -- one age: a = 13
        # ==================================================================
        x13 = axH.c2p(a0, 0)[0]
        # one dashed segment per chart (a gap for the hazard chart's title)
        guide = VGroup(*[DashedLine([x13, y0, 0], [x13, y1, 0], color=INK, stroke_width=2, dash_length=0.08)
                         for y0, y1 in ((H_BASE, H_BASE + H_H + 0.05), (S_BASE, S_BASE + S_H + 0.05))])
        guide.set_stroke(opacity=0.65)
        t13 = MathTex(str(a0), font_size=FS_TICK + 4, color=INK).next_to(axH.c2p(a0, 0), DOWN, buff=0.13)

        cap, ca = cap_swap(None, rf"take one age: {a0} business days", 1.0)
        self.play(Create(guide), FadeIn(t13, shift=UP * 0.1), *ca, run_time=1.0)
        self.bring_to_back(guide)       # behind the bars
        self.wait(0.9)

        # still open at 13 (panel row at the dot's height)
        s_dot = Dot(axS.c2p(a0, s13), radius=0.08, color=SURVIVAL)
        s_words = Tex(rf"still open at age {a0}", font_size=FS_LABEL, color=INK)
        s_math = MathTex(rf"S({a0})", "=", f"{s13:.2f}", font_size=36, color=SURVIVAL)
        s_block = VGroup(s_words, s_math).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
        s_block.shift([PANEL_X - s_block.get_left()[0], s_dot.get_y() - s_math.get_y(), 0])
        s_lead = DashedLine(s_dot.get_center() + RIGHT * 0.12, [PANEL_X - 0.15, s_dot.get_y(), 0],
                            color=SURVIVAL, stroke_width=1.6, dash_length=0.06).set_stroke(opacity=0.55)
        self.play(GrowFromCenter(s_dot), Create(s_lead), FadeIn(s_block, shift=LEFT * 0.15), run_time=1.0)
        self.wait(1.0)

        # then win that day (panel row at the bar's height)
        y_bar = axH.c2p(a0, h13)[1]
        h_words = Tex(r"then win that day", font_size=FS_LABEL, color=INK)
        h_math = MathTex(rf"h_w({a0})", "=", f"{h13:.3f}", font_size=36, color=KERNEL)
        h_block = VGroup(h_words, h_math).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
        h_block.shift([PANEL_X - h_block.get_left()[0], y_bar - h_math.get_y(), 0])
        h_lead = DashedLine([x13 + 0.1, y_bar, 0], [PANEL_X - 0.15, y_bar, 0],
                            color=KERNEL, stroke_width=1.6, dash_length=0.06).set_stroke(opacity=0.55)
        others = [b for i, b in enumerate(h_bars) if i != a0]
        self.play(*[b.animate.set_fill(opacity=0.22) for b in others],
                  Create(h_lead), FadeIn(h_block, shift=LEFT * 0.15), run_time=1.1)
        self.wait(1.0)

        # their product (below both factors)
        p_words = Tex(rf"so a new deal wins at exactly age {a0}", font_size=FS_LABEL, color=INK)
        p_math = MathTex(rf"k({a0})", "=", f"{s13:.2f}", r"\times", f"{h13:.3f}", r"\approx", f"{k13:.3f}",
                         font_size=36)
        p_math[0].set_color(KERNEL)
        p_math[2].set_color(SURVIVAL)
        p_math[4].set_color(KERNEL)
        p_math[6].set_color(KERNEL)
        p_block = VGroup(p_words, p_math).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
        p_block.next_to(h_block, DOWN, buff=0.42, aligned_edge=LEFT)

        self.play(FadeIn(p_words, shift=UP * 0.1),
                  TransformFromCopy(s_math[2], p_math[2]),
                  TransformFromCopy(h_math[2], p_math[4]),
                  FadeIn(p_math[3]), run_time=1.4)
        self.play(FadeIn(VGroup(p_math[0], p_math[1])), Write(VGroup(p_math[5], p_math[6])), run_time=0.9)
        self.wait(0.8)

        # the general formula, assembled from the instance
        F = MathTex("k(a)", "=", "S(a)", r"\;\cdot\;", "h_w(a)", font_size=FS_FORMULA)
        F[0].set_color(KERNEL)
        F[2].set_color(SURVIVAL)
        F[4].set_color(KERNEL)
        F.move_to(F_POS)
        br_s = Brace(F[2], DOWN, buff=0.1, color=SURVIVAL)
        br_h = Brace(F[4], DOWN, buff=0.1, color=KERNEL)
        bw_s = Tex(r"survive to $a$", font_size=FS_LABEL, color=SURVIVAL).next_to(br_s, DOWN, buff=0.08)
        bw_h = Tex(r"win at $a$", font_size=FS_LABEL, color=KERNEL).next_to(br_h, DOWN, buff=0.08)
        gap = bw_h.get_left()[0] - bw_s.get_right()[0]
        if gap < 0.2:
            bw_s.shift(LEFT * (0.2 - gap) / 2)
            bw_h.shift(RIGHT * (0.2 - gap) / 2)
        braces = VGroup(br_s, br_h, bw_s, bw_h)

        cap, ca = cap_swap(cap, r"first still open, then win that day", 1.6)
        self.play(TransformFromCopy(p_math[0], F[0]),
                  TransformFromCopy(s_math[0], F[2]),
                  TransformFromCopy(h_math[0], F[4]),
                  FadeIn(F[1]), FadeIn(F[3]),
                  VGroup(s_block, h_block, p_block).animate.set_opacity(0.5),
                  VGroup(s_lead, h_lead).animate.set_stroke(opacity=0.25),
                  *ca, run_time=1.6)
        self.play(GrowFromCenter(br_s), GrowFromCenter(br_h),
                  FadeIn(bw_s, shift=UP * 0.08), FadeIn(bw_h, shift=UP * 0.08), run_time=0.9)
        self.wait(4.0)

        # ==================================================================
        # Beat 4 -- every age: multiply, then zoom into the result
        # ==================================================================
        ghost = h_bars.copy().set_fill(opacity=0.0).set_stroke(KERNEL, width=1.2, opacity=0.5)
        sw = ValueTracker(float(a0))
        y_mid = 0.5 * (H_BASE + S_BASE + S_H + 0.05)

        guide.add_updater(lambda m: m.move_to([axH.c2p(sw.get_value(), 0)[0], y_mid, 0]))
        s_dot.add_updater(lambda m: m.move_to(axS.c2p(
            np.clip(sw.get_value(), 0, 45), float(np.interp(np.clip(sw.get_value(), 0, 45), AGES, S)))))
        cap, ca = cap_swap(cap, r"multiply at every age", 1.2)
        self.play(FadeOut(VGroup(s_block, h_block, p_block, s_lead, h_lead)),
                  FadeOut(t13),
                  h_bars.animate.set_fill(opacity=0.95),
                  FadeIn(ghost),
                  sw.animate.set_value(0.0),
                  *ca, run_time=1.2)
        self.add(ghost, h_bars)        # ghost outlines behind the shrinking bars

        bar_px = [b.get_bottom().copy() for b in h_bars]
        uy = axH.y_axis.unit_size

        def shrink(group):
            g = sw.get_value()
            for a, b in enumerate(group):
                f = smoothstep(g - a + 0.5)
                h = hw[a] * (1 - f + f * S[a])
                b.stretch_to_fit_height(max(h * uy, 1e-3))
                b.move_to(bar_px[a], aligned_edge=DOWN)

        h_bars.add_updater(shrink)
        self.play(sw.animate.set_value(45.6), run_time=4.0, rate_func=rate_functions.ease_in_out_sine)
        h_bars.clear_updaters()
        guide.clear_updaters()
        s_dot.clear_updaters()
        self.wait(0.4)

        # zoom: the result takes the stage on a tight axis, and gets its name
        axK = place(make_axes([0, 45, 5], [0, K_TOP, 0.01], 45 * UB, K_H), XB, K_BASE)
        k_bars = bars(axK, AGES, k, KERNEL, width=0.8, fill_opacity=0.95)
        k_yt = tick_labels(axK, y_values=[0.01, 0.02, 0.03], fmt_y="{:.2f}")[1]
        xb_vals = list(range(0, 46, 5))
        k_xt = tick_labels(axK, x_values=xb_vals)[0]
        k_xtitle = x_title.copy().next_to(k_xt, DOWN, buff=0.14).set_x(axK.c2p(22.5, 0)[0])
        k_lab1 = label_line(r"win kernel $k(a)$", colors=(KERNEL,), font_size=FS_BODY)
        k_lab2 = label_line(r"chance a new deal wins at exactly age $a$")
        k_lab = VGroup(k_lab1, k_lab2).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        k_lab.move_to(axK.c2p(23.5, 0.0255), aligned_edge=LEFT)

        xt_moves = [ReplacementTransform(lab, k_xt[xb_vals.index(v)]) for v, lab in zip(xa_vals, h_xt)]
        new_x = VGroup(*[k_xt[i] for i, v in enumerate(xb_vals) if v not in xa_vals])
        T = 2.6
        self.play(FadeOut(VGroup(axS, s_curve, s_yt, s_title, s_dot), shift=UP * 0.25, rate_func=delayed(0, 0.35)),
                  FadeOut(VGroup(ghost, guide, braces), rate_func=delayed(0, 0.35)),
                  FadeOut(h_title, shift=UP * 0.12, rate_func=delayed(0, 0.3)),
                  Transform(axH, axK, rate_func=delayed(0.15, 0.85, rate_functions.ease_in_out_sine)),
                  Transform(h_bars, k_bars, rate_func=delayed(0.15, 0.85, rate_functions.ease_in_out_sine)),
                  FadeOut(h_yt, rate_func=delayed(0, 0.2)),
                  FadeIn(k_yt, rate_func=delayed(0.6, 0.4)),
                  *[a.set_rate_func(delayed(0.15, 0.85, rate_functions.ease_in_out_sine)) for a in xt_moves],
                  FadeIn(new_x, rate_func=delayed(0.6, 0.4)),
                  x_title.animate(rate_func=delayed(0.15, 0.85, rate_functions.ease_in_out_sine)).move_to(k_xtitle),
                  FadeIn(k_lab, shift=UP * 0.12, rate_func=delayed(0.65, 0.35)),
                  run_time=T)
        self.wait(0.7)
        kb = h_bars                     # the kernel bars now on screen

        # ==================================================================
        # Beat 5 -- payoff: the cohort of 100 agrees
        # ==================================================================
        dots_info = sorted(D.cohort.dots, key=lambda d: d["slot"])
        col_of = {"won": WON, "lost": LOST, "open": OPEN}
        grid = cohort_grid(spacing=GRID_SP, radius=GRID_R).move_to(GRID_C)
        for d, rec in zip(grid, dots_info):
            d.set_fill(col_of[rec["outcome"]])
        won_n = int(D.cohort.won_total)
        lost_n = int(D.cohort.lost_total)
        open_n = int(D.cohort.open_end)
        g_lab = Tex(r"100 brand-new deals", font_size=FS_LABEL, color=INK)
        g_lab.next_to(grid, RIGHT, buff=0.32).align_to(grid, UP).shift(DOWN * 0.12)
        counts = label_line(rf"{won_n} won", r" \textperiodcentered{} ", rf"{lost_n} lost",
                            r" \textperiodcentered{} ", rf"{open_n} still open",
                            colors=(KERNEL, MUTED, LOST_TXT, MUTED, SURVIVAL))
        counts.next_to(g_lab, DOWN, buff=0.2, aligned_edge=LEFT)

        self.play(FadeOut(cap, shift=UP * 0.12, rate_func=delayed(0, 0.3)),
                  LaggedStart(*[GrowFromCenter(d) for d in grid], lag_ratio=0.008),
                  FadeIn(g_lab, shift=LEFT * 0.12), FadeIn(counts, shift=LEFT * 0.12), run_time=1.3)
        regroup(self, grid)
        cap = None
        self.wait(0.4)

        # the axis now counts winners out of 100; the bars become outlines to fill
        n_yt = VGroup(*[MathTex(str(n), font_size=FS_TICK, color=MUTED).move_to(lab, aligned_edge=RIGHT)
                        for n, lab in zip((1, 2, 3), k_yt)])
        n_title = Tex(r"winners (of 100)", font_size=FS_LABEL, color=MUTED)
        n_title.next_to(axK.c2p(0, K_TOP), UP, buff=0.2).align_to(n_yt, LEFT)
        self.play(kb.animate.set_fill(opacity=0.16).set_stroke(KERNEL, width=1.6, opacity=0.9),
                  ReplacementTransform(k_yt, n_yt), FadeIn(n_title, shift=UP * 0.1),
                  run_time=1.0)

        # winners fly, in order of the age they won, and stack one block per deal
        winners = sorted([r for r in dots_info if r["outcome"] == "won"], key=lambda r: (r["age"], r["slot"]))
        level = {}
        flights, pills = [], VGroup()
        pw_w, pw_h = 0.8 * UB * 0.84, U1 - 0.07
        for r in winners:
            a = int(r["age"])
            j = level.get(a, 0)
            level[a] = j + 1
            c = axK.c2p(a, 0) + UP * (j + 0.5) * U1
            p = pill(pw_w, pw_h, WON, c)
            pills.add(p)
            flights.append(TransformFromCopy(grid[r["slot"]], p, path_arc=0.7))
        cap = caption(r"the winners pile up in the shape of $k(a)$")
        self.play(LaggedStart(*flights, lag_ratio=0.075),
                  FadeIn(cap, shift=UP * 0.12, rate_func=delayed(0.78, 0.22)), run_time=3.0)
        self.wait(3.0)

        # ==================================================================
        # Beat 6 -- shape: two humps
        # ==================================================================
        k_yt2 = tick_labels(axK, y_values=[0.01, 0.02, 0.03], fmt_y="{:.2f}")[1]
        self.play(FadeOut(pills),
                  kb.animate.set_fill(opacity=0.3).set_stroke(width=0, opacity=0),
                  ReplacementTransform(n_yt, k_yt2), FadeOut(n_title),
                  VGroup(grid, g_lab, counts).animate.set_opacity(0.3),
                  run_time=1.0)
        k_curve = curve(axK, AGES, ks, KERNEL, stroke_width=5)
        self.play(Create(k_curve), run_time=2.0, rate_func=rate_functions.ease_in_out_sine)

        m1 = int(np.argmax(ks[:9]))
        m2 = 9 + int(np.argmax(ks[9:20]))
        humps = VGroup()
        for m, y_lab in ((m1, float(k[:9].max()) + 0.0022), (m2, float(k[9:17].max()) + 0.0022)):
            top = axK.c2p(m, ks[m])
            dl = DashedLine(axK.c2p(m, 0), top, color=KERNEL, stroke_width=2, dash_length=0.07)
            dl.set_stroke(opacity=0.8)
            pk = Dot(top, radius=0.06, color=KERNEL)
            lab = MathTex(rf"\approx {m}", r"\text{ days}", font_size=FS_LABEL + 3, color=INK)
            lab.move_to([top[0], axK.c2p(0, y_lab)[1], 0], aligned_edge=DOWN)
            humps.add(VGroup(dl, pk, lab))
        cap, ca = cap_swap(cap, r"two typical decision times", 1.4)
        self.play(LaggedStart(*[AnimationGroup(Create(g[0]), GrowFromCenter(g[1]), FadeIn(g[2], shift=DOWN * 0.12))
                                for g in humps], lag_ratio=0.45), *ca, run_time=1.4)
        self.wait(2.4)

        # ==================================================================
        # Beat 7 -- area: the chance of ever winning
        # ==================================================================
        pw = float(K.p_win_total)
        pl = float(K.p_loss_total)
        po = 1.0 - pw - pl
        area = area_under(axK, AGES, ks, KERNEL, opacity=0.38)
        F2 = MathTex(r"\sum_a", "k(a)", "=", f"{pw:.2f}", font_size=FS_FORMULA)
        F2[1].set_color(KERNEL)
        F2[3].set_color(KERNEL)
        F2.move_to(F, aligned_edge=LEFT)
        F2.shift(UP * (F[0].get_y() - F2[1].get_y()))        # k(a) stays on its line
        a_words = VGroup(Tex(r"chance a new deal is ever won", font_size=FS_LABEL, color=INK),
                         Tex(r"(within 45 days)", font_size=FS_LABEL, color=MUTED)
                         ).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        a_words.next_to(F2, DOWN, buff=0.2).align_to(F2, LEFT)

        cap, ca = cap_swap(cap, r"add up every age: the area under $k(a)$", 1.2)
        self.play(FadeIn(area), kb.animate.set_fill(opacity=0.15), *ca, run_time=1.5)
        self.play(TransformMatchingTex(F, F2), FadeIn(a_words, shift=UP * 0.1, rate_func=delayed(0.5, 0.5)),
                  run_time=1.6)
        self.wait(0.8)

        # the 100% bar: won / lost / still open
        BW, BH = 4.5, 0.34
        bx0 = F2.get_left()[0]
        by = a_words.get_bottom()[1] - 0.42
        segs = VGroup()
        x = bx0
        for frac, col in ((pw, KERNEL), (pl, LOST), (po, SURVIVAL)):
            r = Rectangle(width=BW * frac, height=BH, stroke_width=0, fill_color=col, fill_opacity=0.95)
            r.move_to([x, by, 0], aligned_edge=LEFT)
            segs.add(r)
            x += BW * frac
        frame = Rectangle(width=BW, height=BH, stroke_color=MUTED, stroke_width=1.2, fill_opacity=0)
        frame.move_to([bx0, by, 0], aligned_edge=LEFT)
        seg_labs = VGroup(
            label_line(r"won ", f"${pw:.2f}$", colors=(KERNEL, KERNEL)),
            label_line(r"lost ", f"${pl:.2f}$", colors=(LOST_TXT, LOST_TXT)),
            label_line(r"still open ", f"${po:.2f}$", colors=(SURVIVAL, SURVIVAL)),
        )
        for lab, s in zip(seg_labs, segs):
            lab.next_to(s, DOWN, buff=0.14)
        seg_labs[0].align_to(segs[0], LEFT)
        seg_labs[1].align_to(segs[1], LEFT).shift(RIGHT * 0.1)
        seg_labs[2].align_to(segs[2], RIGHT)

        self.play(Create(frame, rate_func=delayed(0, 0.35)),
                  GrowFromEdge(segs[0], LEFT, rate_func=delayed(0.1, 0.45)),
                  area.animate(rate_func=lambda t: there_and_back(np.clip((t - 0.05) / 0.6, 0, 1))).set_fill(opacity=0.62),
                  GrowFromEdge(segs[1], LEFT, rate_func=delayed(0.55, 0.45)),
                  GrowFromEdge(segs[2], LEFT, rate_func=delayed(0.55, 0.45)),
                  run_time=1.7)

        hl = SurroundingRectangle(counts, corner_radius=0.1, stroke_width=2, color=KERNEL, buff=0.12)
        cap, ca = cap_swap(cap, rf"the cohort agrees: {won_n} won, {lost_n} lost, {open_n} still open", 1.2)
        self.play(FadeIn(seg_labs, shift=UP * 0.1),
                  VGroup(grid, g_lab, counts).animate.set_opacity(1.0), Create(hl), *ca, run_time=1.2)
        self.wait(2.8)

        # ==================================================================
        # Beat 8 -- takeaway on a clean kernel curve
        # ==================================================================
        takeaway_k(self, (r"$k(a)$", r": when a new deal wins, and how often"), (KERNEL, None),
                   KERNEL, old_caption=cap,
                   also=[FadeOut(VGroup(grid, g_lab, counts, hl, segs, frame, seg_labs, a_words, kb)),
                         area.animate.set_fill(opacity=0.22)])
        close_chapter(self)
