# Publish BadLabz repos to GitHub

Run from the **ai-eng-bootcamp** workspace root on a machine where `gh auth login` has **BadLabz org** create-repo permission.

## Prerequisites

1. Org exists: https://github.com/BadLabz
2. `gh auth login` (your account, not the cloud agent cursor bot)

## One command

```bash
chmod +x scripts/publish-to-github.sh
./scripts/publish-to-github.sh
```

Creates and pushes:

- **BadLabz/Projects** — this hub (`badlabz-projects/`)
- **BadLabz/autozyte** — shop platform (`autozyte/`)

## Manual

### Projects hub

```bash
cd badlabz-projects
git init && git branch -M main
git add -A && git commit -m "Initial BadLabz Projects hub"
gh repo create BadLabz/Projects --public --source=. --remote=origin --push
```

### AutoZyte

```bash
cd ../autozyte
git init && git branch -M main
git add -A && git commit -m "Initial AutoZyte"
gh repo create BadLabz/autozyte --public --source=. --remote=origin --push
```

## Access model

| Org | Who | What |
|-----|-----|------|
| **BadLabz** | Product collaborators | AutoZyte, Spoiler Saver, FerdAI work |
| **CTATX** | Training / personal bootcamp | ai-eng-bootcamp, syllabus — separate access |

Cloud agents need the **Cursor GitHub App** installed on **BadLabz** with read/write on each repo you want agents to push to.
