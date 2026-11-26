#!/usr/bin/env python3
"""gldq - Garden Linux Docs Quality Tool.

Checks documentation for structural quality markers documented in
docs/contributing/documentation/writing_good_docs.md.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterator, Sequence

import yaml

__version__ = "0.1.0"

ERROR = "error"
WARNING = "warning"
NO_REPO_GROUP = "(no repo)"

SKIP_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    ".vitepress",
    "__pycache__",
    "_build",
    "dist",
    "node_modules",
    "public",
}
TOP_LEVEL_SECTIONS = {"tutorials", "how-to", "explanation", "reference", "contributing"}
GENERIC_LINK_TEXTS = {
    "",
    "here",
    "click here",
    "this link",
    "read more",
    "learn more",
    "see here",
}

HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.*)$")
FENCE_OPEN_RE = re.compile(r"^\s*(`{3,}|~{3,})(.*)$")
FENCE_CLOSE_RE = re.compile(r"^\s*(`{3,}|~{3,})[ \t]*$")
MD_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]*)\)")
MD_LINK_RE = re.compile(r"(?<!!)\[([^\]]*)\]\(([^)]*)\)")
HTML_IMG_RE = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
ALT_ATTR_RE = re.compile(
    r"(?<![\w-])alt\s*=\s*(?:\"([^\"]*)\"|'([^']*)'|([^\s>]+))",
    re.IGNORECASE,
)
EMOJI_RE = re.compile("[\U0001f000-\U0001faff\u2300-\u23ff\u2600-\u27bf\u2b00-\u2bff]")
SUPPRESSION_RE = re.compile(
    r"<!--\s*gldq:\s*(disable-file|disable-next-line|disable)\s+([^>]*?)-->",
    re.IGNORECASE,
)
DEFAULT_EXCLUDE_FILE = Path(".gldq-exclude.yml")

VITEPRESS_CALLOUT_TYPES = {"info", "tip", "warning", "danger", "details"}
CALLOUT_OPEN_RE = re.compile(r"^\s*(:{3,})\s*([A-Za-z][A-Za-z0-9_-]*)\b(.*)$")
CALLOUT_CLOSE_RE = re.compile(r"^\s*(:{3,})\s*$")
GITHUB_CALLOUT_RE = re.compile(
    r"^\s*>\s*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*$", re.IGNORECASE
)


@dataclass(frozen=True)
class RuleInfo:
    """Metadata for a single lint rule."""

    rule_id: str
    severity: str
    description: str


RULES: dict[str, RuleInfo] = {
    "FM-YAML": RuleInfo("FM-YAML", ERROR, "Front matter must be valid YAML"),
    "FM-TITLE": RuleInfo(
        "FM-TITLE", WARNING, "Front matter must include a non-empty title"
    ),
    "FM-DESC": RuleInfo(
        "FM-DESC", WARNING, "Front matter must include a non-empty description"
    ),
    "FM-ORDER": RuleInfo(
        "FM-ORDER", WARNING, "Front matter order must be an integer when present"
    ),
    "FM-REPO": RuleInfo(
        "FM-REPO",
        ERROR,
        "Front matter must include github_org and github_repo",
    ),
    "FM-RELATED": RuleInfo(
        "FM-RELATED", ERROR, "related_topics must be a list of existing documents"
    ),
    "H1-ONE": RuleInfo(
        "H1-ONE", WARNING, "Document must have exactly one level-1 heading"
    ),
    "H1-EMPTY": RuleInfo("H1-EMPTY", ERROR, "Headings must not be empty"),
    "HEAD-SKIP": RuleInfo("HEAD-SKIP", WARNING, "Heading levels must not be skipped"),
    "CODE-LANG": RuleInfo(
        "CODE-LANG", WARNING, "Fenced code blocks must declare a language"
    ),
    "CODE-BALANCE": RuleInfo(
        "CODE-BALANCE", ERROR, "Fenced code blocks must be closed"
    ),
    "IMG-ALT": RuleInfo("IMG-ALT", ERROR, "Images must have non-empty alt text"),
    "LINK-TEXT": RuleInfo("LINK-TEXT", ERROR, "Links must use descriptive link text"),
    "EMOJI": RuleInfo("EMOJI", WARNING, "Emoji are not allowed outside code fences"),
    "SECTION-INDEX": RuleInfo(
        "SECTION-INDEX",
        ERROR,
        "Section index pages must include <SectionIndex />",
    ),
    "RELATED-TOPICS-END": RuleInfo(
        "RELATED-TOPICS-END",
        ERROR,
        "<RelatedTopics /> must be the last content block",
    ),
    "RELATED-TOPICS-FM": RuleInfo(
        "RELATED-TOPICS-FM",
        ERROR,
        "<RelatedTopics /> requires related_topics in front matter",
    ),
    "RELATED-TOPICS-PRESENT": RuleInfo(
        "RELATED-TOPICS-PRESENT",
        WARNING,
        "Non-index pages should include <RelatedTopics />",
    ),
    "CALLOUT-INVALID-TYPE": RuleInfo(
        "CALLOUT-INVALID-TYPE",
        ERROR,
        "Invalid VitePress container type; use info, tip, warning, danger, or details",
    ),
    "CALLOUT-GITHUB-STYLE": RuleInfo(
        "CALLOUT-GITHUB-STYLE",
        ERROR,
        "GitHub-style callouts are not supported; use VitePress ::: syntax",
    ),
    "CALLOUT-UNCLOSED": RuleInfo(
        "CALLOUT-UNCLOSED",
        ERROR,
        "VitePress container is not closed with :::",
    ),
}

CHECKS: list[Callable[["Document"], Iterator["Finding"]]] = []


@dataclass(frozen=True)
class Finding:
    """A single lint finding."""

    rule_id: str
    severity: str
    path: Path
    line: int | None
    column: int | None
    message: str
    group: str = "(no repo)"

    @property
    def sort_key(self) -> tuple[str, int, int, str]:
        return (
            str(self.path),
            self.line if self.line is not None else 0,
            self.column if self.column is not None else 0,
            self.rule_id,
        )


@dataclass
class Suppressions:
    """Inline suppression directives for one document."""

    file_rules: set[str] = field(default_factory=set)
    from_line: list[tuple[int, set[str]]] = field(default_factory=list)
    next_line: dict[int, set[str]] = field(default_factory=dict)

    def suppresses(self, rule_id: str, line: int | None) -> bool:
        """Return whether a finding is suppressed."""
        if rule_id in self.file_rules or "*" in self.file_rules:
            return True
        if line is None:
            return False
        for start, rules in self.from_line:
            if line >= start and (rule_id in rules or "*" in rules):
                return True
        rules = self.next_line.get(line, set())
        return rule_id in rules or "*" in rules


@dataclass(frozen=True)
class ExclusionRule:
    """A rule and path pattern pair from an exclude file."""

    rule_patterns: tuple[str, ...]
    path_patterns: tuple[str, ...]
    entry: int


@dataclass
class ExcludeConfig:
    """Rule-aware exclusions loaded from a YAML file."""

    rules: list[ExclusionRule] = field(default_factory=list)
    path: Path | None = None

    def matches(self, rule_id: str, path: Path, root: Path) -> bool:
        """Return whether a finding matches any exclusion rule."""
        rule_id = rule_id.upper()
        try:
            relative = path.relative_to(root).as_posix()
        except ValueError:
            relative = path.as_posix()
        root_relative = f"{root.name}/{relative}" if root.name else relative
        full = path.as_posix()
        candidates = (relative, root_relative, full)

        for exclusion in self.rules:
            if not any(
                fnmatch.fnmatchcase(rule_id, pattern.upper())
                for pattern in exclusion.rule_patterns
            ):
                continue
            if any(
                _path_matches(candidate, pattern)
                for pattern in exclusion.path_patterns
                for candidate in candidates
            ):
                return True
        return False


@dataclass
class Fence:
    """A fenced code block opening."""

    line: int
    info: str
    closed: bool = False


@dataclass
class Heading:
    """An ATX heading."""

    line: int
    level: int
    text: str


@dataclass
class Document:
    """A parsed markdown document."""

    path: Path
    root: Path
    relative: Path
    lines: list[str]
    frontmatter: dict | None
    frontmatter_error: str | None
    has_frontmatter: bool
    body_start: int
    no_fence_lines: list[str]
    prose_lines: list[str]
    headings: list[Heading]
    fences: list[Fence]
    suppressions: Suppressions

    @property
    def is_home(self) -> bool:
        return bool(self.frontmatter and self.frontmatter.get("layout") == "home")

    @property
    def is_index(self) -> bool:
        return self.path.name == "index.md"

    @property
    def is_excluded(self) -> bool:
        return bool(self.frontmatter and self.frontmatter.get("exclude") is True)

    @property
    def no_fence_text(self) -> str:
        return "\n".join(self.no_fence_lines)


def _first_line(text: str) -> str:
    return text.splitlines()[0] if text.splitlines() else str(text)

def _parse_frontmatter(
    lines: Sequence[str],
) -> tuple[dict | None, str | None, bool, int]:
    """Parse front matter and return (data, error, has_frontmatter, body_start)."""
    if not lines or lines[0].strip() != "---":
        return None, None, False, 0

    end: int | None = None
    for index in range(1, len(lines)):
        if lines[index].strip() in ("---", "..."):  # Allow "..." as an alternative closing delimiter for front matter.
            end = index
            break

    if end is None:
        return None, "Missing closing front matter delimiter", True, 0

    try:
        data = yaml.safe_load("\n".join(lines[1:end]))
    except yaml.YAMLError as exc:
        return None, _first_line(str(exc)), True, end + 1

    if data is None:
        data = {}
    if not isinstance(data, dict):
        return None, "Front matter must be a YAML mapping", True, end + 1
    return data, None, True, end + 1

def _mask_html_comments(lines: Sequence[str]) -> list[str]:
    """Replace HTML comment content with spaces while preserving lines."""
    masked: list[str] = []
    in_comment = False

    for line in lines:
        chars = list(line)
        index = 0
        while index < len(line):
            if in_comment:
                end = line.find("-->", index)
                if end == -1:
                    for position in range(index, len(line)):
                        chars[position] = " "
                    index = len(line)
                else:
                    for position in range(index, end + 3):
                        chars[position] = " "
                    index = end + 3
                    in_comment = False
            else:
                start = line.find("<!--", index)
                if start == -1:
                    break
                end = line.find("-->", start + 4)
                if end == -1:
                    for position in range(start, len(line)):
                        chars[position] = " "
                    in_comment = True
                    index = len(line)
                else:
                    for position in range(start, end + 3):
                        chars[position] = " "
                    index = end + 3
        masked.append("".join(chars))
    return masked

def _mask_inline_code(line: str) -> str:
    """Replace inline code spans with spaces."""
    chars = list(line)
    index = 0
    length = len(line)

    while index < length:
        if line[index] != "`":
            index += 1
            continue

        opening_end = index
        while opening_end < length and line[opening_end] == "`":
            opening_end += 1
        ticks = opening_end - index

        search = opening_end
        closed = False
        while search < length:
            if line[search] != "`":
                search += 1
                continue

            closing_end = search
            while closing_end < length and line[closing_end] == "`":
                closing_end += 1

            if closing_end - search == ticks:
                for position in range(index, closing_end):
                    chars[position] = " "
                index = closing_end
                closed = True
                break
            search = closing_end

        if not closed:
            index = opening_end

    return "".join(chars)

def _mask_fences(
    lines: Sequence[str], body_start: int
) -> tuple[list[str], list[Fence]]:
    """Mask fenced code blocks and return opening fences."""
    masked = list(lines)
    fences: list[Fence] = []
    fence_char: str | None = None
    fence_length = 0
    current: Fence | None = None

    for index in range(body_start, len(lines)):
        line = lines[index]
        if fence_char is None:
            match = FENCE_OPEN_RE.match(line)
            if match:
                marker = match.group(1)
                current = Fence(line=index + 1, info=match.group(2).strip())
                fences.append(current)
                fence_char = marker[0]
                fence_length = len(marker)
                masked[index] = ""
            continue

        masked[index] = ""
        match = FENCE_CLOSE_RE.match(line)
        if match:
            marker = match.group(1)
            if marker[0] == fence_char and len(marker) >= fence_length:
                if current is not None:
                    current.closed = True
                fence_char = None
                fence_length = 0
                current = None

    for index in range(0, body_start):
        masked[index] = ""

    return masked, fences

def _extract_headings(lines: Sequence[str], body_start: int) -> list[Heading]:
    """Extract ATX headings from masked lines."""
    headings: list[Heading] = []
    for index in range(body_start, len(lines)):
        match = HEADING_RE.match(lines[index])
        if not match:
            continue
        text = re.sub(r"[ \t]+#+[ \t]*$", "", match.group(2).strip()).strip()
        headings.append(Heading(line=index + 1, level=len(match.group(1)), text=text))
    return headings

def _parse_suppressions(lines: Sequence[str]) -> Suppressions:
    """Parse gldq suppression comments."""
    suppressions = Suppressions()
    for index in range(len(lines)):
        line_number = index + 1
        line = lines[index]
        for match in SUPPRESSION_RE.finditer(line):
            kind = match.group(1).lower()
            rules = {
                value.strip().upper()
                for value in re.split(r"[,\s]+", match.group(2).strip())
                if value.strip()
            }
            if not rules:
                continue
            if kind == "disable-file":
                suppressions.file_rules.update(rules)
            elif kind == "disable-next-line":
                suppressions.next_line.setdefault(line_number + 1, set()).update(rules)
            else:
                suppressions.from_line.append((line_number, rules))
    suppressions.from_line.sort(key=lambda item: item[0])
    return suppressions

def _path_matches(path_text: str, pattern: str) -> bool:
    """Match a POSIX path against a wildcard pattern."""
    pattern = pattern.strip().replace("\\", "/")
    while pattern.startswith("./"):
        pattern = pattern[2:]
    if not pattern:
        return False

    path_text = path_text.replace("\\", "/")
    if fnmatch.fnmatchcase(path_text, pattern):
        return True

    prefix = pattern.rstrip("/")
    return bool(prefix) and path_text.startswith(prefix + "/")

def _string_list(value: object, path: Path, entry: int, field_name: str) -> list[str]:
    """Normalize a YAML string or list of strings."""
    if isinstance(value, str):
        values = [value]
    elif isinstance(value, list) and all(isinstance(item, str) for item in value):
        values = value
    else:
        raise ValueError(
            f"{path}: exclude entry {entry} field \'{field_name}\' "
            "must be a string or a list of strings"
        )

    cleaned = [item.strip() for item in values if item.strip()]
    if not cleaned:
        raise ValueError(
            f"{path}: exclude entry {entry} field \'{field_name}\' must not be empty"
        )
    return cleaned

def load_exclude_file(path: Path) -> ExcludeConfig:
    """Load a rule-aware exclusion file."""
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ValueError(f"{path}: invalid YAML: {_first_line(str(exc))}") from exc
    except OSError as exc:
        raise ValueError(f"{path}: cannot read exclude file: {exc}") from exc

    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise ValueError(f"{path}: top-level YAML must be a mapping")

    entries = data.get("exclude")
    if entries is None:
        return ExcludeConfig(path=path)
    if not isinstance(entries, list):
        raise ValueError(f"{path}: \'exclude\' must be a list")

    config = ExcludeConfig(path=path)
    for index, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            raise ValueError(f"{path}: exclude entry {index} must be a mapping")

        rules_value = entry.get("rules")
        if rules_value is None:
            rules_value = ["*"]
        paths_value = entry.get("paths")
        if paths_value is None:
            raise ValueError(f"{path}: exclude entry {index} is missing \'paths\'")

        rule_patterns = _string_list(rules_value, path, index, "rules")
        path_patterns = _string_list(paths_value, path, index, "paths")

        for pattern in rule_patterns:
            normalized = pattern.upper()
            if not any(character in normalized for character in "*?[]"): 
                if normalized not in RULES:
                    raise ValueError(
                        f"{path}: exclude entry {index} references unknown rule: "
                        f"{pattern}"
                    )

        config.rules.append(
            ExclusionRule(
                rule_patterns=tuple(pattern.upper() for pattern in rule_patterns),
                path_patterns=tuple(path_patterns),
                entry=index,
            )
        )

    return config
def _infer_root(path: Path) -> Path:
    """Infer the documentation root for a file or directory path."""
    candidate = path if path.is_dir() else path.parent
    for parent in (candidate, *candidate.parents):
        if parent.name == "docs":
            return parent
    return candidate
def _should_skip(file_path: Path, root: Path, excludes: Sequence[str]) -> bool:
    """Return whether a path should be skipped."""
    try:
        relative = file_path.relative_to(root)
    except ValueError:
        relative = file_path

    if any(part in SKIP_DIRS for part in relative.parts):
        return True
    if file_path.name.startswith("_"):
        return True

    relative_text = relative.as_posix()
    full_text = file_path.as_posix()
    for pattern in excludes:
        cleaned = pattern.strip()
        while cleaned.startswith("./"):
            cleaned = cleaned[2:]
        if not cleaned:
            continue
        if fnmatch.fnmatch(relative_text, cleaned):
            return True
        if fnmatch.fnmatch(full_text, cleaned):
            return True
        if relative_text.startswith(cleaned.rstrip("/") + "/"):
            return True
    return False

def parse_document(path: Path, root: Path) -> Document:
    """Parse a markdown file into a Document."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    frontmatter, frontmatter_error, has_frontmatter, body_start = _parse_frontmatter(
        lines
    )

    comment_masked = _mask_html_comments(lines)
    no_fence_lines, fences = _mask_fences(comment_masked, body_start)
    prose_lines = [
        "" if index < body_start else _mask_inline_code(line)
        for index, line in enumerate(no_fence_lines)
    ]
    headings = _extract_headings(no_fence_lines, body_start)

    return Document(
        path=path,
        root=root,
        relative=path.relative_to(root),
        lines=lines,
        frontmatter=frontmatter,
        frontmatter_error=frontmatter_error,
        has_frontmatter=has_frontmatter,
        body_start=body_start,
        no_fence_lines=no_fence_lines,
        prose_lines=prose_lines,
        headings=headings,
        fences=fences,
        suppressions=_parse_suppressions(lines),
    )


