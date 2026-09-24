"""Sphinx Markdown builder support for documentation aggregation.

When a repository uses ``"structure": "sphinx"`` in repos-config.json, this
module runs ``sphinx-build -M markdown`` to produce plain Markdown output that
can be consumed by VitePress via the normal aggregation pipeline.

Sphinx is invoked via the current Python interpreter (``python -m sphinx``),
so ``sphinx``, ``sphinx-markdown-builder``, and all Sphinx extensions required
by the documented project must be installed in the same Python environment that
runs the aggregator.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, Optional


def build_sphinx_markdown(
    repo_dir: Path,
    docs_path: str,
    output_dir: Path,
    target_map: Optional[Dict[str, str]] = None,
) -> bool:
    """
    Build Sphinx Markdown output from a fetched repository and copy it to
    *output_dir*.

    Steps performed:

    1. Run ``python -m sphinx -M markdown <docs_source> <build_dir>`` using
       the current Python interpreter.
    2. Copy the resulting ``<build_dir>/markdown/`` contents to *output_dir*.
    3. Copy hand-written Markdown files from the raw docs source that carry a
       ``github_target_path`` frontmatter field (e.g. how-to guides).
    4. Inject VitePress frontmatter (``title``, ``description``, and optionally
       ``github_target_path`` from *target_map*) into each generated file.
    5. Strip sphinx-style artifacts that break VitePress compatibility.

    Args:
        repo_dir: Root directory of the cloned/copied repository.
        docs_path: Relative path to the Sphinx docs source within the repo.
        output_dir: Destination directory for the built Markdown files.
        target_map: Optional mapping of generated filename (e.g. ``"cli.md"``)
            to its desired VitePress path (e.g.
            ``"reference/python-gardenlinux-lib-cli.md"``).  When provided,
            the matching files receive a ``github_target_path`` frontmatter
            field so the existing ``copy_targeted_docs`` mechanism places them
            at the correct URL in the docs site.

    Returns:
        ``True`` on success, ``False`` on any failure.
    """
    docs_source = repo_dir / docs_path
    conf_py = docs_source / "conf.py"

    if not conf_py.exists():
        print(
            f"  [sphinx] No conf.py found at {conf_py} — skipping Sphinx build",
            file=sys.stderr,
        )
        return False

    print(f"  [sphinx] Building Markdown documentation from {docs_source}")

    # Step 0: Install the fetched repo so that transitive deps (e.g. podman,
    # semver) required by the locked source are available to Sphinx autodoc.
    # This ensures the installed package always exactly matches the locked
    # source, regardless of what is pinned in requirements.txt.
    print(f"  [sphinx] Installing package from fetched repo: {repo_dir}")
    pip_result = subprocess.run(
        [sys.executable, "-m", "pip", "install", str(repo_dir)],
        capture_output=True,
        text=True,
    )
    if pip_result.stdout:
        for line in pip_result.stdout.splitlines():
            print(f"  [sphinx]   {line}")
    if pip_result.stderr:
        for line in pip_result.stderr.splitlines():
            print(f"  [sphinx]   {line}")
    if pip_result.returncode != 0:
        print(
            f"  [sphinx] pip install failed (exit {pip_result.returncode})",
            file=sys.stderr,
        )
        return False

    with tempfile.TemporaryDirectory() as tmp:
        build_dir = Path(tmp) / "build"
        build_dir.mkdir()

        # Step 1: Run sphinx-build -M markdown via the current Python interpreter.
        # Using sys.executable ensures we run sphinx from the same environment
        # that is running the aggregator, avoiding stale PATH entries.
        #
        # Prepend the repo's src/ directory to PYTHONPATH so sphinx imports
        # the documented project's source code from the fetched repo rather
        # than from any system-installed release version.  This is necessary
        # when the repo's docs reference APIs (e.g. get_parser()) that were
        # added after the last published release.
        print("  [sphinx] Running sphinx-build -M markdown...")
        env = os.environ.copy()
        # Prevent Python 3.13+ argparse from emitting ANSI color codes in
        # help/usage text that sphinxcontrib-autoprogram captures and includes
        # verbatim in the generated Markdown.  NO_COLOR is the standard
        # convention (https://no-color.org/) respected unconditionally by
        # Python 3.13's argparse regardless of TERM or FORCE_COLOR.
        env["NO_COLOR"] = "1"
        src_dir = repo_dir / "src"
        if src_dir.is_dir():
            env["PYTHONPATH"] = str(src_dir) + os.pathsep + env.get("PYTHONPATH", "")
            print(f"  [sphinx] PYTHONPATH prepended with: {src_dir}")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "sphinx",
                "-M",
                "markdown",
                str(docs_source),
                str(build_dir),
            ],
            capture_output=True,
            text=True,
            cwd=str(docs_source),
            env=env,
        )

        if result.stdout:
            for line in result.stdout.splitlines():
                print(f"  [sphinx]   {line}")
        if result.stderr:
            for line in result.stderr.splitlines():
                print(f"  [sphinx]   {line}")

        if result.returncode != 0:
            print(
                f"  [sphinx] sphinx-build failed (exit {result.returncode})",
                file=sys.stderr,
            )
            return False

        # Step 2: Copy built Markdown files to output_dir
        markdown_build = build_dir / "markdown"
        if not markdown_build.exists():
            print(
                f"  [sphinx] Expected output directory not found: {markdown_build}",
                file=sys.stderr,
            )
            return False

        print(f"  [sphinx] Copying Markdown output to {output_dir}")
        output_dir.mkdir(parents=True, exist_ok=True)
        for item in markdown_build.iterdir():
            # Skip Sphinx build artifact directories (_static/, _sources/, etc.)
            # — these contain theme JS/CSS that VitePress does not need and that
            # cause codespell false positives.
            if item.is_dir() and item.name.startswith("_"):
                continue
            target = output_dir / item.name
            if item.is_file():
                shutil.copy2(item, target)
            elif item.is_dir():
                shutil.copytree(item, target, dirs_exist_ok=True)

        # Step 3: Copy hand-written Markdown files from the raw docs source
        # that carry a ``github_target_path`` frontmatter field.  These are
        # manually authored docs pages (how-to guides, overviews, etc.) that
        # live alongside the RST source in the repo.  The sphinx builder only
        # produces output from RST sources, so these files would be silently
        # dropped without this step.
        _copy_manual_markdown(docs_source, output_dir, target_map or {})

        # Step 4: Inject VitePress frontmatter into all generated Markdown files
        _inject_frontmatter_in_dir(output_dir, target_map or {})

        # Step 5: Strip sphinx-style HTML anchor tags and fix heading content
        # that causes VitePress/Vue compatibility issues.
        _strip_sphinx_anchors(output_dir)

        md_count = sum(1 for _ in output_dir.rglob("*.md"))
        print(f"  [sphinx] ✓ Sphinx Markdown build complete ({md_count} .md files)")
        return True


def _copy_manual_markdown(
    docs_source: Path,
    output_dir: Path,
    target_map: Dict[str, str],
) -> None:
    """
    Copy hand-written Markdown files from *docs_source* into the root of
    *output_dir* (flat, no subdirectory), but **only** for files that carry a
    ``github_target_path:`` frontmatter field and whose target path is
    **not** already covered by a sphinx-built file in *target_map*.

    These files are manually authored docs pages (how-to guides, overview
    pages, etc.) that live alongside the RST sources in the repository.  The
    sphinx builder ignores them because they are not RST, so without this step
    they would be silently dropped when the sphinx builder takes over the full
    ``output_dir``.

    Files are copied flat (preserving only the filename, not the source
    subdirectory path) because placement is determined entirely by the
    ``github_target_path`` frontmatter value, which ``copy_targeted_docs``
    reads in Step 1 of the aggregation pipeline.  Preserving subdirectory
    structure would cause the files to be included in the sphinx
    ``target_path`` (e.g. ``projects/python-gardenlinux-lib/how-to/``) with
    relative asset links that cannot be resolved.

    **Exclusion rules:**
    * Files inside ``_build/`` subdirectories are skipped (stale pre-built
      artifacts that may exist in the working tree).
    * Files whose ``github_target_path`` value resolves to the same destination
      as an entry in *target_map* are skipped — the sphinx-built version takes
      precedence over any hand-written placeholder.
    """
    _gtp_re = re.compile(r"^github_target_path\s*:\s*(.+)$", re.MULTILINE)

    # Normalise target_map values to bare paths (strip leading "docs/")
    # so we can compare them against github_target_path values.
    covered_targets = set()
    for dest in target_map.values():
        if dest.startswith("docs/"):
            dest = dest[5:]
        covered_targets.add(dest.strip())

    copied = 0
    for md_file in docs_source.rglob("*.md"):
        # Skip anything inside a _build/ directory
        if "_build" in md_file.parts:
            continue

        try:
            content = md_file.read_text(encoding="utf-8")
        except OSError:
            continue

        gtp_match = _gtp_re.search(content)
        if not gtp_match:
            continue

        # Normalise the target path from the frontmatter (strip quotes and
        # optional leading "docs/" prefix)
        gtp_value = gtp_match.group(1).strip().strip("\"'")
        if gtp_value.startswith("docs/"):
            gtp_value = gtp_value[5:]

        # Skip if the target is already covered by a sphinx-built file
        if gtp_value in covered_targets:
            print(
                f"  [sphinx] Skipping manual markdown (covered by target_map): "
                f"{md_file.relative_to(docs_source)}"
            )
            continue

        # Copy flat into output_dir root — placement is driven by github_target_path
        dest = output_dir / md_file.name
        shutil.copy2(md_file, dest)
        print(
            f"  [sphinx] Carried over manual markdown: {md_file.relative_to(docs_source)}"
        )
        copied += 1

    if copied:
        print(f"  [sphinx] Carried over {copied} manual markdown file(s)")


def _extract_title(content: str) -> Optional[str]:
    """Extract the first H1 heading from Markdown content."""
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return None


def _extract_description(content: str) -> Optional[str]:
    """
    Extract the first plain-text paragraph that immediately follows the H1
    heading in sphinx-markdown-builder output.

    The function skips blank lines, raw HTML lines, and new headings, returning
    the first non-empty plain-text line found after the H1.
    """
    lines = content.splitlines()
    found_h1 = False
    for line in lines:
        stripped = line.strip()
        if not found_h1:
            if stripped.startswith("# "):
                found_h1 = True
            continue
        if not stripped:
            continue
        if stripped.startswith("<") or stripped.startswith("#"):
            continue
        return stripped
    return None


def _inject_frontmatter_in_dir(
    directory: Path,
    target_map: Optional[Dict[str, str]] = None,
) -> None:
    """
    Inject minimal VitePress frontmatter into every Markdown file under
    *directory* that does not already have frontmatter.

    Fields written:
    * ``title`` — from the first ``# Heading`` in the file.
    * ``description`` — from the first paragraph after the H1.
    * ``github_target_path`` — only when the filename matches a *target_map*
      key, so ``copy_targeted_docs`` places the file at the correct VitePress URL.
    """
    target_map = target_map or {}
    for md_file in directory.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
        except OSError:
            continue

        # Skip files that already have frontmatter
        if content.startswith("---\n"):
            continue

        title = _extract_title(content)
        if not title:
            continue

        safe_title = title.replace('"', '\\"')
        fm_lines = [f'title: "{safe_title}"']

        description = _extract_description(content)
        if description:
            safe_desc = description.replace('"', '\\"')
            fm_lines.append(f'description: "{safe_desc}"')

        github_target = target_map.get(md_file.name)
        if github_target:
            if github_target.startswith("docs/"):
                github_target = github_target[5:]
            fm_lines.append(f"github_target_path: {github_target}")
            print(f"  [sphinx] target_map: {md_file.name} → {github_target}")

        frontmatter = "---\n" + "\n".join(fm_lines) + "\n---\n\n"
        md_file.write_text(frontmatter + content, encoding="utf-8")


def _strip_sphinx_anchors(directory: Path) -> None:
    """
    Fix sphinx-markdown-builder output for VitePress compatibility.

    Three issues are addressed:

    1. **Standalone anchor tags** — ``<a id="some.Name"></a>`` lines emitted
       before every heading.  VitePress inlines these into the adjacent heading,
       causing it to use the ``id`` attribute as the permalink anchor instead of
       the slugified heading text.  Multiple symbols sharing a dotted prefix
       then produce duplicate MiniSearch section IDs, crashing the dev server.

    2. **Intra-page links in headings** — ``[TypeName](#qualified.Name)`` links
       in heading lines.  VitePress's ``headingContentRegex`` extracts the
       ``href`` fragment as the section anchor for MiniSearch, so multiple
       method headings referencing the same type produce colliding IDs.

    3. **Angle-bracket metavars in headings** — ``<name>`` placeholders from
       sphinxcontrib-autoprogram (e.g. ``### --arch <arch>``).  Vue's template
       compiler interprets them as unclosed HTML elements and raises
       "Element is missing end tag".

    4. **``_static/`` image references** — Sphinx copies theme assets into
       ``_static/`` relative to the docs build output.  When a generated file
       is placed at a different URL via ``github_target_path`` the relative path
       ``_static/...`` cannot be resolved by Vite/Rollup and breaks the build.
    """
    _anchor_tag_re = re.compile(r"^<a\s+id=\"[^\"]*\"></a>\s*$", re.MULTILINE)
    _heading_link_re = re.compile(r"\[([^\]]+)\]\(#[^)]+\)")
    _heading_metavar_re = re.compile(r"<([a-z][a-z0-9_]*)>")
    # Sphinx copies theme assets into _static/; the relative path breaks when
    # the generated file is placed at a different URL by github_target_path.
    _static_image_re = re.compile(r"!\[[^\]]*\]\(_static/[^)]+\)\n?")

    for md_file in directory.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
        except OSError:
            continue

        # Pass 1: remove standalone anchor tags and _static/ image refs
        new_content = _anchor_tag_re.sub("", content)
        new_content = _static_image_re.sub("", new_content)

        # Pass 2 & 3: heading-line fixups
        lines = new_content.splitlines(keepends=True)
        fixed_lines = []
        for line in lines:
            if re.match(r"^#{1,6}\s", line):
                line = _heading_link_re.sub(r"\1", line)
                line = _heading_metavar_re.sub(r"`<\1>`", line)
            fixed_lines.append(line)
        new_content = "".join(fixed_lines)

        if new_content != content:
            new_content = re.sub(r"\n{3,}", "\n\n", new_content)
            md_file.write_text(new_content, encoding="utf-8")
