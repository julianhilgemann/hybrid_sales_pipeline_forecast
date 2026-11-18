import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import *

# Chapter 07 -- Wins from the open pipeline (3D).
#
# The 14 deals aged 8 (chapter 06's row of bars) -> tilt: one row of a bigger
# picture -> every age bucket rises: the landscape E_stock(a, d) -> ridges run
# along a + d = 5 and a + d = 13 -> from above it is the heat-map -> back up,
# make room, stack each day's column on the far wall: W_stock(d) -> the wall
# faces us: a bar chart that drains, 31.2 expected wins over 15 days.

D = load_data()
H = int(D.meta.horizon)                  # 15 forecast days
A8 = int(D.conditional.a0)               # the worked example: age 8
N8 = int(D.conditional.N_a0)             # 14 deals aged 8
M = D.stock.surface                      # (46, 15) = E_stock(a, d), [a, d-1]
W = D.stock.by_day                       # (15,) = W_stock(d)
W_TOTAL = float(W.sum())                 # 31.2
VMAX = float(M.max())                    # tallest tower, 0.51 expected wins
GAMMA = 0.6                              # heat colour = ramp((value / VMAX) ** GAMMA)

# ---- floor geometry (scene units) ------------------------------------------
CW, CDP = 0.42, 0.14                     # one forecast day / one age bucket
ZS, ZW = 4.7, 0.8                        # height per expected win: cells / wall
GAP = 0.12
X0, Y0 = -3.15, -3.22
X1, Y1 = X0 + H * CW, Y0 + 46 * CDP
ROW8_Y = Y0 + A8 * CDP + 0.5 * CDP * GAP          # front face of the age-8 row
WALL_Y = Y1 - CDP * (1 - GAP)                      # front face of the wall bars
POST_TOP_CELL = 2.62                               # z-axis top, cell scale
POST_TOP_WALL = 2.78                               # z-axis top, wall scale


def dx(d):
    """x of the centre of forecast day d (1..15)."""
    return X0 + (d - 0.5) * CW


def ay(a):
    """y of the centre of age bucket a (0..45)."""
    return Y0 + (a + 0.5) * CDP


# ---- camera views -------------------------------------------------------------
def view(phi, theta, zoom, fc):
    return dict(phi=phi * DEGREES, theta=theta * DEGREES, zoom=zoom, fc=np.array(fc, dtype=float))


V_ROW = view(90, -90, 1.5, (0.0, ay(A8), 1.34))          # level: row 8 is a 2D bar chart
V_LAND = view(56, -60, 1.15, (0.43, -0.98, 0.0))          # the landscape fills the frame
V_RIDGE = view(46, -63, 0.95, (0.33, -0.90, 0.0))         # higher: the floor pattern shows
V_TOP = view(0, -90, 0.78, (3.52, -0.59, 0.0))            # straight down: the heat-map
V_WALL3D = view(62, -58, 0.743, (0.09, 1.38, 0.0))        # pulled back: floor + far wall
V_WALL = view(90, -90, 1.4, (0.0, WALL_Y, 1.43))          # level: the wall is a bar chart


class FL(Line):
    """FloorLine without a camera reference on the instance (so fades and
    copies never deep-copy the camera): always paints under the towers."""
    cam = None

    def __init__(self, start, end, **kwargs):
        kwargs.setdefault("color", GRID)
        kwargs.setdefault("stroke_width", 1.5)
        super().__init__(start, end, **kwargs)
        self.set_shade_in_3d(True)

    def get_z_index_reference_point(self):
        phi, theta = FL.cam.get_phi(), FL.cam.get_theta()
        to_cam = np.array([np.sin(phi) * np.cos(theta), np.sin(phi) * np.sin(theta), np.cos(phi)])
        return -1e3 * to_cam