def iter_documents(
    paths: Sequence[Path], excludes: Sequence[str]
) -> Iterator[Document]:
    """Yield parsed markdown documents for the given paths."""
    seen: set[Path] = set()
    for path in paths:
        if path.is_dir():
            root = path
            candidates = sorted(path.rglob("*.md"))
        else:
            root = _infer_root(path)
            candidates = [path]

        for file_path in candidates:
            if file_path.suffix.lower() != ".md":
                continue
            if _should_skip(file_path, root, excludes):
                continue
            resolved = file_path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            yield parse_document(file_path, root)


def collect_findings(
    documents: Sequence[Document],
    disabled: set[str],
    exclusions: ExcludeConfig | None = None,
) -> tuple[list[Finding], int, int]:
    """Run every check and apply suppressions and exclusions."""
    if exclusions is None:
        exclusions = ExcludeConfig()

    findings: list[Finding] = []
    suppressed = 0
    excluded = 0

    for document in documents:
        for check in CHECKS:
            for finding in check(document):
                if finding.rule_id in disabled or document.suppressions.suppresses(
                    finding.rule_id, finding.line
                ):
                    suppressed += 1
                    continue
                if exclusions.matches(finding.rule_id, document.path, document.root):
                    excluded += 1
                    continue
                findings.append(finding)

    findings.sort(key=lambda item: item.sort_key)
    return findings, suppressed, excluded

