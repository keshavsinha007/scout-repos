#!/usr/bin/env python3
"""scout_tool.py - search, rate and compare GitHub repositories.

Standard library only. Auth is picked up automatically from, in order:
  GITHUB_TOKEN, GH_TOKEN, GITHUB_PERSONAL_ACCESS_TOKEN, or `gh auth token`.
Without a token it still works, at GitHub's lower anonymous rate limit
(60 requests/hour; ~4 requests per repo rated).

Usage:
  scout_tool.py whoami
  scout_tool.py search  "<query>" [--type repositories|code|issues] [--sort stars|updated|best] [--limit 10] [--language python] [--min-stars 50]
  scout_tool.py rate    owner/repo [--json]
  scout_tool.py compare owner/a owner/b ... [--json]
  scout_tool.py find    "<task description>" [--language python] [--limit 5] [--json]
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import math
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.github.com"
_TOKEN: str | None = None
_TOKEN_RESOLVED = False


# --------------------------------------------------------------------------- auth / http
def _token() -> str | None:
    global _TOKEN, _TOKEN_RESOLVED
    if _TOKEN_RESOLVED:
        return _TOKEN
    _TOKEN_RESOLVED = True
    for var in ("GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PERSONAL_ACCESS_TOKEN"):
        if os.environ.get(var):
            _TOKEN = os.environ[var].strip()
            return _TOKEN
    try:
        out = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, timeout=10)
        if out.returncode == 0 and out.stdout.strip():
            _TOKEN = out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return _TOKEN


class GitHubError(RuntimeError):
    pass


def get(path: str, params: dict | None = None, accept: str = "application/vnd.github+json"):
    """GET an API path. Retries once anonymously if the token is rejected."""
    global _TOKEN
    url = path if path.startswith("http") else API + path
    if params:
        url += "?" + urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    headers = {"Accept": accept, "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "scout-repos-plugin"}
    tok = _token()
    if tok:
        headers["Authorization"] = f"Bearer {tok}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read().decode()
            return (json.loads(body) if body else None), dict(r.headers)
    except urllib.error.HTTPError as e:
        if e.code == 401 and tok:
            print("warning: GitHub token rejected (401); continuing anonymously. "
                  "Run the connect step to fix auth.", file=sys.stderr)
            _TOKEN = None
            return get(path, params, accept)
        if e.code == 404:
            return None, dict(e.headers)
        msg = e.read().decode(errors="replace")[:300]
        if e.code in (403, 429) and e.headers.get("X-RateLimit-Remaining") == "0":
            reset = e.headers.get("X-RateLimit-Reset")
            when = dt.datetime.fromtimestamp(int(reset)).strftime("%H:%M") if reset else "later"
            raise GitHubError(f"GitHub rate limit hit (resets at {when}). Connect a token to raise the limit.")
        raise GitHubError(f"GitHub API {e.code} for {url}: {msg}")


# --------------------------------------------------------------------------- helpers
def _days_since(iso: str | None) -> float | None:
    if not iso:
        return None
    t = dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return (dt.datetime.now(dt.timezone.utc) - t).total_seconds() / 86400


def _last_page_count(headers: dict) -> int | None:
    """Read item count from a per_page=1 request's Link header."""
    link = headers.get("Link") or headers.get("link") or ""
    for part in link.split(","):
        if 'rel="last"' in part:
            q = urllib.parse.urlparse(part[part.find("<") + 1: part.find(">")]).query
            return int(urllib.parse.parse_qs(q).get("page", ["0"])[0])
    return None


