import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import *

# ---------------------------------------------------------------------------
# Chapter 09 -- Wins from future arrivals (3D)
#   one cohort: the 14 deals arriving on day 2 replay the kernel from day 2 on,
#   E_arr(t, d) = A_hat(t) k(d - t); every cohort does the same one day later
#   (a triangular band of towers); from above it is the arrivals heat-map;
#   stacking each day's column on the far wall gives W_arr(d), a convolution.
#   Grammar rhymes with chapter 07: level row -> tilt -> all rows rise ->
#   top-view heat-map -> back up -> make room -> stack on the wall -> front view.
# ---------------------------------------------------------------------------

D = load_data()
H = int(D.meta.horizon)                 # 15
CW = 0.42                               # cell width = depth (scene units)
X0, Y0 = -3.15, -3.15                   # floor's lower-left corner
X1, Y1 = X0 + H * CW, Y0 + H * CW       # 3.15, 3.15
ZS = 5.0                                # cell scale: scene units per expected win
ZW = 1.0                                # wall scale
T_DEMO = 2                              # the cohort we follow (Mon 5 May)
Z_TOP = 2.6                             # height of the z-axis line

# camera framings (presets from common.py plus zoom / frame centre). In the
# level views the frame centre sits 1.2-1.3 above the floor, which lowers the
# bar chart on screen; the floor is empty there, so no floor band shows.
FRONT_A = dict(CAM_FRONT, zoom=1.45, frame_center=np.array([0.0, 0.0, 1.2]))
VIEW_3D = dict(CAM_3D, zoom=0.92, frame_center=np.array([0.6, 0.0, 0.55]))
VIEW_TOP = dict(CAM_TOP, zoom=0.7, frame_center=np.array([1.2, -0.45, 0.0]))
FRONT_B = dict(CAM_FRONT, zoom=1.4, frame_center=np.array([0.0, 0.0, 1.6]))

D_LAB_3D = DOWN * 0.12                  # day-number offset at the front edge
DT_3D = ((X0 + 5.5 * CW), Y0 - 0.22, 0.0)   # "forecast day d" anchor at the front edge
DT_OFF_3D = np.array([-0.45, -0.55, 0.0])


def col_x(d):
    """x of the centre of forecast-day column d (1-based)."""
    return X0 + (d - 0.5) * CW


def row_y(t):
    """y of the centre of arrival-day row t (1-based); row_origin="upper": t = 1 farthest."""
    return Y0 + (H - t + 0.5) * CW


def _to_cam(cam):
    phi, theta = cam.get_phi(), cam.get_theta()
    return np.array([np.sin(phi) * np.cos(theta), np.sin(phi) * np.sin(theta), np.cos(phi)])


class FL(Line):
    """FloorLine with the camera as a class attribute (copies made by fades never
    deep-copy the camera): always paints under every shaded mobject."""
    cam = None

    def __init__(self, start, end, **kwargs):
        kwargs.setdefault("color", GRID)
        kwargs.setdefault("stroke_width", 1.5)
        super().__init__(start, end, **kwargs)
        self.set_shade_in_3d(True)

    def get_z_index_reference_point(self):
        return -1e3 * _to_cam(FL.cam)


class FloorPoly(Polygon):
    """A filled polygon on the floor that paints under every shaded mobject."""

    def __init__(self, *points, **kwargs):
        super().__init__(*points, **kwargs)
        self.set_shade_in_3d(True)

    def get_z_index_reference_point(self):
        return -1e3 * _to_cam(FL.cam)


def ctex(*parts, colors=(), font_size=FS_CAPTION, color=INK):
    """Tex from parts; colors[i] (or None) colours part i."""
    t = Tex(*parts, font_size=font_size, color=color)
    for i, c in enumerate(colors):
        if c is not None:
            t[i].set_color(c)
    return t


def cap_of(*parts, colors=()):
    c = ctex(*parts, colors=colors)
    if c.width > 12.4:
        c.scale_to_fit_width(12.4)
    return c.to_edge(DOWN, buff=0.5)