def _resolve_target(root: Path, reference: str) -> bool:
    """Resolve a related_topics reference against the docs root."""
    reference = reference.strip()
    if not reference:
        return False
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", reference) or reference.startswith("//"):
        return True

    reference = reference.split("#", 1)[0].split("?", 1)[0].strip()
    if not reference:
        return False

    reference = reference.lstrip("/")
    if not reference or reference == ".":
        return (root / "index.md").is_file()
    if reference.endswith("/"): 
        return (root / reference / "index.md").is_file()

    candidates = [root / reference]
    if not reference.endswith(".md"):
        candidates.append(root / f"{reference}.md")
        candidates.append(root / reference / "index.md")
    return any(candidate.is_file() for candidate in candidates)

def _finding(
    document: Document,
    rule_id: str,
    line: int | None,
    column: int | None,
    message: str,
) -> Finding:
    rule = RULES[rule_id]
    frontmatter = document.frontmatter or {}
    org = frontmatter.get("github_org")
    repo = frontmatter.get("github_repo")
    group = f"{org}/{repo}" if org and repo else NO_REPO_GROUP
    return Finding(
        rule_id=rule_id,
        severity=rule.severity,
        path=document.path,
        line=line,
        column=column,
        message=message,
        group=group,
    )

def check_frontmatter(document: Document) -> Iterator[Finding]:
    """Check front matter structure and related topics."""
    frontmatter = document.frontmatter or {}

    if document.frontmatter_error:
        yield _finding(
            document,
            "FM-YAML",
            1,
            1,
            f"Invalid front matter: {document.frontmatter_error}",
        )

    if document.is_home:
        return

    title = frontmatter.get("title")
    if not isinstance(title, str) or not title.strip():
        yield _finding(
            document, "FM-TITLE", 1, 1, "Missing or empty title in front matter"
        )

    description = frontmatter.get("description")
    if not isinstance(description, str) or not description.strip():
        yield _finding(
            document,
            "FM-DESC",
            1,
            1,
            "Missing or empty description in front matter",
        )

    if "order" in frontmatter:
        order = frontmatter["order"]
        if isinstance(order, bool) or not isinstance(order, int):
            yield _finding(
                document,
                "FM-ORDER",
                1,
                1,
                "Front matter \'order\' must be an integer",
            )

    if "related_topics" in frontmatter:
        related_topics = frontmatter["related_topics"]
        if not isinstance(related_topics, list):
            yield _finding(
                document,
                "FM-RELATED",
                1,
                1,
                "Front matter \'related_topics\' must be a list",
            )
        else:
            for reference in related_topics:
                if not isinstance(reference, str) or not reference.strip():
                    yield _finding(
                        document,
                        "FM-RELATED",
                        1,
                        1,
                        "Front matter \'related_topics\' entries must be non-empty strings",
                    )
                    continue
                if not _resolve_target(document.root, reference):
                    yield _finding(
                        document,
                        "FM-RELATED",
                        1,
                        1,
                        f"related_topics target not found: {reference}",
                    )