# --------------------------------------------------------------------------- rating
def rate(full_name: str) -> dict:
    repo, _ = get(f"/repos/{full_name}")
    if not repo:
        raise GitHubError(f"Repository {full_name} not found (or private and not accessible).")

    contrib, h = get(f"/repos/{full_name}/contributors", {"per_page": 1, "anon": "true"})
    contributors = _last_page_count(h) or (len(contrib) if isinstance(contrib, list) else 0)

    release, _ = get(f"/repos/{full_name}/releases/latest")
    commits, h = get(f"/repos/{full_name}/commits", {"per_page": 1, "since": (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=90)).isoformat()})
    commits_90d = _last_page_count(h) or (len(commits) if isinstance(commits, list) else 0)

    community, _ = get(f"/repos/{full_name}/community/profile")
    files = (community or {}).get("files") or {}

    stars = repo["stargazers_count"]
    forks = repo["forks_count"]
    open_issues = repo["open_issues_count"]  # includes PRs
    days_push = _days_since(repo.get("pushed_at")) or 9999
    age_days = _days_since(repo.get("created_at")) or 1
    license_id = (repo.get("license") or {}).get("spdx_id")
    has_license = bool(license_id and license_id != "NOASSERTION")

    # --- component scores (each 0..max) ---
    s_pop = min(30.0, 30 * math.log10(stars + 1) / math.log10(50_000))           # 50k stars = full marks
    s_fork = min(5.0, 5 * math.log10(forks + 1) / math.log10(5_000))
    if days_push <= 30:
        s_fresh = 20.0
    elif days_push <= 90:
        s_fresh = 16.0
    elif days_push <= 180:
        s_fresh = 11.0
    elif days_push <= 365:
        s_fresh = 6.0
    elif days_push <= 730:
        s_fresh = 2.0
    else:
        s_fresh = 0.0
    s_activity = min(10.0, 10 * math.log10(commits_90d + 1) / math.log10(100))
    s_team = min(10.0, 10 * math.log10(contributors + 1) / math.log10(100))
    issue_ratio = open_issues / max(stars, 1)
    s_issues = 5.0 if issue_ratio < 0.02 else 3.5 if issue_ratio < 0.05 else 2.0 if issue_ratio < 0.15 else 0.5
    s_license = 8.0 if has_license else 0.0
    has = lambda k: files.get(k) is not None  # API returns an object when present, null when missing
    doc_pts = sum(has(k) for k in ("readme", "contributing", "code_of_conduct", "issue_template", "pull_request_template"))
    s_docs = float(min(7, (3 if has("readme") else 0) + doc_pts))
    s_release = 5.0 if release else 0.0

    score = s_pop + s_fork + s_fresh + s_activity + s_team + s_issues + s_license + s_docs + s_release
    flags = []
    if repo.get("archived"):
        score *= 0.4
        flags.append("ARCHIVED - read-only, no longer maintained")
    if repo.get("disabled"):
        flags.append("DISABLED by GitHub")
    if repo.get("fork"):
        flags.append(f"is a fork of {(repo.get('parent') or {}).get('full_name', 'another repo')} - check the original")
    if not has_license:
        flags.append("no license - legally you may not reuse the code")
    if days_push > 365:
        flags.append(f"no pushes for {int(days_push)} days")
    if stars > 500 and contributors <= 1:
        flags.append("single maintainer (bus-factor risk)")
    if age_days < 60 and stars > 2000:
        flags.append("very new with fast star growth - verify it isn't hype or star-farming")

    score = round(min(score, 100.0), 1)
    grade = "A" if score >= 80 else "B" if score >= 65 else "C" if score >= 50 else "D" if score >= 35 else "F"
    return {
        "repo": repo["full_name"],
        "url": repo["html_url"],
        "description": repo.get("description"),
        "language": repo.get("language"),
        "topics": repo.get("topics", []),
        "stars": stars,
        "forks": forks,
        "open_issues_and_prs": open_issues,
        "contributors": contributors,
        "commits_last_90d": commits_90d,
        "last_push_days_ago": int(days_push),
        "latest_release": (release or {}).get("tag_name"),
        "license": license_id,
        "archived": repo.get("archived", False),
        "default_branch": repo.get("default_branch"),
        "clone_url": repo.get("clone_url"),
        "score": score,
        "grade": grade,
        "breakdown": {
            "popularity(stars)/30": round(s_pop, 1), "forks/5": round(s_fork, 1),
            "freshness/20": s_fresh, "commit_activity/10": round(s_activity, 1),
            "contributors/10": round(s_team, 1), "issue_health/5": s_issues,
            "license/8": s_license, "docs_community/7": s_docs, "releases/5": s_release,
        },
        "flags": flags,
    }


