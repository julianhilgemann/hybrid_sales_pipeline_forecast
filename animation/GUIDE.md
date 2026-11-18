# Pipeline Forecast, second edition: shared guide for chapter authors

## What we are making

A silent, 3Blue1Brown-style explainer film: charts, animation, LaTeX math and short on-screen text, with no narration or audio. It explains the business-day sales-pipeline forecasting model in this repository and ends by reassembling its overview figure (`docs/model-overview.png`).

This is the **second edition**. The first film (seven chapters, in git history at commit `7a9db8f`) was correct but felt like "full force": far too fast and dense, with no explanation of the basics. The viewer we are making this for **has never seen the model and is not a mathematician**. They should come away understanding what an opportunity, a win and a loss are, what a hazard and a survival curve are, why a conditional probability decides how much of the pipeline converts, and how all of it adds up to the forecast, while still seeing the real formulas.

The film proves one claim: **the forecast of daily wins is today's open deals plus tomorrow's new deals, each pushed through daily win and loss chances learned from history.**

It has 11 chapters, about 12 minutes. Each is one manim scene rendered to its own clip; the clips are joined. **You own exactly one chapter.** The other authors are building theirs in parallel right now, so the conventions below are binding: the film must feel like one piece.

Working directory for everything: `animation/` (run every command from there)

Read first, in this order:

1. this guide
2. `../docs/model-overview.png` (open it with Read): the source figure
3. `common.py`: palette, type, data loader, teaching devices, chart and 3D builders
4. `../pipeline_lib/modeling.py`: the model's code
5. `../.claude/skills/manim-explainer/references/manim-pitfalls.md`

## Teaching rules (the point of this edition)

These are binding and are what the coordinator reviews first.

- **Ask, show, name.** Every chapter opens with `open_chapter(..., question=..., part=PART[n])` and ends with `takeaway(...)` then `close_chapter(self)`. In between: show the thing concretely, then give it its name and symbol.
- **Concrete before general.** One deal before many; one age before all ages; one cohort before the formula. Name the instance on screen ("14 deals aged 8").
- **Words before symbols.** The first time the film shows a symbol, it comes with a plain-language label (a `Brace` with words, a `callout`, or a `definition_card`), e.g. $h_w(a)$ with "chance to win today, if still open at age $a$". Inherited symbols may be re-labelled briefly; never assume the viewer remembers.
- **One new idea on screen at a time.** At most one moving focus; dim (opacity 0.25–0.35) what is not being talked about rather than adding more.
- **Reading time.** A caption stays at least 3 s, and nothing new appears during its first 1.5 s. A new formula is built term by term and held at least 4 s. A definition card stays at least 4 s. After the payoff beat, hold at least 2.5 s.
- **Breathing room.** Roughly half of every chapter is stillness or slow ambient motion. If a chapter feels busy, cut a beat rather than speed it up.
- **Captions** are at most 10 words, sentence case, no full stop, in the standard bottom position, changed with `swap_caption` (old out, then new in). The takeaway uses `takeaway()` in the same slot.
- **Numbers on screen** come from `D` and are rounded for reading (0.30, 3.5 wins, 229 deals). Say "expected" for model outputs.

## Polish rules

- Things turn into other things: `Transform`, `ReplacementTransform`, `TransformFromCopy`, `TransformMatchingTex`, or moving the existing object to its new place. Never fade a chart out and fade a near-identical one in.
- Re-layout by moving and scaling what is already on screen (`.animate.move_to(...).scale(...)`), not by rebuilding.
- Timing: entrances 0.8–1.2 s, transforms 1.5–2.5 s, camera moves 3–4 s; nothing visible pops in under 0.5 s. Default rate function `smooth`; long slides `rate_functions.ease_in_out_sine`.
- Emphasis: a soft `SurroundingRectangle(corner_radius=0.1, stroke_width=2)` in the accent colour, or dimming the rest; `Indicate`/`Flash` sparingly.
- Bars grow from their baseline (`GrowFromEdge(bar, DOWN)` in a `LaggedStart`), curves are drawn with `Create`, axes with `Create` (0.8–1.2 s).
- Layout: keep inside x ∈ [−6.75, 6.75], y ∈ [−3.6, 3.6]. The header owns the top-left corner for the whole clip; the caption band (y < −3.0) belongs to captions. Formulas usually sit top-right or top-centre, clear of the header.
- Data fills its axes (at least 60% of the plot height). Start tight and animate a rescale when larger data arrives.
- Every chart has an axis title in words with its unit ("age (business days)", "expected wins per day") and a few tick numbers. Text is never below `FS_TICK` (22).
- In 3D, keep the scene alive during holds of 3 s or more with `self.begin_ambient_camera_rotation(rate=0.03–0.05)`; stop it before the next camera move.

