import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import *

# ---------------------------------------------------------------------------
# Chapter 05 -- Wins from future arrivals
#   each arrival cohort replays the kernel from its arrival day:
#   E_arr(t, d) = A(t) k(d - t);  W_arr(d) = sum_t E_arr(t, d) = (A * k)(d)
# ---------------------------------------------------------------------------

H = 15
SR = 5.0          # ribbon scale: world units per (expected win / day)
SW = 1.0          # back-wall scale: world units per (expected win / day)
S2 = 4.0          # flat 2D cohort chart: world units per win / day
T_DEMO = 2        # the cohort we follow


def early(t):
    return smooth(min(1.0, t * 2.2))


def late(t):
    return smooth(max(0.0, t * 1.8 - 0.8))


def standing(mob):
    """Turn a flat (xy-plane) mobject into one standing in the x-z plane,
    readable from the front (-y side)."""
    return mob.rotate(PI / 2, axis=RIGHT)


class Clip(ThreeDScene):
    def construct(self):
        D = load_data()
        A = D.arrivals.forecast                   # (15,)  A_hat(t)
        k = D.kernel.win_mass                     # (46,)  model kernel
        ks = D.kernel.win_mass_smooth             # (46,)  display kernel
        E = D.arrivals.surface                    # (15,15) [t-1, d-1]
        Wd = D.arrivals.by_day                    # (15,)

        self.set_camera_orientation(**CAM_TOP, zoom=1.0)
        header = open_chapter(self, 5, "Wins from future arrivals", ARRIVALS)

        # ------------------------------------------------------------------
        # 3D axes (built now so the flat d-axis can share their x positions)
        #   x = conversion day d, y = 16 - t (t = 1 at the back), z = wins/day
        # ------------------------------------------------------------------
        ax = make_axes_3d([0, 16, 1], [0, 16, 1], [0, 0.5, 0.1], 8.0, 6.0, 0.5 * SR)
        ax.shift(-ax.c2p(8, 8, 0))

        def P(d, t, w):                      # point on/above the floor (ribbon scale)
            return ax.c2p(d, 16 - t, w)

        def PW(d, w):                        # point on the back wall (wall scale)
            return ax.c2p(d, 16, w * SW / SR)

        def xw(d):
            return ax.c2p(d, 0, 0)[0]

        # ------------------------------------------------------------------
        # Beat 2 -- the two ingredients, flat (camera looks straight down)
        # ------------------------------------------------------------------
        a_ax = make_axes([0, 16, 1], [0, 16, 5], 5.0, 1.55)
        a_ax.move_to([-3.75, 1.55, 0])
        a_bars = bars(a_ax, np.arange(1, H + 1), A, ARRIVALS, width=0.7)
        a_ticks = tick_labels(a_ax, x_values=(1, 5, 10, 15), y_values=(5, 10, 15))
        a_title = MathTex(r"\hat{A}(t)", font_size=FS_LABEL + 4, color=ARRIVALS)
        a_title.next_to(a_ax.c2p(0, 16), UP, buff=0.12).align_to(a_ax.c2p(0, 0), LEFT)
        a_xlab = Tex(r"arrival day $t$", font_size=FS_LABEL, color=MUTED)
        a_xlab.next_to(a_ticks[0], DOWN, buff=0.1)
        a_grp = VGroup(a_ax, a_bars, a_ticks, a_title, a_xlab)

        k_ax = make_axes([0, 45, 5], [0, 0.022, 0.01], 5.0, 1.55)
        k_ax.move_to([3.75, 1.55, 0])
        ages = np.arange(0, 46)
        k_area = area_under(k_ax, ages, ks, KERNEL, opacity=0.18)
        k_curve = curve(k_ax, ages, ks, KERNEL, stroke_width=4)
        k_ticks = tick_labels(k_ax, x_values=(0, 15, 30, 45))
        k_title = MathTex(r"k(a)", font_size=FS_LABEL + 4, color=KERNEL)
        k_title.next_to(k_ax.c2p(0, 0.022), UP, buff=0.12).align_to(k_ax.c2p(0, 0), LEFT)
        k_xlab = Tex(r"age $a$ (business days)", font_size=FS_LABEL, color=MUTED)
        k_xlab.next_to(k_ticks[0], DOWN, buff=0.1)
        k_grp = VGroup(k_ax, k_area, k_curve, k_ticks, k_title, k_xlab)

        ingredients = VGroup(a_grp, k_grp)
        ingredients.shift(DOWN * 1.45)

        cap = caption(r"forecast arrivals $\hat{A}(t)$ and the win kernel $k(a)$")
        cap[0][16:21].set_color(ARRIVALS)
        cap[0][-4:].set_color(KERNEL)
        fix_in_frame(self, cap)

        self.play(Create(a_ax), FadeIn(a_ticks), FadeIn(a_xlab), run_time=0.8)
        self.play(
            LaggedStart(*[GrowFromEdge(b, DOWN) for b in a_bars], lag_ratio=0.08),
            Write(a_title),
            run_time=1.4,
        )
        self.play(Create(k_ax), FadeIn(k_ticks), FadeIn(k_xlab), run_time=0.8)
        self.play(Create(k_curve), FadeIn(k_area), Write(k_title), FadeIn(cap), run_time=1.4)
        self.wait(0.8)

        # ------------------------------------------------------------------
        # Beat 3 -- one cohort: t = 2
        # ------------------------------------------------------------------
        d_y0 = -2.35
        d_line = Line([xw(0), d_y0, 0], [xw(16), d_y0, 0], color=MUTED, stroke_width=2)
        d_tk = VGroup(*[
            Line([xw(d), d_y0 - 0.06, 0], [xw(d), d_y0 + 0.06, 0], color=MUTED, stroke_width=2)
            for d in range(1, 16)
        ])
        d_nums = VGroup(*[
            MathTex(str(d), font_size=FS_TICK, color=MUTED).next_to([xw(d), d_y0, 0], DOWN, buff=0.14)
            for d in (1, 5, 10, 15)
        ])
        d_lab = Tex(r"conversion day $d$", font_size=FS_LABEL, color=MUTED)
        d_lab.next_to([xw(16), d_y0, 0], RIGHT, buff=0.25)
        d_axis = VGroup(d_line, d_tk, d_nums, d_lab)

        def p2(d, w):
            return np.array([xw(d), d_y0 + w * S2, 0.0])

        cap2 = caption(r"a new cohort arrives brand new: age $0$ on day $t$")
        fix_in_frame(self, cap2)
        self.play(
            ingredients.animate.shift(UP * 1.45),
            FadeOut(a_xlab), FadeOut(k_xlab),
            Create(d_axis),
            FadeOut(cap), FadeIn(cap2),
            run_time=1.4,
        )
        a_grp.remove(a_xlab)
        k_grp.remove(k_xlab)

        # highlight the t = 2 bar
        bar2 = a_bars[T_DEMO - 1]
        others = VGroup(*[b for i, b in enumerate(a_bars) if i != T_DEMO - 1])
        t_dot = Dot([xw(T_DEMO), d_y0, 0], radius=0.07, color=ARRIVALS)
        t_lab = MathTex(r"t = 2", font_size=FS_LABEL, color=ARRIVALS)
        t_lab.next_to(t_dot, UP, buff=0.18).shift(LEFT * 0.4)
        self.play(
            others.animate.set_opacity(0.3),
            TransformFromCopy(bar2, t_dot),
            FadeIn(t_lab, shift=UP * 0.1),
            run_time=0.8,
        )

        # the kernel copy flies to start at d = t (age 0 on arrival day)
        a_in = np.arange(0, H - T_DEMO + 1)           # ages 0..13 land on d = 2..15
        a_out = np.arange(H - T_DEMO, 19)             # ages 13..18 fall past the horizon
        kscale = (k_ax.c2p(0, 1)[1] - k_ax.c2p(0, 0)[1])  # kernel-chart units per k
        seg_in = curve(k_ax, a_in, ks[a_in], KERNEL, stroke_width=6)
        seg_out = curve(k_ax, a_out, ks[a_out], KERNEL, stroke_width=6)

        def kpt(a):
            return [xw(T_DEMO + a), d_y0 + ks[a] * kscale, 0]

        land_in = VMobject(color=KERNEL, stroke_width=4).set_points_smoothly([kpt(a) for a in a_in])
        land_out = VMobject(color=KERNEL, stroke_width=4).set_points_smoothly([kpt(a) for a in a_out])
        self.play(
            TransformFromCopy(seg_in, land_in),
            TransformFromCopy(seg_out, land_out),
            run_time=1.8,
        )

        # horizon cut-off
        hz = DashedLine([xw(15.5), d_y0, 0], [xw(15.5), d_y0 + 1.9, 0], color=MUTED,
                        stroke_width=2, dash_length=0.08)
        hz_lab = Tex(r"horizon", font_size=FS_TICK, color=MUTED).next_to(hz, UP, buff=0.1)
        self.play(Create(hz), FadeIn(hz_lab), run_time=0.6)
        self.play(land_out.animate.set_stroke(opacity=0.0), run_time=0.6)
        self.remove(land_out)

        # scaled by the cohort size: x A(2), using the model's kernel k(d - t)
        cap3 = caption(r"its wins follow the kernel, scaled by the cohort size")
        fix_in_frame(self, cap3)
        times = MathTex(r"\times\,\hat{A}(2) \approx " + f"{A[T_DEMO - 1]:.1f}",
                        font_size=FS_LABEL + 2, color=ARRIVALS)
        times.move_to([xw(10.5), d_y0 + 1.95, 0])
        top2 = [p2(d, E[T_DEMO - 1, d - 1]) for d in range(T_DEMO, H + 1)]
        base2 = [p2(d, 0) for d in range(T_DEMO, H + 1)]
        coh2d = ribbon_3d(top2, base2, ARRIVALS, fill_opacity=0.28, stroke_width=4)
        coh2d.set_shade_in_3d(False)
        self.play(TransformFromCopy(bar2, times), FadeOut(cap2), FadeIn(cap3), run_time=1.1)
        self.play(ReplacementTransform(land_in, coh2d[1]), run_time=1.5)
        self.play(FadeIn(coh2d[0]), run_time=0.6)

        f_E = MathTex(r"E_{\text{arr}}(t,d)", r"=", r"\hat{A}(t)", r"\,", r"k(d-t)",
                      r",\quad d \ge t", font_size=FS_FORMULA)
        f_E[2].set_color(ARRIVALS)
        f_E[4].set_color(KERNEL)
        f_E.move_to([0, 0.12, 0])
        fix_in_frame(self, f_E)
        self.play(Write(f_E), FadeOut(times), run_time=1.5)
        self.wait(1.7)

        # ------------------------------------------------------------------
        # Beat 4 -- into 3D: the t = 2 ribbon stands up, then all cohorts
        # ------------------------------------------------------------------
        def ribbon(t, op=0.2):
            ds = list(range(t, H + 1))
            if len(ds) == 1:
                ds_x = [ds[0] - 0.02, ds[0]]
                vals = [E[t - 1, ds[0] - 1]] * 2
            else:
                ds_x = ds
                vals = [E[t - 1, d - 1] for d in ds]
            top = [P(d, t, v) for d, v in zip(ds_x, vals)]
            flo = [P(d, t, 0) for d in ds_x]
            r = ribbon_3d(top, flo, ARRIVALS, fill_opacity=op, stroke_width=2.6)
            r.t, r.ds_x = t, ds_x
            return r

        ribs = {t: ribbon(t) for t in range(1, H + 1)}
        CAM_Z, CAM_C = 0.88, ax.c2p(7.5, 6.5, 0.12)

        def flat(r):
            f = r.copy()
            f.apply_function(lambda p: np.array([p[0], p[1], ax.c2p(0, 0, 0)[2]]))
            return f

        def flat0(r):
            return flat(r).set_opacity(0)

        # floor frame: d axis at the front, t axis on the left
        floor_axes = VGroup(ax.x_axis, ax.y_axis)
        back_edge = Line(ax.c2p(0, 16, 0), ax.c2p(16, 16, 0), color=GRID, stroke_width=2)
        right_edge = Line(ax.c2p(16, 0, 0), ax.c2p(16, 16, 0), color=GRID, stroke_width=2)
        back_edge.set_shade_in_3d(True)
        right_edge.set_shade_in_3d(True)
        dn = VGroup(*[
            MathTex(str(d), font_size=FS_TICK + 8, color=MUTED).move_to(ax.c2p(d, -0.9, 0))
            for d in (1, 5, 10, 15)
        ])
        tn = VGroup(*[
            MathTex(str(t), font_size=FS_TICK + 8, color=MUTED).move_to(ax.c2p(-0.75, 16 - t, 0))
            for t in (1, 5, 10, 15)
        ])
        d_title = Tex(r"conversion day $d$", font_size=FS_LABEL + 8, color=MUTED)
        d_title.move_to(ax.c2p(8, -2.3, 0))
        t_title = Tex(r"arrival day $t$", font_size=FS_LABEL + 8, color=MUTED).rotate(PI / 2)
        t_title.move_to(ax.c2p(-2.0, 8, 0))
        floor_labels = VGroup(dn, tn, d_title, t_title)

        cap4 = caption(r"every cohort replays the kernel, one day later")
        fix_in_frame(self, cap4)

        self.play(
            FadeOut(ingredients), FadeOut(d_axis), FadeOut(hz), FadeOut(hz_lab),
            FadeOut(t_dot), FadeOut(t_lab), FadeOut(cap3),
            f_E.animate.scale(0.9).to_corner(UR, buff=0.45),
            run_time=1.0,
        )
        self.move_camera(
            **CAM_3D, zoom=CAM_Z, frame_center=CAM_C,
            added_anims=[
                ReplacementTransform(coh2d, ribs[T_DEMO]),
                Create(floor_axes), Create(back_edge), Create(right_edge),
                FadeIn(floor_labels),
            ],
            run_time=3.0,
        )
        self.begin_ambient_camera_rotation(rate=-0.022)
        self.play(FadeIn(cap4), run_time=0.6)
        order = [t for t in range(1, H + 1) if t != T_DEMO]
        self.play(
            LaggedStart(*[ReplacementTransform(flat0(ribs[t]), ribs[t]) for t in order],
                        lag_ratio=0.35),
            run_time=4.4,
        )
        self.wait(0.6)
        self.stop_ambient_camera_rotation()

        # ------------------------------------------------------------------
        # Beat 5 -- seen from above this is the README heat-map
        # ------------------------------------------------------------------
        all_ribs = VGroup(*[ribs[t] for t in range(1, H + 1)])
        for r in all_ribs:
            r.save_state()
        tiles = floor_tiles_3d(ax, D.arrivals.surface_smooth, list(range(1, H + 1)),
                               [16 - t for t in range(1, H + 1)], ARRIVALS_RAMP)
        hm_lab = VGroup(
            Tex(r"future-arrivals", font_size=FS_LABEL + 4, color=ARRIVALS),
            Tex(r"heat-map", font_size=FS_LABEL + 4, color=ARRIVALS),
        ).arrange(DOWN, buff=0.12, aligned_edge=LEFT)
        hm_lab.move_to([5.2, 0.6, 0])
        fix_in_frame(self, hm_lab)
        flats = [flat(r).set_opacity(0) for r in all_ribs]
        self.move_camera(
            **CAM_TOP, zoom=0.86, frame_center=[0, 0.25, 0],
            added_anims=[
                FadeOut(cap4),
                FadeIn(tiles, run_time=2.2, rate_func=lambda x: smooth(np.clip(x * 1.3 - 0.3, 0, 1))),
                *[Transform(r, f) for r, f in zip(all_ribs, flats)],
            ],
            run_time=3.0,
        )
        self.play(FadeIn(hm_lab, shift=LEFT * 0.15), run_time=0.8)
        self.wait(2.5)

        # ------------------------------------------------------------------
        # Beat 6 -- sum over cohorts: collapse onto the back wall
        # ------------------------------------------------------------------
        cap6 = caption(r"add up the cohorts, day by day")
        fix_in_frame(self, cap6)
        self.move_camera(
            **CAM_3D, zoom=CAM_Z, frame_center=CAM_C,
            added_anims=[
                FadeOut(hm_lab), FadeOut(tiles),
                *[Restore(r) for r in all_ribs],
            ],
            run_time=3.0,
        )

        # wall scale (wins / day) on the back wall
        wall_grid = VGroup(*[
            Line(PW(0, v), PW(16, v), color=GRID, stroke_width=1.5) for v in (1, 2)
        ])
        wall_nums = VGroup(*[
            standing(MathTex(str(v), font_size=FS_TICK + 2, color=MUTED)).move_to(PW(-0.55, v))
            for v in (1, 2)
        ])
        wall_edge = Line(PW(0, 0), PW(0, 2.6), color=MUTED, stroke_width=2)

        # stacked bands: cohort t occupies [cum_{t-1}(d), cum_t(d)] on the wall
        cum = np.cumsum(E, axis=0)                   # cum[t-1, d-1] = sum_{s<=t} E(s, d)
        bands = []
        for t in range(1, H + 1):
            r = ribs[t]
            lo = [cum[t - 2, int(round(d)) - 1] if t > 1 else 0.0 for d in r.ds_x]
            hi = [cum[t - 1, int(round(d)) - 1] for d in r.ds_x]
            top = [PW(d, v) for d, v in zip(r.ds_x, hi)]
            bot = [PW(d, v) for d, v in zip(r.ds_x, lo)]
            b = ribbon_3d(top, bot, ARRIVALS, fill_opacity=0.35, stroke_width=1.6)
            bands.append(b)

        f_W = MathTex(r"W_{\text{arr}}(d)", r"=", r"\sum_{t\le d}", r"\hat{A}(t)", r"\,",
                      r"k(d-t)", font_size=FS_FORMULA)
        f_W[0].set_color(ARRIVALS)
        f_W[3].set_color(ARRIVALS)
        f_W[5].set_color(KERNEL)
        f_W.scale(0.9).to_corner(UR, buff=0.45)
        fix_in_frame(self, f_W)

        self.play(
            FadeIn(cap6),
            Create(wall_edge), FadeIn(wall_grid), FadeIn(wall_nums),
            ReplacementTransform(f_E[0], f_W[0]), ReplacementTransform(f_E[1], f_W[1]),
            FadeIn(f_W[2]),
            ReplacementTransform(f_E[2], f_W[3]), ReplacementTransform(f_E[3], f_W[4]),
            ReplacementTransform(f_E[4], f_W[5]), FadeOut(f_E[5]),
            run_time=1.4,
        )
        self.play(
            LaggedStart(*[ReplacementTransform(all_ribs[i], bands[i]) for i in range(H)],
                        lag_ratio=0.18),
            run_time=3.4,
        )

        # bands -> daily bars W_arr(d)
        wall_bars = VGroup()
        for d in range(1, H + 1):
            h = max(Wd[d - 1], 0.004)
            bar = Polygon(PW(d - 0.38, 0), PW(d + 0.38, 0), PW(d + 0.38, h), PW(d - 0.38, h),
                          stroke_width=0, fill_color=ARRIVALS, fill_opacity=0.9)
            wall_bars.add(bar)
        band_grp = VGroup(*bands)
        cap6b = caption(r"new cohorts need time to ripen")
        fix_in_frame(self, cap6b)
        self.play(FadeIn(wall_bars), FadeOut(band_grp), FadeOut(cap6), FadeIn(cap6b), run_time=1.2)
        self.wait(2.0)

        # ------------------------------------------------------------------
        # Beat 7 -- name it: a convolution. Face the wall.
        # ------------------------------------------------------------------
        wall_dn = VGroup(*[
            standing(MathTex(str(d), font_size=FS_TICK + 2, color=MUTED)).move_to(PW(d, -0.32))
            for d in (1, 5, 10, 15)
        ])
        wall_base = Line(PW(0, 0), PW(16, 0), color=MUTED, stroke_width=2)
        wall_dt = standing(Tex(r"conversion day $d$", font_size=FS_LABEL, color=MUTED)).move_to(PW(8, -0.75))
        wall_yt = standing(Tex(r"expected wins / day", font_size=FS_LABEL, color=MUTED)).move_to(PW(2.6, 3.05))

        f_C = MathTex(r"W_{\text{arr}}(d)", r"=", r"\sum_{t\le d}", r"\hat{A}(t)", r"\,",
                      r"k(d-t)", r"=", r"(\hat{A} * k)(d)", font_size=FS_FORMULA)
        f_C[0].set_color(ARRIVALS)
        f_C[3].set_color(ARRIVALS)
        f_C[5].set_color(KERNEL)
        f_C[7][1:3].set_color(ARRIVALS)
        f_C[7][4].set_color(KERNEL)
        f_C.to_corner(UR, buff=0.45)
        fix_in_frame(self, f_C)
        cap7 = caption(r"a convolution of arrivals with the kernel")
        fix_in_frame(self, cap7)

        self.move_camera(
            phi=90 * DEGREES, theta=-90 * DEGREES, zoom=1.12, frame_center=PW(8.3, 1.25),
            added_anims=[
                FadeOut(VGroup(floor_axes, back_edge, right_edge, floor_labels), rate_func=early),
                FadeIn(VGroup(wall_dn, wall_dt, wall_yt), rate_func=late), Create(wall_base),
            ],
            run_time=2.7,
        )
        self.play(*[ReplacementTransform(f_W[i], f_C[i]) for i in range(6)], run_time=0.9)
        self.play(
            FadeIn(f_C[6], shift=LEFT * 0.2), FadeIn(f_C[7], shift=LEFT * 0.2),
            FadeOut(cap6b), FadeIn(cap7),
            run_time=1.2,
        )
        self.wait(3.0)
        close_chapter(self)
