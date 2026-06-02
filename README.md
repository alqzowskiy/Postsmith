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
- **Three modes.** `auto` builds everything from your brand, `assisted` wraps a rough idea in
  the brand look, `raw` sends your exact words straight through with no brand and no anti-slop.
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
- *Optional:* [Pillow](https://pypi.org/project/Pillow/) — only used to crop `4:5` and `9:16`
  frames to exact ratio. Without it those frames are saved at full `1024x1536` and postsmith
  tells you so.

## Install

postsmith is a skill directory. Install it once for Claude Code:

```bash
git clone https://github.com/alqzowskiy/postsmith.git
cp -r postsmith/postsmith ~/.claude/skills/postsmith
```

That's it — Claude now triggers postsmith on any "make me a carousel / post / story /
infographic" request. You can also run the scripts directly without Claude (see below).

Then add your key to a `.env` file at your project root (never paste it into chat):

```
OPENAI_API_KEY=sk-...
```

## Quick start

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

The wizard asks format / quality / language / slide count and writes a date-stamped job
folder under `.postsmith/jobs/`. Fill in the master prompt and each slide prompt in that
job's `job.json` (or let Claude do it). Then generate, review, serve, and hand off:

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
  config.json                        persisted defaults (format, quality, language, port)
  brand.json                         your brand, scaffolded from the template
  registry.json                      index of every generated job
  jobs/
    2026-06-02-launch-carousel/
      job.json                       master + per-slide prompts
      master.txt                     the master prompt as plain text
      manifest.json                  per-frame id, file, prompt, cost
      01.png  02.png  ...            generated frames
  exports/                           zips from `export`
```

The workspace is local and self-contained. postsmith **never** edits your `.gitignore` — if
you don't want generated assets in version control, add `.postsmith/` yourself.

## Commands

| Command | What it does | Example |
|---|---|---|
| `init` | Create `.postsmith/`, scaffold `config.json`, `registry.json`, `brand.json` | `postsmith.py init` |
| `wizard` | Interactively create a date-stamped job folder | `postsmith.py wizard` |
| `generate` | Generate a job's frames (default: latest) | `postsmith.py generate --job <id>` |
| `serve` | Serve one job's gallery, or the history of all jobs | `postsmith.py serve` |
| `export` | Zip a job (or `--all`) to `.postsmith/exports/` | `postsmith.py export --job <id>` |

`serve` with no `--job` opens a history grid of every job (newest first) linking into each
job's gallery. Pass `--yes` to `generate` to skip the two interactive confirmations when
running non-interactively. All servers bind to `127.0.0.1` only.

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

## Contributing

Issues and PRs welcome — see [CONTRIBUTING.md](CONTRIBUTING.md). One firm house rule: **no
comments in any code** (Python, JS, HTML). The original design specs live in [`docs/`](docs/).

## License

[MIT](LICENSE) © alqzowskiy. Not affiliated with OpenAI or Anthropic; "gpt-image-2" and
"Claude" are trademarks of their respective owners.
