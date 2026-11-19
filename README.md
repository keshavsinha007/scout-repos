# scout-repos

Lets Claude work with GitHub on your behalf: connect to your account, search GitHub,
rate repositories, clone and install them, and recommend the best code or model for a task.

## Install

In Claude Code:

```
/plugin marketplace add keshavsinha007/scout-repos
/plugin install scout-repos@keshavsinha007
```

Update later with `/plugin marketplace update keshavsinha007`.

## Skills

| Skill | Say something like |
|---|---|
| **account-connect** | "Connect to my GitHub account" |
| **repo-search** | "Search GitHub for Python PDF table extractors" |
| **repo-rating** | "Rate github.com/psf/requests" · "Compare fastapi vs flask" |
| **repo-install** | "Clone and install this repo for me" |
| **find-best-code** | "What's the best open-source OCR model for invoices?" |

## Components

- `.mcp.json` - the official GitHub MCP server (`https://api.githubcopilot.com/mcp/`) for search, file reading, issues and PRs.
- `scripts/scout_tool.py` - dependency-free Python helper: `whoami`, `search`, `rate`, `compare`, `find`.
  Produces a 0-100 health score (stars, freshness, commit activity, contributors, issue health,
  license, docs, releases) with A-F grades and red-flag warnings.

## Setup

Use **one** of these:

1. **GitHub CLI** (easiest): `gh auth login --web` - the helper script uses it automatically.
2. **Personal access token**: create a fine-grained token (read-only Contents, Metadata, Issues,
   Pull requests is enough for search/rate/clone) and set:
   ```bash
   export GITHUB_PERSONAL_ACCESS_TOKEN=github_pat_...   # used by the GitHub MCP server
   export GITHUB_TOKEN=$GITHUB_PERSONAL_ACCESS_TOKEN    # used by the helper script
   ```

Without sign-in the helper still works anonymously (60 API calls/hour; no code search).

Requirements: Python 3.9+, git. Optional: `gh` CLI.

## Safety

- **You choose, Claude installs.** Search only lists numbered options; nothing is installed
  until you pick one by exact name or number and confirm.
- A safety hook (`hooks/hooks.json`) pauses every command that clones or installs code from
  GitHub (`git clone`, `gh repo clone`, `pip install git+…`, `npm install owner/repo`,
  `go install github.com/…`, `curl … | sh`) and asks for your approval.
- Tokens are read only from the environment or `gh`; never pasted into chat or written to disk.
- Installs go into `./repos/<name>`, Python into a virtualenv, no `sudo`, and Claude shows
  install scripts and asks before running them.

## Privacy

No data is collected by the plugin author. See [PRIVACY.md](PRIVACY.md).

## Test before release (maintainers)

Run these on a real machine with internet access:

```bash
python3 scripts/scout_tool.py whoami                       # shows your login and ~5000 calls/hour
python3 scripts/scout_tool.py search "pdf table extraction" --language python --min-stars 100 --limit 5
python3 scripts/scout_tool.py rate psf/requests            # expect grade A
python3 scripts/scout_tool.py compare pallets/flask fastapi/fastapi
python3 scripts/scout_tool.py find "markdown to pdf" --language python --limit 3
echo '{"tool_input":{"command":"git clone https://github.com/psf/requests"}}' \
  | python3 hooks/scripts/confirm_install.py                # expect "permissionDecision": "ask"
```

Then in Claude Code: `claude --plugin-dir .` and ask "find the best Python library for reading Excel files and install it". 
Claude should list numbered options and wait; picking one should trigger an approval prompt before cloning.

## License

[MIT](LICENSE)
