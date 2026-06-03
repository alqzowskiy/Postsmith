# postsmith

**A Claude skill that generates brand-consistent Instagram visuals with OpenAI's gpt-image-2 — and refuses to make AI slop.**

[![License: MIT](https://img.shields.io/badge/License-MIT-e8743b.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-0e3b2e.svg)](https://www.python.org/)
[![Zero dependencies](https://img.shields.io/badge/dependencies-zero-0e3b2e.svg)](#requirements)

postsmith turns a request like *"make a launch carousel"* into a coherent set of posts,
carousel slides, stories, or infographics. It writes the prompts from your brand, generates
the images, self-reviews each frame against a concrete anti-slop checklist, and serves a
local preview gallery. The value is in the **prompt craft and the review** — not in clicking
generate.

It is built as a [Claude Code](https://claude.com/claude-code) skill: drop it in once and it
fires automatically whenever you ask for social-media visuals, in English or Russian, even if
you never say the word "postsmith".

---

## Why

"Don't look like AI" is useless as an instruction — it names no behavior. AI slop is a
specific set of habits: glossy 3D plastic blobs, unmotivated purple-to-blue gradients,
dead-center symmetry, fake bokeh filler, smeared text, stock-photo handshakes, particle and
hexagon clutter. postsmith encodes those as explicit *never* rules in every prompt and runs a
review checklist after generation. See [`postsmith/references/anti-slop.md`](postsmith/references/anti-slop.md).

## Features

- **Brand-consistent sets.** One *master prompt* carries the look (palette, type, light,
  material, grid, mood); each *slide prompt* only changes its subject and caption — so a
  carousel stays visually coherent.
- **Any visual style, free text.** postsmith always asks the style and takes whatever you
  type — `editorial photo`, `anime`, `high-tech futuristic`, `35mm film`, `3D render`,
  `risograph` — and threads it through the whole set.
- **Exact text, optional.** Choose `baked` (the model letters the captions) or `overlay`
  (the model renders only the background and postsmith composites **guaranteed-correct**
  headlines/prices/dates on top, in your brand font — in the gallery for everyone, baked into
  the PNG when Pillow is present).
- **Variants & reshoots.** `-n 3` makes three versions of each slide to pick from; `--only
  02,04` regenerates just the frames you flagged, keeping the rest and the cost low.
- **Three modes.** `auto` builds everything from your brand, `assisted` wraps a rough idea in
  the brand look, `raw` sends your exact words straight through with no brand and no anti-slop.
- **Drive it from chat.** Auto-triggers on a plain request (*"make an anime carousel"*), or use
  the `/postsmith` command to run any subcommand without typing the full script path.
- **Self-initializing workspace.** Everything lives in one `.postsmith/` folder per project,
  created automatically — no files to move or download by hand.
- **Job history & export.** Every run is indexed in `registry.json`; browse all jobs in a
  history gallery, or `export` any job to a single zip.
- **Local preview gallery.** A distinctive dark editorial gallery (no slop in the UI either),
  served on localhost with click-to-zoom and per-frame download.
- **Cost-aware.** Per-image estimate before every run, two explicit confirmations before any
  spend, and a low/medium/high quality dial.
- **Zero dependencies.** Pure Python standard library. Nothing to `pip install`.

## Requirements

- **Python 3.8+** (standard library only).
- An **OpenAI API key** with access to **gpt-image-2** (pinned snapshot
  `gpt-image-2-2026-04-21`). The model may require **Organization Verification** in the
  OpenAI console before your first call.
- *Optional:* [Pillow](https://pypi.org/project/Pillow/) — used to crop `4:5` / `9:16` frames
  to exact ratio and to **bake** overlay captions into the saved PNGs. Without it, crops are
  skipped (saved at full `1024x1536`) and overlay text is composited in the gallery instead —
  postsmith tells you either way. Drop brand `.ttf`/`.otf` files in `.postsmith/fonts/` for
  exact-font baking.

## Install

postsmith is a skill directory. Install it once for Claude Code:

```bash
git clone https://github.com/alqzowskiy/postsmith.git
ln -s "$PWD/postsmith/postsmith" ~/.claude/skills/postsmith
mkdir -p ~/.claude/commands && ln -s "$PWD/postsmith/commands/postsmith.md" ~/.claude/commands/postsmith.md
```

(Symlinking keeps the installed skill in sync with the repo; `cp -r` works too if you prefer a
copy.) That's it — Claude now triggers postsmith on any "make me a carousel / post / story /
infographic" request, and you also get a `/postsmith` chat command. Skills and commands are
read at **session start**, so open a fresh session to pick up a new install. You can also run
the scripts directly without Claude (see below).

Then add your key to a `.env` file at your project root (never paste it into chat):

```
OPENAI_API_KEY=sk-...
```

## Quick start

**The easy way — from Claude Code.** Open a fresh session in your project and just describe
what you want, or use the command:

```
/postsmith make an anime launch carousel, 3 slides, exact text
```

Claude reads your brand, asks the style/format/text questions, writes the prompts, shows the
estimate, generates after your go-ahead, reviews the frames, and serves the gallery. You can
also call a single step: `/postsmith serve`, `/postsmith generate --job <id>`, etc.

**The manual way — plain CLI**, for running without Claude:

```bash
SKILL=~/.claude/skills/postsmith

python $SKILL/scripts/postsmith.py init
```

`init` creates `.postsmith/` in your current project and scaffolds `brand.json`. Edit
`.postsmith/brand.json` to describe your brand (palette, fonts, tone, references, and an
explicit `never` list). Then:

```bash
python $SKILL/scripts/postsmith.py wizard
```

The wizard asks format / quality / **style** (free text) / **text rendering** (baked vs
overlay) / language / slide count and writes a date-stamped job folder under
`.postsmith/jobs/`. Fill in the master prompt and each slide prompt in that job's `job.json`
(or let Claude do it). Then generate, review, serve, and hand off:

```bash
python $SKILL/scripts/postsmith.py generate --job 2026-06-02-launch-carousel
python $SKILL/scripts/postsmith.py serve     --job 2026-06-02-launch-carousel
python $SKILL/scripts/postsmith.py export    --job 2026-06-02-launch-carousel
```

`generate` shows the cost estimate and asks twice — once to read the key, once to spend —
before any API call.

## The `.postsmith` workspace

Every command locates a per-project `.postsmith/` by walking up from the current directory
(the way git finds `.git`), creating it if missing. Nothing is written outside it.

```
.postsmith/
  config.json                        persisted defaults (format, quality, style, text, port)
  brand.json                         your brand, scaffolded from the template
  registry.json                      index of every generated job
  jobs/
    2026-06-02-launch-carousel/
      job.json                       master + per-slide prompts (+ captions for overlay)
      master.txt                     the master prompt as plain text
      manifest.json                  per-frame id, file, prompt, cost, caption
      01.png  01-2.png  02.png  ...  generated frames (and -N variants)
  exports/                           zips from `export`
  fonts/                             drop brand .ttf/.otf here for overlay baking
```

The workspace is local and self-contained. postsmith **never** edits your `.gitignore` — if
you don't want generated assets in version control, add `.postsmith/` yourself.

## Commands

| Command | What it does | Example |
|---|---|---|
| `init` | Create `.postsmith/`, scaffold `config.json`, `registry.json`, `brand.json` | `postsmith.py init` |
| `wizard` | Interactively create a date-stamped job folder | `postsmith.py wizard` |
| `generate` | Generate a job's frames; `-n N` variants, `--only ids` reshoot | `postsmith.py generate --job <id> -n 3` |
| `serve` | Serve one job's gallery, or the history of all jobs | `postsmith.py serve` |
| `export` | Zip a job (or `--all`) to `.postsmith/exports/` | `postsmith.py export --job <id>` |

`serve` with no `--job` opens a history grid of every job (newest first) linking into each
job's gallery. `generate -n 3` makes three versions of each slide; `generate --only 02,04`
regenerates just those frames. Pass `--yes` to skip the two interactive confirmations when
running non-interactively. All servers bind to `127.0.0.1` only; if the port is busy, `serve`
moves to the next free one.

## Style and exact text

postsmith always asks two things most generators skip:

- **Style** (free text) — the rendering treatment, threaded into every branded prompt so the
  whole set shares one medium. Type anything: `anime`, `high-tech futuristic`, `35mm film`.
- **Text rendering** — `baked` lets the model letter the captions (simple, but spelling can
  drift); `overlay` makes the model render only the background and composites the exact
  caption on top. In overlay mode the words live in a per-slide `caption`
  (`{ "headline", "subhead", "position", "color" }`), so prices, dates, and copy are always
  right. The gallery composites them with a `<canvas>` (zero-dep, downloadable as PNG); with
  Pillow installed, postsmith also bakes the text into the saved file.

## Cost

Per-image, USD (OpenAI calculator):

| quality | 1024×1024 | 1024×1536 / 1536×1024 |
|---|---|---|
| low | 0.006 | 0.005 |
| medium | 0.053 | 0.041 |
| high | 0.211 | 0.165 |

Default to **low for drafts**; only bump approved frames to **high**. The Batch API halves
cost (async); thinking mode and reference-image edits add variable cost.

## Security

- Your API key is read from `.env` and is **never** printed, logged, surfaced, or pasted into
  chat. When Claude drives postsmith, it never reads the key value into its own context.
- Generation requires **two explicit confirmations** — one to read the key, one to spend —
  with the cost estimate shown before the spend.
- The preview server is **localhost-only**, on its own port.

## Using it with Claude

Once installed, the skill's description triggers it automatically. Ask Claude for *"a launch
carousel for our new product"* (or *"сделай карусель"*) and it will settle the mode, read
your brand, ask the production questions, write the prompts, show you the estimate, generate
after your go-ahead, review every frame against the anti-slop checklist, and serve the
gallery.

You can also drive it explicitly with the **`/postsmith`** chat command, which accepts either
a CLI subcommand or a plain brief:

```
/postsmith serve
/postsmith generate --job 2026-06-02-launch-carousel
/postsmith export --job 2026-06-02-launch-carousel --all
/postsmith make an anime carousel, 3 slides, exact text
```

It runs the matching CLI subcommand for you (with the spend confirmation kept for
`generate`), so you never type the full `python …/postsmith.py` path.

## Contributing

Issues and PRs welcome — see [CONTRIBUTING.md](CONTRIBUTING.md). One firm house rule: **no
comments in any code** (Python, JS, HTML). The original design specs live in [`docs/`](docs/).

## License

[MIT](LICENSE) © alqzowskiy. Not affiliated with OpenAI or Anthropic; "gpt-image-2" and
"Claude" are trademarks of their respective owners.