# --------------------------------------------------------------------------- search
def search(query: str, kind: str = "repositories", sort: str = "best", limit: int = 10,
           language: str | None = None, min_stars: int | None = None) -> list[dict]:
    q = query
    if language:
        q += f" language:{language}"
    if min_stars and kind == "repositories":
        q += f" stars:>={min_stars}"
    params = {"q": q, "per_page": min(limit, 100)}
    if sort != "best":
        params["sort"] = sort
        params["order"] = "desc"
    if kind == "code" and not _token():
        raise GitHubError("GitHub code search requires a signed-in account. Run the connect step first.")
    data, _ = get(f"/search/{kind}", params)
    items = (data or {}).get("items", [])[:limit]
    out = []
    for it in items:
        if kind == "repositories":
            out.append({"repo": it["full_name"], "url": it["html_url"], "stars": it["stargazers_count"],
                        "language": it.get("language"), "updated": it.get("pushed_at", "")[:10],
                        "archived": it.get("archived"), "license": (it.get("license") or {}).get("spdx_id"),
                        "description": (it.get("description") or "")[:160]})
        elif kind == "code":
            out.append({"repo": it["repository"]["full_name"], "path": it["path"], "url": it["html_url"]})
        else:
            out.append({"title": it["title"], "url": it["html_url"], "state": it["state"],
                        "comments": it.get("comments"), "updated": it.get("updated_at", "")[:10]})
    return out