def check_repo(document: Document) -> Iterator[Finding]:
    """Require github_org and github_repo front matter."""
    if document.is_home or document.is_excluded:
        return

    frontmatter = document.frontmatter or {}
    org = frontmatter.get("github_org")
    repo = frontmatter.get("github_repo")
    if (
        not isinstance(org, str)
        or not org.strip()
        or not isinstance(repo, str)
        or not repo.strip()
    ):
        yield _finding(
            document,
            "FM-REPO",
            1,
            1,
            "Missing github_org or github_repo in front matter",
        )

def check_headings(document: Document) -> Iterator[Finding]:
    """Check heading structure."""
    level_one = [heading for heading in document.headings if heading.level == 1]

    for heading in document.headings:
        if not heading.text:
            yield _finding(document, "H1-EMPTY", heading.line, 1, "Heading is empty")

    if not document.is_home:
        if not level_one:
            yield _finding(document, "H1-ONE", 1, 1, "Document has no level-1 heading")
        elif len(level_one) > 1:
            for heading in level_one[1:]:
                yield _finding(
                    document,
                    "H1-ONE",
                    heading.line,
                    1,
                    "Document has multiple level-1 headings",
                )

    previous: int | None = None
    for heading in document.headings:
        if previous is not None and heading.level > previous + 1:
            yield _finding(
                document,
                "HEAD-SKIP",
                heading.line,
                1,
                f"Heading level jumps from {previous} to {heading.level}",
            )
        previous = heading.level

