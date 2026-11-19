# Repository scoring rubric (scout_tool.py)

Total 100 points. Log scales stop huge repos from dominating.

| Signal | Max | How it's scored |
|---|---|---|
| Stars (popularity) | 30 | `30 * log10(stars+1) / log10(50,000)` - 50k stars = full marks |
| Forks | 5 | `5 * log10(forks+1) / log10(5,000)` |
| Freshness (last push) | 20 | ≤30d 20 · ≤90d 16 · ≤180d 11 · ≤1y 6 · ≤2y 2 · older 0 |
| Commit activity (last 90 days) | 10 | `10 * log10(commits+1) / 2` - 100 commits = full |
| Contributors | 10 | `10 * log10(n+1) / 2` - 100 contributors = full |
| Issue health | 5 | open issues+PRs ÷ stars: <2% 5 · <5% 3.5 · <15% 2 · else 0.5 |
| License | 8 | Any recognised SPDX license = 8, none = 0 |
| Docs & community | 7 | README 3 + 1 each for README/CONTRIBUTING/CODE_OF_CONDUCT/issue template/PR template (cap 7) |
| Releases | 5 | Has a published release = 5 |

**Penalties / flags**
- Archived: total × 0.4
- Fork of another repo: flag - suggest the upstream
- No license, no push in >1 year, single maintainer with >500 stars, <60 days old with >2k stars (possible hype / star farming): flagged

**Caveats to mention when relevant**
- Mature "finished" libraries (e.g. small utilities) can be healthy with few commits.
- Stars can be bought or inflated by social media; cross-check with contributors and dependents.
- Monorepos and mirrors can show misleading numbers.
