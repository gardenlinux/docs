"""Unit tests for the Garden Linux Docs Quality Tool."""

import json
from pathlib import Path

import gldq


def write_doc(tmp_path: Path, relative: str, content: str) -> Path:
    """Write a markdown document below tmp_path."""
    path = tmp_path / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def make_doc(
    body: str,
    frontmatter: str = (
        "title: Page\n"
        "description: A test page\n"
        "github_org: gardenlinux\n"
        "github_repo: docs\n"
    ),
) -> str:
    """Build a markdown document with default valid front matter."""
    return f"---\n{frontmatter}---\n\n{body}"


def make_release_note(body: str = "Chart 📊\n") -> str:
    """Build a valid release note document with a trailing RelatedTopics."""
    return make_doc(
        f"# Release\n\n{body}\n<RelatedTopics />\n",
        frontmatter=(
            "title: Release\n"
            "description: Release notes\n"
            "github_org: gardenlinux\n"
            "github_repo: docs\n"
            "related_topics: []\n"
        ),
    )


def find(
    tmp_path: Path,
    content: str,
    relative: str = "docs/page.md",
    root_relative: str = "docs",
) -> list[gldq.Finding]:
    """Parse one document and return its unsuppressed findings."""
    path = write_doc(tmp_path, relative, content)
    document = gldq.parse_document(path, tmp_path / root_relative)
    findings, _, _ = gldq.collect_findings([document], set())
    return findings


def rule_ids(findings: list[gldq.Finding]) -> list[str]:
    """Return the rule IDs from findings."""
    return [finding.rule_id for finding in findings]


def flatten_json_findings(payload: dict) -> list[dict]:
    """Flatten the grouped JSON payload into a flat list of findings.

    Each finding dict is augmented with its ``group`` and ``path`` for
    assertions that predate the grouped output structure.
    """
    flattened: list[dict] = []
    for group in payload["groups"]:
        for file_entry in group["files"]:
            for finding in file_entry["findings"]:
                flattened.append(
                    {**finding, "group": group["group"], "path": file_entry["path"]}
                )
    return flattened


class TestValidDocuments:
    def test_valid_index_page_has_no_findings(self, tmp_path):
        content = make_doc(
            "# Guide\n\n"
            "Text with a [descriptive link](https://example.com).\n\n"
            "```shell\n"
            "echo hello\n"
            "```\n\n"
            "![diagram](diagram.png)\n"
        )
        findings = find(tmp_path, content, relative="docs/guide/index.md")
        assert findings == []

    def test_home_page_skips_title_and_h1_rules(self, tmp_path):
        content = (
            "---\n" "layout: home\n" "hero:\n" "  name: Test\n" "---\n\n" "Welcome.\n"
        )
        findings = find(tmp_path, content)
        ids = rule_ids(findings)
        assert "FM-TITLE" not in ids
        assert "FM-DESC" not in ids
        assert "H1-ONE" not in ids
        assert "RELATED-TOPICS-PRESENT" not in ids


class TestFrontmatter:
    def test_missing_title_and_description_warn(self, tmp_path):
        findings = find(tmp_path, "---\norder: 1\n---\n\n# Page\n")
        ids = rule_ids(findings)
        assert "FM-TITLE" in ids
        assert "FM-DESC" in ids

    def test_invalid_yaml_is_an_error(self, tmp_path):
        findings = find(tmp_path, "---\ntitle: [broken\n---\n\n# Page\n")
        assert "FM-YAML" in rule_ids(findings)

    def test_unclosed_frontmatter_is_an_error(self, tmp_path):
        findings = find(tmp_path, "---\ntitle: Page\n\n# Page\n")
        assert "FM-YAML" in rule_ids(findings)

    def test_non_mapping_frontmatter_is_an_error(self, tmp_path):
        findings = find(tmp_path, "---\n- one\n- two\n---\n\n# Page\n")
        assert "FM-YAML" in rule_ids(findings)

    def test_non_integer_order_warns(self, tmp_path):
        findings = find(
            tmp_path,
            make_doc(
                "# Page\n", frontmatter="title: Page\ndescription: Page\norder: first\n"
            ),
        )
        assert "FM-ORDER" in rule_ids(findings)

    def test_related_topics_existing_targets_pass(self, tmp_path):
        write_doc(tmp_path, "docs/target.md", make_doc("# Target\n"))
        write_doc(tmp_path, "docs/dir/index.md", make_doc("# Directory\n"))
        content = make_doc(
            "# Page\n",
            frontmatter=(
                "title: Page\n"
                "description: Page\n"
                "related_topics:\n"
                "  - /target.md\n"
                "  - target\n"
                "  - /dir/\n"
                "  - dir/index.md\n"
                "  - https://example.com\n"
                "  - mailto:docs@example.com\n"
            ),
        )
        findings = find(tmp_path, content)
        assert "FM-RELATED" not in rule_ids(findings)

    def test_related_topics_missing_target_is_an_error(self, tmp_path):
        content = make_doc(
            "# Page\n",
            frontmatter=(
                "title: Page\ndescription: Page\nrelated_topics:\n  - /missing.md\n"
            ),
        )
        findings = find(tmp_path, content)
        assert "FM-RELATED" in rule_ids(findings)

    def test_related_topics_must_be_a_list(self, tmp_path):
        content = make_doc(
            "# Page\n",
            frontmatter="title: Page\ndescription: Page\nrelated_topics: target.md\n",
        )
        findings = find(tmp_path, content)
        assert "FM-RELATED" in rule_ids(findings)


