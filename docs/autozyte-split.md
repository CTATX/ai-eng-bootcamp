# AutoZyte split — publish to BadLabz

The full **AutoZyte** product tree lives in [`autozyte/`](../autozyte/). The **BadLabz Projects** hub lives in [`badlabz-projects/`](../badlabz-projects/).

## Publish to GitHub

Org: https://github.com/BadLabz (product work — separate from CTATX training)

From **ai-eng-bootcamp** root, with `gh auth login` as a BadLabz org owner:

```bash
./scripts/publish-to-github.sh
```

Creates and pushes **BadLabz/Projects** and **BadLabz/autozyte**.

Manual steps: [badlabz-projects/docs/publish-badlabz.md](../badlabz-projects/docs/publish-badlabz.md)

## Run locally

```bash
cd autozyte
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
./start.sh
```

## ShopMonkey API key

`autozyte/.env` → `SHOPMONKEY_API_KEY=...` (never commit)

## Access model

| Org | Use |
|-----|-----|
| **BadLabz** | AutoZyte, Spoiler Saver, collaborators |
| **CTATX** | ai-eng-bootcamp training — your personal/syllabus access |
