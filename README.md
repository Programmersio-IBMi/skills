# Skills by Programmers.io

Agent skills for **IBM i**. Drop-in plugins for Claude Code, GitHub Copilot, Cursor, Gemini CLI, OpenAI Codex, and any harness that reads `AGENTS.md`.

## Skills

| Skill | What it does |
|-------|--------------|
| **ia** | IBM i Impact Analysis — where-used, call hierarchy, field impact, file dependents, program-spec generation. |
| **using-ia** | Tiny bootstrap that primes the agent to reach for `ia` on any IBM i task. Loads automatically via session-start hook. |

## Install

### Claude Code

```
/plugin marketplace add programmersio-ibmi/skills
/plugin install ia@skills
```

### IBM Bob

```
npx skills add programmersio-ibmi/skills
```

Installs to `.bob/skills/` in the current project. Add `-g` to install globally to `~/.bob/skills/` and use across all your Bob projects.

### Gemini CLI

```
gemini extensions install https://github.com/programmersio-ibmi/skills
```

### GitHub Copilot CLI

Add this repo to your settings:

```jsonc
// settings.json
{
  "chat.plugins.marketplaces": [
    "https://github.com/programmersio-ibmi/skills"
  ]
}
```

### Cursor

Install from the Cursor plugin marketplace, or clone manually:

```
git clone https://github.com/programmersio-ibmi/skills ~/.cursor/plugins/ia
```

### Any other harness (manual)

```
git clone https://github.com/programmersio-ibmi/skills
cp -r skills/ia ~/.claude/skills/      # or wherever your harness loads skills from
```

## Try it

Once installed, ask the agent something like:

> *Trace where field `CUSTNO` is used in `CUSTMAST`.*

The agent should invoke the `ia` skill automatically (no `/ia` prefix needed) and answer in 1–2 tool calls.

## How it works

The `ia` skill teaches the agent to use the **iA MCP tools** — a read-only suite for IBM i programs, files, fields, dependencies, and call hierarchies.

You also need the iA MCP server running locally and pointed at an iA-parsed repository. For deployment help, contact us (see below).

## Support

For setup help, MCP server deployment, custom tool requests, or anything else:

**Email: `support@programmers.io`**

## License

MIT — see [LICENSE](LICENSE).
