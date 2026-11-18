import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import *

# ---------------------------------------------------------------------------
# Chapter 01 -- What is an opportunity?
#
# One deal before many: a deal card becomes the film's dot; the dot ages one
# business day at a time (weekends do not count); three deals show the three
# ways a deal's story stands (won, lost, still open); the film's question is
# how many wins land on each of the next 15 business days.
# Everything here is the motif (illustrative), so no data values are drawn;
# the horizon (15) is read from the bundle.
# ---------------------------------------------------------------------------

DOT_R = 0.16            # the hero dot (beats 3-4)
LIFE_R = 0.12           # dots on the lifelines (beat 5)

# ---- day strip (beat 4) -----------------------------------------------------
TILE = 0.74
STEP = 0.86
WEEK_GAP = 0.5
YS = -0.1               # strip centre line
DAYS = "MTWTFSS" * 2
SPAN = 13 * STEP + WEEK_GAP


def tile_x(i: int) -> float:
    return -SPAN / 2 + i * STEP + (WEEK_GAP if i >= 7 else 0.0)


def slot(i: int) -> np.ndarray:
    """Where the dot sits inside tile i (upper half; the age stamp sits below)."""
    return np.array([tile_x(i), YS + 0.12, 0.0])


def stamp_pos(i: int) -> np.ndarray:
    return np.array([tile_x(i), YS - 0.215, 0.0])


# ---- lifelines on a shared age axis (beat 5) --------------------------------
X0, U = -4.9, 0.4                       # age 0 at x = X0, U screen units per day
ROWS = {"A": 2.0, "B": 0.3, "C": -1.4}  # one row per deal, aligned with its card
Y_AXIS = -2.05
A_MAX = 15
CARD_LEFT = 2.05                        # left edge of the definition-card column


def L(age: float, row: str) -> np.ndarray:
    return np.array([X0 + age * U, ROWS[row], 0.0])


def deal_card_icon() -> VGroup:
    """A generic CRM 'deal card': rounded panel, lavender header band with a
    placeholder title and a status dot, an avatar and placeholder text lines."""
    w, h, r = 2.6, 1.75, 0.16
    band_c = shade(OPEN, 0.34)
    panel = RoundedRectangle(width=w, height=h, corner_radius=r, fill_color=PANEL, fill_opacity=1,
                             stroke_color=PANEL_EDGE, stroke_width=2)
    bw, bh = w - 0.05, 0.42
    band = RoundedRectangle(width=bw, height=bh, corner_radius=r - 0.02, fill_color=band_c,
                            fill_opacity=1, stroke_width=0)
    band.move_to(panel.get_top() + DOWN * (bh / 2 + 0.025))
    band_low = Rectangle(width=bw, height=bh / 2, fill_color=band_c, fill_opacity=1, stroke_width=0)
    band_low.align_to(band, DOWN).set_x(band.get_x())
    title_bar = RoundedRectangle(width=0.95, height=0.12, corner_radius=0.06, fill_color=INK,
                                 fill_opacity=0.85, stroke_width=0)
    title_bar.move_to(band).align_to(panel, LEFT).shift(RIGHT * 0.26)
    status = VGroup(Dot(radius=0.07, color=OPEN), Tex("open", font_size=FS_TICK, color=OPEN))
    status.arrange(RIGHT, buff=0.1)
    status[0].set_y(status[1][0][0].get_y())          # dot level with the x-height of "open"
    status.move_to(band).align_to(panel, RIGHT).shift(LEFT * 0.3)
    status.shift(UP * (band.get_y() - status[1][0][0].get_y()))
    avatar = Circle(radius=0.2, fill_color=GRID, fill_opacity=1, stroke_color=MUTED, stroke_width=1.2)
    avatar.move_to(panel.get_corner(UL) + np.array([0.46, -0.83, 0]))

    def bar(width, op=0.55):
        return RoundedRectangle(width=width, height=0.09, corner_radius=0.045, fill_color=MUTED,
                                fill_opacity=op, stroke_width=0)

    l1 = bar(1.35, 0.75).next_to(avatar, RIGHT, buff=0.2).shift(UP * 0.09)
    l2 = bar(0.95).next_to(avatar, RIGHT, buff=0.2).shift(DOWN * 0.1)
    l3 = bar(2.05).move_to(panel.get_bottom() + UP * 0.38).align_to(avatar, LEFT)
    l3.set_x(panel.get_x())
    l4 = bar(1.3).next_to(l3, DOWN, buff=0.1).align_to(l3, LEFT)
    l3.shift(UP * 0.05)
    l4.shift(UP * 0.05)
    return VGroup(panel, band, band_low, title_bar, status, avatar, l1, l2, l3, l4)


