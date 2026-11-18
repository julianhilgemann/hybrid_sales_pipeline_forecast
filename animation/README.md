# Animated explainer

A silent, 3Blue1Brown-style film of the forecasting model, written for a viewer who has never seen it: what an opportunity is, how long deals take to decide, why a conditional probability decides how much of today's pipeline converts, and how open deals and new deals add up to the forecast. Eleven chapters in five parts, 14 min 29 s, 1080p60, built with [Manim Community](https://www.manim.community/) from the model's real output (as-of 2025-05-01, 15 business-day horizon, max age 45).

| # | Part | Chapter | Scene | Length |
|---|---|---|---|---|
| 01 | The setting | What is an opportunity? | [s01_opportunity.py](scenes/s01_opportunity.py) | 1:26 |
| 02 | | The pipeline today | [s02_pipeline.py](scenes/s02_pipeline.py) | 1:16 |
| 03 | How long deals take to decide | Win, lose or wait (hazard, survival) | [s03_hazard.py](scenes/s03_hazard.py) | 1:26 |
| 04 | | Learning the rates from history (the estimator) | [s04_estimator.py](scenes/s04_estimator.py) | 1:34 |
| 05 | | The win kernel | [s05_kernel.py](scenes/s05_kernel.py) | 1:04 |
| 06 | Deals already open | Already open (conditional probability) | [s06_conditional.py](scenes/s06_conditional.py) | 1:23 |
| 07 | | Wins from the open pipeline (3D) | [s07_stock3d.py](scenes/s07_stock3d.py) | 1:32 |
| 08 | Deals not yet created | Forecasting new arrivals | [s08_arrivals.py](scenes/s08_arrivals.py) | 0:58 |
| 09 | | Wins from future arrivals (3D) | [s09_arrivals3d.py](scenes/s09_arrivals3d.py) | 1:27 |
| 10 | Putting it together | The forecast and its uncertainty | [s10_forecast.py](scenes/s10_forecast.py) | 1:16 |
| 11 | | The whole machine | [s11_machine.py](scenes/s11_machine.py) | 1:09 |

Rendered video is not committed; build it locally.

## Build

```bash
cd animation
./setup.sh                          # manim environment in ./.venv (needs cairo and LaTeX)
./make_film.sh                      # every chapter at 1080p60, joined and verified -> out/
./render.sh s07 preview             # one chapter at 720p30 (draft | preview | final | still)
../.venv/bin/python build_data.py   # optional: regenerate data/model_data.json from the pipeline
```

`build_data.py` runs with the project's interpreter (it needs duckdb and pandas); everything else runs with `animation/.venv`. On an M1 the eleven 1080p renders add up to about 22 minutes (chapter 07, the densest 3D chapter, about 5); `make_film.sh` runs four at a time.

| File | Role |
|---|---|
| [build_data.py](build_data.py) | runs the real pipeline and writes the one data file every scene reads: kernel, hazards and counts, open pipeline, both surfaces, the forecast, a cohort of 100 deals that follows the real hazards, the conditional worked example, real lifelines, and 400 simulated futures of the same system |
| [common.py](common.py) | palette, type (Source Sans Pro for words, Computer Modern for maths), chapter cards with guiding questions, takeaways, definition cards, chart builders, and `HeatTowers`, the 3D heat-map that rises, flattens into the heat-map and stacks onto a wall as the marginal bar chart |
| [GUIDE.md](GUIDE.md) | the binding author guide: teaching rules, notation, colour semantics, data schema |
| [render.sh](render.sh), [make_film.sh](make_film.sh) | render one chapter; render all and join |
| [tools/](tools/) | contact sheets and stills from a clip, lossless concat, film verification |

## What changed from the first edition

The first edition (seven chapters, 5 min 52 s, commit `7a9db8f`) was correct but too fast and dense to follow: it never said what an opportunity, a win or a loss is, compressed hazards and survival into a few seconds, and showed the heat-maps as ribbons and flat images with abrupt hand-offs to the bar charts. The second edition was rebuilt around the newcomer:

