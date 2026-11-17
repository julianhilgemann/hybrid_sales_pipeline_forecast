import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import *

# chapter 03 -- Wins from the existing pipeline
#
# flat ingredients N(a) and k(a) -> one bucket (a = 8): survived part greys out,
# the window k(a+1..a+15) lights up, is divided by S(8) and multiplied by N(8)
# -> lifts off as a ribbon -> 3D: every age bucket's ribbon -> diagonal crests
# -> straight down: the existing-pipeline heat-map -> back to 3D, collapse along
# age onto the back wall -> W_stock(d) bars.

H = 15
A_MAX = 45            # ages 0..44 carry wins; 45 is the pooled 45+ bucket
A_SEL = 8             # the highlighted bucket

# ---------------------------------------------------------------- 3D geometry
UX, UY, UZ = 0.6, 0.15, 4.0      # world units per forecast day / per age / per win (relief)
UW = 0.8                          # world units per win on the back wall (W_stock)
D_C, A_C = 8.0, 22.0              # floor centre (d, a)
A_WALL = 44.5                     # the back wall sits on the far floor edge
SHEET_OP = 0.13
EDGE_W = 1.8
EDGE_COL = "#FF9DB0"     # lighter rose for the ribbon tops so the relief reads

# the shared CAM_3D angle (d to the right, age receding): ribbons are seen as slices,
# so their crests line up into the diagonal ridges
CAM_PERSP = dict(phi=60 * DEGREES, theta=-58 * DEGREES, zoom=0.9,
                 frame_center=np.array([-0.9, 0.0, -0.9]))
CAM_DOWN = dict(phi=0 * DEGREES, theta=-90 * DEGREES, zoom=0.74,
                frame_center=np.array([0.0, -0.4, 0.0]))
# nearly frontal on the back wall for the W_stock bars
CAM_WALL = dict(phi=74 * DEGREES, theta=-95 * DEGREES, zoom=0.85,
                frame_center=np.array([0.3, 1.5, 0.35]))


def P(d, a, z=0.0):
    """World point for forecast day d, age a, relief value z (wins/day)."""
    return np.array([(d - D_C) * UX, (a - A_C) * UY, z * UZ])


def PW(d, w):
    """World point on the back wall at forecast day d, height w (wins/day, wall scale)."""
    return np.array([(d - D_C) * UX, (A_WALL - A_C) * UY, w * UW])


class DepthPoly(Polygon):
    """Polygon whose depth-sort key is its mean floor position (x = 0, mean y),
    so parallel age-ribbons always sort by age regardless of their height."""
    bias = 0.0

    def get_z_index_reference_point(self):
        y = self.points[:, 1].mean() if len(self.points) else 0.0
        return np.array([0.0, y - self.bias, 0.0])


class DepthPath(VMobject):
    bias = 1e-3     # drawn just after the sheet it belongs to

    def get_z_index_reference_point(self):
        y = self.points[:, 1].mean() if len(self.points) else 0.0
        return np.array([0.0, y - self.bias, 0.0])


def ribbon(a, vals, color=STOCK, op=SHEET_OP, sw=EDGE_W, scale=1.0, edge_color=EDGE_COL):
    top = [P(d, a, max(v * scale, 1e-4)) for d, v in zip(range(1, H + 1), vals)]
    floor = [P(d, a, 0) for d in range(1, H + 1)]
    sheet = DepthPoly(*top, *reversed(floor), stroke_width=0, fill_color=color, fill_opacity=op)
    # near-empty buckets (old ages) get faint edges so they do not stripe the floor
    e_op = 0.14 + 0.86 * min(1.0, float(np.max(vals)) / 0.15)
    edge = DepthPath(stroke_color=edge_color, stroke_width=sw, stroke_opacity=e_op)
    edge.set_points_as_corners(top)
    g = VGroup(sheet, edge)
    g.set_shade_in_3d(True)
    return g


def band(lo, hi, color, op):
    """Stacked band on the back wall between cumulative profiles lo and hi."""
    top = [PW(d, v) for d, v in zip(range(1, H + 1), hi)]
    bot = [PW(d, v) for d, v in zip(range(1, H + 1), lo)]
    sheet = DepthPoly(*top, *reversed(bot), stroke_width=0.8, stroke_color=color, stroke_opacity=op,
                      fill_color=color, fill_opacity=op)
    edge = DepthPath(stroke_color=color, stroke_width=0.01, stroke_opacity=0)
    edge.set_points_as_corners(top)
    g = VGroup(sheet, edge)
    g.set_shade_in_3d(True)
    return g


