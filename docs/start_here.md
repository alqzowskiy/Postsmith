# Build the "postsmith" skill

Build a complete Claude skill called **postsmith**: a generator of brand-consistent
Instagram visuals (posts, carousels, stories, infographics) using OpenAI's
**gpt-image-2**. The skill builds the prompts, pulls the API key from `.env`,
generates the images, self-reviews them for quality, and shows them in a local
preview gallery.

**HARD RULE: write no comments in any code (Python, JS, HTML). None.**

---

## Folder structure

```
postsmith/
  SKILL.md
  scripts/postsmith.py       (entry point: subcommands wizard | generate | serve via argparse)
  scripts/wizard.py
  scripts/generate.py
  scripts/serve.py
  assets/gallery.html
  assets/brand.example.json
  references/anti-slop.md
  references/prompt-templates.md
```

---

## SKILL.md

Frontmatter with `name` and a **pushy** `description` that triggers the skill on any
request to make social-media visuals, carousels, stories, infographics, or to "send a
prompt to the image AI" — even when the word "postsmith" is never used, in both English
and Russian. List trigger phrases.

Body describes the process step by step (imperative voice, explain *why*, keep under
~300 lines):

1. **Settle the prompt mode first:**
   - `auto` (default): build a master prompt + per-slide prompts from the brand.
   - `raw`: send the user's exact prompt to gpt-image-2 unchanged — no brand, no anti-slop.
   - `assisted`: wrap the user's rough idea in the master look.
   In auto/assisted, apply `brand.json` + `anti-slop.md`; in raw, apply neither.

2. **Load `brand.json`** from the user's project (template at `assets/brand.example.json`):
   palette, fonts, tone, language, references, explicit "never" list. Only ask the user
   for fields the brand file does not already answer — do not re-interview them.

3. **Ask production settings as numbered, pick-a-number questions** (format / quality /
   caption language / number of slides). When the **user** runs the wizard in their own
   terminal, show an interactive numbered menu where Enter keeps the default and a custom
   answer can still be typed. When **Claude** is driving via bash (cannot feed an
   interactive terminal), ask the same numbered questions in chat, write `job.json`
   directly, and run generation non-interactively. Topic and tone are not enumerable —
   take those from chat or `brand.json`.

4. **Write prompts.** One **master prompt** carrying everything shared across the set
   (palette, type logic, light, grid, mood, anti-slop constraints) and one prompt per
   slide that inherits the master and only changes that frame's subject. Write into
   `job.json`. Note that gpt-image-2 renders in-image text well (captions, infographic
   copy are viable), but legible text is not the same as correct data — for exact numbers,
   quote literal strings and verify in step 7, and recommend a deterministic HTML/SVG
   render when precision is critical.

5. **Show the estimate and the full prompt list, wait for an explicit yes BEFORE any API
   call.** Everything up to here is free; generation costs money per image.

6. **Generate** (two separate confirmations: one to read the key, one to spend).

7. **Self-review.** `view` every generated PNG and judge each against the slide's intent
   and the `anti-slop.md` checklist; for text frames, confirm the caption is the right
   words, correctly spelled. Give a short per-slide verdict (keep / reshoot), say why for
   reshoots, and offer to regenerate only the flagged frames with a fresh spend confirm.

8. **Serve the local preview gallery.**

End SKILL.md with a safety recap (see Safety section below).

---

## generate.py — exact technical facts

- Model: pinned snapshot `gpt-image-2-2026-04-21`.
- Call: `client.images.generate(model=..., prompt=..., size=..., quality=...)`.
  The response is base64 in `result.data[0].b64_json` — decode it and write a PNG.
- Sizes: `1:1` -> `1024x1024`; `4:5` and `9:16` -> `1024x1536` (portrait, crop to ratio
  afterwards); `16:9` -> `1536x1024`.
- `quality`: `"low" | "medium" | "high"`.
- Key handling: load `.env` via python-dotenv, with a fallback manual `.env` parser if
  dotenv is not installed; read `OPENAI_API_KEY`. If the key is missing, exit with
  "add OPENAI_API_KEY to .env". **Never** ask the user to paste the key into chat, never
  print it, never log it.
- Compose the final prompt: in `branded` mode it is `master` + blank line + slide prompt;
  in `raw` mode it is the slide prompt unchanged.
- Refuse to generate if any slide prompt is empty (list the empty slide ids and exit).
- Before generating, print the estimate and require a `y/N` confirmation unless `--yes`
  is passed.
- Save PNGs to `output/<job-name>/<id>.png` and write a `manifest.json` recording, per
  frame: `id`, `file`, `prompt`, `cost`.

