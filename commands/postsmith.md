---
description: postsmith — brand-consistent visuals with gpt-image-2 (init/wizard/generate/serve/export, or a plain request)
argument-hint: generate --job <id> | serve | export --job <id> | "make an anime carousel"
---

You are driving the **postsmith** skill through its CLI at
`~/.claude/skills/postsmith/scripts/postsmith.py`. Run everything from the user's current
project directory so the `.postsmith/` workspace is created there.

The user typed: `$ARGUMENTS`

Routing:

- If `$ARGUMENTS` begins with `init`, `wizard`, `serve`, or `export`, run that subcommand
  directly:
  `python3 ~/.claude/skills/postsmith/scripts/postsmith.py $ARGUMENTS`
  Run `serve` in the background so the chat stays usable, then tell the user the URL it prints.
- If `$ARGUMENTS` begins with `generate`, follow the spend-safety flow below — never run a
  bare `generate` (it would block on the interactive confirmations).
- If `$ARGUMENTS` is empty, list the five subcommands with one-line descriptions and ask what
  they want.
- Otherwise treat `$ARGUMENTS` as a creative brief and run the full postsmith process from the
  SKILL: settle the prompt mode, read `.postsmith/brand.json`, ask the production settings
  (format, quality, the free-text **style**, baked vs **overlay** text, slide count), write the
  master + slide prompts into a new job folder, show the estimate, generate after an explicit
  yes, self-review the frames, then serve the gallery.

Spend-safety flow for `generate` (non-negotiable):

1. First show the cost for free by declining the key:
   `printf 'n\n' | python3 ~/.claude/skills/postsmith/scripts/postsmith.py $ARGUMENTS`
   This prints the estimate and spends nothing.
2. Show the user the estimated total and wait for an explicit "yes / да".
3. Only after they confirm, run it for real by appending `--yes`:
   `python3 ~/.claude/skills/postsmith/scripts/postsmith.py $ARGUMENTS --yes`
4. Then `view` the generated PNGs and give a short per-slide keep/reshoot verdict.

Hard rules: never print, log, or echo the `OPENAI_API_KEY`; never read its value into your own
context. The preview server binds to `127.0.0.1` only. The workspace is created in the user's
current directory — if they seem to be in the wrong folder, say so before generating.