class TestHeadings:
    def test_missing_h1_warns(self, tmp_path):
        findings = find(tmp_path, make_doc("## No level one\n"))
        assert "H1-ONE" in rule_ids(findings)

    def test_multiple_h1_warn(self, tmp_path):
        findings = find(tmp_path, make_doc("# One\n\n# Two\n"))
        assert rule_ids(findings).count("H1-ONE") == 1

    def test_empty_heading_is_an_error(self, tmp_path):
        findings = find(tmp_path, make_doc("# \n"))
        assert "H1-EMPTY" in rule_ids(findings)

    def test_skipped_heading_level_warns(self, tmp_path):
        findings = find(tmp_path, make_doc("# Page\n\n### Skipped\n"))
        assert "HEAD-SKIP" in rule_ids(findings)


class TestCodeBlocks:
    def test_unclosed_fence_is_an_error(self, tmp_path):
        findings = find(tmp_path, make_doc("# Page\n\n```shell\necho hello\n"))
        assert "CODE-BALANCE" in rule_ids(findings)

    def test_fence_without_language_warns(self, tmp_path):
        findings = find(tmp_path, make_doc("# Page\n\n```\necho hello\n```\n"))
        assert rule_ids(findings).count("CODE-LANG") == 1

    def test_indented_fence_is_detected(self, tmp_path):
        content = make_doc(
            "# Page\n\n"
            "- item\n\n"
            "      ```shell\n"
            "      echo hello\n"
            "      ```\n"
        )
        assert "CODE-BALANCE" not in rule_ids(find(tmp_path, content))

    def test_markdown_inside_fence_is_ignored(self, tmp_path):
        content = make_doc(
            "# Page\n\n"
            "```markdown\n"
            "# Not a heading\n"
            "[click here](https://example.com)\n"
            "![](missing.png)\n"
            "✅\n"
            "```\n"
        )
        ids = rule_ids(find(tmp_path, content))
        assert "HEAD-SKIP" not in ids
        assert "LINK-TEXT" not in ids
        assert "IMG-ALT" not in ids
        assert "EMOJI" not in ids


class TestImages:
    def test_missing_alt_text_is_an_error(self, tmp_path):
        content = make_doc(
            "# Page\n\n"
            "![](diagram.png)\n\n"
            '<img src="x.png">\n\n'
            '<img src="x.png" alt="">\n'
        )
        findings = find(tmp_path, content)
        assert rule_ids(findings).count("IMG-ALT") == 3

    def test_valid_alt_text_passes(self, tmp_path):
        content = make_doc(
            "# Page\n\n"
            "![diagram](diagram.png)\n\n"
            '<img src="x.png" alt="A diagram">\n'
        )
        assert "IMG-ALT" not in rule_ids(find(tmp_path, content))

    def test_data_alt_is_not_a_valid_alt_attribute(self, tmp_path):
        findings = find(
            tmp_path,
            make_doc("# Page\n\n" '<img src="x.png" data-alt="A diagram">\n'),
        )
        assert "IMG-ALT" in rule_ids(findings)

    def test_inline_code_image_is_ignored(self, tmp_path):
        findings = find(tmp_path, make_doc("# Page\n\n`![](missing.png)`\n"))
        assert "IMG-ALT" not in rule_ids(findings)


class TestLinks:
    def test_generic_link_text_is_an_error(self, tmp_path):
        findings = find(
            tmp_path,
            make_doc("# Page\n\n[click here](https://example.com)\n"),
        )
        assert "LINK-TEXT" in rule_ids(findings)

    def test_empty_link_text_is_an_error(self, tmp_path):
        findings = find(tmp_path, make_doc("# Page\n\n[](https://example.com)\n"))
        assert "LINK-TEXT" in rule_ids(findings)

    def test_descriptive_link_text_passes(self, tmp_path):
        findings = find(
            tmp_path,
            make_doc("# Page\n\n[Garden Linux releases](https://example.com)\n"),
        )
        assert "LINK-TEXT" not in rule_ids(findings)

    def test_inline_code_link_is_ignored(self, tmp_path):
        findings = find(
            tmp_path,
            make_doc("# Page\n\n`[click here](https://example.com)`\n"),
        )
        assert "LINK-TEXT" not in rule_ids(findings)


