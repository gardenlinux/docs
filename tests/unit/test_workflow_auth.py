"""Public workflow defaults and optional enterprise credential wiring."""

from pathlib import Path

import yaml

WORKFLOWS = Path(__file__).resolve().parents[2] / ".github" / "workflows"


def load_workflow(name):
    # Actions uses YAML 1.2; BaseLoader preserves the `on` key as a string.
    return yaml.load((WORKFLOWS / name).read_text(), Loader=yaml.BaseLoader)


def test_public_checks_use_builtin_read_only_token_and_preflight():
    workflow = load_workflow("docs-checks.yml")
    aggregate = workflow["jobs"]["aggregate"]
    assert aggregate["runs-on"] == "ubuntu-24.04"
    assert aggregate["permissions"] == {"contents": "read"}
    steps = {step.get("name"): step for step in aggregate["steps"]}
    assert steps["Verify aggregation authentication"]["run"] == (
        "python3 src/aggregate.py --check-auth"
    )
    for name in ("Verify aggregation authentication", "Run aggregate"):
        env = steps[name]["env"]
        assert env["GITHUB_TOKEN"] == "${{ github.token }}"
        assert env["GH_ENTERPRISE_HOST"] == "${{ inputs.enterprise-host }}"
        assert env["GH_ENTERPRISE_TOKEN"] == (
            "${{ inputs.enterprise-host && secrets.GH_ENTERPRISE_TOKEN || '' }}"
        )
    checkout = aggregate["steps"][0]["with"]
    assert checkout["repository"] == "gardenlinux/docs"
    assert checkout["persist-credentials"] == "false"


def test_enterprise_credentials_are_optional_in_both_reusable_workflows():
    for name in ("docs-checks.yml", "aggregated-repo-docs.yml"):
        call = load_workflow(name)["on"]["workflow_call"]
        assert call["inputs"]["enterprise-host"]["required"] == "false"
        assert call["inputs"]["enterprise-host"]["default"] == ""
        assert call["secrets"]["GH_ENTERPRISE_TOKEN"]["required"] == "false"


def test_orchestrator_forwards_enterprise_configuration_explicitly():
    checks = load_workflow("aggregated-repo-docs.yml")["jobs"]["docs-checks"]
    assert checks["with"]["enterprise-host"] == "${{ inputs.enterprise-host }}"
    assert checks["secrets"]["GH_ENTERPRISE_TOKEN"] == (
        "${{ inputs.enterprise-host && secrets.GH_ENTERPRISE_TOKEN || '' }}"
    )


def test_enterprise_guard_keeps_public_forks_available():
    guard = load_workflow("docs-checks.yml")["jobs"]["aggregate"]["if"]
    assert "github.event_name != 'pull_request_target'" in guard
    assert "!inputs.enterprise-host" in guard
    assert "github.event_name != 'pull_request'" in guard
    assert "github.event.pull_request.head.repo.full_name == github.repository" in guard
