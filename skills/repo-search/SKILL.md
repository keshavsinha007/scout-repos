---
name: repo-search
description: >
  This skill should be used when the user asks to "search GitHub", "find a repo for",
  "look for code that does", "search GitHub code", "find examples of X on GitHub",
  "find issues about", or wants to locate repositories, files, functions, or discussions on GitHub.
metadata:
  version: "0.1.0"
---

# Search GitHub

## Tools (use the first that works)

1. **`github` MCP server** - `search_repositories`, `search_code`, `search_issues`, `get_file_contents`.
2. **Helper script** -
   `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/scout_tool.py search "<query>" [--type repositories|code|issues] [--sort best|stars|updated] [--language X] [--min-stars N] [--limit N]`
3. **GitHub CLI** - `gh search repos|code|issues "<query>" --limit 20 --json ...`
4. **Web search** with `site:github.com` as a last resort (no metadata, lower quality).

If all signed-in routes fail, run the `account-connect` skill.

## Build good queries

Turn the user's plain request into 2-4 GitHub queries instead of one. Useful qualifiers:

| Need | Qualifier |
|---|---|
| Language | `language:python` |
| Popular only | `stars:>=100` |
| Still maintained | `pushed:>=2025-01-01` (use a date ~12 months before today) |
| Match name/description/topics | `in:name,description,topics` |
| Topic tag | `topic:llm` |
| Exclude dead repos | `archived:false` |
| Code in a file type | `extension:py`, `path:src/` (code search) |
| Code in a specific repo | `repo:owner/name` |
| Exact function | `"def parse_table"` (code search) |

Example: "a fast Python library to pull tables out of PDFs" →
`pdf table extraction language:python stars:>=100 archived:false`,
`topic:pdf-extraction language:python`, `"extract tables" pdf in:readme language:python`.

## Present results

- Show a short table: repository, one-line description, stars, last updated, license.
- Flag archived repos, missing licenses, and repos not updated in over a year.
- For code results, give the file path and link, and quote at most a few relevant lines.
- Number the results so the user can pick one. Offer the next step: rate the top picks
  (`repo-rating`), compare them (`find-best-code`), or install the one the user chooses
  (`repo-install`). Never install a search result the user hasn't picked.
