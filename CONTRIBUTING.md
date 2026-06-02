# Contributing to postsmith

Thanks for helping improve postsmith. It's a small, dependency-free Claude skill, so the bar
for contributing is low — but there are a few firm rules.

## House rules

1. **No comments in any code.** Python, JavaScript, and HTML must contain zero comments. This
   is enforced by a test (`tests/test_no_comments.py`). Write code that reads clearly without
   them; use docstrings only where a public function genuinely needs one.
2. **Zero runtime dependencies.** The scripts run on the Python standard library alone.
   Pillow is the only optional extra, and it must degrade gracefully when absent. Do not add
   required third-party packages.
3. **Never surface the API key.** It is read from `.env` and must never be printed, logged,
   or echoed. Keep the two-confirmation spend flow intact.
4. **Localhost only.** The preview server binds to `127.0.0.1`. Don't change that.

## Project layout

```
postsmith/            the skill itself (this is what users install)
  SKILL.md
  scripts/            postsmith.py + workspace/wizard/generate/serve/export
  assets/             gallery.html, brand.example.json
  references/         anti-slop.md, prompt-templates.md
tests/                stdlib unittest suite
docs/                 original design specs
```

## Development

No build step. Run the checks the way CI does:

```bash
python -m py_compile postsmith/scripts/*.py
python -m unittest discover -s tests -v
```

The test suite is offline and spends nothing — it never calls the OpenAI API.

## Pull requests

- Keep changes focused and the diff small.
- Update `SKILL.md` and `README.md` if you change commands, paths, or behavior.
- Add or update tests for new logic in `scripts/workspace.py`, `scripts/generate.py`, or
  `scripts/export.py`.
- Add an entry to `CHANGELOG.md` under "Unreleased".

## Reporting bugs

Open an issue with the command you ran, what you expected, and what happened. Never paste your
API key or `.env` contents into an issue.
