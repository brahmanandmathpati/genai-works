"""Update your copy of the course repository safely, even if you edited or ran the notebooks.

    uv run python tools/update_course.py            # back up, reset course files, git pull
    uv run python tools/update_course.py --dry-run  # only show what would happen

What it does, in order:
  1. Finds every course file you changed (edited, or a notebook you ran and saved, staged or not).
  2. Copies each one to  <your home>/genai_course_backups/<date-time>/<same path>  so nothing is lost.
  3. Puts those course files back to the last version you pulled (your .env and your own new files are never touched).
  4. Runs  git pull --ff-only.  If one of your own untracked files is in the way of a new course file, it is moved to
     the backup folder and the pull is tried once more.
Your work repository (genai-course-work) is a different folder and is never touched."""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def git(*args, cwd: Path, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=check)


def repo_root() -> Path:
    try:
        out = git("rev-parse", "--show-toplevel", cwd=Path.cwd()).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        sys.exit("Run this inside the course folder (genai-agents-course). Example:  cd ~\\Documents\\genai-agents-course")
    root = Path(out)
    py = root / "pyproject.toml"
    if not py.exists() or 'name = "genai-agents-course"' not in py.read_text(encoding="utf-8"):
        sys.exit(f"{root} is not the course repository. Run this inside genai-agents-course, not your work repository.")
    return root


def changed_files(root: Path) -> list[str]:
    """Tracked files that differ from the last commit (staged or not), plus tracked files you deleted."""
    out = git("diff", "HEAD", "--name-only", cwd=root).stdout
    return [line.strip() for line in out.splitlines() if line.strip()]


def backup(root: Path, files: list[str], dest: Path) -> list[str]:
    saved = []
    for rel in files:
        src = root / rel
        if src.is_file():
            target = dest / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, target)
            saved.append(rel)
    return saved


_BLOCKING = re.compile(r"untracked working tree files would be overwritten by merge:\n(.*?)\n(?:Please|Aborting)", re.S)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="show what would happen, change nothing")
    ap.add_argument("--backup-root", default=str(Path.home() / "genai_course_backups"), help=argparse.SUPPRESS)
    args = ap.parse_args(argv)

    root = repo_root()
    files = changed_files(root)
    dest = Path(args.backup_root) / datetime.now().strftime("%Y%m%d-%H%M%S")
    print(f"course folder : {root}")
    print(f"files you changed: {len(files)}")
    for f in files:
        print("   ", f)
    if args.dry_run:
        print(f"\n[dry run] would back them up to {dest}, reset them, and run: git pull --ff-only")
        return 0

    if files:
        saved = backup(root, files, dest)
        print(f"\nbacked up {len(saved)} file(s) to {dest}")
        git("reset", "-q", "--", *files, cwd=root)
        git("checkout", "--", *files, cwd=root, check=False)
        still = changed_files(root)
        if still:
            print("could not reset:", still)
            return 1
        print("course files reset to the last version you pulled")

    for attempt in (1, 2):
        r = git("pull", "--ff-only", cwd=root, check=False)
        if r.returncode == 0:
            print("\n" + (r.stdout.strip() or "pulled"))
            print("\nNext:  uv sync   then   uv run pytest -q")
            if files:
                print(f"Your old versions are in: {dest}  (open them side by side if you want your answers back)")
            return 0
        m = _BLOCKING.search(r.stderr)
        if attempt == 1 and m:
            blockers = [line.strip() for line in m.group(1).splitlines() if line.strip()]
            for rel in blockers:
                target = dest / "untracked" / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(root / rel), str(target))
            print(f"moved {len(blockers)} untracked file(s) that were in the way to {dest / 'untracked'}; trying again")
            continue
        print("\ngit pull did not succeed:\n" + r.stderr.strip())
        print("Nothing of yours is lost: your changed files are in", dest if files else "(none changed)")
        print("Ask for help with the message above (common causes: no internet, or you made commits in this folder).")
        return 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
