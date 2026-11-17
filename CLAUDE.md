# Pipeline Forecast

Business-day sales-pipeline forecasting prototype: a win kernel convolved with the open stock and with forecast arrivals. Commands and architecture are in [README.md](README.md).

## Gotchas

- **Two interpreters.** `.venv` runs the pipeline (duckdb, pandas). `animation/.venv` runs manim only. `animation/build_data.py` uses the project `.venv`; everything else under `animation/` uses its own.
- **`outputs/` is generated and git-ignored.** For any other configuration, run the pipeline into a scratch `--output-dir`, so `outputs/` keeps the user's last run.
- **The README chart is its own configuration:** `--as-of-date 2025-05-01 --horizon 15 --max-age 45`. The defaults are horizon 30 and max age 90. The committed image predates the current simulation, so regenerated numbers differ slightly.
- **Day indexing.** Code uses `day_offset` 1..H; the README chart labels the same days 0..H-1. Stock aged `a` converts on day `d` at age `a + d`; an arrival on day `t` converts on day `d` at age `d - t`.
- **The top age is a pooled bucket** (`max_age` means "that age or older"); the model projects no wins from it.

## Animated explainer

The film of the model lives in [animation/](animation/), and [animation/README.md](animation/README.md) records how it was built. To animate another idea, use the `manim-explainer` skill.