def _relevant(task: str, r: dict) -> bool:
    """Keep repos whose name/description mention at least half of the task's key words."""
    stop = {"a", "an", "the", "to", "for", "of", "and", "in", "on", "with", "from", "into", "best", "library", "tool"}
    words = [w for w in task.lower().replace("-", " ").split() if w not in stop and len(w) > 1]
    if not words:
        return True
    text = f"{r['repo']} {r.get('description') or ''}".lower().replace("-", " ").replace("_", " ")
    hits = sum(w in text for w in words)
    if hits < max(1, (len(words) + 1) // 2):
        return False
    conv = _conversion(task)
    if conv:  # "X to Y" task: the repo must produce Y, not merely mention it
        src, dst = conv
        compact = text.replace(" ", "")
        produces = any(p in text for p in (f"to {dst}", f"into {dst}", f"→ {dst}", f"> {dst}", f"{dst} generat", f"{dst} export")) \
            or f"{src}2{dst}" in compact or f"{src}to{dst}" in compact
        return produces
    return True


_ALIASES = {"md": "markdown", "markdown": "md", "txt": "text", "text": "txt", "speech": "audio", "img": "image", "image": "img"}


def _conversion(task: str) -> tuple[str, str] | None:
    """Detect 'convert X to Y' style tasks. Returns (x, y) or None."""
    m = re.search(r"([\w+#.]+)\s+(?:to|into|->|→|2)\s+([\w+#.]+)", task.lower())
    if not m or m.group(1) in {"how", "want", "need", "way", "able", "go", "used"}:
        return None
    return m.group(1), m.group(2)


def find_candidates(task: str, language: str | None = None, n: int = 10) -> list[dict]:
    """Collect candidates in GitHub best-match order (not by stars), focused on name/description/topics."""
    variants = [f"{task} in:name,description,topics", task]
    conv = _conversion(task)
    if conv:  # common repo naming styles: md2pdf, markdown-to-pdf
        src, dst = conv
        for s in {src, _ALIASES.get(src, src)}:
            variants += [f"{s}2{dst} in:name,description", f"{s}-to-{dst} in:name,description"]
    seen: dict[str, dict] = {}
    for v in variants:
        try:
            for r in search(v, limit=20, language=language, min_stars=10):
                if not r.get("archived") and _relevant(task, r):
                    seen.setdefault(r["repo"], r)
        except GitHubError as e:
            print(f"warning: {e}", file=sys.stderr)
    return list(seen.values())[:n]


def find(task: str, language: str | None = None, limit: int = 5) -> list[dict]:
    """Search a few query variants, de-duplicate, rate the top candidates, rank by score."""
    candidates = find_candidates(task, language, max(limit * 2, 6))
    rated = []
    for c in candidates:
        try:
            rated.append(rate(c["repo"]))
        except GitHubError as e:
            print(f"warning: could not rate {c['repo']}: {e}", file=sys.stderr)
            if "rate limit" in str(e):
                break
    return sorted(rated, key=lambda r: r["score"], reverse=True)[:limit]


# --------------------------------------------------------------------------- printing
def _print_rating(r: dict) -> None:
    print(f"\n{r['repo']}  -  score {r['score']}/100 (grade {r['grade']})")
    print(f"  {r['url']}")
    if r["description"]:
        print(f"  {r['description']}")
    print(f"  stars {r['stars']:,} | forks {r['forks']:,} | contributors {r['contributors']} | "
          f"commits(90d) {r['commits_last_90d']} | last push {r['last_push_days_ago']}d ago")
    print(f"  license {r['license'] or 'NONE'} | latest release {r['latest_release'] or '-'} | language {r['language']}")
    print("  breakdown: " + ", ".join(f"{k}={v}" for k, v in r["breakdown"].items()))
    for f in r["flags"]:
        print(f"  ! {f}")


def _print_table(rows: list[dict]) -> None:
    print(f"{'#':>2}  {'repository':45} {'score':>6} {'grade':>5} {'stars':>8} {'push(d)':>7}  license")
    for i, r in enumerate(rows, 1):
        print(f"{i:>2}  {r['repo'][:45]:45} {r['score']:>6} {r['grade']:>5} {r['stars']:>8,} "
              f"{r['last_push_days_ago']:>7}  {r['license'] or 'NONE'}")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("whoami")
    s = sub.add_parser("search")
    s.add_argument("query")
    s.add_argument("--type", default="repositories", choices=["repositories", "code", "issues"])
    s.add_argument("--sort", default="best", choices=["best", "stars", "updated", "forks"])
    s.add_argument("--limit", type=int, default=10)
    s.add_argument("--language")
    s.add_argument("--min-stars", type=int)
    s.add_argument("--json", action="store_true")
    r = sub.add_parser("rate")
    r.add_argument("repo")
    r.add_argument("--json", action="store_true")
    c = sub.add_parser("compare")
    c.add_argument("repos", nargs="+")
    c.add_argument("--json", action="store_true")
    f = sub.add_parser("find")
    f.add_argument("task")
    f.add_argument("--language")
    f.add_argument("--limit", type=int, default=5)
    f.add_argument("--json", action="store_true")
    a = p.parse_args()

    try:
        if a.cmd == "whoami":
            if not _token():
                print("Not signed in. Anonymous access: 60 API requests/hour, no code search.")
                return 1
            me, _ = get("/user")
            if not me:
                print("Signed-in check failed.")
                return 1
            lim, _ = get("/rate_limit")
            core = (lim or {}).get("resources", {}).get("core", {})
            name = f" ({me['name']})" if me.get("name") else ""
            print(f"Signed in as {me['login']}{name}. "
                  f"API calls left this hour: {core.get('remaining')}/{core.get('limit')}")
        elif a.cmd == "search":
            res = search(a.query, a.type, a.sort, a.limit, a.language, a.min_stars)
            print(json.dumps(res, indent=2))
        elif a.cmd == "rate":
            res = rate(a.repo)
            print(json.dumps(res, indent=2)) if a.json else _print_rating(res)
        elif a.cmd == "compare":
            rows = []
            for name in a.repos:
                try:
                    rows.append(rate(name))
                except GitHubError as e:
                    print(f"warning: {e}", file=sys.stderr)
            rows.sort(key=lambda x: x["score"], reverse=True)
            if a.json:
                print(json.dumps(rows, indent=2))
            else:
                _print_table(rows)
                for x in rows:
                    _print_rating(x)
        elif a.cmd == "find":
            rows = find(a.task, a.language, a.limit)
            if a.json:
                print(json.dumps(rows, indent=2))
            else:
                _print_table(rows)
                for x in rows:
                    _print_rating(x)
    except GitHubError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
