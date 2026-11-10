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
    body: str, frontmatter: str = "title: Page\ndescription: A test page\n"
) -> str:
    """Build a markdown document with default valid front matter."""
    return f"---\n{frontmatter}---\n\n{body}"


def make_release_note(body: str = "Chart 📊\n") -> str:
    """Build a valid release note document with a trailing RelatedTopics."""
    return make_doc(
        f"# Release\n\n{body}\n<RelatedTopics />\n",
        frontmatter="title: Release\ndescription: Release notes\nrelated_topics: []\n",
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
        assert payload["findings"] == []

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
        for finding in payload["findings"]:
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
        assert any(finding["rule"] == "EMOJI" for finding in payload["findings"])

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
        path = write_doc(tmp_path, "docs/page.md", "---\norder: 1\n---\n\n# Page\n")
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
        path = write_doc(tmp_path, "docs/page.md", "---\norder: 1\n---\n\n# Page\n")
        assert gldq.main([str(path), "--no-exclude-file", "--format", "json"]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["tool"] == "gldq"
        assert payload["name"] == "Garden Linux Docs Quality"
        assert payload["summary"]["files"] == 1
        assert payload["summary"]["excluded"] == 0
        assert isinstance(payload["findings"], list)

    def test_github_output(self, tmp_path, capsys):
        path = write_doc(tmp_path, "docs/page.md", "---\norder: 1\n---\n\n# Page\n")
        assert gldq.main([str(path), "--no-exclude-file", "--format", "github"]) == 0
        output = capsys.readouterr().out
        assert "::warning" in output
        assert "::notice" in output

    def test_list_rules(self, capsys):
        assert gldq.main(["--list-rules"]) == 0
        output = capsys.readouterr().out
        assert "FM-YAML" in output
        assert "RELATED-TOPICS-PRESENT" in output

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
                    "related_topics:\n"
                    "  - /target.md\n"
                ),
            ),
        )
        assert gldq.main([str(path), "--no-exclude-file"]) == 0
