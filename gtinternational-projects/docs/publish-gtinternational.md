# Publish GTInternational repos to GitHub

Run from the **ai-eng-bootcamp** workspace root on a machine where `gh auth login` has **GTInternational org admin** access.

## Prerequisites

1. Create GitHub org **GTInternational** (if it does not exist):  
   https://github.com/organizations/plan
2. Install GitHub CLI: `gh auth login`

## One command

```bash
chmod +x scripts/publish-to-github.sh
./scripts/publish-to-github.sh
```

## Manual steps

### 1. Projects hub

```bash
cd gtinternational-projects
git init && git branch -M main
git add -A && git commit -m "Initial GTInternational Projects hub"
gh repo create GTInternational/Projects --public --source=. --remote=origin --push
```

### 2. AutoZyte

```bash
cd ../autozyte
git init && git branch -M main
git add -A && git commit -m "Initial AutoZyte — shop, FerdAI, ZyteShelf, Zyren"
gh repo create GTInternational/autozyte --public --source=. --remote=origin --push
```

### 3. Verify

- https://github.com/GTInternational/Projects
- https://github.com/GTInternational/projects/autozyte (path in repo)
- https://github.com/GTInternational/autozyte

## Cloud agent limitation

The Cursor cloud agent token cannot create orgs or repositories. This folder + script is the handoff for CT to push with personal/org credentials.
