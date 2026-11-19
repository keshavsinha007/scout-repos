---
name: find-best-code
description: >
  This skill should be used when the user asks "what's the best library for", "find the best repo for",
  "recommend a GitHub project for", "which open-source model should I use for", "find better code for",
  "is there a better alternative to", or wants Claude to research GitHub and pick the best code,
  tool, framework, or model for a specific skill, task, or operation.
metadata:
  version: "0.1.0"
---

# Find the best code or model on GitHub for a task

## 1. Pin down the need (only ask what's unclear)

- The task in one line (e.g. "OCR for scanned invoices").
- Language / runtime constraints, and whether it must run offline / on CPU.
- License needs (commercial use?).
- If replacing something: which repo/library they use now.

## 2. Cast a wide net

Run the automated finder first:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/scout_tool.py find "<task keywords>" --language <lang> --limit 5
```

Then widen with 2-3 extra searches via the `repo-search` skill using synonyms and topics
(e.g. "OCR" → `topic:ocr`, "text recognition", "document ai"). For ML models, also search
`topic:<task> model`, curated lists (`awesome-<task>`), and - if web search is available -
Papers with Code / Hugging Face for the leading model, then find its GitHub repo.

Collect 5-10 candidates. Drop archived, unlicensed (if the user needs to reuse code), and
anything off-target after reading its description. Keyword search can't tell direction or
role: for "markdown to pdf" it also returns PDF-to-markdown tools, and for "speech to text"
it returns text-to-speech ones. Check each candidate does the task the right way round.

## 3. Rate and compare

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/scout_tool.py compare owner/a owner/b owner/c ...
```

For the top 3, go beyond the score (see `repo-rating`): read the README quick-start,
check recent issues, confirm license fit, and note dependencies/size.

## 4. Recommend

Reply with:

1. **Pick** - one repo, with the one-sentence reason it fits *this* task.
2. **Comparison table** - repo, score/grade, stars, last update, license, best for.
3. **When to choose the runner-up** - one line each for 1-2 alternatives.
4. **Your choice** - number the options and ask which one to install, if any. Then stop.
   Do not install anything in the same turn, even if the user asked to "find and install";
   install (`repo-install`) only after the user replies with their pick.

Be explicit that popularity ≠ fit: a grade-B repo that does exactly the task beats a grade-A
general framework. If nothing is good, say so and suggest the closest option or building it.
