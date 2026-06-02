# Changelog

All notable changes to this project are documented here.

The format is loosely based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
