# AutoZyte split — publish to GitHub

The full **AutoZyte** product tree lives in this folder. It was extracted from `ai-eng-bootcamp` on 2026-08-18.

## Publish to GTInternational/autozyte

When the org repo exists:

```bash
cd autozyte
git init
git branch -M main
git add -A
git commit -m "Initial AutoZyte import from ai-eng-bootcamp split"
git remote add origin git@github.com:GTInternational/autozyte.git
git push -u origin main
```

Then remove `autozyte/` from this bootcamp repo (or keep as submodule link only).

## Run locally (from this folder)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./start.sh
```

Index entry: `GTInternational/Projects/projects/autozyte`
