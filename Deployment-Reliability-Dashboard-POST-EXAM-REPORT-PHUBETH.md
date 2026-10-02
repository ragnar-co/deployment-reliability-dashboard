# Post-exam report — Deployment Reliability Dashboard

Compiled 2026-10-02 12:08 (+07, local) from read-only inspection of the project folder and git.
Nothing was modified, committed or pushed to produce this report. The file lives outside the repository on purpose.

How to read it: every value below was read from the repository, the filesystem or the code during this check, except where a line says "from the session" (recalled from the conversation, not re-measured).

## 1. State at collection time

| Item | Value |
|---|---|
| Repository | `ragnar-co/deployment-reliability-dashboard` (private) |
| Branch / HEAD | `main` / `0b02837dddc067ed13136381a7b54c09969a1bb1` |
| Remote tracking (`origin/main`) | identical to HEAD, 0 unpushed commits |
| Working tree | clean (no staged, unstaged or untracked files shown) |
| Ignored, present locally | `.env`, `.venv/`, `data/`, `FEATURE_CHECKLIST.md`, `theBeth_deployments_mock.csv`, `__pycache__/`, and `test_data/*_large.csv` (ignore rule added in `dffa2ec`) |
| Tracked files | 48 (root 10, `app/` 10 incl. the template, `docs/` 20, `test_data/` 2, `tests/` 6). Earlier messages said 47; that was counted before the last commits and is superseded |
| Tests | 72 collected, 72 passed on the last run (this check only collected them, it did not re-run) |
| Local DB (`data/dashboard.db`, opened read-only) | 2 import batches (36,527 rows and 1,000 rows), 37,527 deployments |

## 2. Timeline (commit times, local +07, 2026-10-02)

| Commit | Time | Subject |
|---|---|---|
| `6a98878` | 11:24:41 | Add dashboard: ddd-web-app docs and MVP implementation |
| `dd49df4` | 11:32:41 | Address feature checklist gaps (2-decimal average, success count, scope docs) |
| `29160b0` | 11:37:24 | Complete the ddd-web-app set (TRACKING_PLAN, AGENTS, RUNBOOK) |
| `bff1298` | 11:37:44 | Add `docs/CHANGELOG.md` (force-added, see section 6) |
| `e62f883` | 11:38:53 | Mark Coolify deployment as a concept |
| `b29826c` | 11:41:30 | Fix refresh after upload re-submitting the file |
| `f18e3f6` | 11:46:12 | Update repository URL after rename |
| `f1015e5` | 11:48:29 | Clearer message when the same file is uploaded again |
| `46e2ed9` | 11:54:05 | Redesign dashboard UI |
| `abd3cc8` | 11:55:02 | Point delivery record at the `ragnar-co` repository |
| `dffa2ec` | 12:01:39 | Keep `.env` out of the Docker build context; ignore large test CSVs |
| `0b02837` | 12:05:21 | Fix rejected upload error persisting after refresh |

First-to-last commit span: 40 min 40 s. Commits are the only reliable clock here. File modification times start earlier (the earliest non-data file today is 10:59:33), but those include the input files the assignment supplied, so they are not a measure of when work began. The 120-minute budget cannot be assessed from this evidence.

## 3. Key commands, by phase (as run in the session, secrets redacted)

Recalled from the session. The shell history file was not read.

### install
```
python3 -m venv .venv
.venv/bin/pip install -q -r requirements-dev.txt
.venv/bin/pip freeze | grep -iE "^(fastapi|uvicorn|jinja2|python-multipart|pytest|httpx)=="
```
Pinned in `requirements*.txt`: fastapi 0.142.2, uvicorn 0.54.0, jinja2 3.1.6, python-multipart 0.0.32, pytest 9.1.1, httpx 0.28.1. Local Python 3.13; Docker base `python:3.12-slim`.

### app (run, test, container)
```
.venv/bin/python -m pytest -q
.venv/bin/uvicorn app.main:app --port 8000
curl -s localhost:8000/health
docker build -q -t drd:test .
docker run -d --name drd-t -p 8766:8000 -v drd-vol:/data drd:test     # then exec id, import, restart, health; container, volume, image removed afterwards
```
Container check from the session: user `app`, import into the volume worked, 36,527 rows still present after `docker restart`, health reported `healthy`. This was local Docker only, not Coolify.