def lab(tex, fs=FS_TICK, color=MUTED, math=True):
    return (MathTex if math else Tex)(tex, font_size=fs, color=color)


class Clip(ThreeDScene):
    def pin(self, *mobs):
        fix_in_frame(self, *mobs)

    def anchor(self, mob, point, offset=ORIGIN):
        """Label that follows the projected 3D ``point`` and sits at a fixed *screen*
        ``offset`` from it (so it never foreshortens or drifts into the data)."""
        A = np.array(point, dtype=float)
        mob.move_to(A + np.array(offset, dtype=float))
        self.add_fixed_orientation_mobjects(mob, center_func=lambda: A)
        self.remove(mob)
        return mob

    def pin3d(self, *mobs):
        """Labels that live at a 3D point but always face the camera."""
        self.add_fixed_orientation_mobjects(*mobs)
        self.remove(*mobs)

    def move_cam(self, phi, theta, zoom, frame_center, run_time=3.0, dip=0.0, added_anims=()):
        """Camera move like ``move_camera`` but the zoom dips by ``dip`` mid-way, so the
        floor never swings out of frame (or into the caption) while phi/theta change."""
        cam = self.renderer.camera
        z0 = cam.get_zoom()
        span = zoom - z0

        def zrate(t):
            return smooth(t) - dip * np.sin(np.pi * t) / span

        anims = [
            cam.phi_tracker.animate(rate_func=smooth).set_value(phi),
            cam.theta_tracker.animate(rate_func=smooth).set_value(theta),
            cam.zoom_tracker.animate(rate_func=zrate).set_value(zoom),
            cam._frame_center.animate(rate_func=smooth).move_to(frame_center),
        ]
        self.play(*anims, *added_anims, run_time=run_time)
        self.remove(cam._frame_center)

    def swap_caption(self, old, new, run_time=0.7):
        self.pin(new)
        if old is None:
            self.play(FadeIn(new, shift=UP * 0.15), run_time=run_time)
        else:
            # sequential: the old caption is gone before the new one arrives (never superimposed)
            self.play(FadeOut(old, shift=UP * 0.15), run_time=run_time * 0.4)
            self.play(FadeIn(new, shift=UP * 0.15), run_time=run_time * 0.6)
        return new

    def construct(self):
        D = load_data()
        cam = self.renderer.camera
        cam.should_apply_shading = False          # flat colours; shade flag only drives depth sorting
        N = D.stock.N
        k_raw = D.kernel.win_mass
        k_s = D.kernel.win_mass_smooth
        S = D.kernel.survival
        E = D.stock.surface                       # [a, d-1]
        W = D.stock.by_day
        n_sel = int(N[A_SEL])
        S_sel = float(S[A_SEL])
        e_sel = E[A_SEL]

        header = open_chapter(self, 3, "Wins from the existing pipeline", STOCK)

        # ==============================================================
        # 2. ingredients, flat
        # ==============================================================
        AX0, AW = -5.9, 8.0
        ua = AW / 46.0

        def ax(a):
            return AX0 + (a + 0.5) * ua

        NB, un = 0.45, 0.13          # N chart base y, units per opportunity
        N_CLIP = 16
        KB, uk = -2.45, 52.0         # k chart base y, units per probability

        n_axis = Line([AX0, NB, 0], [AX0 + AW, NB, 0], color=MUTED, stroke_width=2)
        n_yaxis = Line([AX0, NB, 0], [AX0, NB + N_CLIP * un, 0], color=MUTED, stroke_width=2)
        n_ticks = VGroup(*[lab(f"{v}").next_to([AX0, NB + v * un, 0], LEFT, buff=0.12) for v in (0, 10)])
        n_title = lab(r"N(a)", FS_LABEL, STOCK).next_to([AX0, NB + N_CLIP * un, 0], UP, buff=0.12)
        n_title.align_to([AX0 - 0.1, 0, 0], LEFT)

        nbars = VGroup()
        for a in range(46):
            h = min(N[a], N_CLIP) * un
            r = Rectangle(width=0.74 * ua, height=max(h, 1e-3), stroke_width=0,
                          fill_color=STOCK, fill_opacity=0.9 if a < A_MAX else 0.45)
            r.move_to([ax(a), NB, 0], aligned_edge=DOWN)
            nbars.add(r)
        # pooled 45+ bucket: clipped, with a break mark and its true count
        brk = VGroup(*[Line(LEFT * 0.11 + DOWN * 0.03, RIGHT * 0.11 + UP * 0.03, color=BG, stroke_width=3)
                       .move_to([ax(A_MAX), NB + (N_CLIP - 2.5 - 1.2 * i) * un, 0]) for i in range(2)])
        pooled_lab = lab(rf"{int(N[A_MAX])}", FS_TICK, MUTED).next_to(nbars[A_MAX], UP, buff=0.08)

        k_axis = Line([AX0, KB, 0], [AX0 + AW, KB, 0], color=MUTED, stroke_width=2)
        k_yaxis = Line([AX0, KB, 0], [AX0, KB + 0.04 * uk, 0], color=MUTED, stroke_width=2)
        k_ticks = VGroup(*[lab(t).next_to([AX0, KB + v * uk, 0], LEFT, buff=0.12)
                           for v, t in ((0, "0"), (0.02, "0.02"), (0.04, "0.04"))])
        k_title = lab(r"k(a)", FS_LABEL, KERNEL).next_to([AX0, KB + 0.04 * uk, 0], UP, buff=0.12)
        k_title.align_to([AX0 - 0.1, 0, 0], LEFT)
        a_ticks = VGroup(*[lab(f"{v}").next_to([ax(v), KB, 0], DOWN, buff=0.14) for v in (0, 10, 20, 30, 40)])
        a_ticks.add(lab(r"45{+}").next_to([ax(A_MAX), KB, 0], DOWN, buff=0.14))
        a_title = Tex(r"age $a$", font_size=FS_LABEL, color=MUTED).next_to([AX0 + AW, KB, 0], RIGHT, buff=0.25)

        def kcurve(lo, hi, color, width=4):
            ages = np.arange(lo, hi + 1)
            pts = [np.array([ax(a), KB + k_s[a] * uk, 0.0]) for a in ages]
            c = VMobject(stroke_color=color, stroke_width=width)
            c.set_points_smoothly(pts)
            fill = VMobject(stroke_width=0, fill_color=color, fill_opacity=0.18)
            fill.set_points(c.points)
            fill.add_line_to(np.array([ax(hi), KB, 0.0]))
            fill.add_line_to(np.array([ax(lo), KB, 0.0]))
            fill.add_line_to(pts[0])
            return VGroup(fill, c)

        k_left = kcurve(0, A_SEL, KERNEL)
        k_right = kcurve(A_SEL, A_MAX - 1, KERNEL)

        n_chart = VGroup(n_axis, n_yaxis, n_ticks, n_title)
        k_chart = VGroup(k_axis, k_yaxis, k_ticks, k_title, a_ticks, a_title)
        self.pin(n_chart, nbars, brk, pooled_lab, k_chart, k_left, k_right)

        self.play(Create(VGroup(n_axis, n_yaxis)), FadeIn(n_ticks), FadeIn(n_title), run_time=0.8)
        self.play(LaggedStart(*[GrowFromEdge(b, DOWN) for b in nbars], lag_ratio=0.04),
                  run_time=1.4)
        self.play(FadeIn(brk), FadeIn(pooled_lab), run_time=0.4)
        cap = self.swap_caption(None, caption(rf"{int(D.stock.total_active)} open opportunities, by age"))
        self.play(Create(VGroup(k_axis, k_yaxis)), FadeIn(k_ticks), FadeIn(k_title),
                  FadeIn(a_ticks), FadeIn(a_title), run_time=0.8)
        self.play(Create(k_left[1]), Create(k_right[1]), FadeIn(k_left[0]), FadeIn(k_right[0]),
                  run_time=1.4)
        self.wait(1.0)

        # ==============================================================
        # 3. one bucket
        # ==============================================================
        bar8 = nbars[A_SEL]
        others = VGroup(*[b for i, b in enumerate(nbars) if i != A_SEL])
        n8_lab = MathTex(rf"N({A_SEL})", "=", rf"{n_sel}", font_size=FS_LABEL, color=STOCK)
        n8_lab.next_to(bar8, UP, buff=0.12)
        vline = DashedLine([ax(A_SEL), KB, 0], [ax(A_SEL), NB + n_sel * un, 0], color=MUTED,
                           stroke_width=1.6, dash_length=0.07)
        self.pin(n8_lab, vline)
        self.play(others.animate.set_fill(opacity=0.25), brk.animate.set_opacity(0.25),
                  pooled_lab.animate.set_opacity(0.4), bar8.animate.set_fill(color="#FF8FA3"),
                  FadeIn(n8_lab, shift=UP * 0.1), run_time=0.8)
        cap = self.swap_caption(cap, caption(rf"${n_sel}$ open opportunities are ${A_SEL}$ days old"))
        self.wait(1.5)

        # survived part greys out, window a+1 .. a+15 lights up (raw k used by the model)
        stems = VGroup()
        stems_tall = VGroup()
        for dd in range(1, H + 1):
            age = A_SEL + dd
            for grp, val in ((stems, k_raw[age]), (stems_tall, k_raw[age] / S_sel)):
                top = [ax(age), KB + val * uk, 0]
                st = VGroup(Line([ax(age), KB, 0], top, color=KERNEL, stroke_width=4),
                            Dot(top, radius=0.045, color=KERNEL))
                grp.add(st)
        win_lo, win_hi = ax(A_SEL + 0.5), ax(A_SEL + H + 0.5)
        brace = BraceBetweenPoints([win_lo, KB - 0.06, 0], [win_hi, KB - 0.06, 0], DOWN, color=KERNEL, buff=0.04)
        brace_lab = MathTex(r"a+d,\ d=1\dots15", font_size=FS_TICK, color=KERNEL)
        brace_lab.next_to(brace, DOWN, buff=0.06)
        self.pin(stems, brace)
        cap = self.swap_caption(cap, caption(rf"they have already survived ${A_SEL}$ days"),
                                run_time=0.6)
        self.play(k_left[1].animate.set_stroke(color=MUTED, opacity=0.5),
                  k_left[0].animate.set_fill(color=GRID, opacity=0.5), Create(vline), run_time=1.0)
        self.play(k_right[1].animate.set_stroke(opacity=0.35), k_right[0].animate.set_fill(opacity=0.07),
                  a_ticks.animate.set_opacity(0.0),
                  LaggedStart(*[Create(s) for s in stems], lag_ratio=0.08),
                  FadeIn(brace), run_time=1.3)
        self.pin(brace_lab)
        self.play(FadeIn(brace_lab), run_time=0.3)
        self.wait(0.8)

        # divide by S(a): the window stretches upward
        F = MathTex(r"E_{\text{stock}}(a,d)", "=", r"N(a)", r"\cdot", r"\frac{", r"k(a+d)", r"}{",
                    r"S(a)", r"}", font_size=FS_FORMULA)
        F[0].set_color(STOCK)
        F[2].set_color(STOCK)
        F[5].set_color(KERNEL)
        F[7].set_color(SURVIVAL)
        F.to_corner(UR, buff=0.5).shift(DOWN * 0.05)
        s_lab = MathTex(r"\div\, S(8) = " + f"{S_sel:.2f}", font_size=FS_LABEL, color=SURVIVAL)
        s_lab[0][2:6].set_color(SURVIVAL)
        s_lab.next_to([ax(A_SEL + H + 1), KB + 0.028 * uk, 0], RIGHT, buff=0.1)
        self.pin(F, s_lab)
        cap = self.swap_caption(cap, caption(r"divide by $S(8)$: the chance of getting this far"),
                                run_time=0.6)
        self.play(Transform(stems, stems_tall), FadeIn(s_lab, shift=UP * 0.15), run_time=1.4)
        self.play(Write(F[4:]), run_time=0.9)
        self.wait(1.5)

        # multiply by N(a): lift off to its own chart over d = 1..15
        MX0, MW = 2.85, 3.75
        um = MW / 15.0
        MB, uv = -0.9, 3.4

        def mx(d):
            return MX0 + (d - 0.5) * um

        m_axis = Line([MX0, MB, 0], [MX0 + MW, MB, 0], color=MUTED, stroke_width=2)
        m_yaxis = Line([MX0, MB, 0], [MX0, MB + 0.6 * uv, 0], color=MUTED, stroke_width=2)
        m_dt = VGroup(*[lab(f"{v}").next_to([mx(v), MB, 0], DOWN, buff=0.14) for v in (1, 5, 10, 15)])
        m_vt = VGroup(*[lab(t).next_to([MX0, MB + v * uv, 0], LEFT, buff=0.12)
                        for v, t in ((0, "0"), (0.5, "0.5"))])
        m_title = Tex(r"forecast day $d$", font_size=FS_LABEL, color=MUTED)
        m_title.next_to(m_dt, DOWN, buff=0.12)
        m_name = MathTex(r"E_{\text{stock}}(8,d)", font_size=FS_LABEL, color=STOCK)
        m_name.next_to([MX0, MB + 0.6 * uv, 0], UP, buff=0.15).align_to([MX0 - 0.1, 0, 0], LEFT)
        m_chart = VGroup(m_axis, m_yaxis, m_dt, m_vt, m_title)
        mini_stems = VGroup()
        for dd in range(1, H + 1):
            top = [mx(dd), MB + e_sel[dd - 1] * uv, 0]
            mini_stems.add(VGroup(Line([mx(dd), MB, 0], top, color=STOCK, stroke_width=4),
                                  Dot(top, radius=0.045, color=STOCK)))
        tops = [[mx(dd), MB + e_sel[dd - 1] * uv, 0] for dd in range(1, H + 1)]
        floors = [[mx(dd), MB, 0] for dd in range(1, H + 1)]
        mini_sheet = Polygon(*tops, *reversed(floors), stroke_width=0, fill_color=STOCK, fill_opacity=0.35)
        mini_edge = VMobject(stroke_color=STOCK, stroke_width=3.0)
        mini_edge.set_points_as_corners(tops)
        mini_rib = VGroup(mini_sheet, mini_edge)
        self.pin(m_chart, m_name, mini_stems, mini_rib)
        n_fly = n8_lab[0].copy()
        self.pin(n_fly)
        cap = self.swap_caption(cap, caption(r"times $N(8)$: expected wins on each coming day"),
                                run_time=0.6)
        self.play(Create(VGroup(m_axis, m_yaxis)), FadeIn(m_dt), FadeIn(m_vt), FadeIn(m_title),
                  ReplacementTransform(n_fly, F[2]), FadeIn(F[3]), FadeIn(F[0:2]), run_time=1.1)
        self.play(ReplacementTransform(stems, mini_stems), FadeOut(s_lab), FadeOut(brace),
                  FadeOut(brace_lab), FadeIn(m_name, shift=UP * 0.1), run_time=1.6)
        self.play(Create(mini_edge), FadeIn(mini_sheet), mini_stems.animate.set_opacity(0.0),
                  run_time=0.9)
        self.remove(mini_stems)
        self.wait(0.8)

        # ==============================================================
        # 4. into 3D
        # ==============================================================
        self.set_camera_orientation(**CAM_PERSP)
        cam.reset_rotation_matrix()

        ribs = {}
        for a in range(A_MAX - 1, -1, -1):                       # far -> near
            if E[a].max() <= 1e-9:
                continue
            ribs[a] = ribbon(a, E[a])
        order = list(ribs)                                       # far -> near
        rib8_emph = ribbon(A_SEL, E[A_SEL], op=0.32, sw=3.0, edge_color=STOCK)

        # 2D stand-in at the projected screen position of the a = 8 ribbon
        tops3 = cam.project_points(np.array([P(d, A_SEL, max(v, 1e-4)) for d, v in zip(range(1, H + 1), e_sel)]))
        floors3 = cam.project_points(np.array([P(d, A_SEL, 0) for d in range(1, H + 1)]))
        tops3[:, 2] = 0
        floors3[:, 2] = 0
        proj_sheet = Polygon(*tops3, *reversed(floors3), stroke_width=0, fill_color=STOCK, fill_opacity=0.32)
        proj_edge = VMobject(stroke_color=STOCK, stroke_width=3.0)
        proj_edge.set_points_as_corners(tops3)

        # floor frame + axes (d along the front, age up the right side, relief scale at the front-right)
        x_axis = Line(P(0.5, -0.5), P(15.5, -0.5), color=MUTED, stroke_width=2)
        y_axis = Line(P(15.5, -0.5), P(15.5, 44.5), color=MUTED, stroke_width=2)
        far_x = Line(P(0.5, 44.5), P(15.5, 44.5), color=GRID, stroke_width=1.5)
        far_y = Line(P(0.5, -0.5), P(0.5, 44.5), color=GRID, stroke_width=1.5)
        z_axis = Line(P(0.5, -0.5), P(0.5, -0.5, 0.5), color=MUTED, stroke_width=2)
        z_ticks = VGroup(*[Line(P(0.5, -0.5, v), P(0.5, -0.5, v) + np.array([-0.08, 0, 0]),
                                color=MUTED, stroke_width=2) for v in (0.2, 0.4)])
        floor_axes = VGroup(far_x, far_y, x_axis, y_axis)

        d_labs = [self.anchor(lab(f"{v}"), P(v, -0.5), DOWN * 0.3) for v in (1, 5, 10, 15)]
        a_labs = [self.anchor(lab(f"{v}"), P(15.5, v), RIGHT * 0.36) for v in (10, 20, 30, 40)]
        d_title = self.anchor(Tex(r"forecast day $d$", font_size=FS_LABEL, color=MUTED),
                              P(7.5, -0.5), DOWN * 0.62 + LEFT * 0.55)
        a_title3 = self.anchor(Tex(r"age $a$", font_size=FS_LABEL, color=MUTED), P(15.5, 25), RIGHT * 1.15)
        z_labs = [self.anchor(lab(f"{v:.1f}"), P(0.5, -0.5, v), LEFT * 0.34) for v in (0.2, 0.4)]
        z_title = self.anchor(MathTex(r"E_{\text{stock}}", font_size=FS_LABEL, color=STOCK),
                              P(0.5, -0.5, 0.5), UP * 0.3 + LEFT * 0.2)
        self.pin(proj_sheet, proj_edge)

        F_small_target = F.copy().scale(0.82).to_corner(UR, buff=0.45)
        self.play(
            FadeOut(n_chart), FadeOut(nbars), FadeOut(brk), FadeOut(pooled_lab), FadeOut(n8_lab),
            FadeOut(k_chart), FadeOut(k_left), FadeOut(k_right), FadeOut(vline),
            FadeOut(m_chart), FadeOut(m_name),
            Transform(mini_sheet, proj_sheet), Transform(mini_edge, proj_edge),
            Transform(F, F_small_target),
            run_time=2.0,
        )
        self.remove(mini_sheet, mini_edge)
        self.add(rib8_emph)
        a8_tag = self.anchor(MathTex(r"a = 8", font_size=FS_LABEL, color=STOCK),
                             P(1, A_SEL, e_sel[0]), UP * 0.35 + LEFT * 0.25)
        self.play(Create(floor_axes), Create(z_axis), Create(z_ticks), FadeIn(a8_tag),
                  *[FadeIn(m) for m in (*d_labs, *a_labs, d_title, a_title3, *z_labs, z_title)],
                  run_time=1.0)

        # every other age's ribbon rises (far -> near)
        risers = {a: ribbon(a, E[a], scale=0.0).set_opacity(0.0) for a in order if a != A_SEL}
        for a in order:                       # scene order far -> near keeps ties stable
            if a != A_SEL:
                self.add(risers[a])
        cap = self.swap_caption(cap, caption(r"every age bucket, pushed through its remaining kernel"),
                                run_time=0.6)
        self.begin_ambient_camera_rotation(rate=0.015)
        self.play(
            LaggedStart(*[Transform(risers[a], ribs[a]) for a in order if a != A_SEL], lag_ratio=0.06),
            FadeOut(a8_tag),
            run_time=3.4,
        )
        self.wait(1.6)

        # ==============================================================
        # 5. why the ridges are diagonal
        # ==============================================================
        peaks = [i for i in range(1, A_MAX - 1) if k_s[i] >= k_s[i - 1] and k_s[i] >= k_s[i + 1]
                 and k_s[i] > 0.5 * k_s.max()]
        guides = VGroup()
        guide_labs = []
        for c in peaks:
            segs = VGroup()
            d0, d1 = 0.5, min(15.5, c + 0.5)
            ds = np.linspace(d0, d1, max(int((d1 - d0) * 2), 2) + 1)
            for u, v in zip(ds[:-1], ds[1:]):
                s = DepthPath(stroke_color=KERNEL, stroke_width=3.5)
                s.set_points_as_corners([P(u, c - u), P(v, c - v)])
                s.set_shade_in_3d(True)
                segs.add(s)
            guides.add(segs)
            # label where the crest line meets the a = 0 edge, below-right of that point
            gl = self.anchor(MathTex(rf"a+d={c}", font_size=FS_LABEL, color=KERNEL), P(c, -0.5),
                             np.array([0.85, -0.25, 0]))
            guide_labs.append(gl)
        cap = self.swap_caption(cap, caption(r"one day later, everyone is one day older"), run_time=0.6)
        self.play(*[Create(g, lag_ratio=1.0) for g in guides], *[FadeIn(g) for g in guide_labs],
                  run_time=1.8)
        self.wait(2.2)

        # ==============================================================
        # 6. this is the heat-map
        # ==============================================================
        self.stop_ambient_camera_rotation()
        tiles = floor_tiles_3d(_AxesShim(), D.stock.surface_smooth[:A_MAX],
                               list(range(1, H + 1)), list(range(A_MAX)), STOCK_RAMP)
        vmax = tiles.vmax
        for t in tiles:
            t.set_fill(opacity=0.0)
            t.set_stroke(opacity=0.0)
        self.add(tiles)
        # colour bar (screen-fixed, top view only)
        cb_h, cb_n = 3.0, 24
        cbar = VGroup(*[Rectangle(width=0.22, height=cb_h / cb_n, stroke_width=0.8,
                                  stroke_color=ramp_color(STOCK_RAMP, (i + 0.5) / cb_n),
                                  fill_color=ramp_color(STOCK_RAMP, (i + 0.5) / cb_n), fill_opacity=1)
                        .move_to([0, (i + 0.5) * cb_h / cb_n, 0]) for i in range(cb_n)])
        cbar_frame = Rectangle(width=0.22, height=cb_h, stroke_color=GRID, stroke_width=1.2).move_to(cbar)
        cbar_g = VGroup(cbar, cbar_frame)
        cbar_g.move_to([-5.0, -0.1, 0])
        cb_t = VGroup(lab("0").next_to(cbar_g.get_corner(DR), RIGHT, buff=0.1),
                      lab(f"{vmax:.2f}").next_to(cbar_g.get_corner(UR), RIGHT, buff=0.1))
        cb_title = Tex(r"wins / day", font_size=FS_TICK, color=MUTED).next_to(cbar_g, UP, buff=0.15)
        cb_all = VGroup(cbar_g, cb_t, cb_title)
        self.pin(cb_all)

        all_ribs = [risers[a] for a in order if a != A_SEL] + [rib8_emph]
        cap_hm = caption(r"seen from above: the existing-pipeline heat-map")
        self.pin(cap_hm)
        early = lambda t: smooth(min(1.0, 2.5 * t))     # gone before the camera swings
        self.move_cam(
            **CAM_DOWN, run_time=3.2, dip=0.2,
            added_anims=[
                *[r.animate.set_opacity(0.0) for r in all_ribs],
                *[t.animate.set_fill(opacity=1.0).set_stroke(opacity=1.0) for t in tiles],
                FadeOut(guides), *[FadeOut(g, rate_func=early) for g in guide_labs],
                FadeOut(z_axis), FadeOut(z_ticks), *[FadeOut(m) for m in (*z_labs, z_title)],
                FadeOut(far_x), FadeOut(far_y),
                FadeOut(cap, shift=UP * 0.15, rate_func=early),
            ],
        )
        self.remove(*all_ribs)
        self.play(FadeIn(cb_all), FadeIn(cap_hm, shift=UP * 0.15), run_time=0.8)
        cap = cap_hm
        self.wait(2.5)

        # ==============================================================
        # 7. sum over age
        # ==============================================================
        flat2 = {a: ribbon(a, E[a], scale=0.0).set_opacity(0.0) for a in order}
        for a in order:
            self.add(flat2[a])
        self.move_cam(
            **CAM_WALL, run_time=3.0, dip=0.15,
            added_anims=[
                *[t.animate.set_fill(opacity=0.0).set_stroke(opacity=0.0) for t in tiles],
                FadeOut(cb_all), FadeOut(cap, shift=UP * 0.15, rate_func=lambda t: smooth(min(1.0, 2.5 * t))),
                *[Transform(flat2[a], ribbon(a, E[a])) for a in order],
                FadeIn(far_x), FadeIn(far_y),
            ],
        )
        self.remove(tiles)

        # wall axis (its own scale: W_stock is ~10x a single cell)
        wall_axis = Line(PW(0.5, 0), PW(0.5, 3.5), color=MUTED, stroke_width=2)
        wall_ticks = VGroup(*[Line(PW(0.5, v), PW(0.5, v) + np.array([-0.08, 0, 0]),
                                   color=MUTED, stroke_width=2) for v in (1, 2, 3)])
        wall_labs = [self.anchor(lab(f"{v}"), PW(0.5, v), LEFT * 0.3) for v in (1, 2, 3)]
        wall_title = self.anchor(Tex(r"wins / day", font_size=FS_LABEL, color=MUTED), PW(0.5, 3.5),
                                 UP * 0.3 + RIGHT * 0.2)

        # cumulative stacking along age (young ages at the bottom)
        ages_sorted = sorted(ribs)                 # 0 .. 44
        cum = np.zeros(H)
        targets = {}
        for i, a in enumerate(ages_sorted):
            lo = cum.copy()
            cum = cum + E[a]
            col = STOCK if i % 2 == 0 else "#B5475B"
            targets[a] = band(lo, cum, col, 0.9)
        assert np.allclose(cum, W, atol=1e-6)

        cap = caption(r"summed over age: expected wins per day from stock")
        self.pin(cap)
        self.play(Create(wall_axis), Create(wall_ticks), *[FadeIn(m) for m in (*wall_labs, wall_title)],
                  FadeIn(cap, shift=UP * 0.15), run_time=0.8)
        # near -> far: the youngest ribbons slide back first and form the bottom of the stack
        self.play(LaggedStart(*[Transform(flat2[a], targets[a]) for a in reversed(order)], lag_ratio=0.06),
                  run_time=3.0)
        self.wait(0.6)
        bars3 = VGroup()
        for dd in range(1, H + 1):
            h = W[dd - 1]
            bars3.add(Polygon(PW(dd - 0.36, 0), PW(dd + 0.36, 0), PW(dd + 0.36, h), PW(dd - 0.36, h),
                              stroke_width=0.8, stroke_color=STOCK, fill_color=STOCK, fill_opacity=1.0))
        Wf = MathTex(r"W_{\text{stock}}(d)", "=", r"\sum_a", r"N(a)", r"\,", r"\frac{", r"k(a+d)", r"}{",
                     r"S(a)", r"}", font_size=FS_FORMULA)
        Wf[0].set_color(STOCK)
        Wf[3].set_color(STOCK)
        Wf[6].set_color(KERNEL)
        Wf[8].set_color(SURVIVAL)
        Wf.to_corner(UR, buff=0.45)
        self.pin(Wf)
        # the age layers merge into one solid area, the bars appear on top in the same colour,
        # then the area between the bars falls away
        self.play(
            *[flat2[a][0].animate.set_fill(STOCK, opacity=1.0).set_stroke(STOCK, opacity=1.0) for a in order],
            FadeOut(F[0]), FadeIn(Wf[0]), ReplacementTransform(F[1], Wf[1]),
            FadeIn(Wf[2]), ReplacementTransform(F[2], Wf[3]), FadeOut(F[3]),
            ReplacementTransform(F[5], Wf[6]), ReplacementTransform(F[6], Wf[7]),
            ReplacementTransform(F[7], Wf[8]),
            run_time=1.2,
        )
        self.play(FadeIn(bars3), run_time=0.4)
        self.play(*[FadeOut(flat2[a]) for a in order], run_time=0.9)
        self.wait(3.0)
        close_chapter(self)

class _AxesShim:
    """floor_tiles_3d only needs ``c2p``; route it through our own floor mapping."""

    def c2p(self, d, a, z=0.0):
        return P(d, a, z)
