#!/usr/bin/env bash
# Create a new GitHub repository for this project and push it.
#
# Usage: scripts/push_to_github.sh [repo-name] [private|public]
# Needs the GitHub CLI (https://cli.github.com) and a logged-in account.
set -euo pipefail

cd "$(dirname "$0")/.."

REPO_NAME="${1:-optimitylogics-scraper}"
VISIBILITY="${2:-private}"
DESCRIPTION="Polite crawler and data extractor for optimitylogics.com with JSON/CSV/SQLite export and an SEO audit report"

if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI (gh) not found. Install it from https://cli.github.com and re-run." >&2
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "Not logged in to GitHub; starting 'gh auth login'..."
  gh auth login
fi

[ -d .git ] || git init -b main

git add -A
if ! git diff --cached --quiet; then
  git commit -m "Initial commit: optimitylogics.com scraper"
fi

if git remote get-url origin >/dev/null 2>&1; then
  echo "Remote 'origin' already exists; pushing to it."
  git push -u origin HEAD
else
  gh repo create "$REPO_NAME" "--$VISIBILITY" --source=. --remote=origin --push --description "$DESCRIPTION"
fi

echo "Done: $(gh repo view --json url -q .url)"
