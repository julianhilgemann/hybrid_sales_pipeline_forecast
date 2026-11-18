"""Chapter 03 -- Win, lose or wait.

The survival-analysis tangent for a non-mathematician: one open deal faces three
outcomes each business day; a hazard is the chance of an outcome *among the deals
still open*; a cohort of 100 new deals makes the conditional idea concrete; the
share still open is the survival curve S(a), a chain of daily "stay open" chances.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import *

D = load_data()
K = D.kernel
CO = D.cohort
AGES = np.arange(46)
SURV = np.asarray(K.survival, dtype=float)

# ---- layout of the cohort part (beats 4-9) --------------------------------
GRID_C = np.array([-4.95, 0.0, 0.0])
GRID_SP, DOT_R = 0.30, 0.09
PITCH, PAD = 0.26, 0.12                     # tray dot pitch, tray padding
TRAY_X0 = -2.45
TRAY_W = 10 * PITCH + 2 * PAD
WON_ROWS, LOST_ROWS = 3, 6
WON_TOP = 1.43
WON_H = WON_ROWS * PITCH + 2 * PAD
LOST_TOP = WON_TOP - WON_H - 0.6            # leaves room for the "lost" label
LOST_H = LOST_ROWS * PITCH + 2 * PAD
COUNT_Y = -1.95                             # "still open" counter under the grid
AGE_Y = 1.95                                # age counter above the grid

# survival chart (lower right)
CH_X0, CH_Y0, CH_W, CH_H = 1.85, -2.0, 4.5, 2.15

# ---- the cohort's clock: real seconds per age ------------------------------
DUR = np.zeros(46)
DUR[:6] = 1.2                               # ages 0..5: slow, one by one
DUR[6:45] = np.interp(np.arange(6, 45), [6, 12, 20, 30, 44], [0.40, 0.32, 0.23, 0.15, 0.11])
T_AGE = np.concatenate([[0.0], np.cumsum(DUR[:45])])   # T_AGE[a]: clock time at the start of age a


def g_of(t):
    """Age shown by the clock at clock time t (continuous)."""
    return float(np.interp(t, T_AGE, AGES))


def tray_slot(top, rows, k):
    """Centre of slot k in a tray, filled bottom-up, left to right, rows of 10."""
    r, c = divmod(k, 10)
    bottom = top - 2 * PAD - rows * PITCH + PAD
    return np.array([TRAY_X0 + PAD + PITCH * (c + 0.5), bottom + PITCH * (r + 0.5), 0.0])


class NumberSlot(VGroup):
    """A counter that swaps whole typeset numbers (cached per value), keeping its
    left edge and vertical centre. Used instead of ``Integer(mob_class=Tex)``,
    whose ``set_value`` falls back to Computer Modern digits."""

    def __init__(self, value: int, make):
        super().__init__()
        self.make, self.cache, self.value = make, {}, value
        self.add(self._get(value))

    def _get(self, v):
        if v not in self.cache:
            self.cache[v] = self.make(v)
        return self.cache[v].copy()

    def set_number(self, v: int):
        if v == self.value:
            return self
        new = self._get(v)
        new.move_to(self.get_left(), aligned_edge=LEFT)
        old = list(self.submobjects)
        self.remove(*old)
        self.add(new)
        # Cairo renders the family list captured when the play started: blank the
        # old glyphs so they do not linger (the same trick DecimalNumber uses)
        for m in old:
            for f in m.get_family():
                f.points = np.zeros((0, 3))
        self.value = v
        return self


class Clip(Scene):
    def construct(self):
        open_chapter(self, 3, "Win, lose or wait", SURVIVAL,
                     question="What happens to an open deal on each business day?", part=PART[2])

        # ==================================================================
        # Beat 2 -- one deal, one day
        # ==================================================================
        S0 = np.array([-3.3, 0.0, 0.0])
        PW, PL, PO = np.array([-0.4, 1.9, 0.0]), np.array([-0.4, -1.9, 0.0]), np.array([3.0, 0.0, 0.0])
        RB = 0.16
        d0 = Dot(S0, radius=RB, color=OPEN)
        lab0 = Tex(r"open at age $a$", font_size=FS_BODY, color=OPEN).next_to(d0, LEFT, buff=0.3)

        def branch(end, col, text):
            arr = Arrow(S0, end, buff=0.32, stroke_width=4, color=col, tip_length=0.2,
                        max_tip_length_to_length_ratio=0.2)
            dot = Dot(end, radius=RB, color=col)
            lab = Tex(text, font_size=FS_BODY, color=col).next_to(dot, RIGHT, buff=0.25)
            return arr, dot, lab

        aW, dW, labW = branch(PW, WON, "won today")
        aL, dL, labL = branch(PL, LOST, "lost today")
        aO, dO, labO = branch(PO, OPEN, r"still open at age $a+1$")

        def normal(arr, side):
            u = arr.get_end() - arr.get_start()
            u = u / np.linalg.norm(u)
            return side * np.array([-u[1], u[0], 0.0])

        hw_lab = MathTex("h_w(a)", font_size=38, color=WON)
        hw_lab.next_to(aW.get_center(), normal(aW, 1), buff=0.12)
        hl_lab = MathTex(r"h_\ell(a)", font_size=38, color=LOST)
        hl_lab.next_to(aL.get_center(), normal(aL, -1), buff=0.12)
        ho_lab = MathTex("1", "-", "h_w(a)", "-", r"h_\ell(a)", font_size=38)
        ho_lab[2].set_color(WON)
        ho_lab[4].set_color(LOST)
        ho_lab.next_to(aO.get_center(), UP, buff=0.16).shift(RIGHT * 0.25)

        self.play(GrowFromCenter(d0), FadeIn(lab0, shift=RIGHT * 0.15), run_time=1.0)
        cap = swap_caption(self, None, "every business day: win, lose, or wait")
        self.wait(1.0)
        for arr, dot, lab in ((aW, dW, labW), (aL, dL, labL), (aO, dO, labO)):
            self.play(GrowArrow(arr), run_time=0.6)
            self.play(GrowFromCenter(dot), FadeIn(lab, shift=RIGHT * 0.12), run_time=0.5)
        self.wait(0.4)
        self.play(LaggedStart(FadeIn(hw_lab, scale=0.9), FadeIn(hl_lab, scale=0.9), FadeIn(ho_lab, scale=0.9),
                              lag_ratio=0.75), run_time=2.1)
        self.wait(1.6)

        # ==================================================================
        # Beat 3 -- a hazard is a conditional probability
        # ==================================================================
        keep = VGroup(d0, lab0, aW, dW, labW, hw_lab)
        gone = VGroup(aL, dL, labL, hl_lab, aO, dO, labO, ho_lab)
        self.play(FadeOut(gone), keep.animate.shift(UP * 0.85), run_time=1.0)

        card = definition_card("Hazard", ["the chance it happens today,", "given the deal is still open"], KERNEL)
        card.to_edge(RIGHT, buff=0.45).set_y(1.95)
        self.play(FadeIn(card, shift=UP * 0.15), run_time=1.0)
        self.wait(1.5)

        fH = MathTex("h_w(a)", "=", r"P\bigl(", r"\text{win at age } a", r"\;\mid\;", r"\text{open at age } a",
                     r"\bigr)", font_size=FS_FORMULA)
        fH[0].set_color(WON)
        fH[3].set_color(WON)
        fH[5].set_color(OPEN)
        fH.move_to([0, -0.4, 0])
        self.play(TransformFromCopy(hw_lab, fH[0]), FadeIn(fH[1]), run_time=1.2)
        p_tag = Tex("chance of", font_size=FS_TICK + 2, color=MUTED).next_to(fH[2], UP, buff=0.14)
        self.play(Write(VGroup(fH[2], fH[3])), FadeIn(p_tag, shift=DOWN * 0.08), run_time=0.9)
        self.play(Write(VGroup(fH[4], fH[5], fH[6])), run_time=0.9)
        br = Brace(VGroup(fH[4], fH[5]), DOWN, buff=0.12, color=OPEN)
        br_lab = Tex("only deals still open count", font_size=FS_LABEL, color=OPEN).next_to(br, DOWN, buff=0.12)
        self.play(GrowFromCenter(br), FadeIn(br_lab, shift=UP * 0.1), run_time=0.9)
        cap = swap_caption(self, cap, "a hazard is a conditional probability")
        self.wait(1.6)
        loss_f = MathTex(r"h_\ell(a)", "=", r"P\bigl(", r"\text{lost at age } a", r"\;\mid\;", r"\text{open at age } a",
                         r"\bigr)", font_size=FS_LABEL + 5)
        loss_f[0].set_color(LOST)
        loss_f[3].set_color(LOST)
        loss_f[5].set_color(OPEN)
        loss_line = VGroup(Tex("likewise for a loss:", font_size=FS_LABEL, color=MUTED), loss_f).arrange(RIGHT, buff=0.3)
        loss_line.move_to([0, -2.3, 0])
        self.play(FadeIn(loss_line, shift=UP * 0.1), run_time=0.8)
        self.wait(1.1)

        # ==================================================================
        # Beat 4 -- a cohort of 100 brand-new deals
        # ==================================================================
        self.play(FadeOut(VGroup(card, fH, p_tag, br, br_lab, loss_line, aW, dW, labW, hw_lab, lab0)),
                  FadeOut(cap, shift=UP * 0.12), d0.animate.move_to(GRID_C), run_time=1.1)
        cap = None

        grid = cohort_grid(spacing=GRID_SP, radius=DOT_R).shift(GRID_C)
        grid.set_z_index(3)
        copies = VGroup(*[d0.copy() for _ in range(100)])
        self.add(copies)
        self.remove(d0)
        order = np.argsort([np.linalg.norm(grid[s].get_center() - GRID_C) for s in range(100)], kind="stable")
        title = Tex("100 new deals, age 0", font_size=FS_BODY, color=INK).move_to([GRID_C[0], AGE_Y, 0])
        self.play(LaggedStart(*[Transform(copies[s], grid[s]) for s in order], lag_ratio=0.02, run_time=1.6),
                  Succession(Wait(0.7), FadeIn(title, shift=DOWN * 0.1, run_time=0.9)))
        self.remove(*copies)          # the LaggedStart group holds the dots individually
        self.add(grid)

        won_tray = RoundedRectangle(width=TRAY_W, height=WON_H, corner_radius=0.1, stroke_color=WON, stroke_width=2,
                                    fill_color=WON, fill_opacity=0.06)
        won_tray.move_to([TRAY_X0 + TRAY_W / 2, WON_TOP - WON_H / 2, 0])
        lost_tray = RoundedRectangle(width=TRAY_W, height=LOST_H, corner_radius=0.1, stroke_color=LOST, stroke_width=2,
                                     fill_color=LOST, fill_opacity=0.06)
        lost_tray.move_to([TRAY_X0 + TRAY_W / 2, LOST_TOP - LOST_H / 2, 0])
        won_lab = Tex("won", font_size=FS_LABEL, color=WON).next_to(won_tray, UP, buff=0.1).align_to(won_tray, LEFT)
        lost_lab = Tex("lost", font_size=FS_LABEL, color=LOST).next_to(lost_tray, UP, buff=0.1).align_to(lost_tray, LEFT)

        ref = Tex("still open: ", "100", font_size=FS_BODY, color=OPEN)
        open_word = ref[0]
        open_num = NumberSlot(100, lambda v: Tex(str(v), font_size=FS_BODY, color=OPEN))
        open_num.move_to(ref[1], aligned_edge=LEFT)
        open_counter = VGroup(open_word, open_num).move_to([GRID_C[0], COUNT_Y, 0])

        self.wait(0.3)
        self.play(Create(won_tray), Create(lost_tray), FadeIn(won_lab), FadeIn(lost_lab),
                  FadeIn(open_counter, shift=UP * 0.1), run_time=1.1)
        self.wait(0.4)

        # ---- the cohort machinery: one clock drives dots, counters and curve ----
        recs = {int(r["slot"]): r for r in CO.dots}
        movers = sorted([s for s in range(100) if recs[s]["outcome"] in ("won", "lost")],
                        key=lambda s: (recs[s]["age"], s))
        age_of = {s: int(recs[s]["age"]) for s in movers}
        out_of = {s: recs[s]["outcome"] for s in movers}
        start_pos = {s: grid[s].get_center().copy() for s in movers}
        target_pos, target_col, start_col = {}, {}, {}
        kw = kl = 0
        for s in movers:
            if out_of[s] == "won":
                target_pos[s], target_col[s] = tray_slot(WON_TOP, WON_ROWS, kw), ManimColor(WON)
                kw += 1
            else:
                target_pos[s], target_col[s] = tray_slot(LOST_TOP, LOST_ROWS, kl), ManimColor(LOST)
                kl += 1
            start_col[s] = ManimColor(OPEN)
        t_dep = {s: T_AGE[age_of[s]] + min(0.25, 0.3 * DUR[age_of[s]]) for s in movers}
        tau = {s: (0.75 if age_of[s] <= 5 else 0.6) for s in movers}
        t_count = np.array([t_dep[s] + 0.15 * tau[s] for s in movers])
        landed = set()
        clock = ValueTracker(0.0)

        def move_dots(group):
            t = clock.get_value()
            for s in movers:
                if s in landed:
                    continue
                p = (t - t_dep[s]) / tau[s]
                if p <= 0:
                    continue
                p = min(p, 1.0)
                e = smooth(p)
                group[s].move_to(start_pos[s] + (target_pos[s] - start_pos[s]) * e)
                group[s].set_color(interpolate_color(start_col[s], target_col[s], min(1.0, p / 0.3)))
                if p >= 1.0:
                    landed.add(s)

        def open_count(t):
            return 100 - int(np.sum(t >= t_count))

        grid.add_updater(move_dots)

        # ==================================================================
        # Beat 5 -- days pass, slowly at first
        # ==================================================================
        ref = Tex("age ", "$a =$ ", "$0$", font_size=FS_BODY + 4, color=INK)
        age_num = NumberSlot(0, lambda v: Tex(f"${v}$", font_size=FS_BODY + 4, color=INK))
        age_num.move_to(ref[2], aligned_edge=LEFT)
        age_counter = VGroup(ref[0], ref[1], age_num).move_to([GRID_C[0], AGE_Y, 0])

        def upd_age(m):
            m.set_number(min(int(np.floor(g_of(clock.get_value()) + 1e-9)), 45))

        def upd_open(m):
            m.set_number(open_count(clock.get_value()))

        self.play(FadeOut(title, shift=UP * 0.15), run_time=0.4)
        self.play(FadeIn(age_counter, shift=UP * 0.15), run_time=0.6)
        age_num.add_updater(upd_age)
        open_num.add_updater(upd_open)
        cap = swap_caption(self, None, "new deals rarely decide in their first days")
        self.wait(0.2)
        self.play(clock.animate.set_value(T_AGE[5]), run_time=T_AGE[5], rate_func=linear)

        # ==================================================================
        # Beat 6 -- the conditional moment at age 5
        # ==================================================================
        n5 = int(CO.open_at_age[5])
        w5 = [s for s in movers if age_of[s] == 5 and out_of[s] == "won"]
        l5 = [s for s in movers if age_of[s] == 5 and out_of[s] == "lost"]
        before5 = [s for s in movers if age_of[s] < 5]
        side = 9 * GRID_SP + 2 * DOT_R
        footprint = Rectangle(width=side, height=side).move_to(GRID_C)   # the grid's own square
        rect = SurroundingRectangle(VGroup(footprint, open_counter), buff=0.16, corner_radius=0.1, stroke_width=2,
                                    color=OPEN)
        self.play(Create(rect), *[grid[s].animate.set_opacity(0.3) for s in before5],
                  FadeOut(cap, shift=UP * 0.12, run_time=0.4), run_time=1.0)
        cap = swap_caption(self, None, rf"at age 5, only the {n5} still open can decide")
        self.wait(1.2)

        RX = 3.85
        L0 = Tex("today: ", f"{len(w5)} win", ", ", f"{len(l5)} are lost", font_size=FS_BODY, color=INK)
        L0[1].set_color(WON)
        L0[3].set_color(LOST)
        L0.move_to([RX, 1.85, 0])
        self.play(*[grid[s].animate.set_color(WON) for s in w5], *[grid[s].animate.set_color(LOST) for s in l5],
                  FadeIn(L0, shift=UP * 0.1), run_time=1.0)
        for s in w5 + l5:
            start_col[s] = target_col[s]
        self.wait(0.3)

        hw5 = float(K.win_hazard[5])
        F = MathTex("h_w(5)", r"\approx", r"\frac{", f"{len(w5)}", "}{", f"{n5}", "}", r"\approx",
                    f"{len(w5) / n5:.3f}", font_size=FS_FORMULA)
        F[0].set_color(WON)
        F[3].set_color(WON)
        F[5].set_color(OPEN)
        F.move_to([RX, 0.95, 0])
        self.play(Write(VGroup(F[0], F[1], F[2], F[4], F[6])),
                  TransformFromCopy(VGroup(*[grid[s] for s in w5]), F[3]), run_time=1.0)
        self.play(TransformFromCopy(open_num, F[5]), run_time=1.0)
        self.play(Write(VGroup(F[7], F[8])), run_time=0.6)
        L2 = Tex("divide by the ", f"{n5} still open", ", not by ", "100", font_size=FS_LABEL, color=INK)
        L2[1].set_color(OPEN)
        L2[3].set_color(MUTED)
        L2.next_to(F, DOWN, buff=0.45)
        self.play(FadeIn(L2, shift=UP * 0.1), run_time=0.8)
        self.wait(0.4)
        L3 = VGroup(Tex("close to the real value", font_size=FS_LABEL, color=MUTED),
                    MathTex("h_w(5)", "=", f"{hw5:.3f}", font_size=FS_LABEL + 5))
        L3[1][0].set_color(WON)
        L3.arrange(RIGHT, buff=0.22).next_to(L2, DOWN, buff=0.3)
        self.play(FadeIn(L3, shift=UP * 0.1), run_time=0.7)
        self.wait(2.8)
        self.play(clock.animate.set_value(T_AGE[6]), run_time=DUR[5], rate_func=linear)

        # ==================================================================
        # Beat 7 -- accelerate to age 45; the survival curve
        # ==================================================================
        ax = make_axes([0, 45, 5], [0, 1, 0.5], CH_W, CH_H)
        ax.shift(np.array([CH_X0, CH_Y0, 0.0]) - ax.c2p(0, 0))
        ticks = tick_labels(ax, x_values=[0, 15, 30, 45], y_values=[0.5, 1])
        x_title = Tex("age (business days)", font_size=FS_LABEL, color=MUTED)
        x_title.next_to(ticks[0], DOWN, buff=0.12).set_x(ax.c2p(22.5, 0)[0])
        y_title = Tex("share still open", font_size=FS_LABEL, color=MUTED).rotate(PI / 2)
        y_title.next_to(ticks[1], LEFT, buff=0.15).set_y(ax.c2p(0, 0.5)[1])
        s_full = curve(ax, AGES, SURV, SURVIVAL, stroke_width=4, smooth=False)
        s_trace = s_full.copy()
        s_trace.pointwise_become_partial(s_full, 0, 1e-4)
        head = Dot(ax.c2p(0, 1), radius=0.07, color=SURVIVAL)
        draw_g = ValueTracker(0.0)
        follow = {"on": False}

        def upd_trace(m):
            gd = g_of(clock.get_value()) if follow["on"] else draw_g.get_value()
            m.pointwise_become_partial(s_full, 0, max(gd, 1e-4) / 45)
            head.move_to(ax.c2p(gd, float(np.interp(gd, AGES, SURV))))

        self.play(FadeOut(VGroup(rect, L0, F, L2, L3), run_time=0.8), FadeOut(cap, shift=UP * 0.12, run_time=0.4),
                  *[grid[s].animate(run_time=0.8).set_opacity(1.0) for s in before5],
                  Succession(Wait(0.3), Create(ax, run_time=1.0)),
                  Succession(Wait(0.5), FadeIn(VGroup(ticks, x_title, y_title), run_time=0.8)))
        cap = None
        s_trace.add_updater(upd_trace)
        self.add(s_trace, head)
        self.play(draw_g.animate.set_value(6.0), FadeIn(head), run_time=1.0)
        follow["on"] = True
        last_event = max(age_of.values())
        self.play(clock.animate.set_value(T_AGE[last_event + 1]), run_time=T_AGE[last_event + 1] - T_AGE[6],
                  rate_func=linear)
        # the tail (no more decisions): name the curve while the clock runs out
        s_name = VGroup(MathTex("S(a)", font_size=FS_FORMULA - 4, color=SURVIVAL),
                        Tex(r"share still open at age $a$", font_size=FS_LABEL, color=SURVIVAL))
        s_name.arrange(DOWN, buff=0.12)
        s_name.move_to([ax.c2p(29, 0)[0], ax.c2p(0, 0.82)[1], 0])
        tail = T_AGE[45] - T_AGE[last_event + 1]
        self.play(clock.animate(rate_func=linear, run_time=tail).set_value(T_AGE[45]),
                  FadeIn(s_name, shift=UP * 0.1, run_time=max(tail, 0.9)))
        s_trace.clear_updaters()
        grid.clear_updaters()
        age_num.clear_updaters()
        open_num.clear_updaters()
        self.wait(1.3)

        # ==================================================================
        # Beat 8 -- payoff: survival is a product
        # ==================================================================
        texts = VGroup(won_lab, lost_lab, age_counter, open_counter)
        trays = VGroup(won_tray, lost_tray)
        cap = caption(r"each day, multiply by the chance of staying open")
        self.play(grid.animate.set_opacity(0.3), texts.animate.set_opacity(0.3),
                  *[t.animate.set_fill(opacity=0.02).set_stroke(opacity=0.3) for t in trays],
                  Succession(Wait(0.3), FadeIn(cap, shift=UP * 0.12, run_time=0.6)), run_time=0.9)
        self.wait(1.0)

        def colour_s(f, s_idx, hw_idx, hl_idx):
            for i in s_idx:
                f[i].set_color(SURVIVAL)
            f[hw_idx].set_color(WON)
            f[hl_idx].set_color(LOST)

        f1 = MathTex("S(a+1)", "=", "S(a)", r"\,\bigl(1-", "h_w(a)", "-", r"h_\ell(a)", r"\bigr)",
                     font_size=FS_FORMULA)
        colour_s(f1, [0, 2], 4, 6)
        f1.move_to([2.6, 2.75, 0])
        self.play(Write(f1[0]), run_time=0.7)
        self.play(Write(VGroup(f1[1], f1[2])), run_time=0.7)
        self.play(Write(VGroup(*f1[3:])), run_time=1.0)
        self.wait(0.8)

        f2 = MathTex("S(a)", "=", r"\prod_{j<a}", r"\bigl(1-", "h_w(j)", "-", r"h_\ell(j)", r"\bigr)",
                     font_size=FS_FORMULA)
        colour_s(f2, [0], 4, 6)
        f2.move_to([3.4, 1.55, 0])
        f2.shift((f1[3].get_left()[0] - f2[3].get_left()[0]) * RIGHT)   # factors in the same columns
        self.play(Write(VGroup(f2[0], f2[1], f2[2])), run_time=0.8)
        # the daily factor drops out of the recursion into the chain (same columns, no crossing)
        self.play(*[TransformFromCopy(f1[i], f2[i]) for i in range(3, 8)], run_time=1.1)
        br2 = Brace(VGroup(*f2[3:]), DOWN, buff=0.1, color=MUTED)
        br2_lab = Tex(r"chance to stay open on day $j$", font_size=FS_LABEL, color=INK).next_to(br2, DOWN, buff=0.1)
        self.play(GrowFromCenter(br2), FadeIn(br2_lab, shift=UP * 0.1), run_time=0.9)
        self.wait(4.0)

        # ==================================================================
        # Beat 9 -- end state
        # ==================================================================
        won_cnt = Tex(f"won: {int(CO.won_total)}", font_size=FS_LABEL, color=WON).move_to(won_lab, aligned_edge=LEFT)
        lost_cnt = Tex(f"lost: {int(CO.lost_total)}", font_size=FS_LABEL, color=LOST).move_to(lost_lab, aligned_edge=LEFT)
        end_pt = ax.c2p(45, SURV[45])
        s45 = MathTex(f"{SURV[45]:.2f}", font_size=FS_LABEL, color=SURVIVAL).next_to(end_pt, UP, buff=0.15)
        self.play(grid.animate.set_opacity(1.0), VGroup(age_counter, open_counter).animate.set_opacity(1.0),
                  *[t.animate.set_fill(opacity=0.06).set_stroke(opacity=1.0) for t in trays],
                  ReplacementTransform(won_lab, won_cnt), ReplacementTransform(lost_lab, lost_cnt),
                  FadeIn(s45, shift=DOWN * 0.1),
                  FadeOut(cap, shift=UP * 0.12, run_time=0.4), run_time=1.1)
        cap = swap_caption(self, None, rf"after 45 business days: {int(CO.won_total)} won, "
                                       rf"{int(CO.lost_total)} lost, {int(CO.open_end)} open")
        self.wait(2.4)

        # ==================================================================
        # Beat 10 -- takeaway
        # ==================================================================
        takeaway(self, r"survival is a chain of daily ``still open'' chances", SURVIVAL, old_caption=cap)
        close_chapter(self)
