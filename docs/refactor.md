# Refactor postsmith: a self-initializing `.postsmith` workspace

You already built the **postsmith** skill. Now change where its state and output live.
Right now outputs go to `output/` and `job.json` sits in the project root, which means
files scatter and have to be moved/downloaded each time. Replace that with a single,
self-initializing per-project workspace folder: `.postsmith/`.

**HARD RULE (unchanged): no comments in any code (Python, JS, HTML).**

---

## The `.postsmith` workspace

The skill is installed once. On **any** command, it locates the workspace and creates it
if missing — there is no required manual setup step (though a `postsmith init` command
should also exist for explicitness). Creating the folder and writing into it is a normal
local action; do it automatically, idempotently (never clobber existing files).

**Discovery:** walk up from the current directory to find an existing `.postsmith/`
(like git finds `.git`); if none is found, create `.postsmith/` in the current directory.
A `resolve_workspace()` helper in a new `scripts/workspace.py` should return the path and
be used by every command.

### Layout

```
.postsmith/
  config.json
  brand.json                         (created from the template on init if absent)
  registry.json                      (index of all jobs, with dates + metadata)
  jobs/
    2026-06-02-launch-carousel/
      job.json
      manifest.json
      master.txt                     (the master prompt, saved as plain text)
      01.png
      02.png
  exports/                           (zips produced by the export command)
```

Job folder names are `<YYYY-MM-DD>-<slug-of-name>`; if two jobs share a date+slug, append
`-2`, `-3`, etc. Slugify the job name (lowercase, spaces -> hyphens, strip non-alphanumerics).

### config.json

Persisted defaults so the user is not re-asked every run:

```json
{
  "version": 1,
  "brand_path": ".postsmith/brand.json",
  "defaults": { "format": "4:5", "quality": "low", "language": "ru", "port": 4848 }
}
```

On init, write this if absent. The wizard's defaults come from here; when the user changes
a setting, that does not have to overwrite config unless they pass a flag — keep it simple.

### registry.json

Append an entry whenever a job finishes generating:

```json
{
  "jobs": [
    {
      "id": "2026-06-02-launch-carousel",
      "name": "launch-carousel",
      "created": "2026-06-02T14:30:00Z",
      "format": "4:5",
      "quality": "low",
      "frames": 5,
      "cost": 0.03
    }
  ]
}
```

Use UTC ISO-8601 timestamps. This is the source of truth for listing history and for the
gallery's "all jobs" view.

---

## Command changes

- **`init`** (new): resolve/create `.postsmith/`, write `config.json` and `registry.json`
  if absent, copy `assets/brand.example.json` to `.postsmith/brand.json` if absent, then
  print the workspace path and tell the user to fill in `brand.json`. Running it twice is
  safe and changes nothing already present.

- **`wizard`**: ensure the workspace exists first (auto-init). Read defaults from
  `config.json`. Read brand from `config.brand_path`. Write `job.json` into a fresh
  date-stamped job folder under `.postsmith/jobs/`, not the project root. Also write
  `master.txt` (empty for now). Print the job folder path.

- **`generate`**: ensure workspace exists. Take a job by its folder id (default: the most
  recent job in the registry, or `--job <id>`). Save PNGs and `manifest.json` into that
  job's folder, save the composed master prompt to `master.txt`, then append/update the
  job's entry in `registry.json` with frame count and total cost. All key-handling and
  spend-confirmation rules from before stay exactly as they are.

- **`serve`**: ensure workspace exists. Two modes: `--job <id>` serves one job's gallery
  (as before), and with no `--job` it serves a **history view** reading `registry.json` —
  a grid of all jobs (newest first) showing date, name, format, frame count, cost, and a
  thumbnail, each linking into that job's full gallery. Still bound to `127.0.0.1` on the
  configured port.

- **`export`** (new): zip a job folder into `.postsmith/exports/<id>.zip` so the user can
  hand off or download everything in one file. `--job <id>` for one job (default: latest),
  `--all` to zip the whole `jobs/` tree. Print the resulting path. This is the "grab it in
  one command" path — no re-downloading anything.

---

## SKILL.md updates

- State that the skill maintains a persistent `.postsmith/` workspace per project, created
  automatically on first use; the user installs the skill once and never moves files by hand.
- Update every path reference (outputs now live in `.postsmith/jobs/<date>-<name>/`, brand
  in `.postsmith/brand.json`, defaults in `.postsmith/config.json`).
- In the self-review step, `view` the PNGs from the job folder under `.postsmith/jobs/`.
- Add a one-line note: the user may add `.postsmith/` to `.gitignore` if they don't want
  generated assets in version control — leave that choice to them, don't edit `.gitignore`
  automatically.
- Keep the safety recap; add that the workspace is local to the project and self-contained.

---

## assets/gallery.html

Make it work for both views. When served for a single job it reads that job's
`manifest.json` as before. When served as the history view it reads `registry.json` and
renders the job grid; clicking a job opens its gallery. Keep it one file, no build step, no
localStorage, and keep the distinctive non-slop look.

---

When done: confirm `.postsmith/` is created automatically by every command, confirm there
are zero code comments, and give me a one-paragraph summary plus the new command list
(`init`, `wizard`, `generate`, `serve`, `export`) with one example each.