"""Chapter 04 -- Learning the rates from history.

The daily win and loss chances are estimated from the last 60 business days:
line the deals up by age, count at every age the deals at risk r(a) and the
deals won w(a) / lost l(a) at exactly that age, and divide (with alpha
smoothing). Still-open (censored) deals count as at risk up to their current
age. Chaining the hazards gives the survival S(a): a life-table estimator with
two competing outcomes. Every count matches estimate_kernel_from_training.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import *

D = load_data()
K = D.kernel
SAMPLE = D.training.sample
ALPHA = float(D.meta.smoothing_alpha)
AGES = np.arange(46)

# ---- geometry ----------------------------------------------------------------
X0, U = -5.9, 0.145                 # age a -> x = X0 + U * a (one shared age axis)
XL = X0 - 0.5 * U                   # left edge of every plot (y-axes sit here)


def X(a):
    return X0 + U * a


def XC(c):
    """Calendar day c (-59 .. 0, 0 = today) on the same scale as age."""
    return X0 + (c + 59) * U


XR = X(45) + 0.5 * U                # right end of the age axis
ROW_TOP, ROW_DY = 2.72, 0.128       # Gantt rows (36 deals, oldest on top)
AX_Y = -2.02                        # shared age axis = baseline of the lower chart
R_BASE, R_H, R_MAX = 0.12, 2.5, 750.0     # upper chart: r(a), later S(a)
WL_H, WL_MAX = 1.4, 50.0                  # lower chart: w(a), l(a)
H_MAX = 0.11                              # lower chart after the division: hazards
UY_R, UY_WL, UY_H = R_H / R_MAX, WL_H / WL_MAX, WL_H / H_MAX
PX = 3.95                           # centre of the right-hand panel (x 1.2 .. 6.7)
LOST_TXT = interpolate_color(ManimColor(LOST), ManimColor(INK), 0.3)   # slate, legible as text
LINE_OP = 0.6                       # closed deal lines
SLIDE = rate_functions.ease_in_out_sine


# ---- small builders ------------------------------------------------------------
def hline(x0, x1, y, color=MUTED, width=2):
    return Line([x0, y, 0], [x1, y, 0], color=color, stroke_width=width)


def x_tick(x, y, text):
    mark = Line([x, y, 0], [x, y - 0.08, 0], color=MUTED, stroke_width=2)
    lab = MathTex(text, font_size=FS_TICK, color=MUTED).next_to(mark, DOWN, buff=0.1)
    return VGroup(mark, lab)


def y_tick(y, text):
    mark = Line([XL, y, 0], [XL - 0.08, y, 0], color=MUTED, stroke_width=2)
    lab = MathTex(text, font_size=FS_TICK, color=MUTED).next_to(mark, LEFT, buff=0.08)
    return VGroup(mark, lab)


def rect(xc, y0, h, w, color, op=0.92):
    h = max(h, 1e-3)
    r = Rectangle(width=w, height=h, stroke_width=0, fill_color=color, fill_opacity=op)
    r.move_to([xc, y0 + h / 2, 0])
    return r


def chevron(tip, s=1.0, color=OPEN, width=3.0):
    tip = np.array(tip, dtype=float)
    c = VMobject(stroke_color=color, stroke_width=width)
    c.set_points_as_corners([tip + np.array([-0.085, 0.06, 0]) * s, tip, tip + np.array([-0.085, -0.06, 0]) * s])
    return c


def series_label(sym, words, color, sym_color=None):
    s = MathTex(sym, font_size=FS_LABEL + 5, color=sym_color or color)
    w = Tex(words, font_size=FS_LABEL, color=INK)
    return VGroup(s, w).arrange(RIGHT, buff=0.16)


def r_bars_at(values, color=OPEN):
    return VGroup(*[rect(X(a), R_BASE, v * UY_R, 0.8 * U, color) for a, v in enumerate(values)])


def pair_bars(win_vals, loss_vals, scale):
    w = VGroup(*[rect(X(a) - 0.21 * U, AX_Y, v * scale, 0.4 * U, WON) for a, v in enumerate(win_vals)])
    l = VGroup(*[rect(X(a) + 0.21 * U, AX_Y, v * scale, 0.4 * U, LOST) for a, v in enumerate(loss_vals)])
    return w, l


def swap_with(scene, old, text, *anims, run_time=0.8):
    """swap_caption, with other exits (dimming, panels leaving) riding along on
    the old caption's way out; the new caption still arrives only afterwards."""
    new = caption(text)
    scene.play(FadeOut(old, shift=UP * 0.12, rate_func=delayed(0.0, 0.5)), *anims, run_time=run_time)
    scene.play(FadeIn(new, shift=UP * 0.12), run_time=0.6)
    return new