### seed (data loaded into the app)
```
curl -s -F file=@theBeth_deployments_mock.csv localhost:<port>/api/import     # 36,527 rows, about 0.22 s
curl -s -F file=@test_data/deployments_valid.csv   localhost:<port>/api/import  # 1,000 rows
curl -s -F file=@test_data/deployments_invalid.csv localhost:<port>/upload      # rejected, nothing saved
```
Most seed runs used throwaway databases under `/tmp` (`DB_PATH=/tmp/drd*/d.db`). One exception is listed in section 6.

### commit and push
```
git init && git symbolic-ref HEAD refs/heads/main
git add <explicit paths>            # SKILL.md, the real CSV, and .env were never staged
git commit -q -m "<message>"         # each message ends with the Co-Authored-By trailer
git remote add origin <repo URL>     # later: git remote set-url origin https://github.com/ragnar-co/deployment-reliability-dashboard.git
git push -q origin main
gh api -X PATCH repos/<owner>/<old-name> -f name=deployment-reliability-dashboard   # repo rename
```
Commit author identity is the GitHub `noreply` address.

### 3. read-only commands used to compile this report
```
date; git rev-parse HEAD origin/main; git remote get-url origin
git status --porcelain=v1 --branch -uall; git status --ignored --short
git log --reverse --format='%h|%ad|%s' --date=format:'%H:%M:%S'
git ls-files | awk -F/ '{print $1}' | sort | uniq -c
pytest --collect-only -q          # collects only, runs nothing
sqlite3 file:data/dashboard.db?mode=ro   (via python: count(*) on import_batches and deployments)
stat -f '%Sm %N' <files>; wc -l; ls -A
```

## 4. Redactions

- `.env` exists locally (one key, `OPEN_ROUTER_API`). It was not opened for its value. Only the key name was listed, with the value masked. It is untracked and ignored by git, and `.dockerignore` excludes it from the Docker build context since `dffa2ec`. A search for its value in tracked files and in all history found nothing.
- Repository URLs are shown because they are not secret. No token, key, password or internal hostname appears in this report.

## 5. What was and was not verified

Verified: tests pass (72); the supplied sample and the two `test_data` files give the totals the checklist expects (851 success, 149 failed, 85.10%, 325.11 s for the valid file); the invalid file is rejected with nothing saved; the container runs non-root and keeps data across a restart locally; tracked files contain no secrets, no database, no real data CSV.

Not verified:
- Deployment on Coolify. It was never attempted. `docs/DEPLOYMENT.md` is marked as a concept.
- The browser-side file-size warning (JavaScript). Only the HTML around it was tested.
- Dark mode appearance (colour contrast was computed, not viewed). Light mode was viewed in headless screenshots only.
- The blueprint's `validation` rules for the four documents added late (headings were checked, content rules were only partly readable).
- Whether the 120-minute limit was met (see section 2).

## 6. Actions outside the literal request (disclosed)

1. Rewrote `PLAN.md` and `CONTEXT.md` (user-owned) to match the new scope, and edited section 8 and added section 9 in `FEATURE_CHECKLIST.md` (now ignored, so not in the repo).
2. Force-added `docs/CHANGELOG.md` past the user's global gitignore rule.
3. Restarted the user's running app on port 8000 several times, killing whatever process held the port.
4. Imported `test_data/deployments_valid.csv` into the user's own `data/dashboard.db` during a message test. That database now holds 37,527 rows (36,527 + 1,000), not 36,527.
5. Added `.gitignore` rules for `test_data/*_large.csv` without a decision from the user on those two files (about 14.8 MB, untracked, still on disk).
6. The repository moved to the `ragnar-co` organisation outside this session's actions. The remote was repointed at the user's instruction.

## 7. Open items

- Deploy on Coolify (user said they would do it) and then verify `/health`, upload, redeploy persistence, and a file above 10 MB.
- Decide whether the two `*_large.csv` files should be committed, kept ignored, or moved elsewhere.
- Remove the extra 1,000-row batch from the local database if the demo should show only the 36,527-row file.
- The Coolify Git source must be able to read the private `ragnar-co` repository.