class TestEmoji:
    def test_emoji_outside_code_warns(self, tmp_path):
        findings = find(tmp_path, make_doc("# Page\n\nAll good ✅\n"))
        assert "EMOJI" in rule_ids(findings)

    def test_emoji_in_code_fence_is_ignored(self, tmp_path):
        findings = find(tmp_path, make_doc("# Page\n\n```text\n✅\n```\n"))
        assert "EMOJI" not in rule_ids(findings)

    def test_emoji_in_inline_code_is_ignored(self, tmp_path):
        findings = find(tmp_path, make_doc("# Page\n\n`✅`\n"))
        assert "EMOJI" not in rule_ids(findings)

    def test_emoji_in_frontmatter_is_ignored(self, tmp_path):
        content = make_doc(
            "# Page\n",
            frontmatter="title: Page\ndescription: A page with ✅\n",
        )
        findings = find(tmp_path, content)
        assert "EMOJI" not in rule_ids(findings)

    def test_disable_next_line(self, tmp_path):
        content = make_doc("# Page\n\n<!-- gldq: disable-next-line EMOJI -->\n✅\n")
        assert "EMOJI" not in rule_ids(find(tmp_path, content))

    def test_disable_from_line(self, tmp_path):
        content = make_doc("# Page\n\n<!-- gldq: disable EMOJI -->\n✅\n")
        assert "EMOJI" not in rule_ids(find(tmp_path, content))

    def test_disable_file(self, tmp_path):
        content = make_doc("# Page\n\n<!-- gldq: disable-file EMOJI -->\n✅\n")
        assert "EMOJI" not in rule_ids(find(tmp_path, content))


class TestComponents:
    def test_section_index_requires_component(self, tmp_path):
        findings = find(
            tmp_path,
            make_doc("# Explanation\n"),
            relative="docs/explanation/index.md",
        )
        assert "SECTION-INDEX" in rule_ids(findings)

    def test_section_index_with_component_passes(self, tmp_path):
        findings = find(
            tmp_path,
            make_doc("# Explanation\n\n<SectionIndex />\n"),
            relative="docs/explanation/index.md",
        )
        assert "SECTION-INDEX" not in rule_ids(findings)

    def test_related_topics_requires_frontmatter(self, tmp_path):
        findings = find(tmp_path, make_doc("# Page\n\n<RelatedTopics />\n"))
        assert "RELATED-TOPICS-FM" in rule_ids(findings)

    def test_related_topics_must_be_last(self, tmp_path):
        content = make_doc(
            "# Page\n\n<RelatedTopics />\n\n## After\n",
            frontmatter="title: Page\ndescription: Page\nrelated_topics: []\n",
        )
        findings = find(tmp_path, content)
        assert "RELATED-TOPICS-END" in rule_ids(findings)

    def test_related_topics_last_passes(self, tmp_path):
        content = make_doc(
            "# Page\n\n<RelatedTopics />\n",
            frontmatter="title: Page\ndescription: Page\nrelated_topics: []\n",
        )
        findings = find(tmp_path, content)
        assert "RELATED-TOPICS-END" not in rule_ids(findings)

    def test_related_topics_present_warns_on_content_pages(self, tmp_path):
        findings = find(tmp_path, make_doc("# Page\n"))
        assert "RELATED-TOPICS-PRESENT" in rule_ids(findings)

    def test_related_topics_present_skips_index_pages(self, tmp_path):
        findings = find(
            tmp_path,
            make_doc("# Page\n"),
            relative="docs/guide/index.md",
        )
        assert "RELATED-TOPICS-PRESENT" not in rule_ids(findings)

    def test_related_topics_present_skips_excluded_pages(self, tmp_path):
        content = make_doc(
            "# Redirect\n",
            frontmatter="title: Redirect\ndescription: Redirect\nexclude: true\n",
        )
        findings = find(tmp_path, content)
        assert "RELATED-TOPICS-PRESENT" not in rule_ids(findings)

    def test_excluded_pages_still_run_other_rules(self, tmp_path):
        content = make_doc(
            "# Redirect\n\nChart 📊\n",
            frontmatter="title: Redirect\ndescription: Redirect\nexclude: true\n",
        )
        findings = find(tmp_path, content)
        assert "EMOJI" in rule_ids(findings)


class TestFalsePositives:
    def test_markdown_in_inline_code_is_ignored(self, tmp_path):
        content = make_doc(
            "# Page\n\n"
            "`# Not a heading` and `[click here](https://example.com)` "
            "and `![](missing.png)` and `✅`\n"
        )
        ids = rule_ids(find(tmp_path, content))
        assert "LINK-TEXT" not in ids
        assert "IMG-ALT" not in ids
        assert "EMOJI" not in ids
        assert "HEAD-SKIP" not in ids

    def test_markdown_in_frontmatter_is_ignored(self, tmp_path):
        content = make_doc(
            "# Page\n",
            frontmatter=(
                "title: Page\n"
                'description: "Use [click here](https://example.com), '
                '![](missing.png), and ✅"\n'
            ),
        )
        ids = rule_ids(find(tmp_path, content))
        assert "LINK-TEXT" not in ids
        assert "IMG-ALT" not in ids
        assert "EMOJI" not in ids


