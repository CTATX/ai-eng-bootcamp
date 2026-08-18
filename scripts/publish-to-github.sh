#!/usr/bin/env bash
# Publish BadLabz/Projects and BadLabz/autozyte to GitHub.
# Requires: gh auth login with BadLabz org create-repo permission.
#
# Release gate: autozyte/VERSION must match docs/releases/manifest-vX.Y.Z.md
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AUTOZYTE="$ROOT/autozyte"
VERSION="$(tr -d '[:space:]' < "$AUTOZYTE/VERSION")"
MANIFEST="$AUTOZYTE/docs/releases/manifest-v${VERSION}.md"

if ! gh auth status >/dev/null 2>&1; then
  echo "Run: gh auth login"
  exit 1
fi

if ! gh api orgs/BadLabz --jq .login >/dev/null 2>&1; then
  echo "Org BadLabz not found or no access. Check: https://github.com/BadLabz"
  echo "Publish must run on your Mac (or any machine) logged in as a BadLabz org owner."
  exit 1
fi

if [[ ! -f "$MANIFEST" ]]; then
  echo "Missing release manifest for v${VERSION}:"
  echo "  $MANIFEST"
  echo "Add manifest + CHANGELOG entry before publishing."
  exit 1
fi

echo "Publishing AutoZyte v${VERSION}"
echo "  Manifest: docs/releases/manifest-v${VERSION}.md"

publish_repo() {
  local dir="$1"
  local repo="$2"
  local message="$3"
  local tag="${4:-}"
  echo ""
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
    git commit -m "$message"
  fi
  if gh repo view "$repo" >/dev/null 2>&1; then
    echo "Repo $repo exists — pushing main"
    git remote remove origin 2>/dev/null || true
    git remote add origin "https://github.com/$repo.git"
    git push -u origin main
  else
    gh repo create "$repo" --public --source=. --remote=origin --push
  fi
  if [[ -n "$tag" ]] && git rev-parse "$tag" >/dev/null 2>&1; then
    echo "Tag $tag already exists locally"
  elif [[ -n "$tag" ]]; then
    git tag -a "$tag" -m "AutoZyte ${tag#v} — see docs/releases/manifest-${tag}.md"
    git push origin "$tag"
  fi
}

publish_repo "$ROOT/badlabz-projects" "BadLabz/Projects" \
  "Projects hub — AutoZyte v${VERSION} release index"

publish_repo "$AUTOZYTE" "BadLabz/autozyte" \
  "Release v${VERSION}: ShopMonkey ingest + ticket pull (see CHANGELOG.md)" \
  "v${VERSION}"

echo ""
echo "Done."
echo "  https://github.com/BadLabz/Projects"
echo "  https://github.com/BadLabz/autozyte"
echo "  Tag: v${VERSION}"
echo "  Manifest: autozyte/docs/releases/manifest-v${VERSION}.md"