def check_code(document: Document) -> Iterator[Finding]:
    """Check fenced code block language and balance."""
    for fence in document.fences:
        if not fence.info:
            yield _finding(
                document,
                "CODE-LANG",
                fence.line,
                1,
                "Fenced code block has no language",
            )
        if not fence.closed:
            yield _finding(
                document,
                "CODE-BALANCE",
                fence.line,
                1,
                "Fenced code block is not closed",
            )

def check_images(document: Document) -> Iterator[Finding]:
    """Check markdown and HTML image alt text."""
    for index in range(document.body_start, len(document.no_fence_lines)):
        line = document.no_fence_lines[index]
        line_number = index + 1

        for match in MD_IMAGE_RE.finditer(line):
            if document.prose_lines[index][match.start()] != "!":
                continue
            if not match.group(1).strip():
                yield _finding(
                    document,
                    "IMG-ALT",
                    line_number,
                    match.start() + 1,
                    "Image is missing alt text",
                )

        for match in HTML_IMG_RE.finditer(line):
            if document.prose_lines[index][match.start()] != "<":
                continue
            alt_match = ALT_ATTR_RE.search(match.group(0))
            if alt_match is None:
                yield _finding(
                    document,
                    "IMG-ALT",
                    line_number,
                    match.start() + 1,
                    "HTML image is missing alt text",
                )
                continue
            value = next(
                (group for group in alt_match.groups() if group is not None), ""
            )
            if not value.strip():
                yield _finding(
                    document,
                    "IMG-ALT",
                    line_number,
                    match.start() + 1,
                    "HTML image has empty alt text",
                )

