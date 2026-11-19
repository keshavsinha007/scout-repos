#!/usr/bin/env python3
"""PreToolUse guard: any shell command that clones or installs code from GitHub
must be approved by the user before it runs. Everything else passes through."""
import json
import re
import sys

PATTERNS = [
    r"\bgit\s+clone\b",
    r"\bgh\s+repo\s+clone\b",
    r"\bgit\s+submodule\s+(add|update)\b",
    r"\bpip3?\s+install\b[^|;&]*\bgit\+",
    r"\buv\s+(pip\s+install|add)\b[^|;&]*\bgit\+",
    r"\b(npm|pnpm|yarn)\s+(install|i|add)\b[^|;&]*(github:|github\.com|\s[\w.-]+/[\w.-]+(#\S+)?(\s|$))",
    r"\bcargo\s+install\b[^|;&]*--git\b",
    r"\bgo\s+install\b[^|;&]*github\.com/",
    r"(curl|wget)\b[^|;&]*(github\.com|githubusercontent\.com)[^|;&]*\|\s*(sudo\s+)?(ba|z)?sh\b",
]


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    cmd = (data.get("tool_input") or {}).get("command") or ""
    hit = next((p for p in PATTERNS if re.search(p, cmd)), None)
    if not hit:
        return 0
    piped = "| sh" in cmd or "|sh" in cmd or "| bash" in cmd or "|bash" in cmd
    reason = (
        "scout-repos: this command downloads or installs code from GitHub. "
        "Check the exact owner/repo name before approving."
    )
    if piped:
        reason += " WARNING: it pipes a downloaded script straight into a shell."
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": reason,
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
