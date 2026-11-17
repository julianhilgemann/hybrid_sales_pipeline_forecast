"""Smoke test for the toolkit: exercises every shared helper in 2D and 3D on
synthetic data. Render it at draft and final before fanning out, look at one
contact sheet, then delete this file (it must not end up in the film)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import *


class Clip(ThreeDScene):
    def construct(self):
        open_chapter(self, 0, "Toolkit smoke test", TEAL)

        # ---- flat: axes, bars, curve, area, ticks, heat-map, captions ----
        x = np.arange(0, 21)
        k = 0.6 * np.exp(-((x - 5) ** 2) / 8) + 0.5 * np.exp(-((x - 13) ** 2) / 14)
        axes = make_axes([0, 21, 5], [0, 0.8, 0.2], 6.0, 2.6).shift(LEFT * 3.2 + UP * 0.4)
        chart = VGroup(axes, tick_labels(axes, [0, 5, 10, 15, 20], [0.4, 0.8]),
                       bars(axes, x, k * 0.6, ROSE, width=0.7),
                       area_under(axes, x, k, AMBER), curve(axes, x, k, AMBER))
        M = np.outer(np.exp(-((np.arange(10) - 4) ** 2) / 9), k[:15])
        grid = heat_grid(M, 0.22, 0.22, ramp_for(BLUE), origin="upper").shift(RIGHT * 1.6 + DOWN * 0.7)
        formula = MathTex(r"W(d)", "=", r"\sum_a", "N(a)", r"k(a+d)", font_size=FS_FORMULA).to_corner(UR, buff=0.5)
        formula[3].set_color(ROSE)
        formula[4].set_color(AMBER)
        fix_in_frame(self, formula)
        self.play(Create(axes), FadeIn(chart[1]), run_time=0.8)
        self.play(LaggedStart(*[GrowFromEdge(b, DOWN) for b in chart[2]], lag_ratio=0.03),
                  Create(chart[4]), FadeIn(chart[3]), FadeIn(grid), Write(formula), run_time=1.5)
        cap = swap_caption(self, None, "first caption, in the standard position")
        self.wait(0.6)
        cap = swap_caption(self, cap, "second caption: never superimposed on the first")
        self.wait(0.6)
        self.play(FadeOut(chart), FadeOut(grid), FadeOut(cap), run_time=0.6)

        # ---- 3D: ribbons, depth sorting, floor tiles, camera move ----
        def P(d, a, z):
            return np.array([(d - 8) * 0.4, (a - 5) * 0.55, z * 3.0])

        self.set_camera_orientation(**CAM_3D, zoom=0.9)
        ribbons = []
        for a in range(9, -1, -1):                              # far -> near
            vals = M[a]
            ribbons.append(ribbon_3d([P(d + 1, a, vals[d]) for d in range(15)],
                                     [P(d + 1, a, 0) for d in range(15)], BLUE))
        self.play(*[FadeIn(r, rate_func=delayed(0.06 * i, 0.4)) for i, r in enumerate(ribbons)], run_time=1.6)
        tiles = floor_tiles_3d(P, M, np.arange(1, 16), np.arange(10), ramp_for(BLUE))
        self.move_camera(**CAM_TOP, zoom=0.9, run_time=2.0, added_anims=[
            FadeIn(tiles, rate_func=delayed(0.5, 0.5)),
            *[FadeOut(r, rate_func=delayed(0.3, 0.5)) for r in ribbons]])
        self.wait(0.6)
        close_chapter(self)
