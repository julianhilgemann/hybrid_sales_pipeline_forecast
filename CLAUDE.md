# Pipeline Forecast

Business-day sales-pipeline forecasting prototype: a win kernel convolved with the open stock and with forecast arrivals. Commands and architecture are in [README.md](README.md).

## Gotchas

- **Two interpreters.** `.venv` runs the pipeline (duckdb, pandas). `animation/.venv` runs manim only. `animation/build_data.py` uses the project `.venv`; everything else under `animation/` uses its own.
- **`outputs/` is generated and git-ignored.** For any other configuration, run the pipeline into a scratch `--output-dir`, so `outputs/` keeps the user's last run.
- **The README chart is its own configuration:** `--as-of-date 2025-05-01 --horizon 15 --max-age 45`. The defaults are horizon 30 and max age 90. The committed image predates the current simulation, so regenerated numbers differ slightly.
- **Day indexing.** Code uses `day_offset` 1..H; the README chart labels the same days 0..H-1. Stock aged `a` converts on day `d` at age `a + d`; an arrival on day `t` converts on day `d` at age `d - t`.
- **The top age is a pooled bucket** (`max_age` means "that age or older"); the model projects no wins from it.
- **Open question in the stock projection.** `project_wins_from_active_stock` divides by `S(a)`, the chance of being open at the *start* of age `a`. Deals open on the as-of date have already survived that day, which argues for `S(a+1)`: in the README configuration stock wins would rise from 31.2 to 33.2 (+6.5%). Unresolved; the code, the README and the film all use `S(a)`.

## Animated explainer

The film of the model lives in [animation/](animation/), and [animation/README.md](animation/README.md) records how it was built and how to render it. Editing a chapter: [animation/GUIDE.md](animation/GUIDE.md) holds its binding notation, colours, teaching rules and data schema; shared helpers (including the 3D `HeatTowers`) are in `animation/common.py`. To animate another idea, use the `manim-explainer` skill.

- **`animation/common.py` defaults are what the approved chapters were rendered with.** Add a parameter rather than change a default. After touching a helper, re-render a chapter that uses it at `preview` and compare its frames with the approved copy in `animation/out/show/`.
- **Two copies of the helpers.** The skill's `toolkit/common.py` is the generic source new films start from; `animation/common.py` is this film's copy with its palette and data. A fix that is not specific to this film goes into both.
