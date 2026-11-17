# Chapter brief

One brief per chapter, sent as the author's prompt. The guide carries everything shared; the brief carries only what is particular to this chapter.

## Shape

```text
You are one of {{N}} authors building a silent, 3Blue1Brown-style manim explainer film about
{{subject}}. You own **chapter NN: "{{title}}"**. The other chapters are being built in parallel.

Start by reading the shared guide; it is binding: {{absolute path}}/GUIDE.md
Working directory: {{absolute path of FILM}}
Your scene file: scenes/sNN_<slug>.py (class `Clip`). Render with `./render.sh sNN draft|preview`.

## What this chapter must make the viewer understand
{{Two to four sentences: the idea, why it follows from the previous chapter, the target length.}}
{{What the previous chapter ended on and what the next one starts from.}}

## Storyboard (beats in order; refine the staging, keep the ideas and their order)
1. `open_chapter(self, NN, "{{title}}", {{ACCENT}})`.
2. **{{Beat name}}.** {{What appears, what it turns into, which bundle fields it draws, the caption.}}
…
k. **{{Payoff beat}}.** {{The transform that carries the idea, 2.5–3 s, then a hold.}}
n. Hold on {{the object the next chapter inherits}} about 3 s, then `close_chapter(self)`.

## Things to get right
- {{Scale traps, orientation that must match the source figure, depth-sorting risks, text placement.}}

Follow the guide's workflow exactly (draft, contact sheet, critique, fix; at least two full review
passes; then preview and full-resolution stills). The film is judged on smoothness, fidelity and
crispness: a clip that is correct but muddy or cramped is unfinished. End with the guide's report.
```

## Writing beats

- A beat names objects and transforms, and the bundle field behind every number: "the rose bars `W_stock(d)` (`D.forecast.stock`) lift and stack on the blue bars".
- Give the caption text for each beat, nine words at most.
- Start from one concrete instance before the general case: one age bucket, one cohort, one particle. Name the instance and the field it comes from.
- Mark exactly one beat as the payoff and give it time.
- State orientation whenever the result must match the source figure: which axis runs right, which row is on top.
- Offer optional beats as optional: "include it only if it stays clean; a crisp chapter without it beats a crowded one with it".

## Chapter archetypes

| Archetype | Beats |
|---|---|
| **Opening** | film title; the raw phenomenon as the motif (individual records in motion); the cut between known and unknown; the first aggregate emerging from the motif; the question the film answers |
| **Estimation** | forget the irrelevant dimension; count; turn counts into rates with the formula's terms flying out of the bars; run the motif through the rates until its pile takes the shape of the estimate; the clean estimate and its meaning |
| **3D construction** | ingredients, flat; one slice worked through with its formula; into 3D where every slice stands up as a ribbon; why the surface has its shape; straight down, where the surface is the heat-map of the source figure; back to perspective and collapse onto the wall into the marginal bars |
| **Simple forecast** | history; the pattern made visible; fold into groups; the rule; tile the rule forward; a hint that reality scatters around it |
| **Payoff** | add the streams; the full formula; "what is this number?"; one realisation as unit dots; several realisations; tilt into 3D where realisations fan out in depth; collapse to a band whose mean lands on the model; what actually happened |
| **Finale** | rebuild the source figure panel by panel in the order the film taught it; show the flow through it one path at a time with operation glyphs; shrink to make room for the one-line formula, each term flashing with its panel; hold |

Two 3D constructions in one film use the same grammar, so they rhyme.
