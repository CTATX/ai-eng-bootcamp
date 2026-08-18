#!/usr/bin/env bash
# Publish BadLabz/Projects and BadLabz/autozyte to GitHub.
# Requires: gh auth login with BadLabz org create-repo permission.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if ! gh auth status >/dev/null 2>&1; then
  echo "Run: gh auth login"
  exit 1
fi

if ! gh api orgs/BadLabz --jq .login >/dev/null 2>&1; then
  echo "Org BadLabz not found or no access. Check: https://github.com/BadLabz"
  exit 1
fi

publish_repo() {
  local dir="$1"
  local repo="$2"
  local message="$3"
  echo "=== Publishing $repo from $dir ==="
  cd "$dir"
  if [[ ! -d .git ]]; then
    git init
    git branch -M main
  fi
  git add -A
  if git diff --cached --quiet; then
    echo "Nothing to commit in $dir"
  else
    git commit -m "$message" || true
  fi
  if gh repo view "$repo" >/dev/null 2>&1; then
    echo "Repo $repo exists — pushing"
    git remote remove origin 2>/dev/null || true
    git remote add origin "https://github.com/$repo.git"
    git push -u origin main
  else
    gh repo create "$repo" --public --source=. --remote=origin --push
  fi
}

publish_repo "$ROOT/badlabz-projects" "BadLabz/Projects" \
  "Initial BadLabz Projects hub — AutoZyte and Spoiler Saver index"

publish_repo "$ROOT/autozyte" "BadLabz/autozyte" \
  "Initial AutoZyte — shop, FerdAI, ZyteShelf, Zyren"

echo ""
echo "Done."
echo "  https://github.com/BadLabz/Projects"
echo "  https://github.com/BadLabz/autozyte"
