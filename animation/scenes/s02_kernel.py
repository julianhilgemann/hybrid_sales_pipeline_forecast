import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import *

# --------------------------------------------------------------------------
# Chapter 02 -- The decision kernel
# --------------------------------------------------------------------------
X0, UNIT_X = -5.6, 0.25          # age a -> x = X0 + UNIT_X * a  (shared age axis)
AX_LEN = 45 * UNIT_X
BASE = -2.2                      # baseline of the bottom strip / pile / kernel
R_BASE, R_H = 0.30, 1.30         # at-risk strip
WL_H = 1.85                      # wins / losses strip height
S_BASE, S_H = 0.95, 1.50         # survival panel
TRACK_Y = 0.05                   # particle track
LOST_TXT = interpolate_color(ManimColor(LOST), ManimColor(INK), 0.35)

N_PART, N_COH = 600, 12          # particles, cohorts (50 per cohort)
SEED = 176                       # chosen so the won pile shows both modes
DOT_R, PITCH, HALF = 0.05, 0.11, 0.055
U1 = N_PART * PITCH / 2          # scene units per unit of probability in the pile


def X(a):
    return X0 + UNIT_X * a


def place(ax, base_y):
    ax.shift(np.array([X0, base_y, 0.0]) - ax.c2p(0, 0))
    return ax


def age_axes(y_range, y_len, base_y):
    return place(make_axes([0, 45, 5], y_range, AX_LEN, y_len), base_y)


def simulate(hw, hl):
    rng = np.random.default_rng(SEED)
    U = rng.random((N_PART, 46))
    outcome = np.zeros(N_PART, dtype=int)   # 0 open, 1 won, 2 lost
    age = np.full(N_PART, 45, dtype=int)
    for i in range(N_PART):
        for a in range(46):
            if U[i, a] < hw[a]:
                outcome[i], age[i] = 1, a
                break
            if U[i, a] < hw[a] + hl[a]:
                outcome[i], age[i] = 2, a
                break
    jitter = rng.uniform(-1, 1, size=(N_PART, 2))
    return outcome, age, jitter


def stepped(g):
    """Age shown on screen: hop one step at a time (half linear, half smooth)."""
    g = np.asarray(g, dtype=float)
    f = np.floor(g)
    r = g - f
    s = r * r * (3 - 2 * r)
    return f + 0.45 * r + 0.55 * s


def swap(old, new):
    """Caption change: fade the old one out, then the new one in (no ghosting)."""
    return Succession(FadeOut(old, run_time=0.4), FadeIn(new, run_time=0.5))


