---
name: repo-rating
description: >
  This skill should be used when the user asks to "rate this repo", "is this repository good",
  "check the quality of a GitHub repo", "is this repo maintained", "should I use this library",
  "compare these repos", "score this repository", or pastes a github.com link and asks whether it is trustworthy.
metadata:
  version: "0.1.0"
---

# Rate a GitHub repository

## Run the scorer

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/scout_tool.py rate owner/repo          # one repo
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/scout_tool.py compare a/x b/y c/z      # ranked table
```

Add `--json` to get machine-readable output. Accept full URLs from the user and convert them
to `owner/repo` first. Each rating costs ~5 API calls; with anonymous access (60/hour) rate at
most ~10 repos, otherwise suggest `account-connect`.

If the script cannot reach GitHub, gather the same signals with the `github` MCP tools or
`gh api repos/OWNER/REPO` and apply the rubric in `references/scoring-rubric.md` by hand.

## Interpret the score (0-100)

| Grade | Score | Meaning |
|---|---|---|
| A | 80+ | Popular, actively maintained, licensed - safe default choice |
| B | 65-79 | Solid; check the flagged weak spots |
| C | 50-64 | Usable with care; often niche or slowing down |
| D | 35-49 | Risky - small, stale, or missing basics |
| F | <35 | Avoid unless nothing else exists |

The score measures **health and trust signals, not code correctness**. Always add a short
qualitative check before recommending:

1. Read the README: does it actually do what the user needs? Is there a quick-start?
2. Skim the 5 most recent open issues for show-stoppers (security, data loss, "is this dead?").
3. Check that the license fits the user's use (MIT/Apache/BSD permissive; GPL/AGPL copyleft; none = cannot legally reuse).
4. Note any red flags the script printed (`!` lines).

## Report format

Lead with the verdict in one sentence ("Good choice - grade A, actively maintained, MIT."),
then a compact table of the key numbers, then flags and the qualitative notes. When comparing,
name a winner and say in one line why it beats the runner-up.

See `references/scoring-rubric.md` for the full weighting.