class Clip(ThreeDScene):
    # ---- helpers -----------------------------------------------------------
    def screen(self, pts):
        """Screen (frame) coordinates of 3D points for the current camera."""
        cam = self.renderer.camera
        cam.reset_rotation_matrix()
        return cam.project_points(np.array(pts, dtype=float))

    def pin(self, mob, point, offset=ORIGIN):
        """Camera-facing label at a 3D anchor with a screen offset; the anchor
        can move later (move_pins)."""
        mob.anchor = np.array(point, dtype=float)
        mob.offset = np.array(offset, dtype=float)
        mob.move_to(mob.anchor + mob.offset)
        self.add_fixed_orientation_mobjects(mob, center_func=lambda m=mob: m.anchor)
        self.remove(mob)
        return mob

    def move_pins(self, items):
        """Slide pinned labels: items of (mob, new_anchor or None, new_offset or None)."""
        data = []
        for m, a1, o1 in items:
            a0, o0 = m.anchor.copy(), m.offset.copy()
            data.append((m, a0, o0, a0 if a1 is None else np.array(a1, float), o0 if o1 is None else np.array(o1, float)))

        def upd(_, alpha):
            a = smooth(alpha)
            for m, a0, o0, a1, o1 in data:
                m.anchor = a0 + (a1 - a0) * a
                m.offset = o0 + (o1 - o0) * a
                m.move_to(m.anchor + m.offset)

        return UpdateFromAlphaFunc(self.host, upd)

    def move_lines(self, lines, vec):
        """Translate 3D lines by ``vec``."""
        vec = np.array(vec, dtype=float)
        data = [(l, l.get_center().copy()) for l in lines]

        def upd(_, alpha):
            a = smooth(alpha)
            for l, c0 in data:
                l.move_to(c0 + vec * a)

        return UpdateFromAlphaFunc(self.host, upd)

    def grow(self, T, ks, f_from, f_to, starts=None, length=1.0, fade_in=False):
        """Towers ``ks`` from f_from to f_to times their native height, each in
        [start, start + length] of the animation; ``fade_in`` raises their
        opacity from 0 in the first quarter of their rise."""
        ks = np.asarray(ks, dtype=int)
        starts = np.zeros(len(ks)) if starts is None else np.asarray(starts, dtype=float)
        faces = [list(T.tower_list[k]) for k in ks]

        def upd(_, alpha):
            t = np.clip((alpha - starts) / length, 0, 1)
            r = np.array([smooth(x) for x in t])
            T.h[ks] = T.base_h[ks] * (f_from + (f_to - f_from) * r)
            if fade_in:
                op = np.clip(t / 0.25, 0, 1)
                for fs, o in zip(faces, op):
                    for f in fs:
                        f.set_fill(opacity=o)
                        f.set_stroke(opacity=o)
            T._refresh(ks)

        return UpdateFromAlphaFunc(self.host, upd)

    def recolor_faces(self, faces, targets):
        """Animate each face's fill and stroke to its target colour."""
        c0 = [f.get_fill_color() for f in faces]
        c1 = [ManimColor(c) for c in targets]

        def upd(_, alpha):
            a = smooth(alpha)
            for f, a0, a1 in zip(faces, c0, c1):
                c = interpolate_color(a0, a1, a)
                f.set_fill(c)
                f.set_stroke(c)

        return UpdateFromAlphaFunc(self.host, upd)

    @staticmethod
    def solid(kind, color, front=1.0):
        if kind == "top":
            return ManimColor(color)
        if kind in ("front", "back"):
            return shade(color, front)
        return shade(color, 0.46)

    # ---- the chapter ---------------------------------------------------------
    def construct(self):
        flat_shading(self)
        FL.cam = self.renderer.camera
        # driver for the custom updaters; added first, so whenever it animates every
        # mobject after it (all of them) is redrawn (else Cairo freezes the towers)
        self.host = Mobject()
        self.add(self.host)
        A = D.arrivals.forecast                   # (15,) A_hat(t)
        k = D.kernel.win_mass                     # (46,) k(a)
        E = D.arrivals.surface                    # (15, 15) [t-1, d-1]
        W = D.arrivals.by_day                     # (15,) W_arr(d)
        a2 = float(A[T_DEMO - 1])                 # 14.07

        self.set_camera_orientation(**FRONT_A)
        open_chapter(self, 9, "Wins from future arrivals", ARRIVALS,
                     question="When will deals that don't exist yet start to win?",
                     part=PART[4])

        # ==================================================================
        # Beat 2 -- re-establish the two ingredients (2D overlays, pinned)
        # ==================================================================
        ax_a = make_axes([0, 16, 1], [0, 20, 5], 5.0, 2.6).move_to([-3.45, -0.5, 0])
        bars_a = bars(ax_a, np.arange(1, H + 1), A, ARRIVALS, width=0.72)
        tk_a = VGroup(
            VGroup(*[MathTex(str(v), font_size=FS_TICK, color=MUTED).next_to(ax_a.c2p(v, 0), DOWN, buff=0.14)
                     for v in (1, 5, 10, 15)]),
            VGroup(*[MathTex(str(v), font_size=FS_TICK, color=MUTED).next_to(ax_a.c2p(0, v), LEFT, buff=0.14)
                     for v in (5, 10, 15)]),
        )
        xl_a = Tex(r"arrival day $t$", font_size=FS_LABEL, color=MUTED).next_to(tk_a[0], DOWN, buff=0.14)
        ti_a = ctex(r"$\hat{A}(t)$", r"\,: new deals per day", colors=(ARRIVALS,), font_size=FS_LABEL + 3)
        ti_a.next_to(ax_a.c2p(0, 20), UP, buff=0.45).align_to(ax_a.c2p(0, 0), LEFT)
        grp_a = VGroup(ax_a, tk_a, xl_a, ti_a)

        K_TOP = 0.035
        ax_k = make_axes([0, 46, 5], [0, K_TOP, 0.01], 5.0, 2.6).move_to([3.45, -0.5, 0])
        bars_k = bars(ax_k, np.arange(46) + 0.5, k, KERNEL, width=0.78)
        tk_k = VGroup(
            VGroup(*[MathTex(str(v), font_size=FS_TICK, color=MUTED).next_to(ax_k.c2p(v + 0.5, 0), DOWN, buff=0.14)
                     for v in (0, 15, 30, 45)]),
            VGroup(*[MathTex(f"{v:.2f}", font_size=FS_TICK, color=MUTED).next_to(ax_k.c2p(0, v), LEFT, buff=0.14)
                     for v in (0.01, 0.02, 0.03)]),
        )
        xl_k = Tex(r"age $a$ (business days)", font_size=FS_LABEL, color=MUTED).next_to(tk_k[0], DOWN, buff=0.14)
        ti_k = ctex(r"$k(a)$", r"\,: chance a new deal wins at age $a$", colors=(KERNEL,), font_size=FS_LABEL + 3)
        ti_k.next_to(ax_k.c2p(0, K_TOP), UP, buff=0.45).align_to(ax_k.c2p(0, 0), LEFT)
        grp_k = VGroup(ax_k, tk_k, xl_k, ti_k)

        fix_in_frame(self, grp_a, bars_a, grp_k, bars_k)
        self.play(Create(ax_a), Create(ax_k), FadeIn(tk_a), FadeIn(tk_k), FadeIn(xl_a), FadeIn(xl_k),
                  run_time=1.0)
        self.play(LaggedStart(*[GrowFromEdge(b, DOWN) for b in bars_a], lag_ratio=0.06),
                  LaggedStart(*[GrowFromEdge(b, DOWN) for b in bars_k], lag_ratio=0.02),
                  FadeIn(ti_a), FadeIn(ti_k), run_time=1.4)
        self.wait(0.4)

        # highlight t = 2: Monday 5 May
        b2 = bars_a[T_DEMO - 1]
        ring = SurroundingRectangle(b2, corner_radius=0.1, stroke_width=2, color=ARRIVALS, buff=0.07)
        lab2 = VGroup(Tex("Mon 5 May", font_size=FS_LABEL, color=INK),
                      MathTex(rf"\hat{{A}}(2) = {a2:.1f}", font_size=FS_LABEL + 2, color=ARRIVALS))
        lab2.arrange(DOWN, buff=0.1, aligned_edge=LEFT).next_to(ring, UP, buff=0.12).align_to(ring, LEFT)
        fix_in_frame(self, ring, lab2)
        self.play(*[b.animate.set_opacity(0.3) for i, b in enumerate(bars_a) if i != T_DEMO - 1],
                  Create(ring), FadeIn(lab2, shift=UP * 0.1), run_time=1.0)
        cap = swap_caption(self, None, "14 new deals arrive on day 2")
        self.wait(2.4)

        # ==================================================================
        # Beat 3 -- one cohort, level camera: the row t = 2 is a bar chart
        # ==================================================================
        T = HeatTowers(E, cell_w=CW, cell_d=CW, z_scale=ZS, ramp=ARRIVALS_RAMP,
                       origin=(X0, Y0, 0), row_origin="upper")
        T.set_lift(0.0)
        row_ks = [tw.k for tw in T.tower_list if tw.i == T_DEMO - 1]
        other_ks = [tw.k for tw in T.tower_list if tw.i != T_DEMO - 1]
        row_faces = [f for kk in row_ks for f in T.tower_list[kk]]
        heat_cols = [f.get_fill_color() for f in row_faces]          # the row's heat colours, for later
        for f in row_faces:                                          # the demo row starts solid blue
            c = self.solid(f.kind, ARRIVALS, front=1.0)
            f.set_fill(c)
            f.set_stroke(c)
        for kk in row_ks + other_ks:
            for f in T.tower_list[kk]:
                f.set_fill(opacity=0.0)
                f.set_stroke(opacity=0.0)
        self.add(T)

        hd = float(T.hd[0])
        hw = float(T.hw[0])
        y_row = row_y(T_DEMO) - hd                 # front face of the demo row

        # day axis in front of the row (it slides to the floor's front edge later)
        day_axis = FL((X0, y_row, 0), (X1, y_row, 0), color=MUTED, stroke_width=2)
        d_main = {d: self.pin(MathTex(str(d), font_size=FS_TICK, color=MUTED), (col_x(d), y_row, 0), DOWN * 0.3)
                  for d in (5, 10, 15)}
        d_one = self.pin(MathTex("1", font_size=FS_TICK, color=MUTED), (col_x(1), y_row, 0), DOWN * 0.3)
        d_two = self.pin(MathTex("2", font_size=FS_TICK + 2, color=ARRIVALS), (col_x(2), y_row, 0), DOWN * 0.3)
        day_title = self.pin(Tex(r"forecast day $d$", font_size=FS_LABEL, color=MUTED),
                             (0.5 * (X0 + X1), y_row, 0), DOWN * 0.78)

        # z-axis post at the row's left end (it slides back to the far-left corner later)
        post = FL((X0, y_row, 0), (X0, y_row, Z_TOP), color=MUTED, stroke_width=2)
        post_marks = VGroup(*[FL((X0 - 0.09, y_row, z), (X0, y_row, z), color=MUTED, stroke_width=2)
                              for z in (1.0, 2.0)])
        post_labels = [self.pin(MathTex(s, font_size=FS_TICK, color=MUTED), (X0, y_row, z), LEFT * 0.38)
                       for s, z in (("0.2", 1.0), ("0.4", 2.0))]
        post_title = self.pin(Tex("expected wins", font_size=FS_LABEL, color=MUTED).rotate(PI / 2),
                              (X0, y_row, 0.5 * Z_TOP), LEFT * 0.9)

        # the 14 deals as blue dots standing on day 2
        p_base = self.screen([(col_x(2), y_row, 0)])[0]
        dots = VGroup(*[Dot(radius=0.055, color=ARRIVALS) for _ in range(14)])
        dots.arrange_in_grid(rows=7, cols=2, buff=0.075)
        dots.move_to(p_base + UP * (dots.height / 2 + 0.09))
        fix_in_frame(self, dots)
        # the bar breaks into 14 slices, each becomes one deal (same structure: nothing unpinned)
        slices = VGroup(*[Rectangle(width=b2.width, height=b2.height / 14, stroke_width=0,
                                    fill_color=ARRIVALS, fill_opacity=0.9) for _ in range(14)])
        slices.arrange(UP, buff=0).move_to(b2)
        fix_in_frame(self, slices)
        self.add(slices)
        self.remove(b2)

        kgroup = VGroup(grp_k, bars_k)
        self.play(FadeOut(grp_a), FadeOut(VGroup(*[b for i, b in enumerate(bars_a) if i != T_DEMO - 1])),
                  FadeOut(ring), FadeOut(lab2),
                  kgroup.animate.scale(0.72).to_corner(UR, buff=0.4).shift(DOWN * 0.15),
                  run_time=1.1)
        self.play(ReplacementTransform(slices, dots),
                  Create(day_axis), Create(post), Create(post_marks),
                  *[FadeIn(m) for m in (*d_main.values(), d_one, d_two, day_title, *post_labels, post_title)],
                  run_time=1.4)
        cap = swap_caption(self, cap, "their wins follow the kernel, from day 2 on")
        self.wait(1.5)

        # kernel bars (ages 0..13) -> outlines over days 2..15, scaled by 14.1
        outlines = VGroup()
        for d in range(T_DEMO, H + 1):
            kk = [tw.k for tw in T.tower_list if tw.i == T_DEMO - 1 and tw.j == d - 1][0]
            h = float(T.base_h[kk])
            p0, p1 = self.screen([(col_x(d) - hw, y_row, 0), (col_x(d) + hw, y_row, h)])
            r = Rectangle(width=p1[0] - p0[0], height=max(p1[1] - p0[1], 0.01),
                          stroke_color=KERNEL, stroke_width=2, fill_color=KERNEL, fill_opacity=0.14)
            r.move_to([(p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2, 0])
            outlines.add(r)
        fix_in_frame(self, outlines)
        movers = VGroup(*[bars_k[a].copy() for a in range(H - T_DEMO + 1)])
        fix_in_frame(self, movers)
        self.add(movers)
        self.play(*[ReplacementTransform(m, o) for m, o in zip(movers, outlines)],
                  FadeOut(grp_k), FadeOut(bars_k), run_time=2.2)
        self.wait(0.4)

        # the row rises into the outlines, left to right
        js = np.array([T.tower_list[kk].j for kk in row_ks], dtype=float)
        st = (js - js.min()) / np.ptp(js) * 0.45
        self.play(self.grow(T, row_ks, 0, 1, starts=st, length=0.55, fade_in=True),
                  FadeOut(outlines, rate_func=delayed(0.72, 0.28)), run_time=2.8)
        self.wait(0.3)

        # the formula, term by term, with words
        F = MathTex(r"E_{\text{arr}}(t,d)", "=", r"\hat{A}(t)", r"\,k(d-t)", font_size=FS_FORMULA)
        F[0].set_color(ARRIVALS)
        F[2].set_color(ARRIVALS)
        F[3].set_color(KERNEL)
        w1 = ctex(r"expected wins on day $d$ from day-$t$ arrivals", font_size=FS_LABEL, color=MUTED)
        w2 = ctex(r"brand new on day $t$: no conditioning needed", font_size=FS_LABEL)
        blk = VGroup(F, w1, w2).arrange(DOWN, aligned_edge=RIGHT, buff=0.2)
        blk.to_corner(UR, buff=0.45)
        fix_in_frame(self, blk)
        self.play(Write(F[0]), FadeIn(w1, shift=UP * 0.08), run_time=1.0)
        self.play(FadeIn(F[1]), FadeIn(F[2]), run_time=0.8)
        self.play(FadeIn(F[3]), run_time=0.8)
        self.play(FadeIn(w2, shift=UP * 0.08), run_time=0.8)
        self.wait(3.0)

        # ==================================================================
        # Beat 4 -- tilt, then every cohort rises
        # ==================================================================
        grid = VGroup()
        for c in range(H + 1):
            grid.add(FL((X0 + c * CW, Y0, 0), (X0 + c * CW, Y1, 0), stroke_width=1.5 if c in (0, H) else 0.9))
        for r in range(H + 1):
            grid.add(FL((X0, Y0 + r * CW, 0), (X1, Y0 + r * CW, 0), stroke_width=1.5 if r in (0, H) else 0.9))
        t_labels = [self.pin(MathTex(str(t), font_size=FS_TICK, color=MUTED), (X0 - 0.22, row_y(t), 0), LEFT * 0.14)
                    for t in (5, 10, 15)]
        t_title = self.pin(Tex(r"arrival day $t$", font_size=FS_LABEL, color=MUTED), (X0 - 0.22, 0.0, 0), LEFT * 1.55)

        dy_front = (Y0 - 0.0) - y_row               # day axis: row -> front edge
        dy_back = Y1 - y_row                         # z-axis post: row -> far-left corner
        front_faces = [f for f in row_faces if f.kind == "front"]
        self.move_camera(**VIEW_3D, run_time=3.75, added_anims=[
            FadeOut(dots, rate_func=delayed(0.0, 0.25)),
            FadeOut(VGroup(d_one, d_two), rate_func=delayed(0.0, 0.25)),
            FadeOut(w2, rate_func=delayed(0.0, 0.3)),
            self.move_lines([day_axis], [0, dy_front, 0]),
            self.move_lines([post, *post_marks], [0, dy_back, 0]),
            self.move_pins([(m, (col_x(d), Y0 - 0.22, 0), D_LAB_3D) for d, m in d_main.items()]
                           + [(day_title, DT_3D, DT_OFF_3D)]
                           + [(m, m.anchor + [0, dy_back, 0], None) for m in (*post_labels, post_title)]),
            self.recolor_faces(front_faces, [shade(ARRIVALS, 0.66)] * len(front_faces)),
            FadeIn(grid, rate_func=delayed(0.3, 0.5)),
            *[FadeIn(m, rate_func=delayed(0.6, 0.4)) for m in (*t_labels, t_title)],
        ])
        cap = swap_caption(self, cap, "each cohort replays the kernel, one day later")
        self.wait(1.5)
        ii = np.array([T.tower_list[kk].i for kk in other_ks], dtype=float)
        st = (ii - ii.min()) / np.ptp(ii) * 0.62
        rec = self.recolor_faces(row_faces, heat_cols)
        rec.rate_func = delayed(0.0, 0.3)
        self.play(self.grow(T, other_ks, 0, 1, starts=st, length=0.38, fade_in=True), rec, run_time=3.5)
        self.begin_ambient_camera_rotation(rate=0.035)
        self.wait(0.8)

        # the empty triangle: nothing before a deal exists (d < t)
        stair = [(X0, Y0, 0)]
        for t in range(H, T_DEMO - 1, -1):
            xb = X0 + (t - 1) * CW
            stair += [(xb, Y0 + (H - t) * CW, 0), (xb, Y0 + (H - t + 1) * CW, 0)]
        stair += [(X0, Y0 + (H - 1) * CW, 0)]
        tri = FloorPoly(*stair, stroke_color=INK, stroke_width=1.6, stroke_opacity=0.7,
                        fill_color=INK, fill_opacity=0.07)
        tl = VGroup(ctex("nothing before", font_size=FS_LABEL), ctex(r"a deal exists ($d < t$)", font_size=FS_LABEL))
        tl.arrange(DOWN, buff=0.1)
        tri_lab = self.pin(tl, (X0 + 1.9, Y0 + 1.75, 0))
        self.play(FadeIn(tri), FadeIn(tri_lab, shift=UP * 0.08), run_time=1.0)
        self.wait(3.0)
        self.play(FadeOut(tri), FadeOut(tri_lab), run_time=0.7)
        self.stop_ambient_camera_rotation()

        # ==================================================================
        # Beat 5 -- seen from above: the arrivals heat-map
        # ==================================================================
        z_axis = VGroup(post, post_marks)
        z_labels = VGroup(*post_labels, post_title)
        vmax = T.vmax
        n_sw = 24
        sw = VGroup(*[Rectangle(width=2.6 / n_sw, height=0.22, stroke_width=0,
                                fill_color=ramp_color(ARRIVALS_RAMP, (i + 0.5) / n_sw), fill_opacity=1)
                      for i in range(n_sw)]).arrange(RIGHT, buff=0)
        sw_frame = SurroundingRectangle(sw, buff=0, stroke_color=PANEL_EDGE, stroke_width=1.2)
        sw_nums = VGroup(*[MathTex(s, font_size=FS_TICK, color=MUTED).next_to(sw.get_left() + RIGHT * 2.6 * v / vmax, DOWN, buff=0.12)
                           for s, v in (("0", 0.0), ("0.2", 0.2), ("0.4", 0.4))])
        sw_title = Tex("expected wins", font_size=FS_LABEL, color=MUTED).next_to(sw, UP, buff=0.14).align_to(sw, LEFT)
        key = VGroup(sw_title, sw, sw_frame, sw_nums).move_to([4.5, 0.3, 0])
        fix_in_frame(self, key)
        self.move_camera(**VIEW_TOP, run_time=3.5, added_anims=[
            T.lift(1, 0),
            FadeOut(z_axis, rate_func=delayed(0.0, 0.3)),
            FadeOut(z_labels, rate_func=delayed(0.0, 0.3)),
            FadeIn(key, rate_func=delayed(0.72, 0.28)),
        ])
        cap = swap_caption(self, cap, "from above: the arrivals heat-map")
        self.wait(3.0)

        # ==================================================================
        # Beat 6 -- back up, and make room on the wall scale
        # ==================================================================
        self.move_camera(**VIEW_3D, run_time=3.0, added_anims=[
            T.lift(0, 1),
            FadeOut(key, rate_func=delayed(0.0, 0.3)),
            FadeIn(z_axis, rate_func=delayed(0.55, 0.4)),
            FadeIn(z_labels, rate_func=delayed(0.6, 0.4)),
        ])
        cap = swap_caption(self, cap, "now add up each day")
        self.wait(1.5)
        wall_grid = VGroup(*[FL((X0, Y1, z), (X1, Y1, z), color=GRID, stroke_width=1.2) for z in (1.0, 2.0)])
        wall_labels = [self.pin(MathTex(s, font_size=FS_TICK, color=MUTED), (X0, Y1, z), LEFT * 0.3)
                       for s, z in (("1", 1.0), ("2", 2.0))]
        wall_title = self.pin(Tex("expected wins per day", font_size=FS_LABEL, color=MUTED).rotate(PI / 2),
                              (X0, Y1, 0.5 * Z_TOP), LEFT * 0.75)
        self.play(T.lift(1, ZW / ZS),
                  *[FadeOut(m, shift=UP * 0.1, rate_func=delayed(0.0, 0.4)) for m in (*post_labels, post_title)],
                  *[FadeIn(m, shift=UP * 0.1, rate_func=delayed(0.45, 0.55)) for m in (*wall_labels, wall_title)],
                  Create(wall_grid, rate_func=delayed(0.4, 0.6)),
                  run_time=2.2)
        self.wait(0.3)

        # ==================================================================
        # Beat 7 -- payoff: stack every column onto the wall
        # ==================================================================
        self.play(T.collapse(axis="y", z_scale_wall=ZW), run_time=3.7)
        B = T.merge(self, ARRIVALS, run_time=1.0)
        cap = swap_caption(self, cap, cap_of(r"each day's column, stacked: ", r"$W_{\text{arr}}(d)$",
                                             colors=(None, ARRIVALS)))
        self.wait(2.6)

        # ==================================================================
        # Beat 8 -- the wall faces us: a bar chart of W_arr(d)
        # ==================================================================
        y_wall = float(B.cy[0] - B.hd[0])          # front face of the wall bars
        dyw = y_wall - Y0
        b_front = [f for tw in B.tower_list for f in tw if f.kind == "front"]
        self.move_camera(**FRONT_B, run_time=3.0, added_anims=[
            FadeOut(grid, rate_func=delayed(0.0, 0.35)),
            *[FadeOut(m, rate_func=delayed(0.0, 0.3)) for m in (*t_labels, t_title)],
            self.move_lines([day_axis], [0, dyw, 0]),
            self.move_lines([post, *post_marks, *wall_grid], [0, y_wall - Y1, 0]),
            self.move_pins([(m, (col_x(d), y_wall, 0), DOWN * 0.3) for d, m in d_main.items()]
                           + [(day_title, (0.5 * (X0 + X1), y_wall, 0), DOWN * 0.78)]
                           + [(m, m.anchor + [0, y_wall - Y1, 0], None) for m in (*wall_labels, wall_title)]),
            self.recolor_faces(b_front, [ARRIVALS] * len(b_front)),
        ])

        # E_arr(t, d) = A(t) k(d-t)  ->  W_arr(d) = sum_{t<=d} A(t) k(d-t)
        G = MathTex(r"W_{\text{arr}}(d)", "=", r"\sum_{t \le d}", r"\hat{A}(t)", r"\,k(d-t)", font_size=FS_FORMULA)
        G[0].set_color(ARRIVALS)
        G[3].set_color(ARRIVALS)
        G[4].set_color(KERNEL)
        G.to_corner(UR, buff=0.45)
        br = Brace(G[2:], DOWN, buff=0.1, color=MUTED)
        br_txt = ctex(r"a convolution: arrivals smeared by the kernel", font_size=FS_LABEL)
        br_txt.next_to(br, DOWN, buff=0.1).align_to(G, RIGHT)
        fix_in_frame(self, G, br, br_txt)
        self.play(Transform(F[0], G[0]), Transform(F[1], G[1]), Transform(F[2], G[3]), Transform(F[3], G[4]),
                  FadeIn(G[2]), FadeOut(w1, rate_func=delayed(0.0, 0.4)), run_time=1.8)
        self.play(GrowFromCenter(br), FadeIn(br_txt, shift=UP * 0.08), run_time=1.0)
        self.wait(0.8)

        p_ax = self.screen([(X0, y_wall, 2.42)])[0]
        tot = ctex(rf"{W.sum():.1f}", rf" expected wins over {H} days", colors=(ARRIVALS,), font_size=FS_BODY)
        tot.move_to(p_ax, aligned_edge=LEFT).shift(RIGHT * 0.45)
        fix_in_frame(self, tot)
        v_first = self.pin(MathTex(f"{W[0]:.1f}", font_size=FS_TICK, color=INK), (col_x(1), y_wall, W[0] * ZW), UP * 0.24)
        v_last = self.pin(MathTex(f"{W[-1]:.1f}", font_size=FS_TICK, color=INK), (col_x(H), y_wall, W[-1] * ZW), UP * 0.24)
        self.play(FadeIn(tot, shift=UP * 0.1), FadeIn(v_first, shift=DOWN * 0.08),
                  FadeIn(v_last, shift=DOWN * 0.08), run_time=1.0)
        self.wait(0.8)
        cap = swap_caption(self, cap, "new deals need time to ripen")
        self.wait(3.2)

        # ==================================================================
        # Beat 9 -- takeaway
        # ==================================================================
        takeaway(self, "new deals' wins build up across the horizon", ARRIVALS, old_caption=cap)
        self.remove(self.host)
        close_chapter(self)