## The model: notation is binding

**The mechanism in plain words.** An *opportunity* (op, deal) is a potential sale. It is created on some business day and is *open* while the sales team works it. Its *age* $a$ counts business days since creation (0 on the creation day; weekends and holidays do not count). It ends in one of two ways: **won** (the customer signs: a conversion) or **lost** (it falls through). Deals not yet decided are **still open**; in historical data such a deal is *censored*: we know it survived up to its current age, not how it ends.

On each business day an open deal of age $a$ faces two competing risks: it wins that day with probability $h_w(a)$ and is lost with probability $h_\ell(a)$, otherwise it stays open. These *hazards* are **conditional probabilities**: chances among deals still open at age $a$. They are estimated from the last 60 business days by counting, at each age, how many deals were at risk and how many won or lost. Chaining the daily "still open" chances gives the *survival* $S(a)$; surviving to $a$ and then winning gives the *win kernel* $k(a)$: the chance that a brand-new deal wins at exactly age $a$.

A deal that is already open at age $a$ today is not brand new: we know it survived to $a$. Its chance to win on forecast day $d$ is the **conditional** probability $k(a+d)/S(a)$. Summed over today's open deals this gives the wins from the existing pipeline. New deals arriving on future day $t$ start at age 0, so they follow $k$ directly, shifted by $t$ (a convolution). The forecast adds both.

| symbol | meaning | formula / source |
|---|---|---|
| $a$ | age in business days since creation | 0 on the creation day |
| $d$ | forecast day, 1 = first business day after the as-of date | $d = 1, \dots, H$, $H = 15$ |
| $t$ | arrival day of a future deal | $t = 1, \dots, H$ |
| $r(a)$ | deals **at risk** at age $a$ in the training window (open when they reached age $a$, watched that day) | `D.kernel.at_risk` |
| $w(a)$, $\ell(a)$ | deals **won** / **lost** at exactly age $a$ in the window | `D.kernel.wins`, `D.kernel.losses` |
| $\alpha$ | additive smoothing, 0.25 | `D.meta.smoothing_alpha` |
| $h_w(a)$ | win hazard: P(win at age $a$ ∣ open at age $a$) | $\dfrac{w(a)+\alpha}{r(a)+2\alpha}$ |
| $h_\ell(a)$ | loss hazard: P(lost at age $a$ ∣ open at age $a$) | $\dfrac{\ell(a)+\alpha}{r(a)+2\alpha}$ |
| $S(a)$ | survival: P(still open at age $a$) | $S(a) = \prod_{j<a}\bigl(1-h_w(j)-h_\ell(j)\bigr)$, $S(0)=1$ |
| $k(a)$ | win kernel: P(a new deal wins at exactly age $a$) | $k(a) = S(a)\,h_w(a)$; $\sum_a k(a) = 0.30$ |
| | conditional win chance of an open deal aged $a$ on day $d$ | $P(\text{win at } a{+}d \mid \text{open at } a) = \dfrac{k(a+d)}{S(a)}$ |
| $N(a)$ | deals open today (as-of 2025-05-01) at age $a$; index 45 pools 45+ | `D.stock.N`, 229 in total |
| $E_{\text{stock}}(a,d)$ | expected wins on day $d$ from the deals aged $a$ today | $N(a)\,\dfrac{k(a+d)}{S(a)}$ |
| $W_{\text{stock}}(d)$ | expected wins on day $d$ from today's open deals | $\sum_a E_{\text{stock}}(a,d)$ |
| $\hat{A}(t)$ | forecast number of new deals arriving on day $t$ | weekday means (seasonal naive) |
| $E_{\text{arr}}(t,d)$ | expected wins on day $d$ from the deals arriving on day $t$ | $\hat{A}(t)\,k(d-t)$ for $d \ge t$ |
| $W_{\text{arr}}(d)$ | expected wins on day $d$ from future arrivals | $\sum_{t \le d} \hat{A}(t)\,k(d-t)$ |
| $\hat{W}(d)$ | the forecast: expected wins on day $d$ | $W_{\text{stock}}(d) + W_{\text{arr}}(d)$ |

