# Changelog

## 1.1.0 - 2026-11-19
- Meets Anthropic directory rules for unverified publishers: removed the command hook and its
  script, and removed the `network` field.
- GitHub token is now an optional plugin setting (stored in secure storage) instead of an
  environment variable. GitHub CLI sign-in still works for the helper script.
- Added displayName, documentation and support links for the directory listing.

## 1.0.0 - 2026-11-19
- `find` ranks candidates by GitHub relevance (not stars), drops archived and off-topic repos, and understands "X to Y" conversion direction (also searches md2pdf-style names).
- Renamed plugin to scout-repos (skills: account-connect, repo-search, repo-rating, repo-install, find-best-code).
- First public release: connect, search, rate (0-100, A-F), install, find-best-code.
- Install guard: nothing is cloned or installed from GitHub without the user's pick and approval.
- MIT license, privacy policy, marketplace file.

## 0.2.0
- Search shows numbered options; installs need the user's explicit choice.
- Safety hook pauses GitHub clone/install commands for approval.

## 0.1.0
- Initial build.
