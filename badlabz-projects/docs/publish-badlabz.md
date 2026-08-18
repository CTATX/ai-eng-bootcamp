# Publish BadLabz repos to GitHub

Run from the **ai-eng-bootcamp** workspace root on a machine where `gh auth login` has **BadLabz org** create-repo permission.

## Prerequisites

1. Org exists: https://github.com/BadLabz
2. `gh auth login` (your account — **not** the cloud agent cursor bot)
3. Release artifacts for the version in `autozyte/VERSION`:
   - `autozyte/CHANGELOG.md` entry
   - `autozyte/docs/releases/manifest-vX.Y.Z.md`

## One command

```bash
chmod +x scripts/publish-to-github.sh
./scripts/publish-to-github.sh
```

Creates or updates and pushes:

- **BadLabz/Projects** — hub (`badlabz-projects/`)
- **BadLabz/autozyte** — shop platform (`autozyte/`) with git tag `vX.Y.Z`

The script **blocks** publish if the manifest for `VERSION` is missing.

## After publish (Mac shop clone)

```bash
cd ~/autozyte
git pull origin main
git tag -l 'v*'    # confirm tag, e.g. v0.2.0
cat VERSION
cat docs/releases/manifest-v0.2.0.md
```

## Release checklist (best practice)

| Step | Done when |
|------|-----------|
| Bump `autozyte/VERSION` | Semver reflects user-visible change |
| Update `CHANGELOG.md` | Added section for version |
| Write `docs/releases/manifest-vX.Y.Z.md` | Summary, verification, upgrade steps |
| Run tests | `cd autozyte && python -m unittest discover -s tests` |
| Publish | `./scripts/publish-to-github.sh` from Mac |
| Verify on GitHub | Tag + manifest visible on BadLabz/autozyte |

## Access model

| Org | Who | What |
|-----|-----|------|
| **BadLabz** | Product collaborators | AutoZyte, Spoiler Saver, FerdAI work |
| **CTATX** | Training / personal bootcamp | ai-eng-bootcamp — separate access |

Cloud agents edit **CTATX/ai-eng-bootcamp**; **you** publish to BadLabz with your `gh` login.

Optional: create a [GitHub Release](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository) from tag `vX.Y.Z` and paste the manifest summary in release notes.
