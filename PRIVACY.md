# Privacy Policy - scout-repos

_Last updated: 19 November 2026_

scout-repos is an open-source plugin that runs entirely inside your own Claude session.
**The plugin author does not run any server and does not collect, store, or receive any of your data.**

## What the plugin talks to

| Service | Why | What is sent |
|---|---|---|
| GitHub REST API (`api.github.com`) | Search, read and rate repositories | Your search terms, the repository names you ask about, and your GitHub token if you signed in |
| GitHub MCP server (`api.githubcopilot.com/mcp/`) | Optional GitHub tools inside Claude | The same, plus whatever GitHub action you ask Claude to perform |
| github.com (git) | Cloning a repository you chose | The repository address |

These requests go directly from your machine to GitHub and are covered by
[GitHub's Privacy Statement](https://docs.github.com/site-policy/privacy-policies/github-general-privacy-statement).
Your conversation with Claude is covered by Anthropic's privacy policy.

## Your GitHub token

- Read only from your environment (`GITHUB_TOKEN`, `GH_TOKEN`, `GITHUB_PERSONAL_ACCESS_TOKEN`) or the GitHub CLI.
- Never written to disk, logged, or sent anywhere except GitHub.
- You can revoke it at any time at https://github.com/settings/tokens.

## Files on your computer

The plugin only writes where you tell it to (by default `./repos/<name>` for cloned repositories).
It does not collect analytics or telemetry.

## Contact

Open an issue at the plugin's GitHub repository.