class TestDiscovery:
    def test_partials_and_excluded_paths_are_skipped(self, tmp_path):
        write_doc(tmp_path, "docs/keep.md", make_doc("# Keep\n"))
        write_doc(tmp_path, "docs/_partial.md", make_doc("# Partial\n"))
        write_doc(tmp_path, "docs/skip/ignored.md", make_doc("# Ignored\n"))

        documents = list(gldq.iter_documents([tmp_path / "docs"], []))
        names = {document.path.name for document in documents}
        assert "keep.md" in names
        assert "_partial.md" not in names
        assert "ignored.md" in names

        documents = list(gldq.iter_documents([tmp_path / "docs"], ["skip/**"]))
        names = {document.path.name for document in documents}
        assert "ignored.md" not in names


class TestExcludeFile:
    def write_exclude(
        self, tmp_path: Path, content: str, name: str = ".gldq-exclude.yml"
    ) -> Path:
        path = tmp_path / name
        path.write_text(content, encoding="utf-8")
        return path

    def test_default_exclude_file_excludes_release_note_emoji(
        self, tmp_path, monkeypatch, capsys
    ):
        self.write_exclude(
            tmp_path,
            "exclude:\n"
            '  - rules: ["EMOJI"]\n'
            "    paths:\n"
            '      - "docs/reference/releases/release-notes/**"\n',
        )
        write_doc(
            tmp_path,
            "docs/reference/releases/release-notes/archived/2150-6-0.md",
            make_release_note(),
        )
        monkeypatch.chdir(tmp_path)

        assert gldq.main(["docs", "--strict", "--format", "json"]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["summary"]["excluded"] == 1
        assert payload["summary"]["warnings"] == 0
        assert flatten_json_findings(payload) == []

    def test_exclusion_is_scoped_to_rule_and_path(self, tmp_path, monkeypatch, capsys):
        self.write_exclude(
            tmp_path,
            "exclude:\n"
            '  - rules: ["EMOJI"]\n'
            '    paths: ["docs/reference/releases/release-notes/**"]\n',
        )
        write_doc(
            tmp_path,
            "docs/reference/releases/release-notes/archived/release.md",
            make_release_note("Chart 📊 and [click here](https://example.com)\n"),
        )
        write_doc(
            tmp_path,
            "docs/guide/index.md",
            make_doc("# Guide\n\nChart 📊\n"),
        )
        monkeypatch.chdir(tmp_path)

        assert gldq.main(["docs", "--format", "json"]) == 1
        payload = json.loads(capsys.readouterr().out)
        assert payload["summary"]["excluded"] == 1

        findings_by_path: dict[str, list[str]] = {}
        for finding in flatten_json_findings(payload):
            findings_by_path.setdefault(finding["path"], []).append(finding["rule"])

        release_rules = next(
            rules for path, rules in findings_by_path.items() if "release-notes" in path
        )
        guide_rules = next(
            rules for path, rules in findings_by_path.items() if "guide" in path
        )
        assert "EMOJI" not in release_rules
        assert "LINK-TEXT" in release_rules
        assert "EMOJI" in guide_rules

    def test_rule_wildcard_and_relative_path(self, tmp_path):
        path = self.write_exclude(
            tmp_path,
            "exclude:\n"
            '  - rules: ["CODE-*"]\n'
            '    paths: ["reference/features/**"]\n',
            name="wildcards.yml",
        )
        config = gldq.load_exclude_file(path)
        root = Path("docs")
        document = Path("docs/reference/features/a.md")

        assert config.matches("CODE-LANG", document, root)
        assert config.matches("CODE-BALANCE", document, root)
        assert not config.matches("EMOJI", document, root)
        assert not config.matches("CODE-LANG", Path("docs/reference/other/a.md"), root)

    def test_star_and_omitted_rules_match_all(self, tmp_path):
        path = self.write_exclude(
            tmp_path,
            "exclude:\n"
            '  - rules: ["*"]\n'
            '    paths: ["reference/**"]\n'
            '  - paths: ["tutorials/**"]\n',
            name="all.yml",
        )
        config = gldq.load_exclude_file(path)
        root = Path("docs")

        assert config.matches("EMOJI", Path("docs/reference/a.md"), root)
        assert config.matches("FM-DESC", Path("docs/tutorials/a.md"), root)

    def test_path_patterns_match_relative_and_full(self, tmp_path):
        full = self.write_exclude(
            tmp_path,
            "exclude:\n"
            '  - rules: ["EMOJI"]\n'
            '    paths: ["docs/reference/releases/release-notes/**"]\n',
            name="full.yml",
        )
        relative = self.write_exclude(
            tmp_path,
            "exclude:\n"
            '  - rules: ["EMOJI"]\n'
            '    paths: ["reference/releases/release-notes/**"]\n',
            name="relative.yml",
        )
        root = Path("docs")
        document = Path("docs/reference/releases/release-notes/a.md")

        assert gldq.load_exclude_file(full).matches("EMOJI", document, root)
        assert gldq.load_exclude_file(relative).matches("EMOJI", document, root)

    def test_directory_prefix_pattern_matches(self, tmp_path):
        path = self.write_exclude(
            tmp_path,
            "exclude:\n" '  - rules: ["EMOJI"]\n' '    paths: ["reference/features"]\n',
            name="prefix.yml",
        )
        config = gldq.load_exclude_file(path)
        assert config.matches(
            "EMOJI",
            Path("docs/reference/features/a.md"),
            Path("docs"),
        )

    def test_comments_and_string_values(self, tmp_path):
        path = self.write_exclude(
            tmp_path,
            "# comment\n\n"
            "exclude:\n"
            '  - rules: "EMOJI"\n'
            '    paths: "reference/**"\n',
            name="comments.yml",
        )
        config = gldq.load_exclude_file(path)
        assert config.matches("EMOJI", Path("docs/reference/a.md"), Path("docs"))
        assert not config.matches("FM-DESC", Path("docs/reference/a.md"), Path("docs"))

    def test_empty_exclude_list_is_valid(self, tmp_path):
        path = self.write_exclude(tmp_path, "exclude: []\n", name="empty.yml")
        assert gldq.load_exclude_file(path).rules == []

    def test_missing_explicit_exclude_file(self, tmp_path, capsys):
        write_doc(tmp_path, "docs/page.md", make_doc("# Page\n"))
        missing = tmp_path / "missing.yml"

        assert gldq.main([str(tmp_path / "docs"), "--exclude-file", str(missing)]) == 2
        assert "exclude file not found" in capsys.readouterr().err

    def test_invalid_yaml_exclude_file(self, tmp_path, capsys):
        write_doc(tmp_path, "docs/page.md", make_doc("# Page\n"))
        path = self.write_exclude(tmp_path, "exclude: [\n", name="bad.yml")

        assert gldq.main([str(tmp_path / "docs"), "--exclude-file", str(path)]) == 2
        assert "invalid YAML" in capsys.readouterr().err

    def test_unknown_literal_rule_is_an_error(self, tmp_path, capsys):
        write_doc(tmp_path, "docs/page.md", make_doc("# Page\n"))
        path = self.write_exclude(
            tmp_path,
            'exclude:\n  - rules: ["NOPE"]\n    paths: ["docs/**"]\n',
            name="unknown.yml",
        )

        assert gldq.main([str(tmp_path / "docs"), "--exclude-file", str(path)]) == 2
        assert "unknown rule" in capsys.readouterr().err

    def test_missing_paths_is_an_error(self, tmp_path, capsys):
        write_doc(tmp_path, "docs/page.md", make_doc("# Page\n"))
        path = self.write_exclude(
            tmp_path,
            'exclude:\n  - rules: ["EMOJI"]\n',
            name="missing-paths.yml",
        )

        assert gldq.main([str(tmp_path / "docs"), "--exclude-file", str(path)]) == 2
        assert "missing 'paths'" in capsys.readouterr().err

    def test_no_exclude_file_disables_autoload(self, tmp_path, monkeypatch, capsys):
        self.write_exclude(
            tmp_path,
            "exclude:\n"
            '  - rules: ["EMOJI"]\n'
            '    paths: ["docs/reference/releases/release-notes/**"]\n',
        )
        write_doc(
            tmp_path,
            "docs/reference/releases/release-notes/a.md",
            make_release_note(),
        )
        monkeypatch.chdir(tmp_path)

        assert gldq.main(["docs", "--no-exclude-file", "--format", "json"]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["summary"]["excluded"] == 0
        assert any(
            finding["rule"] == "EMOJI" for finding in flatten_json_findings(payload)
        )

    def test_custom_exclude_file(self, tmp_path, capsys):
        path = self.write_exclude(
            tmp_path,
            "exclude:\n"
            '  - rules: ["EMOJI"]\n'
            '    paths: ["docs/reference/releases/release-notes/**"]\n',
            name="custom.yml",
        )
        write_doc(
            tmp_path,
            "docs/reference/releases/release-notes/a.md",
            make_release_note(),
        )

        assert (
            gldq.main(
                [
                    str(tmp_path / "docs"),
                    "--exclude-file",
                    str(path),
                    "--format",
                    "json",
                ]
            )
            == 0
        )
        payload = json.loads(capsys.readouterr().out)
        assert payload["summary"]["excluded"] == 1
        assert payload["summary"]["exclude_file"] == path.as_posix()

    def test_excluded_count_in_text_output(self, tmp_path, monkeypatch, capsys):
        self.write_exclude(
            tmp_path,
            "exclude:\n"
            '  - rules: ["EMOJI"]\n'
            '    paths: ["docs/reference/releases/release-notes/**"]\n',
        )
        write_doc(
            tmp_path,
            "docs/reference/releases/release-notes/a.md",
            make_release_note(),
        )
        monkeypatch.chdir(tmp_path)

        assert gldq.main(["docs"]) == 0
        output = capsys.readouterr().out
        assert "1 finding(s) excluded by .gldq-exclude.yml" in output

    def test_excluded_count_in_github_output(self, tmp_path, monkeypatch, capsys):
        self.write_exclude(
            tmp_path,
            "exclude:\n"
            '  - rules: ["EMOJI"]\n'
            '    paths: ["docs/reference/releases/release-notes/**"]\n',
        )
        write_doc(
            tmp_path,
            "docs/reference/releases/release-notes/a.md",
            make_release_note(),
        )
        monkeypatch.chdir(tmp_path)

        assert gldq.main(["docs", "--format", "github"]) == 0
        output = capsys.readouterr().out
        assert "1 excluded by .gldq-exclude.yml" in output


class TestCli:
    def test_warning_only_exit_codes(self, tmp_path):
        path = write_doc(
            tmp_path,
            "docs/page.md",
            "---\norder: 1\ngithub_org: gardenlinux\ngithub_repo: docs\n---\n\n# Page\n",
        )
        assert gldq.main([str(path), "--no-exclude-file"]) == 0
        assert gldq.main([str(path), "--no-exclude-file", "--strict"]) == 1

    def test_error_exit_code(self, tmp_path):
        path = write_doc(
            tmp_path,
            "docs/page.md",
            make_doc("# \n"),
        )
        assert gldq.main([str(path), "--no-exclude-file"]) == 1

    def test_disable_cli_rule(self, tmp_path):
        path = write_doc(
            tmp_path,
            "docs/guide/index.md",
            make_doc("# Page\n\n✅\n"),
        )
        assert gldq.main([str(path), "--no-exclude-file", "--strict"]) == 1
        assert (
            gldq.main(
                [
                    str(path),
                    "--no-exclude-file",
                    "--strict",
                    "--disable",
                    "EMOJI",
                ]
            )
            == 0
        )

    def test_json_output(self, tmp_path, capsys):
        path = write_doc(
            tmp_path,
            "docs/page.md",
            "---\norder: 1\ngithub_org: gardenlinux\ngithub_repo: docs\n---\n\n# Page\n",
        )
        assert gldq.main([str(path), "--no-exclude-file", "--format", "json"]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["tool"] == "gldq"
        assert payload["name"] == "Garden Linux Docs Quality"
        assert payload["summary"]["files"] == 1
        assert payload["summary"]["excluded"] == 0
        assert isinstance(payload["groups"], list)

    def test_github_output(self, tmp_path, capsys):
        path = write_doc(
            tmp_path,
            "docs/page.md",
            "---\norder: 1\ngithub_org: gardenlinux\ngithub_repo: docs\n---\n\n# Page\n",
        )
        assert gldq.main([str(path), "--no-exclude-file", "--format", "github"]) == 0
        output = capsys.readouterr().out
        assert "::warning" in output
        assert "::notice" in output

    def test_list_rules(self, capsys):
        assert gldq.main(["--list-rules"]) == 0
        output = capsys.readouterr().out
        assert "FM-YAML" in output
        assert "FM-REPO" in output
        assert "RELATED-TOPICS-PRESENT" in output
        assert "CALLOUT-INVALID-TYPE" in output
        assert "CALLOUT-GITHUB-STYLE" in output
        assert "CALLOUT-UNCLOSED" in output

    def test_missing_path_returns_usage_error(self, tmp_path, capsys):
        assert gldq.main([str(tmp_path / "missing"), "--no-exclude-file"]) == 2
        assert "path not found" in capsys.readouterr().err

    def test_single_file_infers_docs_root_for_related_topics(self, tmp_path):
        write_doc(tmp_path, "docs/target.md", make_doc("# Target\n"))
        path = write_doc(
            tmp_path,
            "docs/page.md",
            make_doc(
                "# Page\n",
                frontmatter=(
                    "title: Page\n"
                    "description: Page\n"
                    "github_org: gardenlinux\n"
                    "github_repo: docs\n"
                    "related_topics:\n"
                    "  - /target.md\n"
                ),
            ),
        )
        assert gldq.main([str(path), "--no-exclude-file"]) == 0


class TestCallouts:
    """Tests for VitePress container callout validation."""

    @staticmethod
    def callout_ids(findings: list[gldq.Finding]) -> list[str]:
        """Return only CALLOUT rule IDs from findings."""
        return [rule for rule in rule_ids(findings) if rule.startswith("CALLOUT")]

    def test_valid_containers_pass(self, tmp_path):
        content = make_doc(
            "# Page\n\n"
            ":::tip\nAdvice\n:::\n\n"
            "::: info\nInformation\n:::\n\n"
            "::: tip Spaced\nAdvice\n:::\n\n"
            "::: details Click to expand\nDetails\n:::\n\n"
            ":::warning\nCaveat\n:::\n\n"
            ":::danger\nCritical\n:::\n"
        )
        assert self.callout_ids(find(tmp_path, content)) == []

    def test_false_friends_are_errors(self, tmp_path):
        content = make_doc(
            "# Page\n\n"
            ":::note\nNote\n:::\n\n"
            ":::important\nImportant\n:::\n\n"
            ":::success\nSuccess\n:::\n\n"
            "::: error\nError\n:::\n"
        )
        ids = self.callout_ids(find(tmp_path, content))
        assert ids.count("CALLOUT-INVALID-TYPE") == 4

    def test_github_style_callouts_are_errors(self, tmp_path):
        content = make_doc(
            "# Page\n\n"
            "> [!NOTE]\n"
            "> Text\n\n"
            "> [!IMPORTANT]\n"
            "> Text\n\n"
            "  > [!WARNING]  \n"
        )
        ids = self.callout_ids(find(tmp_path, content))
        assert ids.count("CALLOUT-GITHUB-STYLE") == 3

    def test_fenced_examples_are_ignored(self, tmp_path):
        content = make_doc(
            "# Page\n\n"
            "```markdown\n"
            ":::note\n"
            "> [!NOTE]\n"
            ":::\n"
            "```\n"
        )
        assert self.callout_ids(find(tmp_path, content)) == []

    def test_indented_container_in_list_passes(self, tmp_path):
        content = make_doc(
            "# Page\n\n"
            "- item\n\n"
            "  ::: tip\n"
            "  Advice\n"
            "  :::\n"
        )
        assert self.callout_ids(find(tmp_path, content)) == []

    def test_nested_containers_balance(self, tmp_path):
        content = make_doc(
            "# Page\n\n"
            "::: details\n"
            "Outer\n\n"
            ":::: tip\n"
            "Inner\n"
            "::::\n\n"
            ":::\n"
        )
        assert "CALLOUT-UNCLOSED" not in self.callout_ids(find(tmp_path, content))

    def test_unclosed_container_is_an_error(self, tmp_path):
        content = make_doc("# Page\n\n:::tip\nAdvice\n")
        findings = [
            finding
            for finding in find(tmp_path, content)
            if finding.rule_id == "CALLOUT-UNCLOSED"
        ]
        assert len(findings) == 1
        assert findings[0].line == 10

    def test_suppression_comment_is_honored(self, tmp_path):
        content = make_doc(
            "# Page\n\n"
            "<!-- gldq: disable-next-line CALLOUT-GITHUB-STYLE -->\n"
            "> [!NOTE]\n"
            "> Text\n"
        )
        assert "CALLOUT-GITHUB-STYLE" not in self.callout_ids(find(tmp_path, content))

    def test_path_matches_wildcard_and_dot_prefix(self):
        assert gldq._path_matches(
            "reference/features/a.md", "./reference/features/**"
        )
        assert not gldq._path_matches(
            "docs/reference/other/a.md", "./reference/features/**"
        )


class TestGrouping:
    def _finding(self, path, group, rule="FM-TITLE", line=1, column=1):
        return gldq.Finding(
            rule_id=rule,
            severity=gldq.WARNING,
            path=Path(path),
            line=line,
            column=column,
            message="message",
            group=group,
        )

    def test_group_is_derived_from_frontmatter(self, tmp_path):
        findings = find(
            tmp_path,
            make_doc(
                "# Page\n",
                frontmatter=(
                    "title: Page\n"
                    "description: A page\n"
                    "github_org: gardenlinux\n"
                    "github_repo: builder\n"
                ),
            ),
        )
        assert findings
        assert all(f.group == "gardenlinux/builder" for f in findings)

    def test_group_defaults_to_no_repo(self, tmp_path):
        findings = find(
            tmp_path,
            make_doc("# Page\n", frontmatter="title: Page\ndescription: A page\n"),
        )
        assert findings
        assert all(f.group == gldq.NO_REPO_GROUP for f in findings)

    def test_partial_frontmatter_falls_back_to_no_repo(self, tmp_path):
        findings = find(
            tmp_path,
            make_doc(
                "# Page\n",
                frontmatter=(
                    "title: Page\n"
                    "description: A page\n"
                    "github_org: gardenlinux\n"
                ),
            ),
        )
        assert findings
        assert all(f.group == gldq.NO_REPO_GROUP for f in findings)

    def test_group_findings_orders_groups_and_files(self):
        findings = [
            self._finding("docs/z.md", "gardenlinux/builder"),
            self._finding("docs/a.md", "gardenlinux/builder"),
            self._finding("docs/b.md", "gardenlinux/daily"),
            self._finding("docs/c.md", gldq.NO_REPO_GROUP),
        ]
        grouped = gldq._group_findings(findings)
        labels = [label for label, _ in grouped]
        assert labels == [
            "gardenlinux/builder",
            "gardenlinux/daily",
            gldq.NO_REPO_GROUP,
        ]
        builder_files = [path.as_posix() for path, _ in grouped[0][1]]
        assert builder_files == ["docs/a.md", "docs/z.md"]

    def test_group_findings_keeps_sort_key_within_file(self):
        findings = [
            self._finding("docs/a.md", "org/repo", rule="CODE-LANG", line=5),
            self._finding("docs/a.md", "org/repo", rule="FM-TITLE", line=1),
        ]
        grouped = gldq._group_findings(findings)
        _, file_findings = grouped[0][1][0]
        assert [f.line for f in file_findings] == [1, 5]

    def test_text_output_is_grouped(self, tmp_path, monkeypatch, capsys):
        write_doc(
            tmp_path,
            "docs/a.md",
            make_doc(
                "# A\n",
                frontmatter=(
                    "title: A\n"
                    "description: Page A\n"
                    "github_org: gardenlinux\n"
                    "github_repo: builder\n"
                ),
            ),
        )
        write_doc(
            tmp_path,
            "docs/b.md",
            make_doc("# B\n", frontmatter="title: B\ndescription: Page B\n"),
        )
        monkeypatch.chdir(tmp_path)
        assert gldq.main(["docs", "--no-exclude-file"]) != 2
        output = capsys.readouterr().out
        assert "## gardenlinux/builder" in output
        assert f"## {gldq.NO_REPO_GROUP}" in output
        assert output.index("## gardenlinux/builder") < output.index(
            f"## {gldq.NO_REPO_GROUP}"
        )

    def test_json_output_is_grouped(self, tmp_path, monkeypatch, capsys):
        write_doc(
            tmp_path,
            "docs/a.md",
            make_doc(
                "# A\n",
                frontmatter=(
                    "title: A\n"
                    "description: Page A\n"
                    "github_org: gardenlinux\n"
                    "github_repo: builder\n"
                ),
            ),
        )
        write_doc(
            tmp_path,
            "docs/b.md",
            make_doc("# B\n", frontmatter="title: B\ndescription: Page B\n"),
        )
        monkeypatch.chdir(tmp_path)
        gldq.main(["docs", "--no-exclude-file", "--format", "json"])
        payload = json.loads(capsys.readouterr().out)
        assert "findings" not in payload
        labels = [group["group"] for group in payload["groups"]]
        assert labels == ["gardenlinux/builder", gldq.NO_REPO_GROUP]
        builder = payload["groups"][0]["files"][0]
        assert builder["path"] == "docs/a.md"
        assert "path" not in builder["findings"][0]

    def test_github_output_wraps_groups(self, tmp_path, monkeypatch, capsys):
        write_doc(
            tmp_path,
            "docs/b.md",
            make_doc("# B\n", frontmatter="title: B\ndescription: Page B\n"),
        )
        monkeypatch.chdir(tmp_path)
        gldq.main(["docs", "--no-exclude-file", "--format", "github"])
        output = capsys.readouterr().out
        assert f"::group::{gldq.NO_REPO_GROUP}" in output
        assert "::endgroup::" in output


class TestRepo:
    def _no_repo_doc(self, body: str = "# Page\n") -> str:
        return make_doc(body, frontmatter="title: Page\ndescription: A page\n")

    def test_missing_repo_fields_is_an_error(self, tmp_path):
        findings = find(tmp_path, self._no_repo_doc())
        repo_findings = [f for f in findings if f.rule_id == "FM-REPO"]
        assert len(repo_findings) == 1
        assert repo_findings[0].severity == gldq.ERROR
        assert repo_findings[0].group == gldq.NO_REPO_GROUP

    def test_both_repo_fields_present_passes(self, tmp_path):
        findings = find(tmp_path, make_doc("# Page\n"))
        assert "FM-REPO" not in rule_ids(findings)

    def test_missing_only_repo_is_an_error(self, tmp_path):
        content = make_doc(
            "# Page\n",
            frontmatter=(
                "title: Page\ndescription: A page\ngithub_org: gardenlinux\n"
            ),
        )
        assert "FM-REPO" in rule_ids(find(tmp_path, content))

    def test_home_page_is_exempt(self, tmp_path):
        content = "---\nlayout: home\nhero:\n  name: Test\n---\n\nWelcome.\n"
        assert "FM-REPO" not in rule_ids(find(tmp_path, content))

    def test_excluded_page_is_exempt(self, tmp_path):
        content = make_doc(
            "# Page\n",
            frontmatter="title: Page\ndescription: A page\nexclude: true\n",
        )
        assert "FM-REPO" not in rule_ids(find(tmp_path, content))

    def test_missing_repo_fails_run_as_error(self, tmp_path, monkeypatch, capsys):
        write_doc(tmp_path, "docs/page.md", self._no_repo_doc())
        monkeypatch.chdir(tmp_path)
        assert gldq.main(["docs", "--no-exclude-file"]) == 1
        output = capsys.readouterr().out
        assert f"## {gldq.NO_REPO_GROUP}" in output
        assert "FM-REPO" in output
