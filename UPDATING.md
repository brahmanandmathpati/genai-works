# Updating your copy of the course repository

The notebooks for Sessions 9a to 16 have been rewritten with much longer explanations: every notebook now starts with **Part A** (why the topic matters, the words you need, how the session is built), every section follows the same six steps, and each ends with **Part C** (summary, interview questions, troubleshooting). Session 9a also has a brand-new notebook: `module01/s09a_first_call.ipynb`.

The code and the checkpoint tests did not change in any way that affects your submitted work. **Your work repository (`genai-course-work`) is a different folder and is not touched by anything on this page.**

## Why `git pull` may refuse

If you ran a notebook and saved it, Git sees the notebook as *changed by you* (your answers and outputs are inside the file). When the course version of the same notebook changes, `git pull` stops with:

```
error: Your local changes to the following files would be overwritten by merge:
        module01/s09_tokens.ipynb
Please commit your changes or stash them before you merge.
```

Nothing is broken. You only need to put your copy somewhere safe first.

## This time: four steps (Windows, PowerShell, in VS Code's terminal)

```powershell
cd ~\Documents\genai-agents-course

# 1. Back up both module folders (your answers and outputs are kept here)
New-Item -ItemType Directory -Force "$HOME\genai_course_backups\before-update" | Out-Null
Copy-Item -Recurse -Force module01, module02 "$HOME\genai_course_backups\before-update"

# 2. Put the course files back to the last version you pulled (your .env is NOT affected: it is git-ignored)
git stash push -m "my notebook edits before the update"

# 3. Get the new version
git pull
uv sync

# 4. Check
uv run pytest tests/test_s09a.py -q
```

**What you should see:** `git pull` lists the updated notebooks, and the last command says `6 passed`. Then open any notebook, e.g. `uv run jupyter lab module02/s16_structured.ipynb`, and start with Part A.

Mac/Linux: step 1 is `mkdir -p ~/genai_course_backups/before-update && cp -R module01 module02 ~/genai_course_backups/before-update/`. Steps 2–4 are the same.

## From now on: one command

This update adds a small tool that does the same steps for you, with a time-stamped backup each time:

```powershell
cd ~\Documents\genai-agents-course
uv run python tools/update_course.py --dry-run    # shows what it would do, changes nothing
uv run python tools/update_course.py              # back up, reset course files, git pull
uv sync
```

It copies every course file you changed to `genai_course_backups\<date-time>\` in your home folder, puts those files back to the last version you pulled, and runs `git pull`. It never touches `.env` or files you created yourself (if one of your own files is in the way of a new course file, it is moved into the backup folder first, and the tool tells you).

## Getting your old answers back

Your old notebooks are in `genai_course_backups\before-update\module01` and `...\module02` (or the time-stamped folder the tool printed). Open the old and the new notebook side by side in VS Code and copy your answers across (for example `my_guess = ...`, the `OVERRIDES` and `MEASURED` values in Session 10, your reflections).

Re-running is cheap: Sessions 15 and 16 remember every model answer on disk (`~/.genai_course/`), so re-running an unchanged cell costs no tokens. Earlier sessions call the model again, so re-run only the cells you need.

## If something goes wrong

| You see | It means | Do this |
|---|---|---|
| `Your local changes ... would be overwritten` | a notebook you saved still differs from the course version | do steps 1–2 again, then `git pull` |
| `untracked working tree files would be overwritten` | you created a file with the same name as a new course file (for example `s09a_first_call.ipynb`) | move or rename your file, then `git pull` |
| `Not possible to fast-forward` / `divergent branches` | you made commits inside the course folder | copy your files out (step 1), then `git fetch` and `git reset --hard origin/main` (this discards your commits in the course folder only) |
| `No stash entries found` when you look later | `git stash` found nothing to save | fine: you had no changes |
| `uv run pytest ...` says `skipped` | the live test needs your key in `.env` | a skip is not a pass: check `.env`, see Session 2 |

`git stash list` shows what step 2 saved. You do not need it if you made the backup in step 1; `git stash drop` removes it when you are sure.
