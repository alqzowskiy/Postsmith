---
name: postsmith
description: Use when the user wants Instagram or social-media visuals of any kind — a post, carousel, story, reel cover, infographic, ad creative, or branded image set — or asks to "send a prompt to the image AI", "generate an image", "make a post", "make a carousel", "design a story", or in Russian "сделай пост", "сделай карусель", "сгенерируй картинку", "нарисуй сторис", "оформи инфографику", "отправь промпт нейросети". Triggers even when the word "postsmith" is never said. Use whenever someone needs brand-consistent image generation with gpt-image-2.
---

# postsmith

Generate brand-consistent Instagram visuals (posts, carousels, stories, infographics)
with OpenAI's **gpt-image-2**. postsmith builds the prompts, reads the API key from
`.env`, generates the images, self-reviews them against an anti-slop checklist, and serves
a local preview gallery. The whole point is to *not* produce AI slop — so the work is in the
prompt craft and the review, not in clicking generate.

**Zero setup, persistent workspace.** The scripts use only the Python standard library —
nothing to `pip install`. The skill is installed once. On any command it locates a
per-project `.postsmith/` workspace (walking up from the current directory, the way git
finds `.git`) and creates it if missing — no manual setup step. Everything postsmith writes
(config, brand file, job folders, generated images, the gallery, exports) lives inside that
one `.postsmith/` folder, so the user never moves or downloads files by hand. The only thing
they must provide is their own `OPENAI_API_KEY` in `.env`.

## Trigger phrases

Any request to make social visuals fires this skill, in English or Russian, with or without
the word "postsmith":

- "make me an Instagram post / carousel / story / infographic"
- "design a launch carousel", "ad creative", "brand image set", "reels cover"
- "send a prompt to the image AI", "generate an image", "use gpt-image"
- "сделай пост / карусель / сторис", "сгенерируй картинку", "нарисуй сторис",
  "оформи инфографику", "отправь промпт нейросети"

## Files

- `scripts/postsmith.py` — entry point: `init | wizard | generate | serve | export`
- `scripts/workspace.py` — finds/creates `.postsmith/`, owns every path, config & registry
- `scripts/wizard.py`, `scripts/generate.py`, `scripts/serve.py`, `scripts/export.py`
- `assets/gallery.html`, `assets/brand.example.json`
- `references/anti-slop.md` — the do/don't list (the core value)
- `references/prompt-templates.md` — how to write master + slide prompts

## Workspace layout (created automatically in the user's project)

```
.postsmith/
  config.json                        persisted defaults (format, quality, language, port)
  brand.json                         copied from assets/brand.example.json, then edited
  registry.json                      index of every generated job (dates, frames, cost)
  jobs/
    2026-06-02-launch-carousel/
      job.json                       the master + per-slide prompts
      master.txt                     the master prompt as plain text
      manifest.json                  per-frame id, file, prompt, cost
      01.png  02.png  ...            generated frames
  exports/                           zips produced by `export`
```

Job folder ids are `<YYYY-MM-DD>-<slug-of-name>`; a same-day collision gets `-2`, `-3`. The
workspace is local to the project and self-contained. The user **may** add `.postsmith/` to
their `.gitignore` if they don't want generated assets in version control — that choice is
theirs; postsmith never edits `.gitignore`.

## Process

### 1. Settle the prompt mode first

Decide this before anything else, because it changes whether brand and anti-slop apply:

- **auto** (default): build a master prompt + per-slide prompts from the brand.
- **raw**: send the user's exact prompt to gpt-image-2 unchanged — no brand, no anti-slop.
- **assisted**: wrap the user's rough idea in the master look.

In auto and assisted, apply `brand.json` + `anti-slop.md`. In raw, apply **neither**. In
`job.json` auto and assisted both write `mode: "branded"`; raw writes `mode: "raw"`.

### 2. Load the brand

Read `.postsmith/brand.json`. If the workspace does not exist yet, run `init` (or any
command auto-creates it) to scaffold `brand.json` from `assets/brand.example.json`. It holds
palette, fonts, tone, language, references, and the explicit `never` list. Only ask the user
for fields the brand file does **not** already answer. Do not re-interview them on things the
brand already states.

### 3. Ask production settings as numbered, pick-a-number questions

Format, quality, caption language, number of slides. Defaults come from
`.postsmith/config.json`. Topic and tone are not enumerable — take those from chat or
`brand.json`.