class Clip(Scene):
    def construct(self):
        D = load_data()
        K = D.kernel
        ages = np.arange(46)
        open_chapter(self, 2, "The decision kernel", KERNEL)

        # ==================================================================
        # Beat 2 -- forget the calendar, keep only age
        # ==================================================================
        lex = make_axes([0, 45, 15], [0, 25, 5], 6.75, 3.75)
        lex.shift(np.array([-3.4, -1.9, 0]) - lex.c2p(0, 0))
        lex_x = Tex("calendar time", font_size=FS_LABEL, color=MUTED).next_to(lex.x_axis, DOWN, buff=0.2)
        lex_y = Tex("age", font_size=FS_LABEL, color=MUTED).next_to(lex.y_axis, LEFT, buff=0.2)

        L = D.lifelines
        closed = [l for l in L if l["outcome"] in ("won", "lost") and l["ttc"] is not None
                  and 3 <= l["ttc"] <= 20 and -44 <= l["created_rel"] <= -l["ttc"] - 1]
        won = sorted([l for l in closed if l["outcome"] == "won"], key=lambda l: l["created_rel"])
        lost = sorted([l for l in closed if l["outcome"] == "lost"], key=lambda l: l["created_rel"])
        cens = sorted([l for l in L if l["outcome"] == "censored" and -22 <= l["created_rel"] <= -9],
                      key=lambda l: l["created_rel"])
        pick = ([won[int(i)] for i in np.linspace(0, len(won) - 1, 4)]
                + [lost[int(i)] for i in np.linspace(0, len(lost) - 1, 4)]
                + [cens[0], cens[-1]])
        lives = []
        for l in pick:
            c = l["created_rel"]
            a_end = l["ttc"] if l["ttc"] is not None else -c
            col = {"won": KERNEL, "lost": LOST, "censored": SURVIVAL}[l["outcome"]]
            lives.append((c, a_end, col))
        lives.sort(key=lambda v: v[0])

        lines, starts, ends = VGroup(), VGroup(), VGroup()
        for c, a_end, col in lives:
            p0, p1 = lex.c2p(c + 45, 0), lex.c2p(c + 45 + a_end, a_end)
            lines.add(Line(p0, p1, color=INK, stroke_width=2.5, stroke_opacity=0.75))
            starts.add(Dot(p0, radius=0.045, color=INK))
            ends.add(Dot(p1, radius=0.075, color=col))

        self.play(Create(lex), FadeIn(lex_x), FadeIn(lex_y), run_time=0.8)
        self.play(LaggedStart(*[Create(l) for l in lines], lag_ratio=0.12),
                  LaggedStart(*[FadeIn(d) for d in starts], lag_ratio=0.12),
                  run_time=1.3)
        self.play(LaggedStart(*[GrowFromCenter(d) for d in ends], lag_ratio=0.08), run_time=0.5)

        # shared age axis (bottom strip baseline)
        ax_wl = age_axes([0, 50, 25], WL_H, BASE)
        age_ticks = tick_labels(ax_wl, x_values=range(0, 46, 5))[0]
        age_title = Tex("age (business days)", font_size=FS_LABEL, color=MUTED)
        age_title.next_to(age_ticks, DOWN, buff=0.16).set_x(X(22.5))
        age_axis = ax_wl.x_axis

        cap1 = caption(r"forget the calendar --- keep only age")
        n = len(lives)
        rows_y = np.linspace(1.75, -1.0, n)
        row_lines = VGroup(*[Line([X(0), y, 0], [X(a), y, 0], color=INK, stroke_width=2.5, stroke_opacity=0.75)
                             for (c, a, col), y in zip(lives, rows_y)])
        self.play(
            *[Transform(lines[i], row_lines[i]) for i in range(n)],
            *[starts[i].animate.move_to(row_lines[i].get_start()) for i in range(n)],
            *[ends[i].animate.move_to(row_lines[i].get_end()) for i in range(n)],
            ReplacementTransform(lex.x_axis, age_axis),
            FadeOut(lex.y_axis), FadeOut(lex_y),
            ReplacementTransform(lex_x, age_title),
            FadeIn(age_ticks),
            FadeIn(cap1, shift=UP * 0.15),
            run_time=2.2,
        )
        self.wait(0.2)
        # every lifeline now travels left -> right along age: let them settle onto the axis
        self.play(
            *[lines[i].animate.move_to(row_lines[i].get_center() + (BASE - rows_y[i]) * UP).set_stroke(opacity=0)
              for i in range(n)],
            *[starts[i].animate.move_to([X(0), BASE, 0]).set_opacity(0) for i in range(n)],
            *[ends[i].animate.move_to([X(lives[i][1]), BASE, 0]) for i in range(n)],
            run_time=1.3,
        )
        self.remove(lines, starts)
        self.wait(0.3)

        # ==================================================================
        # Beat 3 -- counting by age
        # ==================================================================
        tw = int(D.meta.training_window)
        cap2 = caption(rf"count by age over the last {tw} business days")
        ax_r = age_axes([0, 750, 350], R_H, R_BASE)
        r_base = ax_r.x_axis
        r_yt = tick_labels(ax_r, y_values=[350, 700])[1]
        r_bars = bars(ax_r, ages, K.at_risk, INK, width=0.8, fill_opacity=0.16)
        r_bars.set_stroke(INK, width=1.2, opacity=0.85)
        r_sym = MathTex("R(a)", font_size=FS_LABEL + 4, color=INK)
        r_word = Tex("at risk", font_size=FS_LABEL, color=MUTED)
        r_lab = VGroup(r_word, r_sym).arrange(RIGHT, buff=0.15)
        r_lab.move_to([X(45), R_BASE + 0.8, 0], aligned_edge=RIGHT)

        wl_yt = tick_labels(ax_wl, y_values=[25, 50])[1]
        w_bars = bars(ax_wl, ages - 0.2, K.wins, KERNEL, width=0.4, fill_opacity=0.95)
        l_bars = bars(ax_wl, ages + 0.2, K.losses, LOST, width=0.4, fill_opacity=0.95)
        w_sym = MathTex("W(a)", font_size=FS_LABEL + 4, color=KERNEL)
        w_word = Tex("wins", font_size=FS_LABEL, color=KERNEL)
        w_lab = VGroup(w_word, w_sym).arrange(RIGHT, buff=0.15)
        l_sym = MathTex("L(a)", font_size=FS_LABEL + 4, color=LOST_TXT)
        l_word = Tex("losses", font_size=FS_LABEL, color=LOST_TXT)
        l_lab = VGroup(l_word, l_sym).arrange(RIGHT, buff=0.15)
        w_lab.move_to([X(45), BASE + 1.45, 0], aligned_edge=RIGHT)
        l_lab.move_to([X(45), BASE + 0.95, 0], aligned_edge=RIGHT)
        w_lab.align_to(l_lab, RIGHT)

        self.play(swap(cap1, cap2), FadeOut(ends), run_time=0.8)
        self.play(Create(r_base), Create(ax_r.y_axis), FadeIn(r_yt),
                  LaggedStart(*[GrowFromEdge(b, DOWN) for b in r_bars], lag_ratio=0.03),
                  FadeIn(r_lab, shift=LEFT * 0.2),
                  run_time=1.5)
        self.play(FadeIn(wl_yt), Create(ax_wl.y_axis),
                  LaggedStart(*[GrowFromEdge(b, DOWN) for b in w_bars], lag_ratio=0.03),
                  LaggedStart(*[GrowFromEdge(b, DOWN) for b in l_bars], lag_ratio=0.03),
                  FadeIn(w_lab, shift=LEFT * 0.2), FadeIn(l_lab, shift=LEFT * 0.2),
                  run_time=1.5)
        self.wait(1.0)

        # ==================================================================
        # Beat 4 -- hazards
        # ==================================================================
        cap3 = caption(r"each day, an open deal faces two competing risks")

        def hazard_tex(h, top, col):
            f = MathTex(h, "=", r"\frac{", top, r"+\alpha", "}{", "R(a)", r"+2\alpha", "}",
                        font_size=FS_FORMULA)
            f[0].set_color(col)
            f[3].set_color(col)
            f[4].set_color(MUTED)
            f[7].set_color(MUTED)
            return f

        f_w = hazard_tex("h_w(a)", "W(a)", KERNEL)
        f_l = hazard_tex(r"h_\ell(a)", "L(a)", LOST_TXT)
        fpair = VGroup(f_w, f_l).arrange(RIGHT, buff=0.9).move_to([2.1, 2.45, 0])
        alpha_note = Tex(rf"$\alpha = {D.meta.smoothing_alpha:g}$ (smoothing)", font_size=FS_TICK, color=MUTED)
        alpha_note.next_to(fpair, DOWN, buff=0.18).align_to(fpair, RIGHT)

        self.play(swap(cap2, cap3), run_time=0.8)
        self.play(
            Write(VGroup(f_w[0], f_w[1], f_w[2], f_w[5], f_w[8])),
            Succession(Wait(1.0), FadeIn(VGroup(f_w[4], f_w[7]), run_time=0.6)),
            TransformFromCopy(w_sym, f_w[3]),
            TransformFromCopy(r_sym, f_w[6]),
            Indicate(w_bars, color=KERNEL, scale_factor=1.0),
            run_time=1.6,
        )
        self.play(
            Write(VGroup(f_l[0], f_l[1], f_l[2], f_l[5], f_l[8])),
            TransformFromCopy(l_sym, f_l[3]),
            TransformFromCopy(r_sym, f_l[6]),
            Succession(Wait(1.0), FadeIn(VGroup(f_l[4], f_l[7], alpha_note), run_time=0.6)),
            run_time=1.6,
        )
        self.wait(1.0)

        # counts -> hazards (divide by the risk set)
        ax_h = age_axes([0, 0.12, 0.05], WL_H, BASE)
        h_yt = tick_labels(ax_h, y_values=[0.05, 0.10], fmt_y="{:.2f}")[1]
        hw_bars = bars(ax_h, ages - 0.2, K.win_hazard, KERNEL, width=0.4, fill_opacity=0.95)
        hl_bars = bars(ax_h, ages + 0.2, K.loss_hazard, LOST, width=0.4, fill_opacity=0.95)
        hw_lab = VGroup(Tex("win hazard", font_size=FS_LABEL, color=KERNEL),
                        MathTex("h_w(a)", font_size=FS_LABEL + 4, color=KERNEL)).arrange(RIGHT, buff=0.15)
        hl_lab = VGroup(Tex("loss hazard", font_size=FS_LABEL, color=LOST_TXT),
                        MathTex(r"h_\ell(a)", font_size=FS_LABEL + 4, color=LOST_TXT)).arrange(RIGHT, buff=0.15)
        hw_lab.move_to(w_lab, aligned_edge=RIGHT)
        hl_lab.move_to(l_lab, aligned_edge=RIGHT)
        self.play(
            Transform(w_bars, hw_bars), Transform(l_bars, hl_bars),
            Transform(wl_yt, h_yt),
            Transform(w_lab, hw_lab), Transform(l_lab, hl_lab),
            FadeOut(VGroup(r_bars, r_base, ax_r.y_axis, r_yt, r_lab), shift=UP * 0.3),
            run_time=1.8,
        )
        self.wait(1.0)

        # ==================================================================
        # Beat 5 -- the stochastic machine
        # ==================================================================
        hw, hl = K.win_hazard, K.loss_hazard
        outcome, ev_age, jit = simulate(hw, hl)
        coh = np.arange(N_PART) // (N_PART // N_COH)

        # step clock: G(T) (cohort-0 age) as a function of seconds T
        g_grid = np.linspace(0, 60, 6001)
        dur = np.interp(g_grid, [0, 24, 36, 60], [0.21, 0.21, 0.06, 0.06])
        t_grid = np.concatenate([[0], np.cumsum(0.5 * (dur[1:] + dur[:-1]) * np.diff(g_grid))])
        G_end = (N_COH - 1) + 45 + 0.001
        T_run = float(np.interp(G_end, g_grid, t_grid)) + 0.6
        t_event = np.interp(coh + ev_age, g_grid, t_grid)

        # pile slots (rank within bin by event time)
        slot = np.zeros((N_PART, 3))
        counts = np.zeros(46, dtype=int)
        for i in np.argsort(t_event, kind="stable"):
            if outcome[i] == 1:
                a, r = ev_age[i], counts[ev_age[i]]
                counts[a] += 1
                slot[i] = [X(a) + (-HALF if r % 2 == 0 else HALF), BASE + 0.06 + HALF + (r // 2) * PITCH, 0]

        ax_s = age_axes([0, 1, 1], S_H, S_BASE)
        s_yt = tick_labels(ax_s, y_values=[0, 1])[1]
        s_full = curve(ax_s, ages, K.survival, SURVIVAL, stroke_width=4)
        s_trace = s_full.copy()
        s_trace.pointwise_become_partial(s_full, 0, 0.0)
        s_head = Dot(ax_s.c2p(0, 1), radius=0.06, color=SURVIVAL)
        s_lab = VGroup(MathTex("S(a)", font_size=FS_LABEL + 4, color=SURVIVAL),
                       Tex("still open", font_size=FS_LABEL, color=SURVIVAL)).arrange(RIGHT, buff=0.15)
        s_lab.next_to(ax_s.c2p(2, 1), UP, buff=0.12).align_to(ax_s.c2p(1.0, 1), LEFT)

        f_s = MathTex("S(a)", "=", r"\prod_{j<a}", r"\bigl(1 -", "h_w(j)", "-", r"h_\ell(j)", r"\bigr)",
                      font_size=FS_FORMULA)
        f_s[0].set_color(SURVIVAL)
        f_s[4].set_color(KERNEL)
        f_s[6].set_color(LOST_TXT)
        f_s.move_to([0, 2.45, 0]).align_to([X(45) + 0.15, 0, 0], RIGHT)

        track = Line([X(0) - 0.15, TRACK_Y, 0], [X(45) + 0.15, TRACK_Y, 0], color=GRID, stroke_width=2)
        gate = Line([X(0) - 0.15, TRACK_Y - 0.36, 0], [X(0) - 0.15, TRACK_Y + 0.36, 0], color=MUTED, stroke_width=2)
        pile_lab = Tex(r"won at age $a$ $\to$ lands in bin $a$", font_size=FS_LABEL, color=KERNEL)
        pile_lab.move_to([X(32), BASE + 0.75, 0])

        cap4 = caption(r"each day: win, lose, or survive one more day")
        cap5 = caption(r"the won pile takes the shape of the kernel")

        self.play(
            FadeOut(VGroup(f_w, f_l, alpha_note), shift=UP * 0.2),
            FadeOut(VGroup(w_bars, l_bars, wl_yt, w_lab, l_lab, ax_wl.y_axis)),
            swap(cap3, cap4),
            run_time=1.0,
        )
        self.play(Create(ax_s.x_axis), Create(ax_s.y_axis), FadeIn(s_yt), FadeIn(s_lab),
                  Create(track), Create(gate), run_time=0.9)

        # particles
        dots = VGroup(*[Dot(ORIGIN, radius=DOT_R, color=INK, fill_opacity=0.0) for _ in range(N_PART)])
        base_pts = dots[0].get_points().copy()
        state = np.full(N_PART, -1)            # 0 travelling, 1 won, 2 lost, 3 open
        state_col = {0: INK, 1: KERNEL, 2: LOST, 3: SURVIVAL}
        last_op = np.full(N_PART, -1.0)
        T = ValueTracker(0.0)
        y0 = TRACK_Y + 0.27 * jit[:, 0]
        xj = 0.07 * jit[:, 1]

        def update_dots(group):
            t = T.get_value()
            G = float(np.interp(t, t_grid, g_grid))
            g = G - coh
            alive = g >= 0
            ga = np.minimum(np.maximum(g, 0), ev_age)
            xs = X(stepped(ga)) + xj
            ys = y0.copy()
            op = np.where(alive, np.clip(g / 0.5, 0, 1), 0.0) * 0.9
            sc = np.ones(N_PART)
            st = np.where(alive, 0, -1)
            dt = t - t_event
            done = alive & (dt >= 0)
            # won: flash, then drop into its bin
            w = done & (outcome == 1)
            if w.any():
                p = np.clip((dt[w] - 0.12) / 0.5, 0, 1)
                xs[w] = xs[w] + (slot[w, 0] - xs[w]) * (p * p * (3 - 2 * p))
                ys[w] = ys[w] + (slot[w, 1] - ys[w]) * p * p
                sc[w] = 1 + 0.9 * np.clip(1 - dt[w] / 0.3, 0, 1)
                op[w] = 1.0
                st[w] = 1
            lo = done & (outcome == 2)
            if lo.any():
                p = np.clip(dt[lo] / 0.7, 0, 1)
                ys[lo] = ys[lo] - 0.4 * p
                op[lo] = 0.9 * (1 - p)
                st[lo] = 2
            oo = done & (outcome == 0)
            if oo.any():
                p = np.clip(dt[oo] / 1.0, 0, 1)
                xs[oo] = xs[oo] + 0.35 * p
                op[oo] = 0.9 * (1 - p)
                st[oo] = 3
            for i, d in enumerate(group):
                if st[i] != state[i] and st[i] >= 0:
                    d.set_fill(state_col[int(st[i])])
                    state[i] = st[i]
                    last_op[i] = -1
                if abs(op[i] - last_op[i]) > 1e-3:
                    d.set_fill(opacity=op[i])
                    last_op[i] = op[i]
                if op[i] > 0:
                    d.set_points(base_pts * sc[i] + np.array([xs[i], ys[i], 0]))
            # survival trace follows the front cohort
            fa = float(min(stepped(max(G, 0)), 45))
            s_trace.pointwise_become_partial(s_full, 0, fa / 45)
            s_head.move_to(ax_s.c2p(fa, float(np.interp(fa, ages, K.survival))))

        dots.add_updater(update_dots)
        self.add(dots, s_trace, s_head)
        t1, t2 = 1.6, 5.0
        self.play(T.animate.set_value(t1), run_time=t1, rate_func=linear)
        self.play(T.animate.set_value(t2), Write(f_s), run_time=t2 - t1, rate_func=linear)
        t3 = t2 + 1.2
        self.play(T.animate.set_value(t3), swap(cap4, cap5), FadeIn(pile_lab),
                  run_time=t3 - t2, rate_func=linear)
        self.play(T.animate.set_value(T_run), run_time=T_run - t3, rate_func=linear)
        dots.clear_updaters()
        won_idx = np.where(outcome == 1)[0]
        others = [dots[i] for i in range(N_PART) if outcome[i] != 1]
        self.remove(*others)
        self.wait(0.3)

        # ==================================================================
        # Beat 6 -- the kernel
        # ==================================================================
        f_k = MathTex("k(a)", "=", "S(a)", r"\cdot", "h_w(a)", font_size=FS_FORMULA)
        f_k[0].set_color(KERNEL)
        f_k[2].set_color(SURVIVAL)
        f_k[4].set_color(KERNEL)
        f_k.move_to([0, 2.45, 0]).align_to(f_s, RIGHT)
        cap6 = caption(r"survive to age $a$, then win at age $a$")

        self.play(FadeOut(VGroup(*[f_s[i] for i in range(1, 8)])), FadeOut(pile_lab),
                  FadeOut(cap5), run_time=0.6)
        self.play(
            ReplacementTransform(f_s[0], f_k[2]),
            FadeIn(VGroup(f_k[0], f_k[1], f_k[3], f_k[4])),
            FadeIn(cap6),
            run_time=1.0,
        )
        self.wait(0.9)

        # pile -> exact bars of k(a) (same scale as the pile)
        ax_k1 = age_axes([0, 0.06, 0.01], 0.06 * U1, BASE)
        k_bars1 = bars(ax_k1, ages, K.win_mass, KERNEL, width=0.8, fill_opacity=0.9)
        bin_groups = {a: VGroup(*[dots[i] for i in won_idx if ev_age[i] == a]) for a in range(46)}
        morphs = []
        for a in range(46):
            if len(bin_groups[a]):
                morphs.append(ReplacementTransform(bin_groups[a], k_bars1[a]))
            else:
                morphs.append(GrowFromEdge(k_bars1[a], DOWN))
        self.play(*morphs, FadeOut(VGroup(track, gate, ax_s.x_axis, ax_s.y_axis, s_yt, s_lab, s_trace, s_head)),
                  run_time=1.5)

        # zoom: grow the kernel into the hero chart
        ax_k = age_axes([0, 0.032, 0.01], 3.3, BASE)
        k_yt = tick_labels(ax_k, y_values=[0.01, 0.02, 0.03], fmt_y="{:.2f}")[1]
        k_bars = bars(ax_k, ages, K.win_mass, KERNEL, width=0.8, fill_opacity=0.9)
        self.play(Transform(k_bars1, k_bars), Create(ax_k.y_axis), FadeIn(k_yt), run_time=1.7)
        self.wait(0.4)

        # exact bars -> display-smoothed curve with soft fill
        ks = K.win_mass_smooth
        k_curve = curve(ax_k, ages, ks, KERNEL, stroke_width=4.5)
        k_area = area_under(ax_k, ages, ks, KERNEL, opacity=0.22)
        self.play(Create(k_curve), k_bars1.animate.set_fill(opacity=0.35), run_time=1.5)
        self.play(FadeOut(k_bars1), FadeIn(k_area), run_time=0.8)

        m1 = int(np.argmax(ks[:9]))
        m2 = 9 + int(np.argmax(ks[9:20]))
        cap7 = caption(r"two typical decision times")
        marks = VGroup()
        for m in (m1, m2):
            top = ax_k.c2p(m, ks[m])
            tick = DashedLine(ax_k.c2p(m, 0), top, color=KERNEL, stroke_width=2, dash_length=0.06)
            tick.set_stroke(opacity=0.7)
            lab = MathTex(rf"\approx {m}\ \text{{days}}", font_size=FS_LABEL, color=INK)
            lab.next_to(top, UP, buff=0.18)
            marks.add(VGroup(tick, lab))
        self.play(swap(cap6, cap7),
                  LaggedStart(*[AnimationGroup(Create(g[0]), FadeIn(g[1], shift=DOWN * 0.15)) for g in marks],
                              lag_ratio=0.4),
                  run_time=1.3)
        self.wait(1.2)

        # ==================================================================
        # Beat 7 -- mass
        # ==================================================================
        pw = float(K.p_win_total)
        pl = float(K.p_loss_total)
        po = 1.0 - pw - pl
        f_m = MathTex(r"\sum_a", "k(a)", r"\approx", f"{pw:.2f}", font_size=FS_FORMULA)
        f_m[1].set_color(KERNEL)
        f_m[3].set_color(KERNEL)
        f_m.next_to(f_k, DOWN, buff=0.35).align_to(f_k, RIGHT)
        cap8 = caption(r"area under the kernel: the chance of ever winning")

        BW, BH = 5.0, 0.22
        bar_right = f_k.get_right()[0]
        bar_y = f_m.get_bottom()[1] - 0.55
        x_l = bar_right - BW
        segs = VGroup()
        for frac, col, x_start in ((pw, KERNEL, x_l), (pl, LOST, x_l + BW * pw), (po, SURVIVAL, x_l + BW * (pw + pl))):
            r = Rectangle(width=BW * frac, height=BH, stroke_width=0, fill_color=col, fill_opacity=0.95)
            r.move_to([x_start, bar_y, 0], aligned_edge=LEFT)
            segs.add(r)
        seg_labs = VGroup()
        for (txt, val, col), s in zip((("won", pw, KERNEL), ("lost", pl, LOST_TXT), ("open", po, SURVIVAL)), segs):
            lab = Tex(rf"{txt} ${val:.2f}$", font_size=FS_TICK, color=col)
            lab.next_to(s, DOWN, buff=0.14)
            seg_labs.add(lab)
        seg_labs[2].align_to(segs[2], RIGHT)

        self.play(swap(cap7, cap8), k_area.animate.set_fill(opacity=0.5), Write(f_m), run_time=1.5)
        self.play(TransformFromCopy(k_area, segs[0]), k_area.animate.set_fill(opacity=0.22), run_time=1.2)
        self.play(GrowFromEdge(segs[1], LEFT), GrowFromEdge(segs[2], LEFT),
                  FadeIn(seg_labs, shift=UP * 0.1), run_time=1.0)
        self.wait(2.1)

        # ==================================================================
        # Beat 8 -- the win kernel
        # ==================================================================
        final_lab = MathTex(r"k(a)", r"\ \text{--- the win kernel}", font_size=FS_FORMULA - 4)
        final_lab[0].set_color(KERNEL)
        final_lab.move_to([0, 1.6, 0]).align_to(f_k, RIGHT)
        self.play(FadeOut(VGroup(f_m, segs, seg_labs, cap8, f_k[1], f_k[2], f_k[3], f_k[4])), run_time=0.6)
        self.play(ReplacementTransform(f_k[0], final_lab[0]), FadeIn(final_lab[1], shift=LEFT * 0.2),
                  run_time=0.9)
        self.wait(2.6)
        close_chapter(self)