def _normalize_link_text(text: str) -> str:
    text = re.sub(r"`+", "", text)
    text = re.sub(r"[*_~]", "", text)
    text = " ".join(text.split()).strip().lower()
    return text.strip(" .,:;!?()[]{}<>\"'")

def check_links(document: Document) -> Iterator[Finding]:
    """Check for missing or generic link text."""
    for index in range(document.body_start, len(document.no_fence_lines)):
        line = document.no_fence_lines[index]
        for match in MD_LINK_RE.finditer(line):
            if document.prose_lines[index][match.start()] != "[":
                continue
            text = match.group(1)
            if _normalize_link_text(text) in GENERIC_LINK_TEXTS:
                yield _finding(
                    document,
                    "LINK-TEXT",
                    index + 1,
                    match.start() + 1,
                    f"Link text is not descriptive: {text!r}",
                )

def check_emoji(document: Document) -> Iterator[Finding]:
    """Check for emoji outside code fences and front matter."""
    for index in range(document.body_start, len(document.prose_lines)):
        match = EMOJI_RE.search(document.prose_lines[index])
        if match:
            yield _finding(
                document,
                "EMOJI",
                index + 1,
                match.start() + 1,
                f"Emoji outside code fence: {match.group(0)}",
            )

def _first_line_with(lines: Sequence[str], needle: str) -> int | None:
    for index, line in enumerate(lines):
        if needle in line:
            return index + 1
    return None

def _last_line_with(lines: Sequence[str], needle: str) -> int | None:
    for index in range(len(lines) - 1, -1, -1):
        if needle in lines[index]:
            return index + 1
    return None

def check_components(document: Document) -> Iterator[Finding]:
    """Check VitePress component requirements."""
    text = document.no_fence_text
    has_related_topics = "<RelatedTopics" in text

    relative_parts = document.relative.parts
    is_top_level_index = (
        document.is_index
        and len(relative_parts) == 2
        and relative_parts[0] in TOP_LEVEL_SECTIONS
    )
    if is_top_level_index and "<SectionIndex" not in text:
        yield _finding(
            document,
            "SECTION-INDEX",
            1,
            1,
            "Section index page is missing <SectionIndex />",
        )

    if has_related_topics:
        frontmatter = document.frontmatter or {}
        related_line = _last_line_with(document.no_fence_lines, "<RelatedTopics")
        if "related_topics" not in frontmatter:
            yield _finding(
                document,
                "RELATED-TOPICS-FM",
                related_line,
                1,
                "<RelatedTopics /> requires related_topics in front matter",
            )

        if related_line is not None:
            line_index = related_line - 1
            match = re.search(
                r"<RelatedTopics\b[^>]*>", document.no_fence_lines[line_index]
            )
            tail = (
                document.no_fence_lines[line_index][match.end() :].strip()
                if match
                else ""
            )
            if tail:
                yield _finding(
                    document,
                    "RELATED-TOPICS-END",
                    related_line,
                    1,
                    "<RelatedTopics /> must be the last content block",
                )
            else:
                for index in range(line_index + 1, len(document.no_fence_lines)):
                    if document.no_fence_lines[index].strip():
                        yield _finding(
                            document,
                            "RELATED-TOPICS-END",
                            related_line,
                            1,
                            "<RelatedTopics /> must be the last content block",
                        )

    if (
        not document.is_home
        and not document.is_index
        and not document.is_excluded
        and not has_related_topics
    ):
        yield _finding(
            document,
            "RELATED-TOPICS-PRESENT",
            1,
            1,
            "Non-index pages should include <RelatedTopics />",
        )