- When the **user** runs the wizard in their own terminal, they get an interactive numbered
  menu: Enter keeps the default, a digit picks an option, free text gives a custom answer.
  The wizard writes a fresh job folder under `.postsmith/jobs/` and prints its id.
- When **Claude** is driving via bash, you cannot feed an interactive terminal. So ask the
  same numbered questions in chat, then create the job folder yourself: pick the id
  `<today>-<slug-of-name>`, write `.postsmith/jobs/<id>/job.json` directly, and run
  generation non-interactively with `--job <id> --yes` (after the two confirmations in chat).

### 4. Write the prompts

One **master prompt** carrying everything shared across the set — palette, type logic, light,
material, grid, mood, and the relevant anti-slop "never" lines — and one **slide prompt** per
frame that inherits the master and changes only that frame's subject and verbatim caption.
Write them into the job's `job.json`. See `references/prompt-templates.md`.

gpt-image-2 renders in-image text well, so captions and infographic copy are viable — but
**legible is not the same as correct**. For exact numbers, quote the literal string in the
prompt and verify it in step 7. When precision is critical (pricing tables, real chart data),
recommend a deterministic HTML/SVG render instead of trusting the model to letter the data.

### 5. Show the estimate and the full prompt list — wait for an explicit yes

Everything up to here is free. Generation costs money per image. Print the estimate and the
complete list of prompts, and get an explicit yes **before any API call**.

### 6. Generate

Two separate confirmations: one to **read the key**, one to **spend**. The estimate is shown
before the spend confirm.

```
python <skill>/scripts/postsmith.py generate --job <id>
```

With no `--job`, the most recent job is used. When Claude runs it non-interactively (after
both confirmations in chat), pass `--yes`. PNGs, `manifest.json`, and `master.txt` are
written into the job folder, and the job is appended to `registry.json`.

### 7. Self-review

`view` every generated PNG in `.postsmith/jobs/<id>/`. Judge each frame against the slide's
intent and the `anti-slop.md` checklist. For text frames, confirm the caption is the **right
words**, correctly spelled, and any numbers are exactly correct. Give a short per-slide
verdict — **keep** or **reshoot** — and say why for reshoots. Offer to regenerate only the
flagged frames, with a fresh spend confirmation.

### 8. Serve the gallery, and export to hand off

```
python <skill>/scripts/postsmith.py serve --job <id>     one job's gallery
python <skill>/scripts/postsmith.py serve                history of every job
python <skill>/scripts/postsmith.py export --job <id>    zip a job to .postsmith/exports/
```

`serve --job <id>` opens that job's gallery; `serve` with no job opens a history grid of
every job (newest first) that links into each job's gallery. Localhost-only on the configured
port (default 4848). `export` zips a job folder (or `--all` for the whole tree) so the user
can grab everything in one file.

## Cost

Per-image, USD (OpenAI calculator):

| quality | 1024x1024 | 1024x1536 / 1536x1024 |
|---|---|---|
| low | 0.006 | 0.005 |
| medium | 0.053 | 0.041 |
| high | 0.211 | 0.165 |

Default to **low for drafts**; only bump approved frames to **high**. The **Batch API**
halves cost (async). Thinking mode and reference-image edits add variable cost. gpt-image-2
may require **Organization Verification** in the OpenAI console before the first call.

## Running it end to end

```
python <skill>/scripts/postsmith.py init
python <skill>/scripts/postsmith.py wizard
```
→ fill in `.postsmith/brand.json` and the new job's master + slide prompts →
```
python <skill>/scripts/postsmith.py generate --job <id>
python <skill>/scripts/postsmith.py serve --job <id>
python <skill>/scripts/postsmith.py export --job <id>
```

`<skill>` is wherever the postsmith skill is installed; all `.postsmith/` artifacts are
created in the user's current project directory.

## Safety recap

- The key is read from `.env`, and is **never** surfaced, printed, logged, or pasted into
  chat. Claude never reads the key value into its own context.
- Two separate confirmations: reading the key, and spending — the estimate is shown before
  the spend.
- The server is localhost-only, on its own port. The workspace is local to the project and
  self-contained; postsmith never edits the user's `.gitignore`.
- Generation and the server need the user's networked environment with the project `.env`
  (their own Claude Code / Cowork), not a sandboxed web chat with no network. If there is no
  network, stop after the estimate step and hand over the job folder for the user to run.
