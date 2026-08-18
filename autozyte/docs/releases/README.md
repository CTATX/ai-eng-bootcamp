# Release manifests

Each production publish to **[BadLabz/autozyte](https://github.com/BadLabz/autozyte)** should have:

1. **`VERSION`** bumped at repo root (semver).
2. **`CHANGELOG.md`** entry under `[Unreleased]` → new version section.
3. **`docs/releases/manifest-vX.Y.Z.md`** — audit trail: summary, problem, files, verification, upgrade steps.
4. **Git tag** `vX.Y.Z` on BadLabz `main` (created by publish script).

## Publish flow

From **ai-eng-bootcamp** root, on a machine with `gh auth login` and **BadLabz org** access:

```bash
./scripts/publish-to-github.sh
```

The script refuses to publish if the manifest for the current `VERSION` is missing.

## Index

| Version | Date | Manifest |
|---------|------|----------|
| 0.2.0 | 2026-08-18 | [manifest-v0.2.0.md](manifest-v0.2.0.md) |
| 0.1.0 | 2026-08-18 | [manifest-v0.1.0.md](manifest-v0.1.0.md) |

## Source of truth

| Repo | Role |
|------|------|
| **CTATX/ai-eng-bootcamp** | Staging / bootcamp — `autozyte/` folder edited here first |
| **BadLabz/autozyte** | Production — what GT International runs (`git clone`) |

Training stays in CTATX; product ships from BadLabz.