LaTeX spellings to use everywhere (split into separate `MathTex` strings to colour terms): `a`, `d`, `t`, `r(a)`, `w(a)`, `\ell(a)`, `\alpha`, `h_w(a)`, `h_\ell(a)`, `S(a)`, `k(a)`, `k(a+d)`, `\frac{k(a+d)}{S(a)}`, `N(a)`, `E_{\text{stock}}(a,d)`, `W_{\text{stock}}(d)`, `\hat{A}(t)`, `k(d-t)`, `E_{\text{arr}}(t,d)`, `W_{\text{arr}}(d)`, `\hat{W}(d)`, `P(\text{win at } a{+}d \mid \text{open at } a)`. Products and sums: `\prod_{j<a}`, `\sum_a`, `\sum_{t \le d}`. Words for the same things: "opportunity" or "deal" (both fine; "op" only in chapter 01's definition), "won", "lost", "still open", "at risk", "hazard", "survival", "win kernel", "open pipeline", "new deals" / "arrivals", "expected wins".

Facts you may quote (all from the bundle): P(win within 45 days) = 0.30, P(lost) = 0.58, still open after 45 days 0.12; the kernel's two humps at about 5 and 13 business days; 229 open deals today, 58 of them pooled at 45+; 14 open deals aged 8 with $S(8) = 0.61$; expected wins over the 15 days: 31.2 from the open pipeline, 18.5 from arrivals, 49.7 in total; the simulated mean of the same system 49.3.

## Colour semantics

Colour the maths like the objects it denotes (aliases in `common.py`):

| thing | constant |
|---|---|
| a win, the win kernel $k(a)$, win hazard $h_w(a)$, win counts $w(a)$ | `WON` = `KERNEL` (amber) |
| a loss, loss hazard $h_\ell(a)$, loss counts $\ell(a)$ | `LOST` (slate) |
| still open: an open deal's dot, survival $S(a)$, at-risk counts $r(a)$ | `OPEN` = `SURVIVAL` (lavender) |
| today's open pipeline $N(a)$, $E_{\text{stock}}$, $W_{\text{stock}}(d)$ | `STOCK` (rose); heat ramp `STOCK_RAMP` |
| future arrivals $\hat{A}(t)$, $E_{\text{arr}}$, $W_{\text{arr}}(d)$ | `ARRIVALS` (blue); heat ramp `ARRIVALS_RAMP` |
| the forecast $\hat{W}(d)$ | `TOTAL` (teal) |
| neutral text and marks | `INK`; secondary `MUTED`; grid `GRID`; panels `PANEL` |

**The motif:** one opportunity is always a small dot. Open = lavender, won = amber, lost = slate. Once open deals become "today's pipeline" they turn rose; future deals are blue. The cohort of 100 brand-new deals (`cohort_grid()`, data `D.cohort`) is the recurring didactic device of chapters 03, 05 and 06. The smooth charts are what the dots do on average.

## Film outline

| # | chapter title (use verbatim) | part | accent | type | target |
|---|---|---|---|---|---|
| 01 | What is an opportunity? | `PART[1]` | `TOTAL` | 2D | 60 s |
| 02 | The pipeline today | `PART[1]` | `STOCK` | 2D | 60 s |
| 03 | Win, lose or wait | `PART[2]` | `SURVIVAL` | 2D | 70 s |
| 04 | Learning the rates from history | `PART[2]` | `KERNEL` | 2D | 70 s |
| 05 | The win kernel | `PART[2]` | `KERNEL` | 2D | 55 s |
| 06 | Already open | `PART[3]` | `STOCK` | 2D | 65 s |
| 07 | Wins from the open pipeline | `PART[3]` | `STOCK` | 3D | 80 s |
| 08 | Forecasting new arrivals | `PART[4]` | `ARRIVALS` | 2D | 50 s |
| 09 | Wins from future arrivals | `PART[4]` | `ARRIVALS` | 3D | 75 s |
| 10 | The forecast and its uncertainty | `PART[5]` | `TOTAL` | 2D | 65 s |
| 11 | The whole machine | `PART[5]` | `TOTAL` | 2D | 60 s |

Targets may stretch by 15% if the pacing needs it; never compress a beat to hit a length.

Every clip starts from an empty background, calls `open_chapter(self, number, title, accent, question=..., part=PART[n])` (chapter 01 calls `film_title` first), tells its story, calls `takeaway(...)`, and ends with `close_chapter(self)`. Neighbouring chapters are made by other authors, so re-establish any object you inherit with a short build (at most 3 s) instead of assuming it is on screen.

## Data: animate the real numbers

`D = load_data()` returns the model's actual output for as-of 2025-05-01, horizon 15, max age 45, 60-day training window (regenerate with `../.venv/bin/python build_data.py`; do not edit it). Read every value from `D`; bars and curves are data, and only the motif may illustrate.

- `D.meta`: `as_of_date`, `horizon` (15), `max_age` (45), `training_window` (60), `smoothing_alpha` (0.25).
- `D.kernel` (arrays of 46, index = age 0..45): `at_risk` $r(a)$, `wins` $w(a)$, `losses` $\ell(a)$, `win_hazard` $h_w$, `loss_hazard` $h_\ell$, `survival` $S$, `win_mass` $k$, `loss_mass`, `win_mass_smooth` (display only: smoothed $k$, same total), `p_win_total` 0.299, `p_loss_total` 0.582.
- `D.stock`: `N` (46; index 45 is the pooled 45+ bucket with 58 deals, and the model projects **no** wins from it), `total_active` 229, `surface` (46 × 15) indexed `[a, d-1]` = $E_{\text{stock}}(a,d)$, `surface_smooth`, `by_day` (15) = $W_{\text{stock}}(d)$, `by_age` (46).
- `D.conditional`: the worked example. `a0` = 8, `N_a0` = 14, `S_a0` = 0.613, `cond_prob` (15) = $k(8+d)/S(8)$, `cond_total` 0.251, `row` (15) = $E_{\text{stock}}(8,d)$, `row_total` 3.52, `matrix` (46 × 15) = $k(a+d)/S(a)$.
- `D.cohort`: 100 brand-new deals following the real hazards. `won_at_age`, `lost_at_age` (46 ints), `open_at_age` (46: open at the start of age $a$, equals $100\,S(a)$ within rounding), `won_total` 30, `lost_total` 58, `open_end` 12, `dots` (100 records `{slot, outcome: won|lost|open, age}`; slot = index into `cohort_grid()`).
- `D.training`: `window_start_rel` −59, `window_end_rel` 0, `sample` (36 real deals created in the window, `{created_rel, end_age, status: won|lost|open}` as known on the as-of date; `open` = censored at `end_age`), `window_counts` (`won` 166, `lost` 338, `open` 200 of the deals created in the window). The full counts $r, w, \ell$ also include older deals that entered the window already aged, so they are larger than anything the sample shows.
- `D.arrivals`: `forecast` (15) = $\hat{A}(t)$, `forecast_dow` (15; 0 = Monday), `forecast_dates`, `dow_means` (dict weekday → mean), `history` (60 records `{rel, date, dow, arrivals}`: the last 60 business days), `surface` (15 × 15) indexed `[t-1, d-1]` = $E_{\text{arr}}(t,d)$ (zero for $d < t$), `by_day` (15) = $W_{\text{arr}}(d)$, `by_origin` (15).
- `D.forecast`: `day` 1..15, `stock`, `arrivals`, `total` = $\hat{W}(d)$, `total_smooth`, `actual` (15: the wins that really happened).
- `D.monte_carlo`: `n_sims` 400, `stock`, `arrivals`, `total` (400 × 15 integer wins per simulated future), `mean_total`, `q05_total`, `q25_total`, `q75_total`, `q95_total`, `particles` (413 records of one simulated future: `{kind: stock|arrival, age0, t, outcome: won|lost|open, day}`).
- `D.lifelines`: 909 records `{created_rel, outcome: won|lost|censored, ttc, closed_rel}` for deals created from 59 business days before to 15 after the as-of date (relative business-day indices; as-of = 0).

Day indexing: the film numbers forecast days $d = 1..15$ (the README chart labels the same days 0..14). An open deal aged $a$ converts on day $d$ at age $a+d$; an arrival on day $t$ converts on day $d$ at age $d-t$.

## Tools in `common.py`

Teaching devices: `open_chapter(scene, n, title, accent, question=, part=)`, `takeaway(scene, text, accent, old_caption)`, `caption` / `swap_caption`, `definition_card(term, lines, color, icon=)`, `callout(text, point, direction, color)`, `legend_item(text, color, mark)`, `cohort_grid()`, `PART[n]`.

2D: `make_axes`, `tick_labels`, `bars`, `hbars`, `curve`, `area_under`, `heat_grid`, `ramp_color`, `shade`.

3D: `flat_shading(scene)`, `CAM_3D`, `CAM_TOP`, `CAM_FRONT`, `delayed`, `pin_label`, `fix_in_frame`, `floor_grid` / `FloorLine`, `ribbon_3d`, `floor_tiles_3d`, and **`HeatTowers`**, the 3D heat-map:

```python
flat_shading(self)                                  # first line of a 3D construct()
T = HeatTowers(D.stock.surface, cell_w=0.42, cell_d=0.14, z_scale=4.7,
               ramp=STOCK_RAMP, origin=(-3.15, -3.22, 0))   # floor's lower-left corner
T.set_lift(0.0)                                     # start flat (it is then the heat-map)
self.move_camera(**CAM_3D, zoom=0.82, run_time=3.5,
                 added_anims=[T.lift(0, 1, order=lambda T: T.ii, lag=0.5)])   # rise, row by row
self.move_camera(**CAM_TOP, zoom=0.82, run_time=3, added_anims=[T.lift(1, 0)])  # flatten: heat-map
self.play(T.lift(1, 0.8 / 4.7), run_time=1.5)      # make room: rescale heights to the wall scale
self.play(T.collapse(axis="y", z_scale_wall=0.8), run_time=3.5)   # stack on the far wall
B = T.merge(self, STOCK)                            # stacks -> solid bars (a HeatTowers)
self.move_camera(**CAM_FRONT, zoom=0.82, run_time=3)  # the wall faces us: a 2D bar chart
```

Facts about it: tower `(i, j)` sits at column `j` (x) and row `i` (y; `row_origin="lower"` puts row 0 nearest the camera, `"upper"` farthest, like a heat-map with row 0 on top). `T.tower_list[k]` is a `VGroup` of faces with `.i`, `.j`, `.value`; you can fade, recolour or `set_opacity` single towers or rows (e.g. dim all rows but one). `collapse(axis="y")` stacks each column on the far-y wall (sum over rows), `axis="x"` each row on the +x wall (sum over columns); towers nearest the wall go first and land at the bottom; after it, `T.stack_tops[j]` is the top z of stack `j` and `T.wall` the wall coordinate. In `CAM_FRONT` a single raised row of towers looks exactly like a 2D bar chart, which makes the cleanest 2D-to-3D hand-off: start level, then tilt. Position HeatTowers with `shift`/`move_to` only. Lines that must sit behind the towers (floor outline, grid, wall axis and its ticks) are `FloorLine`s / `floor_grid`; labels are `pin_label`. The smoke test rendered 950 tower faces fine.

## Technical rules

- Manim Community 0.22.1, Cairo renderer. Python: `.venv/bin/python`, `.venv/bin/manim`. All text is `Tex`/`MathTex` (Source Sans Pro for words, Computer Modern for maths; the template is set in `common.py`). `\textbf`, `\textit`, `$...$` work in `Tex`; `\text{...}` in `MathTex`.
- Your file is `scenes/sNN_<slug>.py` with one class named `Clip` (`Scene`, `MovingCameraScene` or `ThreeDScene`), starting with:
  ```python
  import sys
  from pathlib import Path
  sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
  from common import *
  ```
- Randomness uses `np.random.default_rng(<fixed seed>)`.
- You edit your own scene file and nothing else. For a gap in a shared helper, work around it inside your file and report it. Leave git and package installation to the coordinator.
- Render with `./render.sh sNN draft|preview|still`. Each clip has its own `media/sNN/`. Ten other authors render at the same time on this 8-core machine: iterate at `draft`, one render at a time. `final` belongs to the coordinator.
- Measured here (alone on the machine): a 31 s smoke clip with 20 s of ~950-face 3D took 16–23 s at `draft` and 80 s at `final`. A chapter whose `draft` takes over five minutes needs simplifying.
- 3D chapters: call `flat_shading(self)`; stay under about 1000 polygons on screen; pin text with `fix_in_frame` before animating it; look at a mid-move frame of every camera move.

## Workflow and verification

1. Write the scene, then `./render.sh sNN draft`.
2. `.venv/bin/python tools/contact_sheet.py out/draft/<file>.mp4 --every 2 -o review/sNN_sheet.png`, then Read the PNG. `--start/--end` with a smaller `--every` zooms into a transition. Each tile carries its timestamp bottom-right.
3. Review every beat as a harsh critic **and as the newcomer viewer**: would someone who has never seen this follow it without the brief? Look for: a symbol shown without words; a beat too fast to read; two things moving for attention; overlapping or clipped text; anything touching the frame edge or the header; text below size 22; wrong colour semantics; a formula that departs from the notation; a number that departs from `D`; dead time; a payoff that rushes; depth-sorting pops; objects left behind; a chart swapped by fade instead of transformed.
4. When the draft is right, `./render.sh sNN preview` and pull full-resolution stills at five or more key moments: `... tools/contact_sheet.py out/preview/<file>.mp4 --at 6,14.5,22 -o review/sNN_still.png`. Read them and fix what is not crisp. Complete at least two full review passes.
5. Leave `out/preview/sNN_*.mp4` in place.

## Report back

Plain text:

- scene file, preview video, duration, preview render time
- the beats in order, one line each with approximate timestamps
- the stills you checked and anything you are not fully happy with
- every gap in the shared helpers and your workaround