### Per-image cost table (USD, OpenAI calculator) for the estimate

| quality | 1024x1024 | 1024x1536 / 1536x1024 |
|---|---|---|
| low | 0.006 | 0.005 |
| medium | 0.053 | 0.041 |
| high | 0.211 | 0.165 |

Default to **low for drafts**; only bump approved frames to high. Mention in SKILL.md that
the Batch API halves cost (async) and that thinking mode / reference-image edits add
variable cost. Note that gpt-image-2 may require Organization Verification in the OpenAI
console before the first call.

---

## wizard.py

Interactive numbered prompts. A helper `ask(question, options, default)` prints a numbered
list, marks the default, accepts Enter (keep default), a digit (pick option), or free text
(custom answer). A second helper `ask_text(question, default)` for non-enumerable answers.
Questions: mode (auto / raw / assisted), format (4:5 / 9:16 / 1:1 / 16:9), quality
(low / medium / high), caption language (default from brand), number of slides, job name.
Map format to size as above. Write a `job.json` with empty `master` and empty slide prompts
(to be filled by Claude or the user), then print where it saved and that the prompts are
still empty.

### job.json schema

```json
{
  "name": "launch-carousel",
  "mode": "branded",
  "format": "4:5",
  "size": "1024x1536",
  "quality": "low",
  "language": "en",
  "model": "gpt-image-2-2026-04-21",
  "brand_path": "brand.json",
  "master": "shared spec, empty when mode is raw",
  "slides": [
    { "id": "01", "prompt": "" }
  ]
}
```

---

## serve.py

Start a local gallery server bound to `127.0.0.1` (not `0.0.0.0`) on a dedicated port
(default 4848), serving the job output directory. Copy `assets/gallery.html` into the job
dir as `index.html`, use `ThreadingTCPServer` with `allow_reuse_address`, open the browser
to the URL after a short delay (skippable with `--no-open`), and stop cleanly on Ctrl+C.

---

## assets/gallery.html

A clean, distinctive gallery (this skill is about avoiding AI slop, so the UI must not look
like slop either). Dark editorial look, a characterful display font (not Inter/Arial/Roboto),
one dominant color with a single accent. On load, `fetch('manifest.json')` and render the
frames in carousel order: each card shows the image, its slide id, the prompt text, the
format/size, and the per-frame cost. Click-to-zoom (lightbox) and a download link per frame.
No localStorage or sessionStorage. No build step — plain HTML/CSS/JS in one file.

---

## assets/brand.example.json

A template the user copies to `brand.json`: `brand_name`, `default_language`, `palette`
(dominant / surface / accent hex), `fonts` (display / body), `tone` (array of adjectives),
`light`, `grid`, `references` (array), and a `never` array of forbidden looks.

---

## references/anti-slop.md

The core value of the skill: a concrete do/don't list, because "don't look like AI" is not
actionable. Include a **forbid** list (glossy plastic 3D blobs; unmotivated purple/blue
gradients on white; dead-center symmetry; fake bokeh filler; blown-out HDR highlights;
smeared/misspelled text; generic stock-photo staging; particle/circuit/hexagon clutter;
heavy bevels and skeuomorphic glass; uncanny over-smooth mascots) and an **aim-for** list
(one clear focal element with asymmetric placement and real negative space; a dominant color
with one decisive accent; one believable named light source; one shared material across the
set; type treated as design with real hierarchy; texture/depth from craft not particles).
End with a short review checklist for step 7.

---

## references/prompt-templates.md

Explain how to write the **master prompt** (palette, type logic, light & material, grid &
composition forbidding dead-center, mood adjectives, the relevant anti-slop "never" lines)
and a **slide prompt** (inherits master, changes only this frame's subject and the verbatim
caption). Note gpt-image-2 prefers full natural-language description over keyword tag-soup,
and captions should be quoted literally. Include the `job.json` schema again, explaining
that `branded` composes master + slide and `raw` sends the slide prompt unchanged.

---

## Safety (put a recap in SKILL.md)

- Key is read from `.env`, never surfaced, printed, logged, or pasted into chat; Claude never
  reads the key value into its own context.
- Two separate confirmations: reading the key, and spending — the estimate is shown before spend.
- The server is localhost-only, on its own port and output folder.
- Generation and the server require the user's networked environment with the project `.env`
  (their own Claude Code / Cowork), not a sandboxed web chat with no network. If there is no
  network, stop after the estimate step and hand over `job.json` for the user to run.

---

When everything is written, do a quick read-through of each file with fresh eyes, confirm
there are zero code comments anywhere, and give me a one-paragraph summary of what you built
and how to run it (`wizard` -> fill prompts -> `generate` -> `serve`).