import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import *

"""Chapter 06 -- The forecast.

The chart is designed in ordinary 2D screen coordinates (x right, y up) and then
"lifted" into the x-z plane of the 3D scene (rotate 90 deg about the x-axis).
The camera starts looking straight at that plane (phi=90, theta=-90), so the
flat chart is pixel-identical to its 2D design.  Simulated futures sit behind
the chart plane at depth +y; the camera tilts to show them and comes back.
"""

H = 15
Y_MAX = 9                       # wins / day shown on the vertical axis
N_FAN = int(os.environ.get("S06_N", 40))                     # simulated futures shown in the 3D fan (of 400)
DEPTH = float(os.environ.get("S06_D", 12.0))     # depth extent of the fan (scene units)
BASE = -2.3                     # design y of the chart baseline
Y0_MAX = 4.5                    # opening y-range (expected values only)
ZOOM0 = Y_MAX / Y0_MAX          # vertical stretch of the opening chart

def _env(name, default):
    return [float(v) for v in os.environ.get(name, default).split(",")]

FLAT = dict(phi=90 * DEGREES, theta=-90 * DEGREES)
_t = _env("S06_TILT", "52,-84,0.56,0.5,6,-2.7")
_d = _env("S06_DRIFT", "57,-76,0.55,0.4,6,-2.8")
TILT = dict(phi=_t[0] * DEGREES, theta=_t[1] * DEGREES, zoom=_t[2], frame_center=_t[3:6])
DRIFT = dict(phi=_d[0] * DEGREES, theta=_d[1] * DEGREES, zoom=_d[2], frame_center=_d[3:6])


def lift(mob):
    """Move a mobject designed in the screen plane into the chart (x-z) plane."""
    return mob.rotate(PI / 2, RIGHT, about_point=ORIGIN)


def delayed(start, length, rf=smooth):
    """Rate function that runs ``rf`` inside [start, start + length] of the animation."""
    def f(t):
        return rf(float(np.clip((t - start) / length, 0.0, 1.0)))
    return f