class Clip(Scene):
    def construct(self):
        n = len(SAMPLE)
        cs = np.array([s["created_rel"] for s in SAMPLE])
        es = np.array([s["end_age"] for s in SAMPLE])
        st = [s["status"] for s in SAMPLE]
        rows_y = ROW_TOP - np.arange(n) * ROW_DY

        # ==================================================================
        # 1. Ask
        # ==================================================================
        header = open_chapter(self, 4, "Learning the rates from history", KERNEL,
                              question="How do we measure these daily chances from past deals?",
                              part=PART[2])

        # ==================================================================
        # 2. History: 36 real deals in calendar time
        # ==================================================================
        cal_axis = hline(XL, XC(0) + 0.5 * U, AX_Y)
        cal_ticks = VGroup(*[x_tick(XC(c), AX_Y, f"{c}") for c in (-50, -40, -30, -20, -10, 0)])
        cal_title = Tex("business days before today", font_size=FS_LABEL, color=MUTED)
        cal_title.next_to(cal_ticks, DOWN, buff=0.16).set_x(0.5 * (XL + XC(0)))
        today = DashedLine([XC(0), AX_Y, 0], [XC(0), ROW_TOP + 0.16, 0], color=INK, stroke_width=2,
                           dash_length=0.08, stroke_opacity=0.7)
        today_lab = Tex("today", font_size=FS_LABEL, color=INK).next_to(today, UP, buff=0.1)

        lines, marks = [], []
        for i in range(n):
            y = rows_y[i]
            x0, x1 = XC(cs[i]), XC(cs[i] + es[i])
            if st[i] == "open":
                lines.append(Line([x0, y, 0], [x1, y, 0], color=OPEN, stroke_width=3.5))
                marks.append(chevron([x1 + 0.07, y, 0]))
            else:
                lines.append(Line([x0, y, 0], [x1, y, 0], color=INK, stroke_width=3, stroke_opacity=LINE_OP))
                marks.append(Dot([x1, y, 0], radius=0.055, color=WON if st[i] == "won" else LOST))

        leg_open = VGroup(VGroup(Line(LEFT * 0.2, RIGHT * 0.1, color=OPEN, stroke_width=3.5),
                                 chevron(RIGHT * 0.17)),
                          Tex("still open", font_size=FS_LABEL))
        leg_open.arrange(RIGHT, buff=0.16)
        legend = VGroup(legend_item("won", WON), legend_item("lost", LOST), leg_open)
        legend.arrange(DOWN, aligned_edge=LEFT, buff=0.24).move_to([4.75, 1.55, 0], aligned_edge=LEFT)
        legend.set_x(3.45, direction=LEFT)

        self.play(Create(cal_axis), FadeIn(cal_ticks), FadeIn(cal_title), Create(today), FadeIn(today_lab),
                  run_time=1.0)
        self.play(LaggedStart(*[Create(l) for l in lines], lag_ratio=0.05), run_time=2.5)
        self.play(LaggedStart(*[GrowFromCenter(m) if isinstance(m, Dot) else Create(m) for m in marks],
                              lag_ratio=0.02),
                  FadeIn(legend, shift=LEFT * 0.15), run_time=0.9)
        wc = D.training.window_counts
        n_window = int(wc.won + wc.lost + wc.open)
        cap = swap_caption(self, None, rf"the last {int(D.meta.training_window)} business days: "
                                       rf"{n} of {n_window} deals")
        self.wait(2.5)

        # ==================================================================
        # 3. Forget the calendar, keep only age
        # ==================================================================
        age_axis = hline(XL, XR, AX_Y)
        age_ticks = VGroup(*[x_tick(X(a), AX_Y, f"{a}") for a in range(0, 46, 5)])
        age_title = Tex("age (business days)", font_size=FS_LABEL, color=MUTED)
        age_title.next_to(age_ticks, DOWN, buff=0.16).set_x(0.5 * (XL + XR))

        cap = swap_caption(self, cap, "forget the calendar: every deal starts at age 0")
        self.wait(0.6)
        slide = []
        for i in range(n):
            d = LEFT * (cs[i] + 59) * U
            slide += [lines[i].animate(rate_func=SLIDE).shift(d), marks[i].animate(rate_func=SLIDE).shift(d)]
        self.play(*slide,
                  Transform(cal_axis, age_axis, rate_func=SLIDE),
                  FadeOut(VGroup(today, today_lab), rate_func=delayed(0.0, 0.3)),
                  FadeOut(cal_ticks, rate_func=delayed(0.0, 0.35)),
                  FadeIn(age_ticks, rate_func=delayed(0.6, 0.4)),
                  FadeOut(cal_title, shift=LEFT * 0.4, rate_func=delayed(0.0, 0.4)),
                  FadeIn(age_title, shift=LEFT * 0.4, rate_func=delayed(0.55, 0.45)),
                  run_time=2.8)
        self.wait(1.0)

        # ==================================================================
        # 4. Censoring: still-open deals
        # ==================================================================
        is_open = [s == "open" for s in st]
        closed_l = VGroup(*[lines[i] for i in range(n) if not is_open[i]])
        closed_m = VGroup(*[marks[i] for i in range(n) if not is_open[i]])
        open_l = VGroup(*[lines[i] for i in range(n) if is_open[i]])
        open_m = VGroup(*[marks[i] for i in range(n) if is_open[i]])

        cap = swap_caption(self, cap, "unfinished deals still teach us something")
        self.play(closed_l.animate.set_stroke(opacity=0.18), closed_m.animate.set_opacity(0.22),
                  open_l.animate.set_stroke(width=4.6), open_m.animate.set_stroke(width=4.0),
                  FadeOut(legend), run_time=0.9)
        card = definition_card("Censored", ["still open: we know it survived", "to this age, not how it ends"], OPEN)
        card.move_to([PX, 2.0, 0])
        self.play(FadeIn(card, shift=UP * 0.15), run_time=0.9)
        # callout from the end of one still-open line into the panel
        i30 = [i for i in range(n) if is_open[i] and es[i] == 30][0]
        p = np.array([X(30) + 0.17, rows_y[i30], 0])
        lead_end = np.array([1.35, rows_y[i30], 0])
        c_dot = Dot(p, radius=0.045, color=INK)
        c_line = Line(p, lead_end, color=INK, stroke_width=1.6)
        c_txt = VGroup(Tex("just counting outcomes would", font_size=FS_LABEL),
                       Tex(rf"ignore {int(wc.open)} unfinished deals", font_size=FS_LABEL))
        c_txt.arrange(DOWN, aligned_edge=LEFT, buff=0.12).next_to(lead_end, RIGHT, buff=0.14)
        self.play(FadeIn(c_dot), Create(c_line), FadeIn(c_txt, shift=RIGHT * 0.1), run_time=0.9)
        self.wait(3.2)
        restore = [FadeOut(card), FadeOut(VGroup(c_dot, c_line, c_txt)),
                   closed_l.animate.set_stroke(opacity=LINE_OP), closed_m.animate.set_opacity(1.0),
                   open_l.animate.set_stroke(width=3.5), open_m.animate.set_stroke(width=3.0)]

        # ==================================================================
        # 5. Counting at one age (a = 5)
        # ==================================================================
        A0 = 5
        risk = [i for i in range(n) if es[i] >= A0]
        gone = [i for i in range(n) if es[i] < A0]
        won5 = [i for i in range(n) if es[i] == A0 and st[i] == "won"]
        lost5 = [i for i in range(n) if es[i] == A0 and st[i] == "lost"]
        n_risk, n_won5, n_lost5 = len(risk), len(won5), len(lost5)
        r5, w5, l5 = int(K.at_risk[A0]), int(K.wins[A0]), int(K.losses[A0])

        cap = swap_with(self, cap, "start with one age: the deals open at age 5", *restore, run_time=0.9)
        self.wait(0.9)
        scan = DashedLine([X(A0), AX_Y, 0], [X(A0), ROW_TOP + 0.13, 0], color=INK, stroke_width=2.5,
                          dash_length=0.07)
        tick5 = age_ticks[1][1]
        self.play(Create(scan), tick5.animate.set_color(INK).scale(1.25), run_time=1.0)
        cross = VGroup(*[Dot([X(A0), rows_y[i], 0], radius=0.034, color=INK)
                         for i in risk if i not in won5 + lost5])
        self.play(VGroup(*[lines[i] for i in gone]).animate.set_stroke(opacity=0.14),
                  VGroup(*[marks[i] for i in gone]).animate.set_opacity(0.18),
                  VGroup(*[lines[i] for i in risk if not is_open[i]]).animate.set_stroke(opacity=0.9),
                  LaggedStart(*[GrowFromCenter(d) for d in cross], lag_ratio=0.04),
                  run_time=1.1)

        def count_row(num, words, color, num_size=FS_BODY + 6):
            a = MathTex(num, font_size=num_size, color=color)
            b = Tex(words, font_size=FS_BODY - 2, color=INK)
            return a, b

        def panel_box(height):
            return RoundedRectangle(width=5.1, height=height, corner_radius=0.14, fill_color=PANEL,
                                   fill_opacity=0.96, stroke_color=PANEL_EDGE, stroke_width=1.5)

        # sample block
        s_head = Tex(rf"in this sample of {n} deals, at age {A0}", font_size=FS_LABEL, color=MUTED)
        s_rows = [count_row(f"{n_risk}", "at risk", OPEN),
                  count_row(f"{n_won5}", f"won at age {A0}", WON),
                  count_row(f"{n_lost5}", f"lost at age {A0}", LOST_TXT)]
        s_box = panel_box(2.0).move_to([PX, 1.92, 0]).set_z_index(-1)
        s_head.move_to(s_box.get_top() + DOWN * 0.34).align_to(s_box, LEFT).shift(RIGHT * 0.3)
        for k, (a, b) in enumerate(s_rows):
            y = s_box.get_top()[1] - 0.82 - 0.43 * k
            a.move_to([PX - 1.55, y, 0], aligned_edge=RIGHT)
            b.next_to(a, RIGHT, buff=0.25)
            b.align_to(np.array([PX - 1.3, 0, 0]), LEFT)
            b.set_y(y)
        self.play(FadeIn(s_box), FadeIn(s_head), FadeIn(s_rows[0][0], scale=0.8), FadeIn(s_rows[0][1]),
                  cross.animate.set_color(OPEN), run_time=1.0)
        self.wait(0.6)
        flashes = [Flash(marks[i], color=WON, line_length=0.12, flash_radius=0.13, num_lines=10) for i in won5]
        flashes += [Flash(marks[i], color=LOST, line_length=0.12, flash_radius=0.13, num_lines=10) for i in lost5]
        self.play(*flashes, *[marks[i].animate.scale(1.35) for i in won5 + lost5],
                  FadeIn(VGroup(*s_rows[1]), shift=RIGHT * 0.1, rate_func=delayed(0.3, 0.7)),
                  FadeIn(VGroup(*s_rows[2]), shift=RIGHT * 0.1, rate_func=delayed(0.3, 0.7)), run_time=1.2)
        self.wait(1.2)

        # every deal in the window
        f_head = Tex(rf"all deals in the window, at age {A0}", font_size=FS_LABEL, color=INK)
        f_rows = [count_row(rf"r({A0}) = {r5}", "at risk", OPEN),
                  count_row(rf"w({A0}) = {w5}", f"won at age {A0}", WON),
                  count_row(rf"\ell({A0}) = {l5}", f"lost at age {A0}", LOST_TXT)]
        f_box = panel_box(2.0).move_to([PX, -0.42, 0]).set_z_index(-1)
        f_head.move_to(f_box.get_top() + DOWN * 0.34).align_to(f_box, LEFT).shift(RIGHT * 0.3)
        for k, (a, b) in enumerate(f_rows):
            y = f_box.get_top()[1] - 0.82 - 0.43 * k
            a.move_to([PX + 0.2, y, 0], aligned_edge=RIGHT)
            b.next_to(a, RIGHT, buff=0.25).set_y(y)
        note = VGroup(Tex("these also count older deals that entered", font_size=FS_TICK + 1, color=MUTED),
                      Tex("the window already aged", font_size=FS_TICK + 1, color=MUTED))
        note.arrange(DOWN, aligned_edge=LEFT, buff=0.1).next_to(f_box, DOWN, buff=0.2).align_to(f_box, LEFT)
        note.shift(RIGHT * 0.3)
        self.play(FadeIn(VGroup(f_box, f_head), rate_func=delayed(0.0, 0.35)),
                  *[TransformFromCopy(s_rows[k][0], f_rows[k][0], rate_func=delayed(0.15, 0.85)) for k in range(3)],
                  *[FadeIn(f_rows[k][1], shift=RIGHT * 0.1, rate_func=delayed(0.4, 0.6)) for k in range(3)],
                  run_time=1.8)
        self.wait(0.3)
        self.play(FadeIn(note), run_time=0.7)
        self.wait(2.3)

        # ==================================================================
        # 6. Every age: the Gantt becomes the count charts
        # ==================================================================
        cap = swap_with(self, cap, "count at every age, for all deals in the window",
                        FadeOut(VGroup(s_box, s_head, *[m for r in s_rows for m in r])),
                        FadeOut(VGroup(f_box, f_head, *[m for r in f_rows for m in r], note)),
                        FadeOut(cross), FadeOut(scan), tick5.animate.set_color(MUTED).scale(1 / 1.25),
                        VGroup(*[lines[i] for i in gone]).animate.set_stroke(opacity=LINE_OP),
                        VGroup(*[marks[i] for i in gone]).animate.set_opacity(1.0),
                        VGroup(*[lines[i] for i in risk if not is_open[i]]).animate.set_stroke(opacity=LINE_OP),
                        *[marks[i].animate.scale(1 / 1.35) for i in won5 + lost5], run_time=0.9)
        self.wait(0.5)

        # sort (longest at the bottom) and compress into the upper chart
        order = sorted(range(n), key=lambda i: (-es[i], cs[i]))
        rank = {i: k for k, i in enumerate(order)}
        slot = R_H * (float(K.at_risk[0]) / R_MAX) / n
        ys = {i: R_BASE + (rank[i] + 0.5) * slot for i in range(n)}
        squeeze = []
        for i in range(n):
            y = ys[i]
            tgt = Line([X(0), y, 0], [X(es[i]), y, 0], stroke_width=2.2,
                       color=OPEN if is_open[i] else INK, stroke_opacity=1.0 if is_open[i] else LINE_OP)
            squeeze.append(Transform(lines[i], tgt))
            if is_open[i]:
                squeeze.append(Transform(marks[i], chevron([X(es[i]) + 0.06, y, 0], s=0.6, width=2.2)))
            else:
                squeeze.append(marks[i].animate.move_to([X(es[i]), y, 0]).scale(0.62))
        self.play(*squeeze, run_time=2.0, rate_func=rate_functions.ease_in_out_sine)
        self.wait(0.2)

        # lower chart: outcomes drop out of the stack and become w(a), l(a)
        wl_yaxis = Line([XL, AX_Y, 0], [XL, AX_Y + WL_H, 0], color=MUTED, stroke_width=2)
        wl_ticks = VGroup(y_tick(AX_Y + 25 * UY_WL, "25"), y_tick(AX_Y + 50 * UY_WL, "50"))
        w_bars, l_bars = pair_bars(K.wins, K.losses, UY_WL)
        fall, grow = [], []
        for kind, bars_, vals in (("won", w_bars, K.wins), ("lost", l_bars, K.losses)):
            for a in AGES:
                ids = sorted([i for i in range(n) if st[i] == kind and es[i] == a], key=lambda i: rank[i])
                m = len(ids)
                bar = bars_[a]
                if m == 0:
                    if vals[a] > 0:
                        grow.append((bar, DOWN))
                    continue
                h = vals[a] * UY_WL
                for j, i in enumerate(ids):
                    sl = rect(bar.get_x(), AX_Y + j * h / m, h / m, bar.width, WON if kind == "won" else LOST)
                    fall.append((marks[i], sl, bar))
        w_lab = series_label("w(a)", r"deals won at age $a$", WON)
        l_lab = series_label(r"\ell(a)", r"deals lost at age $a$", LOST_TXT)
        wl_labs = VGroup(w_lab, l_lab).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
        wl_labs.move_to([X(21), AX_Y + WL_H - 0.36, 0], aligned_edge=LEFT)
        self.play(*[d.animate(rate_func=rate_functions.ease_in_quad).move_to(sl.get_center()).scale(0.85)
                    for d, sl, _ in fall],
                  Create(wl_yaxis), FadeIn(wl_ticks), run_time=1.3)
        self.play(*[ReplacementTransform(d, sl) for d, sl, _ in fall],
                  *[GrowFromEdge(*g) for g in grow],
                  FadeIn(wl_labs, shift=LEFT * 0.1, rate_func=delayed(0.5, 0.5)),
                  run_time=1.6)
        # swap the slices for clean single bars (identical picture)
        self.remove(*[sl for _, sl, _ in fall])
        self.add(w_bars, l_bars)
        self.wait(0.4)

        # upper chart: the stacked lifelines become r(a)
        r_bars = r_bars_at(K.at_risk)
        cells_anims, cell_list = [], []
        n_at = [(es >= a).sum() for a in AGES]
        for i in range(n):
            e, y = es[i], ys[i]
            col = OPEN if is_open[i] else INK
            op = 1.0 if is_open[i] else LINE_OP
            for a in range(e + 1):
                xa, xb = max(X(a) - U / 2, X(0)), min(X(a) + U / 2, X(e))
                cell = Line([xa, y, 0], [xb, y, 0], color=col, stroke_width=2.2, stroke_opacity=op)
                h = K.at_risk[a] * UY_R
                k = rank[i]
                sl = rect(X(a), R_BASE + k * h / n_at[a], h / n_at[a], 0.8 * U, OPEN)
                cell_list.append(cell)
                cells_anims.append(ReplacementTransform(cell, sl, rate_func=delayed(0.0, 0.8, SLIDE)))
        self.remove(*lines)
        self.add(*cell_list)
        r_axis = VGroup(hline(XL, XR, R_BASE), Line([XL, R_BASE, 0], [XL, R_BASE + R_H, 0], color=MUTED, stroke_width=2))
        r_ticks = VGroup(y_tick(R_BASE + 350 * UY_R, "350"), y_tick(R_BASE + 700 * UY_R, "700"))
        r_lab = series_label("r(a)", "deals at risk", OPEN)
        r_lab.move_to([X(21), R_BASE + R_H * 0.66, 0], aligned_edge=LEFT)
        self.play(*cells_anims, GrowFromEdge(r_bars[45], DOWN, rate_func=delayed(0.0, 0.8, SLIDE)),
                  FadeOut(VGroup(*[marks[i] for i in range(n) if is_open[i]]), rate_func=delayed(0.0, 0.35)),
                  Create(r_axis, rate_func=delayed(0.0, 0.5)), FadeIn(r_ticks, rate_func=delayed(0.4, 0.4)),
                  FadeIn(r_lab, shift=LEFT * 0.1, rate_func=delayed(0.7, 0.3)),
                  run_time=2.7)
        self.remove(*[a.target_mobject for a in cells_anims])
        self.add(r_bars)
        self.wait(1.5)

        # ==================================================================
        # 7. The estimator: one age first, then every age
        # ==================================================================
        cap = swap_caption(self, cap, "divide the outcomes by the deals at risk")
        self.wait(0.9)
        ev = MathTex(rf"h_w({A0})", "=", r"\frac{", f"{w5}", f"+{ALPHA:g}", "}{", f"{r5}", f"+{2 * ALPHA:g}", "}",
                     "=", f"{K.win_hazard[A0]:.3f}", font_size=40)
        ev[0].set_color(WON)
        ev[3].set_color(WON)
        ev[6].set_color(OPEN)
        ev[10].set_color(WON)
        ev.move_to([PX, 2.36, 0])
        box_w = SurroundingRectangle(w_bars[A0], color=WON, buff=0.05, corner_radius=0.05, stroke_width=2)
        box_r = SurroundingRectangle(r_bars[A0], color=OPEN, buff=0.05, corner_radius=0.05, stroke_width=2)
        self.play(Create(box_w), Create(box_r), Write(VGroup(ev[0], ev[1])), Create(ev[5]), run_time=1.0)
        self.play(TransformFromCopy(w_bars[A0], ev[3]), run_time=1.1)
        self.play(TransformFromCopy(r_bars[A0], ev[6]), run_time=1.1)
        self.play(FadeIn(VGroup(ev[4], ev[7]), shift=DOWN * 0.05, rate_func=delayed(0.0, 0.5)),
                  Write(VGroup(ev[9], ev[10]), rate_func=delayed(0.4, 0.6)), run_time=1.3)
        per100 = int(round(100 * K.win_hazard[A0]))
        ev_words = VGroup(Tex(rf"win hazard at age {A0}: about {per100} in 100", font_size=FS_LABEL, color=INK),
                          Tex(rf"open deals aged {A0} win that day", font_size=FS_LABEL, color=INK))
        ev_words.arrange(DOWN, aligned_edge=LEFT, buff=0.12).next_to(ev, DOWN, buff=0.32)
        ev_words[0][0][:9].set_color(WON)
        self.play(FadeIn(ev_words, shift=UP * 0.08), run_time=0.8)
        self.wait(1.3)

        a_card = definition_card(rf"$\alpha = {ALPHA:g}$", ["a quarter of a pseudo-deal:", "keeps rare ages away from exactly 0"], INK)
        a_card.next_to(ev_words, DOWN, buff=0.45).set_x(PX)
        self.play(FadeIn(a_card, shift=UP * 0.15), run_time=0.8)
        self.wait(3.7)

        # generalise: the numbers at age 5 become the symbols for every age
        fw = MathTex(r"h_w(a)", "=", r"\frac{", "w(a)", "+", r"\alpha", "}{", "r(a)", "+", r"2\alpha", "}",
                     font_size=FS_FORMULA)
        fw[0].set_color(WON)
        fw[3].set_color(WON)
        fw[7].set_color(OPEN)
        fw.move_to([PX, 2.36, 0])
        fw_words = VGroup(Tex(r"win hazard: chance to win at age $a$,", font_size=FS_LABEL, color=INK),
                          Tex(r"among the deals still open at age $a$", font_size=FS_LABEL, color=INK))
        fw_words.arrange(DOWN, aligned_edge=LEFT, buff=0.12).next_to(fw, DOWN, buff=0.32)
        fw_words[0][0][:10].set_color(WON)
        fl_words = Tex(r"loss hazard $h_\ell(a)$: the same with $\ell(a)$", font_size=FS_LABEL, color=INK)
        fl_words.next_to(fw_words, DOWN, buff=0.3).align_to(fw_words, LEFT)
        fl_words[0][:15].set_color(LOST_TXT)
        fl_words[0][-4:].set_color(LOST_TXT)
        self.play(FadeOut(a_card, rate_func=delayed(0.0, 0.3)), FadeOut(VGroup(box_w, box_r), rate_func=delayed(0.0, 0.3)),
                  ReplacementTransform(ev[0], fw[0]), ReplacementTransform(ev[1], fw[1]),
                  ReplacementTransform(ev[3], fw[3]), ReplacementTransform(ev[4], VGroup(fw[4], fw[5])),
                  ReplacementTransform(ev[5], fw[6]), ReplacementTransform(ev[6], fw[7]),
                  ReplacementTransform(ev[7], VGroup(fw[8], fw[9])),
                  FadeOut(VGroup(ev[9], ev[10]), shift=RIGHT * 0.2),
                  FadeOut(ev_words, rate_func=delayed(0.0, 0.4)),
                  FadeIn(fw_words, rate_func=delayed(0.55, 0.45)),
                  run_time=2.1)
        self.wait(0.9)
        self.play(FadeIn(fl_words, shift=UP * 0.08), run_time=0.8)
        self.wait(1.2)

        # the division sweeps across every age: counts -> hazards
        hw_bars, hl_bars = pair_bars(K.win_hazard, K.loss_hazard, UY_H)
        h_ticks = VGroup(y_tick(AX_Y + 0.05 * UY_H, "0.05"), y_tick(AX_Y + 0.10 * UY_H, "0.10"))
        h_title = Tex("chance per day", font_size=FS_TICK + 1, color=MUTED)
        h_title.next_to([XL, AX_Y + WL_H, 0], UP, buff=0.14).align_to(np.array([XL - 0.5, 0, 0]), LEFT)
        hw_lab = series_label("h_w(a)", "win hazard", WON)
        hl_lab = series_label(r"h_\ell(a)", "loss hazard", LOST_TXT)
        h_labs = VGroup(hw_lab, hl_lab).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
        h_labs.move_to(wl_labs, aligned_edge=LEFT)
        band = Rectangle(width=U * 1.1, height=R_BASE + R_H - AX_Y + 0.1, stroke_width=0,
                         fill_color=INK, fill_opacity=0.10)
        band.move_to([X(0), 0.5 * (AX_Y + R_BASE + R_H), 0])
        self.play(FadeIn(band), run_time=0.4)
        L = 0.12
        sweep = []
        for a in AGES:
            s0 = (1 - L) * a / 45
            sweep += [Transform(w_bars[a], hw_bars[a], rate_func=delayed(s0, L)),
                      Transform(l_bars[a], hl_bars[a], rate_func=delayed(s0, L))]
        self.play(*sweep, band.animate(rate_func=linear).set_x(X(45)),
                  FadeOut(wl_ticks, rate_func=delayed(0.0, 0.12)), FadeIn(h_ticks, rate_func=delayed(0.1, 0.15)),
                  FadeOut(wl_labs, shift=UP * 0.1, rate_func=delayed(0.0, 0.12)),
                  FadeIn(h_labs, shift=UP * 0.1, rate_func=delayed(0.1, 0.15)),
                  FadeIn(h_title, rate_func=delayed(0.0, 0.25)),
                  run_time=3.2)
        self.play(FadeOut(band), run_time=0.4)
        self.wait(2.4)

        # ==================================================================
        # 8. Survival from the hazards
        # ==================================================================
        s_ticks = VGroup(y_tick(R_BASE + 0.5 * R_H, "0.5"), y_tick(R_BASE + 1.0 * R_H, "1"))
        s_lab = series_label("S(a)", "survival: share still open", OPEN)
        s_lab.move_to(r_lab, aligned_edge=LEFT)
        haz = VGroup(*w_bars, *l_bars)
        cap = swap_with(self, cap, "chain the daily chances into survival",
                        FadeOut(fw_words), FadeOut(fl_words), fw.animate.set_opacity(0.5),
                        FadeOut(r_bars), FadeOut(r_ticks, rate_func=delayed(0.0, 0.5)),
                        FadeIn(s_ticks, rate_func=delayed(0.4, 0.6)),
                        FadeOut(r_lab, shift=UP * 0.1, rate_func=delayed(0.0, 0.5)),
                        FadeIn(s_lab, shift=UP * 0.1, rate_func=delayed(0.4, 0.6)),
                        haz.animate.set_opacity(0.4), run_time=1.2)
        fs = MathTex(r"S(a)", "=", r"\prod_{j<a}", r"\bigl(1-", r"h_w(j)", "-", r"h_\ell(j)", r"\bigr)",
                     font_size=38)
        fs[0].set_color(OPEN)
        fs[4].set_color(WON)
        fs[6].set_color(LOST_TXT)
        fs.move_to([PX, 0.75, 0])
        if fs.get_right()[0] > 6.65:
            fs.shift(LEFT * (fs.get_right()[0] - 6.65))
        self.wait(0.4)
        self.play(Write(VGroup(fs[0], fs[1], fs[2], fs[3], fs[5], fs[7])), run_time=1.1)
        self.play(TransformFromCopy(hw_lab[0], fs[4]), TransformFromCopy(hl_lab[0], fs[6]), run_time=1.2)
        fs_words = VGroup(Tex(r"survival: chance a new deal is", font_size=FS_LABEL, color=INK),
                          Tex(r"still open at age $a$", font_size=FS_LABEL, color=INK))
        fs_words.arrange(DOWN, aligned_edge=LEFT, buff=0.12).next_to(fs, DOWN, buff=0.28)
        fs_words.align_to(fs, LEFT).shift(RIGHT * 0.05)
        fs_words[0][0][:9].set_color(OPEN)
        self.play(FadeIn(fs_words, shift=UP * 0.08), run_time=0.7)
        self.wait(1.0)

        pts = [np.array([X(a), R_BASE + K.survival[a] * R_H, 0]) for a in AGES]
        t = ValueTracker(0.0)

        def partial_curve():
            tv = t.get_value()
            k = int(np.floor(tv))
            ps = pts[:k + 1]
            if k < 45:
                f = tv - k
                ps = ps + [pts[k] + (pts[k + 1] - pts[k]) * f]
            if len(ps) < 2:
                ps = [pts[0], pts[0] + RIGHT * 1e-3]
            c = VMobject(stroke_color=OPEN, stroke_width=4)
            c.set_points_as_corners(ps)
            return c

        s_curve = always_redraw(partial_curve)
        tip = always_redraw(lambda: Dot(partial_curve().get_end(), radius=0.06, color=OPEN))
        band2 = Rectangle(width=U * 1.1, height=R_BASE + R_H - AX_Y + 0.1, stroke_width=0,
                          fill_color=INK, fill_opacity=0.10)
        band2.add_updater(lambda m: m.move_to([X(min(t.get_value(), 45)), 0.5 * (AX_Y + R_BASE + R_H), 0]))

        def light(m):
            tv = t.get_value()
            for a in AGES:
                op = 0.95 if a <= tv else 0.4
                w_bars[a].set_fill(opacity=op)
                l_bars[a].set_fill(opacity=op)

        haz.add_updater(light)
        self.add(band2, s_curve, tip)
        self.play(t.animate.set_value(45), run_time=3.6, rate_func=rate_functions.ease_in_out_sine)
        haz.clear_updaters()
        band2.clear_updaters()
        final_curve = partial_curve()
        self.remove(s_curve, tip)
        self.add(final_curve)
        lt = VGroup(Tex(r"a life-table estimator (discrete Kaplan--Meier style)", font_size=FS_TICK + 2, color=MUTED),
                    Tex("with two competing outcomes", font_size=FS_TICK + 2, color=MUTED))
        lt.arrange(DOWN, aligned_edge=LEFT, buff=0.1).next_to(fs_words, DOWN, buff=0.4).align_to(fs_words, LEFT)
        self.play(FadeOut(band2), FadeIn(lt, shift=UP * 0.08), run_time=0.8)
        self.wait(2.6)

        # ==================================================================
        # 9. Takeaway
        # ==================================================================
        takeaway(self, "hazards use every day each deal was watched", KERNEL, old_caption=cap)
        close_chapter(self)
