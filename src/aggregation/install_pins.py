"""Keep python-gardenlinux-lib install pins in sync with repos-config.json.

``repos-config.json`` is the single source of truth for the commit that the
aggregation pipeline fetches and Sphinx-builds. The environments that run the
aggregation must install the *same* commit so Sphinx autodoc can import that
source's transitive dependencies (e.g. ``oci`` -> ``podman``,
``distro_version`` -> ``semver``) and generate the CLI/API reference pages.
Installing an older release tag drops those deps and breaks the
``python-gardenlinux-lib-cli`` reference during the VitePress build.

This module rewrites the ``pip install git+.../python-gardenlinux-lib.git@<ref>``
pin in every file that installs the library, using the commit locked in
``repos-config.json``. It is called from ``aggregate.py`` after the lock file is
regenerated (``--update-locks``) so the install pins never drift from the lock.
"""

import re
from pathlib import Path
from typing import List

REPO_NAME = "python-gardenlinux-lib"

# Files whose python-gardenlinux-lib install pin must match repos-config.json.
# Paths are relative to the project root.
INSTALL_PIN_FILES = (
    "requirements.txt",
    "Makefile",
    ".github/workflows/docs-checks.yml",
    ".github/workflows/tests.yml",
)

# Matches the git ref (tag or commit) after the python-gardenlinux-lib URL.
_INSTALL_RE = re.compile(
    r"(git\+https://github\.com/gardenlinux/python-gardenlinux-lib\.git@)[^\s\"']+"
)


def sync_install_pins(
    project_root: Path,
    commit: str,
    files: List[str] | None = None,
) -> bool:
    """Rewrite python-gardenlinux-lib install pins to *commit*.

    Args:
        project_root: Repository root containing the install files.
        commit: Commit hash locked in repos-config.json.
        files: Optional override of the relative file paths to update
            (defaults to :data:`INSTALL_PIN_FILES`).

    Returns:
        ``True`` if any file was modified, ``False`` otherwise.
    """
    targets = files if files is not None else INSTALL_PIN_FILES

    print(f"Syncing {REPO_NAME} install pins to {commit}")
    changed = False

    for rel in targets:
        path = project_root / rel
        if not path.exists():
            print(f"  Skipped (not found): {rel}")
            continue

        original = path.read_text(encoding="utf-8")
        updated, count = _INSTALL_RE.subn(rf"\g<1>{commit}", original)

        if count == 0:
            print(f"  Skipped (no install pin): {rel}")
            continue
        if updated == original:
            print(f"  Already up to date: {rel}")
            continue

        path.write_text(updated, encoding="utf-8")
        print(f"  Updated {count} pin(s): {rel}")
        changed = True

    if not changed:
        print("No install pins needed updating.")
    return changed