def check_callouts(document: Document) -> Iterator[Finding]:
    """Check VitePress container callouts and reject unsupported syntax."""
    stack: list[tuple[int, str, int]] = []

    for index in range(document.body_start, len(document.no_fence_lines)):
        line = document.no_fence_lines[index]
        line_number = index + 1

        if GITHUB_CALLOUT_RE.match(line):
            yield _finding(
                document,
                "CALLOUT-GITHUB-STYLE",
                line_number,
                1,
                "GitHub-style callouts are not supported; use VitePress ::: syntax",
            )
            continue

        close_match = CALLOUT_CLOSE_RE.match(line)
        if close_match and stack:
            if len(close_match.group(1)) >= stack[-1][2]:
                stack.pop()
            continue

        open_match = CALLOUT_OPEN_RE.match(line)
        if open_match:
            callout_type = open_match.group(2).lower()
            if callout_type not in VITEPRESS_CALLOUT_TYPES:
                yield _finding(
                    document,
                    "CALLOUT-INVALID-TYPE",
                    line_number,
                    1,
                    "Invalid VitePress container type "
                    f"{callout_type!r}; use info, tip, warning, danger, or details",
                )
            stack.append((line_number, callout_type, len(open_match.group(1))))

    for line_number, _, _ in stack:
        yield _finding(
            document,
            "CALLOUT-UNCLOSED",
            line_number,
            1,
            "VitePress container is not closed with :::",
        )


CHECKS.extend(
    [
        check_frontmatter,
        check_repo,
        check_headings,
        check_code,
        check_images,
        check_links,
        check_emoji,
        check_components,
        check_callouts,
    ]
)


def _group_findings(
    findings: Sequence[Finding],
) -> list[tuple[str, list[tuple[Path, list[Finding]]]]]:
    """Group findings by github_org/github_repo, then by filename.

    Groups are sorted alphabetically with the "(no repo)" group last. Files
    within each group are sorted alphabetically by path, and findings within
    each file retain their sort_key ordering.
    """
    by_group: dict[str, dict[Path, list[Finding]]] = {}
    for finding in findings:
        files = by_group.setdefault(finding.group, {})
        files.setdefault(finding.path, []).append(finding)

    def group_sort_key(label: str) -> tuple[bool, str]:
        return (label == NO_REPO_GROUP, label)

    grouped: list[tuple[str, list[tuple[Path, list[Finding]]]]] = []
    for label in sorted(by_group, key=group_sort_key):
        files = by_group[label]
        file_entries = [
            (path, sorted(files[path], key=lambda item: item.sort_key))
            for path in sorted(files, key=lambda item: item.as_posix())
        ]
        grouped.append((label, file_entries))
    return grouped


def _counts(findings: Sequence[Finding]) -> tuple[int, int]:
    errors = sum(1 for finding in findings if finding.severity == ERROR)
    warnings = sum(1 for finding in findings if finding.severity == WARNING)
    return errors, warnings


def _escape_github(text: str) -> str:
    return text.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def _exclude_label(exclude_file: Path | None) -> str:
    return exclude_file.as_posix() if exclude_file else "exclude file"


def _format_location(finding: Finding) -> str:
    location = f"{finding.path}"
    if finding.line is not None:
        location += f":{finding.line}"
        if finding.column is not None:
            location += f":{finding.column}"
    return location


def format_text(
    findings: Sequence[Finding],
    suppressed: int,
    excluded: int,
    file_count: int,
    exclude_file: Path | None = None,
) -> str:
    """Format findings as human-readable text."""
    lines: list[str] = []
    for label, file_entries in _group_findings(findings):
        if lines:
            lines.append("")
        lines.append(f"## {label}")
        for path, file_findings in file_entries:
            lines.append("")
            lines.append(f"{path.as_posix()}:")
            for finding in file_findings:
                lines.append(
                    f"  {_format_location(finding)}: {finding.severity} "
                    f"{finding.rule_id}: {finding.message}"
                )

    if not lines:
        lines.append("No documentation quality findings.")
    else:
        lines.append("")

    errors, warnings = _counts(findings)
    summary = f"{errors} error(s), {warnings} warning(s) in {file_count} file(s)"
    if suppressed:
        summary += f", {suppressed} suppressed inline"
    if excluded:
        summary += (
            f", {excluded} finding(s) excluded by {_exclude_label(exclude_file)}"
        )
    lines.append(summary)
    return "\n".join(lines)


