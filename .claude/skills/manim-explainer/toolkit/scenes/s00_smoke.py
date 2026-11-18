"""Smoke test for the toolkit: exercises every shared helper in 2D and 3D on
synthetic data. Render it at draft and final before fanning out and look at one
contact sheet; then point HeatTowers (or whatever 3D builder the film uses) at
the REAL bundle matrix through its whole grammar, since defects show up on real
data first. Delete this file before the film is assembled."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import *


class Clip(ThreeDScene):
    def construct(self):
        setup_3d(self)                       # first: host mobject, flat shading, FloorLine camera
        open_chapter(self, 0, "Toolkit smoke test", TEAL,
                     question="Does every shared helper render cleanly?",
                     part=r"Part 0 \textperiodcentered{} Preflight", hold=1.2)

        # ---- 2D: definition card, Chart, counter, captions, takeaway ---------
        card = definition_card("Opportunity", ["a potential sale",
                                               (["it ends ", "won", " or ", "lost"], [None, AMBER, None, SLATE])],
                               color=LAVENDER, icon=Dot(radius=0.09, color=LAVENDER), aside="(op, deal)")
        card.move_to(LEFT * 4.1 + UP * 0.5)
        fix_in_frame(self, card)
        self.play(FadeIn(card, shift=UP * 0.15), run_time=0.9)

        x = np.arange(0, 21)
        k = 0.6 * np.exp(-((x - 5) ** 2) / 8) + 0.5 * np.exp(-((x - 13) ** 2) / 14)
        ch = Chart((-0.6, 20.6), (0, 0.8), 6.2, 2.8, origin=(-0.6, -1.7, 0))
        ticks_y = ch.y_ticks([0.4, 0.8], grid=True)
        frame = VGroup(ch.axes(), ch.x_ticks([0, 5, 10, 15, 20]), ticks_y,
                       ch.x_title("age (business days)"), ch.y_title("chance"))
        bars_ = ch.bars(x, k * 0.6, ROSE, width=0.7)
        line = ch.curve(x, k, AMBER)
        total = TexCounter(0, fmt="{:.2f}", font_size=FS_LABEL, color=AMBER)
        sum_label = VGroup(Tex("sum", font_size=FS_LABEL, color=MUTED), total).arrange(RIGHT, buff=0.15)
        sum_label.move_to(ch.p(17, 0.75))
        fix_in_frame(self, frame, bars_, line, sum_label)
        self.play(Create(frame[0]), FadeIn(frame[1:]), run_time=0.9)
        self.play(*[GrowFromEdge(b, DOWN, rate_func=delayed(0.03 * i, 0.4)) for i, b in enumerate(bars_)],
                  Create(line), FadeIn(sum_label), total.count_to(float(k.sum() * 0.6)), run_time=1.6)
        cap = swap_caption(self, None, ["the curve is ", "$k(a)$", ", the bars are data"], colors=[None, AMBER, None])
        self.wait(0.8)

        # rescale while the caption changes inside the same play
        ch2 = ch.with_range(y_range=(0, 0.4))
        ticks_y2 = ch2.y_ticks([0.2, 0.4], grid=True)
        bars2 = ch2.bars(x, k * 0.6, ROSE, width=0.7)
        fix_in_frame(self, ticks_y2, bars2)
        cap, swap = caption_swap(self, cap, "a tight axis: data fills the frame", run_time=2.2)
        self.play(Transform(bars_, bars2), FadeOut(line), FadeOut(ticks_y, rate_func=delayed(0.0, 0.3)),
                  FadeIn(ticks_y2, rate_func=delayed(0.55, 0.4)), *swap, run_time=2.2)
        self.wait(0.8)
        tk = takeaway(self, ["the kernel ", "$k(a)$", " in amber, the data in rose"], TEAL, old_caption=cap,
                      colors=[None, AMBER, None], also=[FadeOut(card)], hold=1.0)
        self.play(FadeOut(VGroup(frame[:2], frame[3:], ticks_y2, bars_, sum_label, tk)), run_time=0.8)

        # ---- 3D: HeatTowers grammar ------------------------------------------
        rows = np.arange(12)[:, None]
        M = np.exp(-((rows - 4) ** 2) / 10) * k[None, 1:16] + 0.02
        X0, Y0, CW, CD, ZS = -3.15, -1.8, 0.42, 0.3, 4.0
        ZW = 2.6 / M.sum(axis=0).max()                       # wall scale: tallest stack 2.6 units
        T = HeatTowers(M, cell_w=CW, cell_d=CD, z_scale=ZS, ramp=ramp_for(ROSE), origin=(X0, Y0, 0), gamma=0.6)
        row0, rest = np.where(T.ii == 0)[0], np.where(T.ii > 0)[0]
        T.set_lift(0.0)
        floor = floor_grid(X0, X0 + 15 * CW, Y0, Y0 + 12 * CD)
        days = [pin_label(self, MathTex(str(d), font_size=FS_TICK, color=MUTED),
                          (X0 + (d - 0.5) * CW, Y0, 0), DOWN * 0.3) for d in (1, 5, 10, 15)]

        self.set_camera_orientation(**CAM_FRONT, zoom=1.25, frame_center=(0, Y0, 0.9))
        self.add(T)
        cap = swap_caption(self, None, "one row, seen level: a bar chart")
        self.play(T.lift(0, 1, ks=row0), *[FadeIn(d) for d in days], run_time=1.5)
        self.wait(0.6)

        cap, swap = caption_swap(self, cap, "tilt: every row stands up", run_time=3.5)
        cam_to(self, view(62, -58, 0.8, (0.3, 0.0, 0.3)), 3.5, zoom_dip=0.08, added_anims=[
            T.lift(0, 1, ks=rest, order=lambda T: T.ii, lag=0.5),
            FadeIn(floor, rate_func=delayed(0.2, 0.4)), *swap])
        self.play(T.tint(lambda t: None if t.i == 4 else BG, mix=0.75), run_time=1.0)
        self.play(T.tint(lambda t: None), run_time=0.8)

        cap, swap = caption_swap(self, cap, "from above: the heat-map", run_time=3.0)
        cam_to(self, view(0, -90, 0.8), 3.0, added_anims=[T.lift(1, 0), *swap])
        self.wait(0.6)

        cap, swap = caption_swap(self, cap, "stack each column on the wall", run_time=3.0)
        cam_to(self, view(62, -58, 0.72, (0.3, 0.8, 0.6)), 3.0, added_anims=[T.lift(0, ZW / ZS), *swap])
        self.play(T.collapse(axis="y", z_scale_wall=ZW), run_time=4.5)
        B = T.merge(self, ROSE)

        wall_y = T.wall
        f1 = MathTex(r"E(a,d)", font_size=FS_FORMULA, color=ROSE).to_corner(UR, buff=0.5)
        f2 = MathTex(r"W(d) = \sum_a E(a,d)", font_size=FS_FORMULA, color=ROSE).to_corner(UR, buff=0.5)
        fix_in_frame(self, f1, f2)
        cap, swap = caption_swap(self, cap, "the wall faces us: the column sums", run_time=3.0)
        cam_to(self, view(90, -90, 1.2, (0, wall_y, 1.4)), 3.0, added_anims=[
            move_pins(self, [(d, (d.anchor[0], wall_y, 0), None) for d in days]),
            FadeOut(floor, rate_func=delayed(0.0, 0.4)), FadeIn(f1, rate_func=delayed(0.5, 0.4)), *swap])
        self.play(pinned(self, Transform(f1, f2)), run_time=1.2)
        self.wait(0.8)
        takeaway(self, "every helper rendered", TEAL, old_caption=cap, hold=1.0)
        close_chapter(self)