class Clip(ThreeDScene):
    # ---------------------------------------------------------------- helpers
    def pin(self, mob, anchor, offset=ORIGIN):
        """Camera-facing label at a 3D anchor with a screen offset; both can be
        animated later with ``move_pins``. Not on screen yet."""
        mob.anchor = np.array(anchor, dtype=float)
        mob.off = np.array(offset, dtype=float)
        mob.move_to(mob.anchor + mob.off)
        self.add_fixed_orientation_mobjects(mob, center_func=lambda m=mob: m.anchor)
        self.remove(mob)
        return mob

    def move_pins(self, moves, rate_func=smooth):
        """Animation: each (mob, new_anchor or None, new_offset or None)."""
        data = []
        for mob, a1, o1 in moves:
            a0, off0 = mob.anchor.copy(), mob.off.copy()
            a1 = a0 if a1 is None else np.array(a1, dtype=float)
            o1 = off0 if o1 is None else np.array(o1, dtype=float)
            data.append((mob, a0, a1, off0, o1))

        def upd(_, alpha):
            s = rate_func(alpha)
            for mob, a0, a1, off0, o1 in data:
                a, o = a0 + (a1 - a0) * s, off0 + (o1 - off0) * s
                mob.shift((a + o) - (mob.anchor + mob.off))
                mob.anchor, mob.off = a, o

        return UpdateFromAlphaFunc(self.host, upd, rate_func=linear)

    def place_pin(self, mob, anchor=None, offset=None):
        """Move a pinned label instantly (while it is off screen)."""
        a = mob.anchor if anchor is None else np.array(anchor, dtype=float)
        o = mob.off if offset is None else np.array(offset, dtype=float)
        mob.shift((a + o) - (mob.anchor + mob.off))
        mob.anchor, mob.off = a, o

    def move_lines(self, lines, delta, rate_func=smooth):
        """Animation: slide FL lines by ``delta`` (no copies of the lines)."""
        delta = np.array(delta, dtype=float)
        state = {"s": 0.0}

        def upd(_, alpha):
            s = rate_func(alpha)
            for ln in lines:
                ln.shift(delta * (s - state["s"]))
            state["s"] = s

        return UpdateFromAlphaFunc(self.host, upd, rate_func=linear)

    def cam_to(self, v, run_time, added_anims=(), rate_func=smooth, zoom_dip=0.0, fc_lead=1.0):
        """Camera move to view ``v`` (phi, theta, zoom, frame centre together);
        ``zoom_dip`` lowers the zoom mid-move so nothing swings off-frame;
        ``fc_lead`` < 1 lets the frame centre arrive early (the content slides
        to its new place before the turn lifts it)."""
        cam = self.renderer.camera
        z0, z1 = cam.get_zoom(), v["zoom"]
        p0, p1 = cam.get_phi(), v["phi"]
        t0, t1 = cam.get_theta(), v["theta"]
        f0 = cam.frame_center.copy()
        f1 = v["fc"]

        def upd(_, alpha):
            s = rate_func(alpha)
            cam.set_phi(p0 + (p1 - p0) * s)
            cam.set_theta(t0 + (t1 - t0) * s)
            cam.set_zoom(z0 + (z1 - z0) * s - zoom_dip * np.sin(np.pi * alpha))
            cam.frame_center = f0 + (f1 - f0) * rate_func(min(1.0, alpha / fc_lead))

        self.play(UpdateFromAlphaFunc(self.host, upd, rate_func=linear), *added_anims, run_time=run_time)

    def drift(self, dtheta_deg, run_time, dphi_deg=0.0):
        """Slow ambient camera drift with eased ends (a living hold)."""
        cam = self.renderer.camera
        v = dict(phi=cam.get_phi() + dphi_deg * DEGREES, theta=cam.get_theta() + dtheta_deg * DEGREES,
                 zoom=cam.get_zoom(), fc=cam.frame_center.copy())
        self.cam_to(v, run_time, rate_func=rate_functions.ease_in_out_sine)

    def hide_during(self, mobs, a=0.25, b=0.75):
        """Animation: fade ``mobs`` out over [0, a] and back in over [b, 1] of
        a move (labels that would sweep through the formula mid-move)."""
        def upd(_, alpha):
            if alpha < 0.5:
                o = 1 - smooth(min(1.0, alpha / a))
            else:
                o = smooth(max(0.0, (alpha - b) / (1 - b)))
            for m in mobs:
                m.set_opacity(o)

        return UpdateFromAlphaFunc(self.host, upd, rate_func=linear)

    def pinned(self, anim):
        """Keep every piece an animation creates (e.g. while aligning two
        formulas) fixed in the frame."""
        orig = anim.begin
        cam = self.renderer.camera

        def begin():
            orig()
            cam.add_fixed_in_frame_mobjects(anim.mobject)

        anim.begin = begin
        return anim

    # ---- tower styling ---------------------------------------------------------
    def rise(self, T, ks, f_from, f_to, key=None, lag=0.0, fade_in=False, recolor=(), rate_func=smooth):
        """Raise (or lower) only the towers ``ks``; optionally fade them in as
        they start and recolour ``recolor`` towers to their heat colours."""
        ks = np.asarray(ks, dtype=int)
        if key is not None and lag > 0:
            kk = np.asarray(key, dtype=float)
            start = (kk - kk.min()) / (np.ptp(kk) or 1.0) * lag
            length = 1.0 - lag
        else:
            start, length = np.zeros(len(ks)), 1.0
        base = T.base_h[ks].copy()
        rec_faces = [f for k in recolor for f in T.tower_list[k]]
        rec_from = [f.get_fill_color() for f in rec_faces]

        def upd(_, alpha):
            t = np.clip((alpha - start) / length, 0.0, 1.0)
            s = np.array([rate_func(x) for x in t])
            T.h[ks] = base * (f_from + (f_to - f_from) * s)
            T._refresh(ks)
            if fade_in:
                op = np.clip(t / 0.3, 0.0, 1.0)
                for k, o in zip(ks, op):
                    for f in T.tower_list[k]:
                        f.set_fill(opacity=o)
                        f.set_stroke(opacity=o)
            if rec_faces:
                c = smooth(float(np.clip(alpha / 0.5, 0, 1)))
                for f, c0 in zip(rec_faces, rec_from):
                    col = interpolate_color(c0, f.heat_c, c)
                    f.set_fill(col)
                    f.set_stroke(col)

        return UpdateFromAlphaFunc(T, upd, rate_func=linear)

    # ------------------------------------------------------------------ scene
    def set_highlight(self, T, mode_of):
        """Per-face highlight colours: 'dim' (dark, opaque), 'amber' (the win
        kernel's colour) or unchanged; animate with ``highlight``."""
        amber = {"top": ManimColor(KERNEL), "front": shade(KERNEL, 0.66), "right": shade(KERNEL, 0.46)}
        rose = {"top": ManimColor(STOCK), "front": shade(STOCK, 0.66), "right": shade(STOCK, 0.46)}
        for t in T.tower_list:
            m = mode_of[t.k]
            for f in t:
                if m == "dim":
                    f.hl_c = shade(f.heat_c, 0.25)
                elif m == "amber":
                    f.hl_c = interpolate_color(f.heat_c, amber[f.kind], 0.85)
                elif m == "lit":
                    f.hl_c = interpolate_color(f.heat_c, rose[f.kind], 0.55)
                else:
                    f.hl_c = f.heat_c

    def highlight(self, T, a_from, a_to, rate_func=smooth):
        faces = [f for t in T.tower_list for f in t]

        def upd(_, alpha):
            s = a_from + (a_to - a_from) * rate_func(alpha)
            for f in faces:
                c = interpolate_color(f.heat_c, f.hl_c, s)
                f.set_fill(c)
                f.set_stroke(c)

        return UpdateFromAlphaFunc(self.host, upd, rate_func=linear)

    def construct(self):
        flat_shading(self)
        cam = self.renderer.camera
        FL.cam = cam
        # The host drives every custom animation. It is the first mobject and
        # always has an updater, so every frame redraws (and depth-sorts) the
        # whole scene: otherwise a play() that animates only a caption freezes
        # the towers into a static background and lines added after them
        # (FL) are painted on top.
        self.host = VMobject()
        self.host.add_updater(lambda m, dt: None)
        self.add(self.host)
        # the frame centre must still be ORIGIN when the first frame renders: Cairo
        # caches its context with the frame centre of that frame, and every pinned
        # overlay (header, captions, formulas) would stay shifted by it
        self.set_camera_orientation(phi=V_ROW["phi"], theta=V_ROW["theta"], zoom=V_ROW["zoom"])

        header = open_chapter(self, 7, "Wins from the open pipeline", STOCK,
                              question=rf"How many wins will today's {int(D.stock.total_active)} open deals bring, day by day?",
                              part=PART[3])
        cam.frame_center = V_ROW["fc"]

        # ---- the towers: row 8 solid rose (chapter 06's bars), the rest hidden --
        T = HeatTowers(M, cell_w=CW, cell_d=CDP, z_scale=ZS, ramp=STOCK_RAMP, origin=(X0, Y0, 0), gap=GAP)
        T.set_lift(0.0)
        n_t = len(T.tower_list)
        row8 = [t.k for t in T.tower_list if t.i == A8]
        others = [t.k for t in T.tower_list if t.i != A8]
        rose_top = interpolate_color(ManimColor(STOCK), ManimColor(WHITE), 0.22)
        # heat colours with a gamma, so mid-sized cells do not sink into the
        # background (the colour bar below uses the same mapping)
        for t in T.tower_list:
            top = ramp_color(STOCK_RAMP, (t.value / VMAX) ** GAMMA)
            for f in t:
                f.heat_c = top if f.kind == "top" else shade(top, T.side_shade[0] if f.kind == "front" else T.side_shade[1])
                f.set_fill(f.heat_c, 1.0)
                f.set_stroke(f.heat_c)
        for k in row8:
            for f in T.tower_list[k]:
                c = {"front": ManimColor(STOCK), "right": shade(STOCK, 0.62), "top": rose_top}[f.kind]
                f.set_fill(c, 1.0)
                f.set_stroke(c)
        for k in others:
            for f in T.tower_list[k]:
                f.set_fill(opacity=0.0)
                f.set_stroke(opacity=0.0)

        # ---- axes in front of row 8 (they slide to the floor's front edge later)
        day_axis = FL([X0, ROW8_Y, 0], [X1, ROW8_Y, 0], color=MUTED, stroke_width=2)
        day_ticks = VGroup(*[FL([dx(d), ROW8_Y, 0], [dx(d), ROW8_Y - 0.09, 0], color=MUTED, stroke_width=2)
                             for d in (1, 5, 10, 15)])
        day_labels = [self.pin(MathTex(str(d), font_size=FS_TICK, color=MUTED), [dx(d), ROW8_Y, 0], DOWN * 0.3)
                      for d in (1, 5, 10, 15)]
        day_title = self.pin(Tex(r"forecast day $d$", font_size=FS_LABEL, color=MUTED), [0, ROW8_Y, 0], DOWN * 0.72)

        z_ticks_cell = (0.25, 0.5)
        post = FL([X0, ROW8_Y, 0], [X0, ROW8_Y, POST_TOP_CELL], color=MUTED, stroke_width=2)
        post_marks = VGroup(*[FL([X0 - 0.09, ROW8_Y, v * ZS], [X0, ROW8_Y, v * ZS], color=MUTED, stroke_width=2)
                              for v in z_ticks_cell])
        post_labels = [self.pin(MathTex(f"{v:g}", font_size=FS_TICK, color=MUTED), [X0, ROW8_Y, v * ZS], LEFT * 0.42)
                       for v in z_ticks_cell]
        post_title = self.pin(Tex("expected wins", font_size=FS_LABEL, color=MUTED).rotate(PI / 2),
                              [X0, ROW8_Y, 0.5 * POST_TOP_CELL], LEFT * 0.98)
        post_all = [post, post_marks, *post_labels, post_title]

        row_label = self.pin(Tex(rf"{N8} deals\\aged {A8}", font_size=FS_LABEL, color=STOCK),
                             [X1, ROW8_Y, 0.0], np.array([0.78, 0.42, 0]))

        # formula, top right, with its words underneath
        def color_formula(F, stock, kernel, surv):
            for i in stock:
                F[i].set_color(STOCK)
            for i in kernel:
                F[i].set_color(KERNEL)
            for i in surv:
                F[i].set_color(SURVIVAL)
            for sm in F.family_members_with_points():
                if sm.width > 4 * max(sm.height, 1e-3) and sm.width > 0.3:   # the fraction bar
                    sm.set_color(INK)
            F.to_corner(UR, buff=0.45)
            return F

        def formula_E(sym):
            F = MathTex(r"E_{\text{stock}}(", sym, ",d)", "=", "N(", sym, r")\,", r"\frac{k(", sym, "+d)",
                        "}{S(", sym, ")}", font_size=FS_FORMULA)
            return color_formula(F, (0, 1, 2, 4, 5, 6), (7, 8, 9), (10, 11, 12))

        F = formula_E(str(A8))
        desc8 = Tex(rf"expected wins on day $d$ from the {N8} deals aged {A8}", font_size=FS_LABEL, color=MUTED)
        desc8.next_to(F, DOWN, buff=0.22).align_to(F, RIGHT)
        fix_in_frame(self, F, desc8)

        # ================= beat 2: the row, level camera (chapter 06's bars) ========
        self.add(T)
        self.play(Create(day_axis), Create(post), run_time=0.9)
        self.play(self.rise(T, row8, 0.0, 1.0, key=T.jj[row8], lag=0.35),
                  *[FadeIn(m) for m in (*day_labels, day_title, *post_labels, post_title)],
                  Create(day_ticks), Create(post_marks), run_time=1.6)
        self.play(FadeIn(row_label, shift=UP * 0.1), run_time=0.8)
        self.play(FadeIn(F, shift=DOWN * 0.1), FadeIn(desc8, shift=DOWN * 0.1), run_time=1.1)
        cap = swap_caption(self, None, rf"the {N8} deals aged {A8}, day by day")
        self.wait(2.6)

        # ================= beat 3: tilt: one row of a bigger picture ===============
        floor_edges = VGroup(
            FL([X0, Y0, 0], [X0, Y1, 0]),                                     # left
            FL([X0, Y1, 0], [X1, Y1, 0]),                                     # back: the wall's foot
            FL([X1, Y1, 0], [X1, Y0, 0], color=MUTED, stroke_width=2),       # right: the age axis
        )
        age_title = VGroup(Tex(r"age $a$", font_size=FS_LABEL, color=MUTED),
                           Tex("business days", font_size=FS_TICK, color=MUTED)).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
        half = age_title.width / 2
        AGE_OFF_3D, AGE_TITLE_3D = np.array([0.36, -0.06, 0]), np.array([0.55 + half, -0.2, 0])
        AGE_TITLE_WALL = np.array([0.5 + half, -0.36, 0])          # the wall view's age axis is shorter
        AGE_OFF_TOP, AGE_TITLE_TOP = RIGHT * 0.34, RIGHT * (0.78 + half)
        age_ticks = VGroup(*[FL([X1, ay(a), 0], [X1 + 0.09, ay(a), 0], color=MUTED, stroke_width=2)
                             for a in (0, 15, 30, 45)])
        age_labels = [self.pin(MathTex(s, font_size=FS_TICK, color=MUTED).set_z_index(0), [X1, ay(a), 0], AGE_OFF_3D)
                      for a, s in ((0, "0"), (15, "15"), (30, "30"), (45, "45{+}"))]
        for m in age_labels:          # left-align the numbers next to the axis
            m.shift(RIGHT * (m.width / 2 - 0.1))
            m.off = m.off + RIGHT * (m.width / 2 - 0.1)
        age_title = self.pin(age_title, [X1, ay(24), 0], AGE_TITLE_3D)

        DAY_OFF_3D, DAY_TITLE_3D = np.array([-0.08, -0.3, 0]), np.array([-0.3, -0.98, 0])
        cap = swap_caption(self, cap, "one row of a bigger picture: every age")
        self.wait(0.6)
        dy = Y0 - ROW8_Y
        axis_lines = [day_axis, *day_ticks, post, *post_marks]
        self.cam_to(V_LAND, 4.0, added_anims=[
            self.move_lines(axis_lines, [0, dy, 0]),
            self.move_pins([(m, m.anchor + [0, dy, 0], DAY_OFF_3D) for m in day_labels]
                           + [(day_title, [dx(8), Y0, 0], DAY_TITLE_3D)]
                           + [(m, m.anchor + [0, dy, 0], None) for m in (*post_labels, post_title)]
                           + [(row_label, None, np.array([0.9, 0.3, 0]))]),
            Create(floor_edges, rate_func=delayed(0.35, 0.55)),
            FadeIn(age_title, rate_func=delayed(0.6, 0.4)),
        ])
        self.wait(0.9)

        # ================= beat 4: every age rises ================================
        cap = swap_caption(self, cap, "every age bucket does the same")
        self.wait(1.0)
        key = np.sqrt(np.abs(T.ii[others] - A8))
        self.play(self.rise(T, others, 0.0, 1.0, key=key, lag=0.62, fade_in=True, recolor=row8),
                  FadeOut(row_label, rate_func=delayed(0.0, 0.25)),
                  Create(age_ticks, rate_func=delayed(0.1, 0.4)),
                  *[FadeIn(m, rate_func=delayed(0.15, 0.4)) for m in age_labels], run_time=4.2)
        # the example becomes the rule: 8 -> a
        Fa = formula_E("a")
        desca = Tex(r"expected wins on day $d$ from the deals aged $a$", font_size=FS_LABEL, color=MUTED)
        desca.next_to(Fa, DOWN, buff=0.22).align_to(Fa, RIGHT)
        fix_in_frame(self, Fa, desca)
        self.remove(*[Fa[i] for i in range(len(Fa))])
        changed = (1, 5, 8, 11)
        self.play(*[self.pinned(Transform(F[i], Fa[i])) for i in range(len(F)) if i not in changed],
                  *[FadeOut(F[i], shift=UP * 0.18) for i in changed],
                  *[FadeIn(Fa[i], shift=UP * 0.18) for i in changed],
                  FadeOut(desc8), run_time=1.5)
        F = VGroup(*[Fa[i] if i in changed else F[i] for i in range(len(F))])   # what is on screen
        self.play(FadeIn(desca, shift=UP * 0.08), run_time=0.7)
        self.drift(8, 3.4)

        # ================= beat 5: why the shape: diagonal ridges ===================
        cc = T.ii + T.jj + 1                                  # a + d of every tower
        band = (np.abs(cc - 5) <= 1) | ((cc >= 11) & (cc <= 16))
        mode = {k: ("amber" if cc[k] in (5, 13) else ("band" if band[k] else "dim")) for k in range(n_t)}
        self.set_highlight(T, mode)
        sw = RoundedRectangle(width=0.22, height=0.22, corner_radius=0.04, fill_color=KERNEL, fill_opacity=1,
                              stroke_width=0)
        leg1 = VGroup(sw, Tex(r"$a+d=5$ \enspace and \enspace $a+d=13$", font_size=FS_BODY, color=KERNEL)
                      ).arrange(RIGHT, buff=0.2)
        leg2 = Tex(r"the win kernel's two humps", font_size=FS_LABEL, color=MUTED)
        legend = VGroup(leg1, leg2).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
        leg2.shift(RIGHT * (sw.width + 0.2))
        legend.to_corner(UL, buff=0.45).shift(DOWN * 0.75)
        fix_in_frame(self, legend)
        cap = swap_caption(self, cap, r"aged $a$ today, $a+d$ on day $d$: ridges run diagonally")
        self.wait(0.6)
        self.cam_to(V_RIDGE, 2.8, added_anims=[
            self.highlight(T, 0.0, 1.0, rate_func=delayed(0.25, 0.75)),
            *[FadeOut(m, rate_func=delayed(0.0, 0.4)) for m in post_all],
        ])
        self.play(FadeIn(leg1, shift=RIGHT * 0.1), run_time=0.8)
        self.play(FadeIn(leg2, shift=RIGHT * 0.1), run_time=0.7)
        self.drift(-6, 3.6)

        # ================= beat 6: seen from above: the heat-map ======================
        bar_n = 48
        cb_w, cb_h = 3.2, 0.24
        cbar = VGroup(*[Rectangle(width=cb_w / bar_n, height=cb_h, stroke_width=0,
                                  fill_color=ramp_color(STOCK_RAMP, (i + 0.5) / bar_n), fill_opacity=1)
                        for i in range(bar_n)]).arrange(RIGHT, buff=0)
        cb_frame = SurroundingRectangle(cbar, buff=0, color=PANEL_EDGE, stroke_width=1)
        cb_ticks = VGroup(*[MathTex(f"{v:g}", font_size=FS_TICK, color=MUTED)
                            .next_to(cbar.get_left() + RIGHT * cb_w * (v / VMAX) ** GAMMA, DOWN, buff=0.12)
                            for v in (0, 0.1, 0.25, 0.5)])
        cb_title = Tex("expected wins", font_size=FS_LABEL, color=MUTED).next_to(cbar, UP, buff=0.16)
        cb = VGroup(cb_title, cbar, cb_frame, cb_ticks).move_to([3.95, 0.3, 0])
        fix_in_frame(self, cb)

        cap = swap_caption(self, cap, "from above: the heat-map")
        self.wait(0.6)
        self.cam_to(V_TOP, 3.6, zoom_dip=0.16, fc_lead=0.45, added_anims=[
            self.hide_during([*age_labels, age_title]),
            T.lift(1, 0),
            self.highlight(T, 1.0, 0.0, rate_func=delayed(0.0, 0.6)),
            FadeOut(legend, rate_func=delayed(0.0, 0.3)),
            self.move_pins([(m, None, DOWN * 0.3) for m in day_labels]
                           + [(day_title, [0, Y0, 0], DOWN * 0.72)]
                           + [(m, None, m.off - AGE_OFF_3D + AGE_OFF_TOP) for m in age_labels]
                           + [(age_title, None, AGE_TITLE_TOP)]),
            FadeIn(cb, rate_func=delayed(0.65, 0.35)),
        ])
        self.wait(3.2)

        # ================= beat 7: back up, with the far wall in view ================
        # the height axis returns on the far wall's left corner (restored to full opacity)
        for m in post_all:
            m.set_opacity(1.0)
        for ln in (post, *post_marks):
            ln.shift([0, Y1 - Y0, 0])
        for m in (*post_labels, post_title):
            self.place_pin(m, m.anchor + [0, Y1 - Y0, 0], None)
        cap = swap_caption(self, cap, "now add up each day's column")
        self.wait(0.9)
        # one day's column (forecast day 3, every age), seen from above where
        # nothing hides it; a plain outline paints on top of the flat field
        col = 3
        xa, xb = X0 + (col - 1) * CW, X0 + col * CW
        col_outline = Polygon([xa, Y0, 0], [xb, Y0, 0], [xb, Y1, 0], [xa, Y1, 0], color=INK, stroke_width=2.5)
        self.set_highlight(T, {k: ("lit" if T.jj[k] == col - 1 else "dim") for k in range(n_t)})
        self.play(self.highlight(T, 0.0, 1.0), Create(col_outline), FadeOut(cb), run_time=0.9)
        self.wait(1.4)
        self.cam_to(V_WALL3D, 3.4, zoom_dip=0.12, added_anims=[
            self.hide_during([*age_labels, age_title]),
            T.lift(0, 1),
            self.highlight(T, 1.0, 0.0, rate_func=delayed(0.3, 0.5)),
            FadeOut(col_outline, rate_func=delayed(0.0, 0.2)),
            self.move_pins([(m, None, DAY_OFF_3D) for m in day_labels]
                           + [(day_title, [dx(8), Y0, 0], DAY_TITLE_3D)]
                           + [(m, None, m.off - AGE_OFF_TOP + AGE_OFF_3D) for m in age_labels]
                           + [(age_title, None, AGE_TITLE_WALL)]),
            *[FadeIn(m, rate_func=delayed(0.75, 0.25)) for m in post_all],
        ])
        self.wait(0.8)

        # ================= beat 8: make room: the sums are much taller ==============
        z_ticks_wall = (1, 2, 3)
        wall_marks = VGroup(*[FL([X0 - 0.09, Y1, v * ZW], [X0, Y1, v * ZW], color=MUTED, stroke_width=2)
                              for v in z_ticks_wall])
        wall_labels = [self.pin(MathTex(f"{v}", font_size=FS_TICK, color=MUTED), [X0, Y1, v * ZW], LEFT * 0.32)
                       for v in z_ticks_wall]
        wall_title = self.pin(Tex("expected wins per day", font_size=FS_LABEL, color=MUTED).rotate(PI / 2),
                              [X0, Y1, 0.5 * POST_TOP_WALL], LEFT * 0.8)
        post_ext = FL([X0, Y1, POST_TOP_CELL], [X0, Y1, POST_TOP_WALL], color=MUTED, stroke_width=2)
        cap = swap_caption(self, cap, "make room: the sums are much taller")
        self.wait(0.7)
        f_sq = ZW / ZS
        self.play(T.lift(1, f_sq),
                  self.move_pins([(m, [X0, Y1, v * ZS * f_sq], None) for m, v in zip(post_labels, z_ticks_cell)]),
                  self.move_lines([post_marks[0]], [0, 0, z_ticks_cell[0] * (ZS * f_sq - ZS)]),
                  self.move_lines([post_marks[1]], [0, 0, z_ticks_cell[1] * (ZS * f_sq - ZS)]),
                  *[FadeOut(m, rate_func=delayed(0.35, 0.5)) for m in (*post_labels, post_marks, post_title)],
                  run_time=2.0)
        self.play(Create(post_ext), Create(wall_marks),
                  *[FadeIn(m, shift=DOWN * 0.08) for m in (*wall_labels, wall_title)], run_time=1.2)
        self.wait(1.2)

        # ================= beat 9: payoff: stack each column onto the wall ============
        cap = swap_caption(self, cap, r"each day's column, stacked: $W_{\text{stock}}(d)$")
        self.wait(0.6)
        self.play(T.collapse(axis="y", z_scale_wall=ZW, lag=0.35), run_time=4.5, rate_func=linear)
        B = T.merge(self, STOCK, run_time=1.2)
        self.drift(5, 2.6)

        # ================= beat 10: the wall faces us ================================
        back_y = Y1 - Y0
        Fw = MathTex(r"W_{\text{stock}}(d)", "=", r"\sum_a", "N(", "a", r")\,", r"\frac{k(", "a", "+d)",
                     "}{S(", "a", ")}", font_size=FS_FORMULA)
        Fw = color_formula(Fw, (0, 3, 4, 5), (6, 7, 8), (9, 10, 11))
        descw = Tex(r"expected wins on day $d$ from all open deals", font_size=FS_LABEL, color=MUTED)
        descw.next_to(Fw, DOWN, buff=0.22).align_to(Fw, RIGHT)
        fix_in_frame(self, Fw, descw)
        self.remove(Fw)

        bar_faces_front = [f for t in B.tower_list for f in t if f.kind == "front"]
        front_from = [f.get_fill_color() for f in bar_faces_front]

        def brighten(_, alpha):
            for f, c0 in zip(bar_faces_front, front_from):
                c = interpolate_color(c0, ManimColor(STOCK), alpha)
                f.set_fill(c)
                f.set_stroke(c)

        self.cam_to(V_WALL, 3.4, added_anims=[
            UpdateFromAlphaFunc(self.host, brighten, rate_func=delayed(0.4, 0.6)),
            *[FadeOut(m, rate_func=delayed(0.0, 0.4)) for m in (floor_edges[0], floor_edges[2], age_ticks, age_title, *age_labels)],
            self.move_lines([day_axis, *day_ticks], [0, back_y, 0]),
            self.move_pins([(m, m.anchor + [0, back_y, 0], DOWN * 0.3) for m in day_labels]
                           + [(day_title, [0, Y1, 0], DOWN * 0.72)]),
        ])
        # the formula sums over ages
        self.play(*[FadeOut(F[i], shift=UP * 0.18) for i in (0, 1, 2)], FadeIn(Fw[0], shift=UP * 0.18),
                  self.pinned(Transform(F[3], Fw[1])),
                  *[self.pinned(Transform(F[i], Fw[i - 1])) for i in range(4, len(F))],
                  FadeIn(Fw[2], shift=RIGHT * 0.1),
                  FadeOut(desca, rate_func=delayed(0.0, 0.4)), run_time=2.0)
        self.play(FadeIn(descw, shift=UP * 0.08), run_time=0.7)
        total = Tex(rf"{W_TOTAL:.1f}", r" expected wins over 15 days", font_size=FS_BODY, color=INK)
        total[0].set_color(STOCK)
        fix_in_frame(self, total)
        total.move_to([3.35, 0.75, 0])
        v_first = self.pin(MathTex(f"{W[0]:.1f}", font_size=FS_TICK, color=INK), [dx(1), WALL_Y, W[0] * ZW], UP * 0.24)
        v_last = self.pin(MathTex(f"{W[-1]:.1f}", font_size=FS_TICK, color=INK), [dx(H), WALL_Y, W[-1] * ZW], UP * 0.24)
        self.play(FadeIn(total, shift=UP * 0.1), run_time=1.0)
        cap = swap_caption(self, cap, "the open pipeline drains")
        self.wait(0.9)
        self.play(FadeIn(v_first, shift=DOWN * 0.08), FadeIn(v_last, shift=DOWN * 0.08), run_time=1.0)
        self.wait(2.6)

        # ================= beat 11: takeaway ============================================
        takeaway(self, "today's open deals: about 31 expected wins, front-loaded", STOCK, old_caption=cap)
        self.remove(self.host)
        close_chapter(self)
