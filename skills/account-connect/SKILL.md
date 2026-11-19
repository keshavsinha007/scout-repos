---
name: account-connect
description: >
  This skill should be used when the user asks to "connect to GitHub", "log in to GitHub",
  "link my GitHub account", "set up GitHub access", "check my GitHub connection", or when any
  other scout-repos skill fails with a 401, "not signed in", or rate-limit error.
metadata:
  version: "0.1.0"
---

# Connect Claude to the user's GitHub account

Goal: leave the session with a working, least-privilege GitHub sign-in that both the
`github` MCP server and the helper script (`${CLAUDE_PLUGIN_ROOT}/skills/repo-rating/scripts/scout_tool.py`) can use.

## 1. Check what already works

Run, in this order, and stop at the first success:

1. `python3 ${CLAUDE_PLUGIN_ROOT}/skills/repo-rating/scripts/scout_tool.py whoami` - reports the login and remaining API calls.
2. `gh auth status` - the GitHub CLI may already be signed in.
3. Try a lightweight `github` MCP tool (for example `get_me`) if the MCP tools are loaded.

If any succeeds, tell the user which account is connected and stop.

## 2. Pick a sign-in method

Offer these, recommended first:

| Method | When to use | What the user does |
|---|---|---|
| **GitHub CLI (`gh auth login`)** | Local machine with a terminal | Run `gh auth login --web --scopes "repo,read:org"` and finish the browser prompt. The script picks the token up automatically. |
| **Plugin token setting** | Extra GitHub tools (issues, PRs, files) | When the plugin is enabled, Claude Code asks for an optional *GitHub token* and stores it securely. Create a fine-grained token at https://github.com/settings/personal-access-tokens/new with **read-only** *Contents*, *Metadata*, *Issues*, *Pull requests*. Change it later via `/plugin` → scout-repos → configure. |
| **Environment variable** | CI / no browser | Set `GITHUB_TOKEN` to a fine-grained token; the helper script picks it up. |
| **Claude GitHub connector** | Using Claude on the web/app | Connect GitHub in Claude's connector settings, then retry. |

Rules:

- Never ask the user to paste a token into the chat. Direct them to set it as an environment variable or use `gh auth login`.
- Never print, echo, log, or write a token to a file. Do not commit `.env` files.
- Request write scopes (`repo` with push, `workflow`) only when the user explicitly wants Claude to push, open PRs, or create repos.

## 3. Verify

Re-run `scout_tool.py whoami`. Confirm the login name and that the hourly limit is ~5,000 (signed-in) rather than 60 (anonymous).

## Troubleshooting

- **401 / bad credentials** - token expired or revoked; create a new one or run `gh auth refresh`.
- **403 with "rate limit"** - anonymous use exhausted; signing in fixes it.
- **403 "SAML enforcement"** - the org requires SSO; authorize the token for that org on the token settings page.
- **Code search fails** - GitHub code search always requires a signed-in account.
- **Proxy / sandbox blocks api.github.com** - say so plainly; ask the user to run the commands on their own machine or connect the GitHub connector.