def format_json(
    findings: Sequence[Finding],
    suppressed: int,
    excluded: int,
    file_count: int,
    exclude_file: Path | None = None,
) -> str:
    """Format findings as JSON."""
    errors, warnings = _counts(findings)
    payload = {
        "tool": "gldq",
        "version": __version__,
        "name": "Garden Linux Docs Quality",
        "summary": {
            "files": file_count,
            "errors": errors,
            "warnings": warnings,
            "suppressed": suppressed,
            "excluded": excluded,
            "exclude_file": exclude_file.as_posix() if exclude_file else None,
        },
        "groups": [
            {
                "group": label,
                "files": [
                    {
                        "path": path.as_posix(),
                        "findings": [
                            {
                                "line": finding.line,
                                "column": finding.column,
                                "rule": finding.rule_id,
                                "severity": finding.severity,
                                "message": finding.message,
                            }
                            for finding in file_findings
                        ],
                    }
                    for path, file_findings in file_entries
                ],
            }
            for label, file_entries in _group_findings(findings)
        ],
    }
    return json.dumps(payload, indent=2)


def format_github(
    findings: Sequence[Finding],
    suppressed: int,
    excluded: int,
    file_count: int,
    exclude_file: Path | None = None,
) -> str:
    """Format findings as GitHub Actions workflow annotations."""
    lines: list[str] = []
    for label, file_entries in _group_findings(findings):
        lines.append(f"::group::{_escape_github(label)}")
        for _, file_findings in file_entries:
            for finding in file_findings:
                kind = "error" if finding.severity == ERROR else "warning"
                properties = [f"file={finding.path}"]
                if finding.line is not None:
                    properties.append(f"line={finding.line}")
                if finding.column is not None:
                    properties.append(f"col={finding.column}")
                message = _escape_github(f"[{finding.rule_id}] {finding.message}")
                lines.append(f"::{kind} {','.join(properties)}::{message}")
        lines.append("::endgroup::")

    if not lines:
        lines.append("::notice title=gldq::No documentation quality findings")

    errors, warnings = _counts(findings)
    summary = (
        "::notice title=gldq::"
        f"{errors} error(s), {warnings} warning(s) in {file_count} file(s)"
    )
    if suppressed:
        summary += f", {suppressed} suppressed inline"
    if excluded:
        summary += f", {excluded} excluded by {_exclude_label(exclude_file)}"
    lines.append(summary)
    return "\n".join(lines)

def print_rules() -> None:
    """Print the rule registry."""
    print(f"{'RULE':22} {'SEVERITY':8} DESCRIPTION")
    for rule in sorted(RULES.values(), key=lambda item: item.rule_id):
        print(f"{rule.rule_id:22} {rule.severity:8} {rule.description}")

def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        prog="gldq",
        description="Garden Linux Docs Quality",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=["docs"],
        help="Files or directories to check (default: docs)",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json", "github"),
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as failures",
    )
    parser.add_argument(
        "--disable",
        action="append",
        default=[],
        metavar="RULE",
        help="Disable a rule (repeatable)",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        metavar="GLOB",
        help="Exclude matching paths (repeatable)",
    )
    exclude_group = parser.add_mutually_exclusive_group()
    exclude_group.add_argument(
        "--exclude-file",
        metavar="PATH",
        help="Use a custom rule-aware exclude file",
    )
    exclude_group.add_argument(
        "--no-exclude-file",
        action="store_true",
        help="Do not auto-load .gldq-exclude.yml",
    )
    parser.add_argument(
        "--list-rules",
        action="store_true",
        help="List available rules and exit",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser

def main(argv: Sequence[str] | None = None) -> int:
    """Run gldq and return an exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_rules:
        print_rules()
        return 0

    paths = [Path(value) for value in args.paths]
    missing = [path for path in paths if not path.exists()]
    if missing:
        for path in missing:
            print(f"gldq: path not found: {path}", file=sys.stderr)
        return 2

    disabled = {rule.strip().upper() for rule in args.disable if rule.strip()}
    unknown = disabled - set(RULES)
    if unknown:
        print(
            f"gldq: unknown rule(s): {','.join(sorted(unknown))}",
            file=sys.stderr,
        )
        return 2

    exclude_file: Path | None = None
    exclusions = ExcludeConfig()
    if args.exclude_file:
        exclude_file = Path(args.exclude_file)
        if not exclude_file.is_file():
            print(
                f"gldq: exclude file not found: {exclude_file}",
                file=sys.stderr,
            )
            return 2
    elif not args.no_exclude_file and DEFAULT_EXCLUDE_FILE.is_file():
        exclude_file = DEFAULT_EXCLUDE_FILE

    if exclude_file is not None:
        try:
            exclusions = load_exclude_file(exclude_file)
        except ValueError as exc:
            print(f"gldq: {exc}", file=sys.stderr)
            return 2

    try:
        documents = list(iter_documents(paths, args.exclude))
    except OSError as exc:
        print(f"gldq: {exc}", file=sys.stderr)
        return 2

    findings, suppressed, excluded = collect_findings(documents, disabled, exclusions)
    file_count = len(documents)

    if args.format == "json":
        print(format_json(findings, suppressed, excluded, file_count, exclude_file))
    elif args.format == "github":
        print(format_github(findings, suppressed, excluded, file_count, exclude_file))
    else:
        print(format_text(findings, suppressed, excluded, file_count, exclude_file))

    errors, warnings = _counts(findings)
    if errors or (args.strict and warnings):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())