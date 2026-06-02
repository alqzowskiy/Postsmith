# Changelog

All notable changes to postsmith are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-06-02

### Added
- Self-initializing per-project `.postsmith/` workspace, discovered by walking up from the
  current directory (like git finds `.git`) and created automatically by every command.
- `init` command: scaffolds `config.json`, `registry.json`, and `brand.json`.
- `export` command: zips a job folder (or `--all`) to `.postsmith/exports/`.
- `config.json` with persisted defaults (format, quality, language, port).
- `registry.json` indexing every generated job (date, frames, cost, thumbnail).
- Date-stamped job folders `jobs/<YYYY-MM-DD>-<slug>/` with `job.json`, `master.txt`,
  `manifest.json`, and frames together in one place.
- History view in `serve` (no `--job`): a grid of every job linking into its gallery.
- Open-source project files: README, LICENSE (MIT), CONTRIBUTING, this changelog, a stdlib
  test suite, and GitHub Actions CI.

### Changed
- `generate` and `serve` now take `--job <id>` (default: the latest job) instead of a path.
- Outputs moved from `output/<name>/` to `.postsmith/jobs/<id>/`.
- gpt-image-2 is called through the standard-library `urllib` instead of the OpenAI SDK,
  removing the last hard dependency.

### Removed
- Automatic editing of the user's `.gitignore`. The workspace is self-contained; adding
  `.postsmith/` to version control (or not) is the user's choice.

## [0.1.0] - 2026-06-01

### Added
- Initial postsmith skill: `wizard`, `generate`, `serve` commands; brand-driven master and
  slide prompts; anti-slop reference and review checklist; local preview gallery; per-image
  cost estimate with a two-step spend confirmation.
