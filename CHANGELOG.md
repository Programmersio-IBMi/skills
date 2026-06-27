# Changelog

All notable changes to this project are documented here.

The format is loosely based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] — 2026-06-27

### Added

- **3D application map generation** (`references/app-map.md`): produce an interactive 3D map of a whole library or application area — menus, programs, data files, display/printer files, and external calls as nodes, with read/write/call/submit relationships as links. Authored as a single JSON data file (the source of truth) and built into a self-contained HTML viewer by `scripts/build_app_map.py` from `templates/app-map-template.html`. Ships with a node-budget recipe, a closed node/link vocabulary the builder validates, and a guided-tour walkthrough.

### Changed

- `SKILL.md` references table and `references/index.md` routing updated to surface the new app-map capability ("app map of library/area X", "3D map").

## [1.1.0] — 2026-06-11

### Added

- **Visual flowchart generation** (`references/flowchart.md`): produce a single-page HTML flowchart of a program — caller context, subroutine/procedure flow, and external-call nodes — from `references/templates/flowchart-template.html`, gated by the `scripts/validate_flowchart.py` lint check.
- **Test case document generation** (`references/test-case-generation.md`): a fifth document type (QA/UAT test scripts) alongside the four audience templates, built from `references/templates/template-testcases.md` and gated by the `scripts/validate_testcases.py` lint check.

### Changed

- Richer Word/PDF export from the markdown converter scripts: branded cover page, styled tables/headings, and broader markdown coverage in both `convert_md_to_docx.py` and `convert_md_to_pdf.py`.
- `SKILL.md` references table, templates README, and the program-documentation workflow refreshed to route to the new flowchart and test-case capabilities.

## [1.0.2] — 2026-06-02

### Changed

- Synced the `ia` skill with the latest upstream guidance. Adds **Rule Zero** (always query iA, never the workspace), **Rule One** (uppercase every name), **Rule Two** (empty result = not found, never substitute), and a **Routing Pitfalls** table that steers each kind of ask to the right tool the first time.
- Added SQL long↔short name guidance (`ia_sql_table_names`) so field-impact and where-used queries resolve long table/column names to their 10-char system names before lookup.
- Documented the new `ia_circular_deps` tool (SELF + MUTUAL cycle detection) and refreshed the program-documentation workflow, playbooks, and query flows to match the current tool set (now 51 tools).

## [1.0.1] — 2026-06-02

### Removed

- Session-start hooks (Claude Code, Cursor, GitHub Copilot CLI). They ran `bash hooks/session-start`, which errored on startup in any environment without `bash` on `PATH` (e.g. Windows without Git Bash or WSL).
- `using-ia` bootstrap meta-skill. It only loaded via the session-start hook, so it no longer served a purpose; the `ia` skill's own description drives discovery.

## [1.0.0] — 2026-05-17

### Added

- Initial public release of the `ia` skill (IBM i Impact Analysis)
- `using-ia` bootstrap meta-skill that primes the agent on session start
- Session-start hooks for Claude Code, Cursor, and GitHub Copilot CLI
- Plugin manifests for:
  - Claude Code (`.claude-plugin/plugin.json` + `marketplace.json`)
  - OpenAI Codex (`.codex-plugin/plugin.json` + `.agents/plugins/marketplace.json`)
  - Cursor (`.cursor-plugin/plugin.json`)
  - Gemini CLI (`gemini-extension.json`)
  - GitHub Copilot Agent Plugins (root `plugin.json` + `.github/plugin/marketplace.json`)
- Context-file pointers: `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`
- Version-sync automation: `.version-bump.json` + `scripts/bump-version.sh`
- CI: `validate.yml` (JSON/YAML + version consistency), `ip-guard.yml` (forbidden-string scan), `release.yml` (tag-driven release)
- MIT license
