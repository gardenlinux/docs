"""Constants and configuration for release documentation generation."""

# Garden Linux color palette for Mermaid Gantt charts
GANTT_THEME = """%%{init: {'theme':'base', 'themeVariables': {
  'primaryColor':'#30a46c',
  'primaryTextColor':'#fff',
  'primaryBorderColor':'#18794e',
  'lineColor':'#30a46c',
  'gridColor':'#30a46c',
  'textColor':'#009f76',
  'taskTextOutsideColor':'#009f76',
  'taskTextLightColor':'#fff',
  'taskTextDarkColor':'#fff',
  'labelTextColor':'#009f76',
  'todayLineColor':'#009f76',
  'sectionBkgColor':'#30a46c',
  'sectionBkgColor2':'#299764',
  'altSectionBkgColor':'#18794e',
  'taskBkgColor':'#30a46c',
  'taskBorderColor':'#18794e',
  'taskTextColor':'#fff',
  'activeTaskBkgColor':'#30a46c',
  'activeTaskBorderColor':'#18794e',
  'critBkgColor':'#087254',
  'critBorderColor':'#065a41',
  'doneTaskBkgColor':'#009f76',
  'doneTaskBorderColor':'#087254'
}}}%%"""

# GitHub URLs
GITHUB_BASE_URL = "https://github.com/gardenlinux/gardenlinux"
RELEASES_TAG_URL = f"{GITHUB_BASE_URL}/releases/tag"
COMMITS_URL = f"{GITHUB_BASE_URL}/commit"

# Lifecycle documentation anchor links
LIFECYCLE_LINKS = {
    "standard": "release-lifecycle.md#standard-maintenance",
    "extended": "release-lifecycle.md#extended-maintenance",
    "eol": "release-lifecycle.md#end-of-maintenance",
    "lts": "release-lifecycle.md#long-term-support-lts",
}
