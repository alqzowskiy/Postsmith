# Prompt templates

postsmith splits every job into one **master prompt** (everything shared across the set) and
one **slide prompt** per frame (inherits the master, changes only that frame's subject and
caption). This keeps a carousel visually coherent: the look is written once, the subject
varies. gpt-image-2 prefers full natural-language description over keyword tag-soup — write
sentences a photographer or art director would say, not a comma-pile of adjectives.

## The master prompt

The master carries the brand's look. Build it from `brand.json` plus the relevant `never`
lines from `anti-slop.md`. Cover, in order:

1. **Palette** — the dominant color, the surface/background, the single accent. Name hex or
   plain color names. State which color owns the frame.
2. **Type logic** — how text should be set when a frame has a caption: the display face's
   character, hierarchy (one dominant size, one quiet secondary), alignment, and that text is
   part of the design, not stuck on top.
3. **Light & material** — one named light source (direction, time, softness) and one shared
   material the whole set lives in (matte paper, ceramic, brushed metal).
4. **Grid & composition** — where the subject sits, the margins, the negative space, and an
   explicit ban on dead-center symmetry.
5. **Mood** — three or four tone adjectives from the brand, phrased as a feeling, not a filter.
6. **Anti-slop "never" lines** — paste the forbidden items that could plausibly show up for
   this brand (no glossy 3D blobs, no unmotivated gradients, no particle/hex clutter, no
   smeared text, etc.).

Write it as flowing description. Example shape (adapt, don't copy verbatim):

> A set of editorial brand frames in a warm, unfussy style. Deep forest green dominates; a
> soft warm-paper surface sits behind; a single burnt-orange accent punctuates each frame.
> One low afternoon side light from the left throws long soft shadows. Everything is shot on
> the same matte uncoated paper material. Subjects sit in the lower-right third with a wide
> calm left margin and real negative space — never dead-center, never mirrored. Confident,
> warm, quiet, editorial. No glossy 3D plastic, no purple/blue gradients, no floating
> particles or fake bokeh, no smeared or misspelled text.

## The slide prompt

A slide prompt inherits the entire master and only describes **this frame's subject** and its
**verbatim caption**. Keep it short — the master already set the world.

- Name the one subject and how it sits in the established grid.
- If the frame has text, quote it **literally** in the prompt: the words to render, in quotes,
  exactly as they must appear. Legible text is not the same as correct text — gpt-image-2 can
  render clean letterforms and still pick the wrong word or digit, so quote it and verify in
  self-review.
- For exact numbers (prices, percentages, dates), quote the literal string and plan to verify
  it. When precision is critical (a pricing table, a chart with real figures), recommend a
  deterministic HTML/SVG render instead of trusting the model to letter the data.

Example slide prompt:

> Slide 03: a single ceramic pour-over cone, lower-right third, steam catching the side light.
> Caption set in the display face, upper-left: "Single origin. Roasted Tuesdays."

## branded vs raw

The final prompt sent to the API depends on `mode`:

- **branded** (covers `auto` and `assisted`): the API prompt is `master` + a blank line +
  the slide prompt. Brand and anti-slop both apply.
- **raw**: the API prompt is the slide prompt **unchanged**. `master` is empty, no brand, no
  anti-slop — the user's exact words go straight to gpt-image-2.

## job.json schema

```json
{
  "name": "launch-carousel",
  "mode": "branded",
  "format": "4:5",
  "size": "1024x1536",
  "quality": "low",
  "style": "editorial photo",
  "text_mode": "baked",
  "language": "en",
  "model": "gpt-image-2-2026-04-21",
  "brand_path": ".postsmith/brand.json",
  "master": "shared spec, empty when mode is raw",
  "slides": [
    { "id": "01", "prompt": "" }
  ]
}
```

`mode` is `branded` or `raw`. `branded` composes `style` + `master` + slide prompt; `raw`
sends the slide prompt unchanged. `size` is derived from `format` (`1:1` → `1024x1024`; `4:5`
and `9:16` → `1024x1536`; `16:9` → `1536x1024`). Every slide needs a non-empty `prompt`
before generation will run.

## Style

`style` is free text describing the rendering treatment — `editorial photo`, `anime`,
`high-tech futuristic`, `35mm film`, `3D render`, `flat illustration`, `risograph`. It is
prepended to every branded prompt as `Overall visual style: <style>.` so the whole set shares
one medium. Always ask the user for it and accept whatever they type; never lock them to a
list. Ignored in `raw` mode.

## Text mode: baked vs overlay

`text_mode` is `baked` (default) or `overlay`.

- **baked** — gpt-image-2 letters the captions. Put the words, quoted, in the slide prompt.
  Fast, but spelling/numbers can come out wrong; verify in self-review.
- **overlay** — the model renders only the background; postsmith composites the exact caption
  on top (gallery canvas for everyone, baked into the PNG when Pillow is present). Do **not**
  put the words in the prompt; describe the scene and leave the caption area clear. Put the
  words in a per-slide `caption`:

```json
{
  "id": "01",
  "prompt": "a single matte kraft coffee bag in the lower-right third, side light",
  "caption": {
    "headline": "NEW SINGLE ORIGIN",
    "subhead": "Ethiopia · Guji — Hambela",
    "position": "top-left",
    "color": "surface"
  }
}
```

`position` is `top-left`, `bottom-left`, or `center-left`. `color` is optional — a brand
palette key (`dominant` / `surface` / `accent`) or a hex value; it defaults to white with a
soft shadow for legibility. Use overlay whenever prices, dates, or exact copy must be right.