class Clip(Scene):
    def construct(self):
        D = load_data()
        H = int(D.meta.horizon)

        # ================================================== 1-2. title, chapter
        film_title(self, "Pipeline Forecast", "how open deals and new deals become a forecast of wins")
        open_chapter(self, 1, "What is an opportunity?", TOTAL,
                     question="What exactly are we counting?", part=PART[1])

        # ================================================== 3. the opportunity
        icon = deal_card_icon().scale(1.2)
        op_card = definition_card("Opportunity", ["a potential sale the team is working on",
                                                  "e.g. a customer asked for a quote"], INK)
        alias = Tex("(op, deal)", font_size=FS_BODY - 2, color=MUTED)
        alias.next_to(op_card[2], RIGHT, buff=0.28).align_to(op_card[2], DOWN)
        op_card.add(alias)
        VGroup(icon, op_card).arrange(RIGHT, buff=1.0).move_to(UP * 0.25)
        self.play(FadeIn(icon, shift=UP * 0.2, scale=0.96), run_time=1.0)
        self.play(FadeIn(op_card, shift=LEFT * 0.25), run_time=0.9)
        self.wait(4.0)

        hero = Dot(UP * 0.25, radius=DOT_R, color=OPEN).set_z_index(3)
        self.play(FadeOut(op_card, shift=RIGHT * 0.2, rate_func=delayed(0, 0.45)),
                  ReplacementTransform(icon[0], hero),
                  FadeOut(icon[1:], target_position=UP * 0.25, scale=0.08),
                  run_time=1.7)
        cap = swap_caption(self, None, "one opportunity = one dot")
        self.wait(1.6)

        # ================================================== 4. age in business days
        tiles, letters = VGroup(), VGroup()
        for i in range(14):
            weekend = i % 7 >= 5
            t = RoundedRectangle(width=TILE, height=TILE, corner_radius=0.1,
                                 fill_color=PANEL, fill_opacity=0.4 if weekend else 1.0,
                                 stroke_color=GRID if weekend else PANEL_EDGE, stroke_width=1.5)
            t.move_to([tile_x(i), YS, 0])
            let = Tex(DAYS[i], font_size=FS_LABEL, color=MUTED).next_to(t, UP, buff=0.14)
            let.set_y(YS + TILE / 2 + 0.25)
            if weekend:
                let.set_opacity(0.4)
            tiles.add(t)
            letters.add(let)
        self.play(LaggedStart(*[FadeIn(VGroup(tiles[i], letters[i]), shift=UP * 0.12) for i in range(14)],
                              lag_ratio=0.06),
                  hero.animate(rate_func=rate_functions.ease_in_out_sine).move_to(slot(2)), run_time=1.5)

        # the counter: "age a = <n>"; the number is its own mobject so it can roll
        def counter(v):
            m = MathTex(r"\text{age}\;\,", "a", "=", str(v), font_size=40, color=INK)
            m[3].set_color(OPEN)
            return m

        c0 = counter(0)
        c0.move_to([tile_x(2), YS + 1.3, 0])
        head, num = VGroup(*c0[:3]), c0[3]

        def next_number(v):
            m = counter(v)
            m.shift(head[0].get_center() - m[0].get_center())   # same typesetting: glyphs coincide
            return m[3]

        created = Tex("created", font_size=FS_TICK + 2, color=MUTED)
        created.next_to(tiles[2], DOWN, buff=0.18)
        stamps = [MathTex("0", font_size=24, color=OPEN).move_to(stamp_pos(2))]
        self.play(FadeIn(head, shift=DOWN * 0.1), FadeIn(num, shift=DOWN * 0.1),
                  FadeIn(stamps[0], scale=0.6), FadeIn(created, shift=UP * 0.08), run_time=0.9)

        cap = swap_caption(self, cap, "age counts business days since creation")
        self.wait(1.6)

        wk_brace = Brace(VGroup(tiles[5], tiles[6]), DOWN, buff=0.1, color=MUTED)
        wk_text = Tex("weekend: not counted", font_size=FS_LABEL, color=INK)
        wk_sub = Tex("(holidays are skipped too)", font_size=FS_TICK + 1, color=MUTED)
        wk_label = VGroup(wk_text, wk_sub).arrange(DOWN, buff=0.1).next_to(wk_brace, DOWN, buff=0.1)

        age = 0
        prev_weekend = False
        for i in range(3, 11):
            weekend = i % 7 >= 5
            dx = slot(i) - hero.get_center()
            anims = [hero.animate.move_to(slot(i)), head.animate.shift(dx), num.animate.shift(dx)]
            if weekend and not prev_weekend:          # the counter greys out: paused
                anims = [hero.animate.move_to(slot(i)), head.animate.shift(dx).set_color(MUTED),
                         num.animate.shift(dx).set_color(MUTED)]
            if not weekend and prev_weekend:
                anims = [hero.animate.move_to(slot(i)), head.animate.shift(dx).set_color(INK),
                         num.animate.shift(dx)]
            self.play(*anims, run_time=0.6, rate_func=smooth)
            if weekend:
                self.wait(0.55)                       # a day passes: nothing is counted
            else:
                age += 1
                new = next_number(age)
                st = MathTex(str(age), font_size=24, color=OPEN).move_to(stamp_pos(i))
                self.play(FadeOut(num, shift=UP * 0.22), FadeIn(new, shift=UP * 0.22),
                          FadeIn(st, scale=0.6), run_time=0.5)
                num = new
                stamps.append(st)
            prev_weekend = weekend
            if i == 4:                                 # Friday: the weekend is next
                self.play(GrowFromCenter(wk_brace), FadeIn(wk_label, shift=UP * 0.08), run_time=0.9)
                self.wait(0.7)
        self.wait(1.0)

        # ================================================== 5. three endings
        # The stamps 0..6 slide together (the weekend gap closes) and become the
        # tick numbers of an age axis; the dot becomes deal A at age 6.
        ax_line = Line([X0, Y_AXIS, 0], [X0 + A_MAX * U, Y_AXIS, 0],
                       stroke_color=MUTED, stroke_width=2)
        ax_ticks = VGroup(*[Line([X0 + a * U, Y_AXIS, 0], [X0 + a * U, Y_AXIS - (0.1 if a % 5 == 0 else 0.055), 0],
                                 stroke_color=MUTED, stroke_width=2) for a in range(A_MAX + 1)])

        def tick_num(a):
            return MathTex(str(a), font_size=FS_TICK, color=MUTED).next_to([X0 + a * U, Y_AXIS, 0], DOWN, buff=0.16)

        ax_title = Tex("age (business days)", font_size=FS_LABEL, color=MUTED)
        ax_title.next_to([X0 + A_MAX * U / 2, Y_AXIS, 0], DOWN, buff=0.52)

        strip_parts = VGroup(tiles, letters, created, wk_brace, wk_label, head, num)
        moves = []
        for k, st in enumerate(stamps):
            tgt = tick_num(k)
            moves.append(st.animate(rate_func=rate_functions.ease_in_out_sine)
                         .scale(FS_TICK / 24).move_to(tgt).set_color(MUTED))
        self.play(FadeOut(strip_parts, rate_func=delayed(0, 0.5)),
                  FadeOut(cap, shift=UP * 0.12, rate_func=delayed(0, 0.3)),
                  hero.animate(rate_func=rate_functions.ease_in_out_sine).move_to(L(6, "A")).scale(LIFE_R / DOT_R),
                  *moves, run_time=2.2)

        nums = VGroup(*[tick_num(a) for a in (0, 5, 10, 15)])

        def lifeline(row, age):
            return Line(L(0, row), L(age, row), stroke_color=OPEN, stroke_width=4).set_stroke(opacity=0.65)

        def deal_name(row):
            return Tex(f"deal {row}", font_size=FS_LABEL, color=MUTED).next_to(L(0, row), LEFT, buff=0.34)

        life_a, name_a = lifeline("A", 6), deal_name("A")
        self.add(nums[0], nums[1])
        self.remove(stamps[0], stamps[5])
        self.play(Create(ax_line), Create(ax_ticks, lag_ratio=0.02),
                  FadeOut(VGroup(*[stamps[k] for k in (1, 2, 3, 4, 6)])),
                  FadeIn(nums[2:]), FadeIn(ax_title),
                  Create(life_a), FadeIn(name_a, shift=RIGHT * 0.1), run_time=1.4)
        cap = swap_caption(self, None, "how does a deal end?")
        self.wait(1.6)

        def card_for(term, lines, color, row):
            c = definition_card(term, lines, color, icon=Dot(radius=0.12, color=color))
            c.move_to([CARD_LEFT + c.width / 2, ROWS[row], 0])
            c[2][0].set_z_index(2)      # the icon must paint above the panel (FadeIn adds it last)
            return c

        def present(card, dot, color, extra=(), run_time=1.2):
            """The deal ends (its dot takes the outcome colour) and its card arrives;
            the card's icon is a copy of that same end dot."""
            rest = VGroup(card[0], card[1], card[2][1], card[3])
            self.play(FadeIn(rest, shift=LEFT * 0.25), dot.animate.set_color(color),
                      TransformFromCopy(dot, card[2][0]), *extra, run_time=run_time)

        # ---- deal A: won at age 6 (a soft amber ring marks the win)
        ring = Circle(radius=LIFE_R, stroke_color=WON, stroke_width=5).move_to(hero)
        card_a = card_for("Won", ["the customer signs:", "the deal converts"], WON, "A")
        present(card_a, hero, WON, extra=[ring.animate(rate_func=rate_functions.ease_out_sine)
                                          .scale(3.6).set_stroke(opacity=0)])
        self.remove(ring)
        self.wait(4.0)

        # ---- deal B: lost at age 11
        dot_b = Dot(L(0, "B"), radius=LIFE_R, color=OPEN).set_z_index(3)
        name_b, life_b = deal_name("B"), lifeline("B", 11)
        self.play(card_a.animate.set_opacity(0.3), FadeIn(dot_b, scale=0.5), FadeIn(name_b, shift=RIGHT * 0.1),
                  run_time=0.8)
        self.play(Create(life_b), dot_b.animate.move_to(L(11, "B")), run_time=1.8,
                  rate_func=rate_functions.ease_in_out_sine)
        card_b = card_for("Lost", ["the deal falls through"], LOST, "B")
        present(card_b, dot_b, LOST)
        self.wait(4.0)

        # ---- deal C: still open today, at age 9
        dot_c = Dot(L(0, "C"), radius=LIFE_R, color=OPEN).set_z_index(3)
        name_c, life_c = deal_name("C"), lifeline("C", 9)
        today = DashedLine(L(9, "C") + DOWN * 0.42, L(9, "C") + UP * 0.42, dash_length=0.07,
                           stroke_color=INK, stroke_width=2).set_stroke(opacity=0.75)
        today_lab = Tex("today", font_size=FS_TICK + 2, color=INK).next_to(today, UP, buff=0.1)
        self.play(card_b.animate.set_opacity(0.3), FadeIn(dot_c, scale=0.5), FadeIn(name_c, shift=RIGHT * 0.1),
                  FadeIn(today), FadeIn(today_lab), run_time=0.9)
        self.play(Create(life_c), dot_c.animate.move_to(L(9, "C")), run_time=1.7,
                  rate_func=rate_functions.ease_in_out_sine)
        future_c = DashedLine(L(9, "C") + RIGHT * 0.18, L(A_MAX, "C"), dash_length=0.1, dashed_ratio=0.5,
                              stroke_color=OPEN, stroke_width=2.5).set_stroke(opacity=0.45)
        qmark = Tex("?", font_size=FS_LABEL + 5, color=OPEN).next_to(L(A_MAX, "C"), RIGHT, buff=0.14)
        card_c = card_for("Still open", ["not decided yet: we only know", "it has survived so far"], OPEN, "C")
        present(card_c, dot_c, OPEN, extra=[Create(future_c), FadeIn(qmark, shift=RIGHT * 0.1)], run_time=1.4)
        self.wait(4.0)

        # ================================================== 6. payoff: the legend
        diagram = VGroup(ax_line, ax_ticks, nums, ax_title, life_a, life_b, life_c, hero, dot_b, dot_c,
                         name_a, name_b, name_c, today, today_lab, future_c, qmark)
        leg_x = X0 + A_MAX * U + 1.05
        legend = VGroup(legend_item("won", WON), legend_item("lost", LOST), legend_item("still open", OPEN))
        for item, row in zip(legend, "ABC"):
            item.move_to([leg_x + item.width / 2, ROWS[row], 0])
        left = name_a.get_left()[0]
        right = legend[2].get_right()[0]
        delta = -(left + right) / 2
        legend.shift(RIGHT * delta)
        sine = rate_functions.ease_in_out_sine
        anims = [diagram.animate(rate_func=sine).shift(RIGHT * delta)]
        for card, item in zip((card_a, card_b, card_c), legend):
            anims += [ReplacementTransform(card[2][0], item[0], rate_func=sine),
                      ReplacementTransform(card[2][1], item[1], rate_func=sine),
                      FadeOut(VGroup(card[0], card[1], card[3]), target_position=item.get_center(), scale=0.12,
                              rate_func=delayed(0, 0.55))]
        self.play(FadeOut(cap, shift=UP * 0.12), run_time=0.4)
        self.play(*anims, run_time=2.8)
        self.add(legend)
        cap = swap_caption(self, None, "every deal ends won or lost, or is still open")
        self.wait(3.0)

        # ================================================== 7. the film's question
        sw, sh, sp = 0.56, 1.5, 0.76
        ys = -0.15
        slots = VGroup()
        for d in range(1, H + 1):
            s = RoundedRectangle(width=sw, height=sh, corner_radius=0.1, fill_color=PANEL, fill_opacity=0.8,
                                 stroke_color=PANEL_EDGE, stroke_width=1.5)
            s.move_to([(d - (H + 1) / 2) * sp, ys, 0])
            slots.add(s)
        d_nums = VGroup(*[MathTex(str(d), font_size=FS_TICK, color=MUTED).next_to(slots[d - 1], DOWN, buff=0.16)
                          for d in range(1, H + 1)])
        d_title = Tex(r"forecast day $d$", font_size=FS_LABEL, color=MUTED).next_to(d_nums, DOWN, buff=0.2)
        heading = Tex(f"next {H} business days", font_size=FS_BODY, color=INK)
        heading.next_to(slots, UP, buff=0.75)
        row = VGroup(slots, d_nums, d_title, heading)

        small = legend.copy().arrange(DOWN, aligned_edge=LEFT, buff=0.16).scale(0.85)
        small.to_corner(UR, buff=0.5)
        self.play(FadeOut(cap, shift=UP * 0.12), run_time=0.4)
        # a pan from the past to the future: the lifelines leave left, the days arrive from the right
        self.play(FadeOut(diagram, shift=LEFT * 4.5, rate_func=delayed(0, 0.6, rate_functions.ease_in_sine)),
                  Transform(legend, small, rate_func=delayed(0, 0.45)),
                  FadeIn(row, shift=LEFT * 4.5, rate_func=delayed(0.35, 0.65, rate_functions.ease_out_sine)),
                  run_time=2.8)

        counts = [0, 1, 0, 2, 0, 1, 0, 0, 2, 1, 0, 0, 1, 0, 1]
        drops = []
        for d, n in enumerate(counts):
            for k in range(n):
                p = slots[d].get_bottom() + UP * (0.22 + 0.3 * k)
                drops.append(Dot(p, radius=0.12, color=WON))
        self.play(LaggedStart(*[FadeIn(dt, shift=DOWN * 0.9, rate_func=rate_functions.ease_in_quad)
                                for dt in drops], lag_ratio=0.18), run_time=1.8)
        qs = VGroup(*[Tex("?", font_size=FS_LABEL + 3, color=TOTAL).next_to(s, UP, buff=0.14) for s in slots])
        self.play(LaggedStart(*[FadeIn(q, shift=DOWN * 0.1) for q in qs], lag_ratio=0.05), run_time=1.0)
        cap = swap_caption(self, None, "how many wins on each coming business day?")
        self.wait(3.0)

        # ================================================== 8. takeaway
        takeaway(self, "a deal is open until it is won or lost", TOTAL, old_caption=cap)
        close_chapter(self)