- **Structure.** Five parts, each chapter opening on a guiding question and closing on a one-line takeaway; chapter 02 ends with a roadmap of the film.
- **The basics first.** Chapter 01 defines an opportunity, business-day age (the counter visibly freezes over the weekend), won, lost and still open.
- **Two tangents.** Chapter 03 follows a cohort of 100 deals day by day to show that a hazard is a conditional probability ("divide by the 82 still open, not by 100") and that survival is a chain of daily factors. Chapter 06 shrinks the cohort to the 61 survivors at age 8 to show why today's deals convert at $k(a+d)/S(a)$, then stretches the kernel by $1/S(8)$.
- **The estimator on screen.** Chapter 04 lines real deals up by age, explains censoring, counts $r$, $w$, $\ell$ at one age, and builds $h_w(a) = \frac{w(a)+\alpha}{r(a)+2\alpha}$ and $S(a)$ from the real counts.
- **Real 3D heat-maps.** Chapters 07 and 09 start from one row that looks like a 2D bar chart, tilt into a field of towers, flatten into the README heat-map from above, then slide each column's towers onto the back wall where they stack into the bar of that day's sum, merge, and turn to face the camera as the 2D chart. The bars are literally made of the cells.
- **Pacing rules.** Words before symbols, captions held at least 3 s, formulas built term by term and held at least 4 s, at most one moving focus, things transform rather than fade.

## How it was made

One coordinating Claude session prepared the ground, eleven parallel Opus subagents each built one chapter, and the coordinator reviewed every clip from contact sheets and full-resolution stills before it was rendered at 1080p.

1. **Concept.** The spec fixed the claim (the forecast is today's open deals plus tomorrow's new deals, each pushed through daily win and loss chances learned from history), the notation from [modeling.py](../pipeline_lib/modeling.py), six colours (amber win/kernel, slate loss, lavender still open/survival, rose open pipeline, blue arrivals, teal forecast), the dot motif, and eleven chapters with their beats.
2. **Data.** `build_data.py` gained the cohort of 100 (cumulative wins and losses are rounded expected counts, so it ends at 30 won, 58 lost, 12 open and tracks $100\,S(a)$ within rounding), the age-8 conditional example (asserted equal to the stock surface's row), the full conditional matrix (asserted to reproduce the stock surface), and a stratified sample of 36 real training-window lifelines.
3. **Shared visual language.** `common.py` was rewritten and smoke-tested before fan-out: chapter cards with questions and part labels, takeaways, definition cards, and `HeatTowers`. The smoke test on the real stock surface caught one defect before any author saw the helper: the smallest towers have only a top face, which left a bright rim at the foot of each stacked bar; `merge` now swaps finished stacks for solid bars.
4. **Guide and briefs.** [GUIDE.md](GUIDE.md) carries the teaching rules, polish rules, notation, colours and data schema; each author got a storyboard with its payoff beat and its hand-offs.
5. **Fan-out and review.** Authors took 15–62 minutes and 210–460k tokens each (about 3.4M in total; the 3D chapters cost the most). Ten chapters were approved on first delivery; chapter 06 went back once, because deals lost between ages 9 and 23 stayed lavender in the cohort grid and so read as still open. The coordinator also corrected one number in the guide that an author caught (the simulated mean is 49.3, not 49.4).

Recurring helper gaps the authors worked around in their own files are worth folding into the toolkit next time: `play(..., rate_func=...)` overrides every animation's own rate function (so `delayed` silently stops working); a `FadeIn` in the same `play` paints over transforms; `swap_caption` cannot run alongside other animations; `HeatTowers` needs subset raising, highlighting and a slower default collapse; `pin_label` anchors cannot move; a scene whose 3D content is driven only by updaters needs a host mobject added first, or Cairo freezes it into the static background.

## Known compromises

- Chapter 01's deal ages (6, 11, 9) and dropped win dots are illustrations; every chart elsewhere is real data.
- The cohort of 100 is a rounded expectation of the real hazards, not a simulation, so its small counts differ slightly from the model at single ages (3 of 82 is 0.037 against $h_w(5) = 0.038$; 16 of 61 is 0.26 against 0.25).
- Chapter 04's 36 lifelines are a sample of the 704 deals created in the window; the counts $r(a)$, $w(a)$, $\ell(a)$ shown after it are the full counts, which also include older deals that entered the window already aged.
- Chapter 08's history bars cover the last 60 business days, while the weekday means come from the model's last 180 calendar days, so the folded columns average slightly differently from the mean lines (labelled on screen).
- Chapter 10's futures are a Monte Carlo of the same system (400 runs, 40 drawn), labelled "simulated"; the model itself outputs the expectation. The simulated 15-day mean is 49.3 against the model's 49.7.
- Chapter 07's tower colours use a gamma of 0.6 on the heat ramp so mid-sized cells are visible; the colour bar uses the same mapping.
- The pooled 45+ bucket (58 deals) is shown in the open pipeline but has no towers: the model projects no wins from it.
- Regenerating as-of 2025-05-01 with today's code gives slightly different numbers than the committed README image, which came from an earlier simulation setup. The film follows the code.