class Clip(ThreeDScene):
    def construct(self):
        D = load_data()
        F, MC = D.forecast, D.monte_carlo
        days = np.arange(1, H + 1)
        self.set_camera_orientation(**FLAT)

        header = open_chapter(self, 6, "The forecast", TOTAL)

        # ---------------------------------------------------------------- chart
        ax = make_axes([0, 16, 1], [0, Y_MAX, 3], 10.0, 4.0, y_axis_config={"include_ticks": False})
        ax.shift(np.array([-5.0, BASE, 0]) - ax.c2p(0, 0))
        ax2d = ax.copy()                              # stays in the design plane
        p2 = ax2d.c2p                                 # design coords
        uy = ax.y_axis.unit_size
        ticks = tick_labels(ax, x_values=[1, 5, 10, 15])

        def ytick(v, top):
            """Tick mark + number for value ``v`` on a y-axis running 0..``top``."""
            y = BASE + v * 4.0 / top
            mark = Line([-5.06, y, 0], [-4.94, y, 0], color=MUTED, stroke_width=2)
            lab = MathTex(f"{v:g}", font_size=FS_TICK, color=MUTED)
            lab.next_to([-5.0, y, 0], LEFT, buff=0.14)
            return VGroup(mark, lab)

        yA_vals, yB_vals = [0, 1, 2, 3, 4], [0, 3, 6, 9]
        yA = VGroup(*[ytick(v, Y0_MAX) for v in yA_vals])      # opening scale 0..4.5
        yB = VGroup(*[ytick(v, Y_MAX) for v in yB_vals])       # simulation scale 0..9
        xt = Tex(r"forecast day $d$", font_size=FS_LABEL, color=MUTED)
        xt.next_to(ax.x_axis.get_right(), DOWN, buff=0.5).align_to(ax.x_axis.get_right(), RIGHT)
        yt = Tex(r"expected wins / day", font_size=FS_LABEL, color=MUTED).rotate(PI / 2)
        yt.next_to(yB, LEFT, buff=0.22)
        yt2d = yt.copy()
        frame_grp = VGroup(ax, ticks, xt, yt, yB)
        lift(frame_grp)
        lift(yA)
        # rescale animation pieces: old ticks sink and fade, new ticks descend into place
        yA_out = yA.copy()
        yB_in = yB.copy()
        for v, item in zip(yA_vals, yA_out):
            item.shift(IN * v * 4.0 * (1 / Y0_MAX - 1 / Y_MAX)).set_opacity(0)
        for v, item in zip(yB_vals, yB_in):
            item.shift(OUT * v * 4.0 * (1 / Y0_MAX - 1 / Y_MAX)).set_opacity(0)
        PIVOT = np.array([0.0, 0.0, BASE])

        def zoom_in(m):
            return m.stretch(ZOOM0, 2, about_point=PIVOT)

        def bar_group(xs, heights, bottoms, color, width, opacity=0.9):
            g = bars(ax2d, xs, heights, color, width=width, fill_opacity=opacity, bottoms=bottoms)
            return lift(g)

        z0 = np.zeros(H)
        rose_side = bar_group(days - 0.2, F.stock, z0, STOCK, 0.38)
        blue_side = bar_group(days + 0.2, F.arrivals, z0, ARRIVALS, 0.38)
        rose_stack = bar_group(days, F.stock, z0, STOCK, 0.74)
        blue_stack = bar_group(days, F.arrivals, F.stock, ARRIVALS, 0.74)

        smooth_line = lift(curve(ax2d, days, F.total_smooth, TOTAL, stroke_width=5))
        for m in (rose_side, blue_side, rose_stack, blue_stack, smooth_line):
            zoom_in(m)

        # ---------------------------------------------------- text (screen-fixed)
        def fixed(*mobs):
            fix_in_frame(self, *mobs)
            return mobs[0] if len(mobs) == 1 else mobs

        lab_s = MathTex(r"W_{\text{stock}}(d)", font_size=FS_FORMULA, color=STOCK)
        lab_s.move_to([p2(3.0, 0)[0], 1.1, 0])
        lab_a = MathTex(r"W_{\text{arr}}(d)", font_size=FS_FORMULA, color=ARRIVALS)
        lab_a.move_to([p2(13.0, 0)[0], 1.1, 0])
        fixed(lab_s, lab_a)

        BAND_Y = 2.45
        f_short = MathTex(r"\hat{W}(d)", "=", r"W_{\text{stock}}(d)", "+", r"W_{\text{arr}}(d)",
                          font_size=FS_FORMULA)
        for i, c in enumerate([TOTAL, INK, STOCK, INK, ARRIVALS]):
            f_short[i].set_color(c)
        f_short.move_to([0.6, BAND_Y, 0])
        f_full = MathTex(r"\hat{W}(d)", "=", r"\sum_a N(a)\,\frac{k(a+d)}{S(a)}", "+",
                         r"\sum_{t\le d}\hat{A}(t)\,k(d-t)", font_size=40)
        for i, c in enumerate([TOTAL, INK, STOCK, INK, ARRIVALS]):
            f_full[i].set_color(c)
        f_full.move_to([1.0, BAND_Y - 0.05, 0])
        fixed(f_short, f_full)

        cap = [None]

        def say(text, wait=0.0, extra=(), run_time=0.5):
            new = fixed(caption(text))
            if cap[0] is not None:
                self.play(FadeOut(cap[0]), run_time=0.3)
            self.play(FadeIn(new, shift=UP * 0.12), *extra, run_time=run_time)
            cap[0] = new
            if wait:
                self.wait(wait)

        # ------------------------------------------------------ beat 2: streams
        self.play(Create(ax), FadeIn(ticks), FadeIn(yA), FadeIn(xt), FadeIn(yt), run_time=1.0)
        self.play(LaggedStart(*[GrowFromEdge(b, IN) for b in rose_side], lag_ratio=0.06),
                  FadeIn(lab_s, shift=UP * 0.2), run_time=1.1)
        self.play(LaggedStart(*[GrowFromEdge(b, IN) for b in blue_side], lag_ratio=0.06),
                  FadeIn(lab_a, shift=UP * 0.2), run_time=1.1)
        say("two streams of expected wins", wait=1.3)

        # --------------------------------------------------------- beat 3: add
        self.play(Transform(rose_side, rose_stack),
                  Transform(blue_side, blue_stack, path_arc=-0.0),
                  run_time=1.7)
        self.play(ReplacementTransform(lab_s, f_short[2]),
                  ReplacementTransform(lab_a, f_short[4]),
                  FadeIn(f_short[0], f_short[1], f_short[3]),
                  run_time=1.2)
        say("the stock runs down while new arrivals ripen")
        self.play(Create(smooth_line), run_time=1.6)
        self.wait(0.6)
        self.play(*[ReplacementTransform(f_short[i], f_full[i]) for i in range(5)], run_time=1.5)
        self.wait(3.2)

        # ------------------------------------------- beat 4: one possible future
        ghost_anims = [
            rose_side.animate.stretch(1 / ZOOM0, 2, about_point=PIVOT)
                .set_fill(opacity=0.10).set_stroke(STOCK, width=1.4, opacity=0.55),
            blue_side.animate.stretch(1 / ZOOM0, 2, about_point=PIVOT)
                .set_fill(opacity=0.10).set_stroke(ARRIVALS, width=1.4, opacity=0.55),
            smooth_line.animate.stretch(1 / ZOOM0, 2, about_point=PIVOT).set_stroke(opacity=0.35),
            Transform(yA, yA_out),
            ReplacementTransform(yB_in, yB),
            FadeOut(f_full, shift=UP * 0.2),
        ]
        yt_sim = Tex(r"wins / day", font_size=FS_LABEL, color=MUTED).rotate(PI / 2)
        yt_sim.move_to(p2(0, 4.5)).align_to(yt2d, RIGHT)
        yt_exp = yt2d.copy()
        lift(yt_sim)
        lift(yt_exp)
        say("but what is this number?", extra=ghost_anims + [Transform(yt, yt_sim)], run_time=1.8)
        self.remove(yA)
        self.wait(0.2)

        won = [p for p in MC.particles if p["outcome"] == "won"]
        dots = VGroup()
        counts = np.zeros(H, dtype=int)
        r = 0.15
        for kind, col in (("stock", STOCK), ("arrival", ARRIVALS)):
            for p in won:
                if p["kind"] != kind:
                    continue
                d = p["day"]
                k = counts[d - 1]
                counts[d - 1] += 1
                dot = Circle(radius=r, stroke_width=0, fill_color=col, fill_opacity=1.0)
                dot.move_to(p2(d, k + 0.5))
                dots.add(dot)
        # deal order: column by column, bottom to top (they "pile up")
        order = sorted(range(len(dots)), key=lambda i: (dots[i].get_center()[0], dots[i].get_center()[1]))
        dots = VGroup(*[dots[i] for i in order])
        lift(dots)
        say("one possible future")
        self.play(LaggedStart(*[FadeIn(dt, shift=IN * 0.9) for dt in dots], lag_ratio=0.08),
                  run_time=2.6)
        self.wait(1.4)

        # ----------------------------------------- beat 5: another, and another
        def step_line(c, depth=0.0, color=INK, width=3.5, opacity=1.0):
            pts = []
            for d in range(1, H + 1):
                pts += [p2(d - 0.5, c[d - 1]), p2(d + 0.5, c[d - 1])]
            ln = VMobject(stroke_color=color, stroke_width=width, stroke_opacity=opacity)
            ln.set_points_as_corners(pts)
            lift(ln)
            ln.shift(UP * depth)
            return ln

        def path_line(c, color=INK, width=3.5, opacity=1.0):
            ln = VMobject(stroke_color=color, stroke_width=width, stroke_opacity=opacity)
            ln.set_points_as_corners([p2(d, c[d - 1]) for d in days])
            return lift(ln)

        run = step_line(counts)
        self.play(Create(run), dots.animate.set_fill(opacity=0.0), run_time=1.3)
        self.remove(dots)
        say("another, and another")
        flick = [0, 1, 2, 3]
        for i in flick:
            self.play(Transform(run, path_line(MC.total[i])), run_time=0.6 if i == flick[0] else 0.55)
            self.wait(0.1)

        # ------------------------------------------------- beat 6: tilt into 3D
        ok = [i for i in range(400) if MC.total[i].max() <= Y_MAX and i not in flick]
        chosen = ok[:N_FAN]
        dz = DEPTH / N_FAN

        def future(c, depth, f):
            """One simulated future as a thin path through the daily counts at its own
            depth. ``f`` = 1 at the front, 0 at the back: brighter/thicker near, dim teal far."""
            col = interpolate_color(ManimColor(TOTAL), ManimColor(INK), f ** 2.2)
            ln = path_line(c, color=col, width=0.9 + 1.5 * f, opacity=0.2 + 0.7 * f ** 1.3)
            return ln.shift(UP * depth)

        finals, starts = [], []
        for j, i in enumerate(chosen):
            depth = (j + 1) * dz
            fin = future(MC.total[i], depth, 1 - j / N_FAN)
            st = fin.copy().shift(-UP * depth).set_stroke(opacity=0)
            finals.append(fin)
            starts.append(st)
        # far-to-near draw order, then the front plane on top
        self.add(*reversed(starts))
        self.bring_to_front(rose_side, blue_side, smooth_line, frame_grp, run)

        say("400 simulated futures of the same system")
        # lagged front-to-back without LaggedStart (whose wrapper Group would be
        # re-added on top of the scene and break the far-to-near draw order)
        fan = [Transform(s, f, rate_func=delayed(0.22 + 0.48 * j / N_FAN, 0.3))
               for j, (s, f) in enumerate(zip(starts, finals))]
        self.move_camera(**TILT, run_time=3.2, added_anims=fan)
        if os.environ.get("S06_STOP") == "tilt":
            return
        self.move_camera(**DRIFT, run_time=3.0, rate_func=smooth)
        if os.environ.get("S06_STOP") == "drift":
            return

        # --------------------------------------------- beat 7: collapse to mean
        back = []
        for j, s_ in enumerate(starts):
            tgt = s_.copy().shift(-UP * ((j + 1) * dz))
            tgt.set_stroke(TOTAL, width=1.4, opacity=0.38)
            back.append(Transform(s_, tgt))
        self.move_camera(**FLAT, zoom=1.0, frame_center=ORIGIN, run_time=3.0,
                         added_anims=back)

        def step_band(lo, hi, color, op):
            top = []
            bot = []
            for d in range(1, H + 1):
                top += [p2(d - 0.5, hi[d - 1]), p2(d + 0.5, hi[d - 1])]
                bot += [p2(d - 0.5, lo[d - 1]), p2(d + 0.5, lo[d - 1])]
            poly = Polygon(*top, *reversed(bot), stroke_width=0, fill_color=color, fill_opacity=op)
            return lift(poly)

        band90 = step_band(MC.q05_total, MC.q95_total, TOTAL, 0.16)
        band50 = step_band(MC.q25_total, MC.q75_total, TOTAL, 0.18)
        mean_ticks = VGroup(*[
            Line(p2(d - 0.37, MC.mean_total[d - 1]), p2(d + 0.37, MC.mean_total[d - 1]),
                 color=INK, stroke_width=5)
            for d in days])
        lift(mean_ticks)

        f_E = MathTex(r"\hat{W}(d)", "=", r"\mathbb{E}\,[\,\text{wins on day } d\,]",
                      font_size=FS_FORMULA)
        f_E[0].set_color(TOTAL)
        f_E.move_to([-1.2, BAND_Y, 0])
        fixed(f_E)

        self.add(band90, band50)
        self.bring_to_front(rose_side, blue_side, smooth_line, frame_grp, run, *starts)
        band90.set_fill(opacity=0)
        band50.set_fill(opacity=0)
        self.play(*[FadeOut(s) for s in starts], FadeOut(run),
                  band90.animate.set_fill(opacity=0.16), band50.animate.set_fill(opacity=0.18),
                  run_time=1.4)
        self.bring_to_front(rose_side, blue_side, smooth_line)
        self.play(rose_side.animate.set_fill(opacity=0.85).set_stroke(width=0),
                  blue_side.animate.set_fill(opacity=0.85).set_stroke(width=0),
                  smooth_line.animate.set_stroke(opacity=1.0),
                  Transform(yt, yt_exp),
                  LaggedStart(*[FadeIn(t, shift=IN * 0.5) for t in mean_ticks], lag_ratio=0.05),
                  run_time=1.6)
        self.play(Write(f_E), run_time=1.2)
        say("the forecast is the average of all these futures", wait=2.4)

        # ------------------------------------------- beat 8: what really happened
        actual = VGroup(*[
            Dot(p2(d, F.actual[d - 1]), radius=0.09, color=INK) for d in days])
        lift(actual)
        # small legend (screen-fixed), top right
        sw_band = Rectangle(width=0.42, height=0.24, stroke_width=0, fill_color=TOTAL, fill_opacity=0.4)
        sw_mean = Line(LEFT * 0.21, RIGHT * 0.21, color=INK, stroke_width=5)
        sw_act = Dot(radius=0.09, color=INK)
        lg_rows = VGroup(
            VGroup(sw_band, Tex("simulated spread", font_size=FS_TICK, color=MUTED)).arrange(RIGHT, buff=0.2),
            VGroup(sw_mean, Tex("mean of simulations", font_size=FS_TICK, color=MUTED)).arrange(RIGHT, buff=0.2),
            VGroup(sw_act, Tex("actual wins", font_size=FS_TICK, color=MUTED)).arrange(RIGHT, buff=0.2),
        )
        for row in lg_rows:
            row[1].shift(RIGHT * (0.62 - (row[1].get_left()[0] - row[0].get_left()[0])))
        lg_rows.arrange(DOWN, aligned_edge=LEFT, buff=0.14)
        lg_rows.move_to([4.9, 2.55, 0])
        fixed(lg_rows)
        self.play(FadeIn(lg_rows[0]), FadeIn(lg_rows[1]), run_time=0.6)
        say("what actually happened: one more draw")
        self.play(LaggedStart(*[FadeIn(a, scale=0.4) for a in actual], lag_ratio=0.08),
                  FadeIn(lg_rows[2]), run_time=1.6)
        self.wait(3.0)
        close_chapter(self)
