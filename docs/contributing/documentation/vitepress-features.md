---
title: "VitePress Features and Customizations"
description: "Guide to custom components, Mermaid diagrams, and VitePress features for documentation writers"
order: 11
related_topics:
  - /contributing/documentation/documentation_workflow.md
  - /contributing/documentation/writing_good_docs.md
  - /contributing/documentation/aggregation-architecture.md
  - /contributing/documentation/adding-repos.md
  - /contributing/documentation/working-locally.md
  - /contributing/documentation/ci-architecture.md
  - /contributing/documentation/ci-workflows-reference.md
  - /contributing/documentation/configuration.md
  - /contributing/documentation/technical.md
  - /contributing/documentation/testing.md
---

# VitePress Features and Customizations

This guide documents the VitePress features and customizations available for writing Garden Linux documentation. It covers custom components, diagram support, and front-matter extensions.

## Custom Components

Garden Linux documentation includes two custom Vue components that are registered globally in the VitePress theme.

### SectionIndex Component

The `<SectionIndex />` component automatically generates a table of contents for the current documentation section. It reads the sidebar configuration, finds the section matching the current page, and displays its child pages as a grid.

**When to use:**

- On section index pages (e.g., `tutorials/index.md`, `how-to/index.md`)
- Any page that should display links to its child pages

**How it works:**

1. Reads the sidebar configuration from the VitePress theme
2. Finds the sidebar group matching the current directory
3. Extracts child items and their descriptions from front-matter
4. Displays them in a responsive grid layout

**Configuration:**

Use the `overviewDescriptions` front-matter field to control whether child page descriptions are shown:

```yaml
---
title: How-To Guides
overviewDescriptions: true # Show descriptions (default)
---
```

Set to `false` to hide descriptions:

```yaml
---
title: Quick Reference
overviewDescriptions: false # Hide descriptions
---
```

**Example usage:**

```markdown
---
title: How-To Guides
description: Step-by-step guides for common Garden Linux tasks
---

# How-To Guides

How-to guides are **task-oriented** directions that guide you through solving a specific problem or achieving a particular goal. They assume you have some familiarity with Garden Linux and focus on practical solutions.

<SectionIndex />
```

### RelatedTopics Component

The `<RelatedTopics />` component displays a curated list of related documentation pages at the bottom of content. It validates that all linked pages exist during the build process.

**When to use:**

- At the end of content pages
- To guide readers to next steps or related documentation

**How it works:**

1. Reads the `related_topics` array from the page's front-matter
2. Resolves file paths to URLs
3. Extracts titles and descriptions from linked pages
4. Displays them as a formatted list with links

**Configuration:**

Define related topics in the page's front-matter using absolute paths:

```yaml
---
title: Building Images
related_topics:
  - /how-to/choosing-flavors.md
  - /how-to/getting-images.md
  - /reference/features.md
---
```

**Example usage:**

```markdown
---
title: Building Images
description: How to build Garden Linux images
related_topics:
  - /how-to/choosing-flavors.md
  - /how-to/getting-images.md
---

# Building Images

<content here>

<RelatedTopics />
```

## Mermaid Diagrams

Garden Linux documentation supports [Mermaid](https://mermaid.js.org/) diagrams through the `vitepress-mermaid-renderer` plugin. This enables flowcharts, Gantt charts, sequence diagrams, and more.

**When to use:**

- Visualizing timelines and release schedules
- Showing process flows and architectures
- Displaying complex relationships

**How it works:**
The plugin automatically renders code blocks marked with `mermaid` as diagrams. It injects a shared set of semantic class definitions into every diagram at build time and supports both light and dark mode — node colors switch automatically when the reader toggles the theme.

**Syntax:**

````markdown
```mermaid
graph TD
    A[Start] --> B{Decision}
    B -->|Yes| C[Continue]
    B -->|No| D[Stop]
```
````

**Gantt chart example:**

````markdown
```mermaid
gantt
    title Release Schedule
    dateFormat YYYY-MM-DD
    section Development
    Feature A :2024-01-01, 30d
    Feature B :2024-01-15, 30d
    section Testing
    Integration Tests :after Feature A, 14d
```
````

### Mermaid styling

Flowchart nodes are styled using five canonical semantic class names. Color values for both light mode and dark mode are defined in `docs/.vitepress/theme/style.css` — **do not write `classDef` or `style X fill:` lines in diagram source**. Use only `class` assignment statements. Every node must be assigned one of these five classes.

| Class name | Semantic use                                        |
|------------|-----------------------------------------------------|
| `decision` | conditional branches, diamond nodes                 |
| `input`    | triggers, external sources                          |
| `process`  | intermediate work, retries                          |
| `output`   | successful terminal states, published artefacts     |
| `neutral`  | sequential steps with no special semantic role      |

**Example:**

````markdown
```mermaid
flowchart TD
    Boot[Power On] --> Check{Feature present?}
    Check -->|Yes| Install[Install to disk]
    Check -->|No| Live[Live boot only]
    Install --> Done[System running]

    class Boot neutral
    class Check decision
    class Install output
    class Live process
    class Done neutral
```
````

**Real-world example:**
See the [Maintained Releases](/reference/releases/maintained-releases) page for a complete Gantt chart showing release maintenance phases.

## Theme-Adaptive Images

Some diagrams and illustrations need different versions for light and dark mode — for example, SVGs with dark strokes that are invisible on a dark background.

Append `#light-mode-only` or `#dark-mode-only` to the image path. The VitePress theme CSS hides the wrong variant automatically.

**Syntax:**

```markdown
![Description of the image](image-light.svg#light-mode-only)
![Description of the image](image-dark.svg#dark-mode-only)
```

Both lines must use identical alt text so screen readers and search engines see a single logical image.

**When to use:**

- SVG diagrams with strokes or text that rely on a white or black background
- Any image where contrast or legibility differs significantly between themes

**Naming convention:** suffix the dark variant's filename with `_dark` before the extension (e.g. `diagram.svg` / `diagram_dark.svg`). Keep both files in the same `.media/` directory as the page.

**Real-world example:**
See [Boot Modes](/explanation/boot-modes) for SVG diagrams that use both variants.

## Container Syntax (Callouts)

VitePress supports special container blocks for callouts and highlighted content. Garden Linux documentation uses these throughout.

**When to use:**

- `:::tip` - Recommendations and helpful hints
- `:::warning` - Important caveats or potential issues
- `:::danger` - Critical warnings about data loss, security, etc.
- `:::info` - Informational notes
- `:::details` - Collapsible content for optional information

**Examples:**

```markdown
:::tip
Use rootless Podman for building images. It provides better security
and doesn't require special privileges.
:::

:::warning
Provide at least 8 GiB of memory to the container runtime. Insufficient
memory may cause builds to fail silently.
:::

:::danger
Do not use the production keyring for testing. Always use test keys
to avoid accidentally publishing unverified packages.
:::

:::details Click to expand for technical details
The build process uses the following steps:

1. Initialize container with base image
2. Apply feature layers
3. Apply customization
4. Create final image

Each step creates an intermediate container.
:::

:::info
This feature requires Garden Linux version 2150.0.0 or later.
:::
```

**Best practices:**

- Use `:::tip` for recommendations and best practices
- Use `:::warning` for important caveats
- Use `:::danger` sparingly and only for critical warnings
- Use `:::details` for optional advanced content that most readers don't need

## Front-matter Fields

Garden Linux documentation uses several front-matter fields for configuration.

### Component Configuration

**`overviewDescriptions`** (boolean, default: true)

Controls whether the `<SectionIndex />` component displays descriptions for child pages. Set to `false` on an index page to hide descriptions in its section listing.

**`related_topics`** (array of strings)

Defines related pages for the `<RelatedTopics />` component. Each entry is an absolute file path (starting with `/`) to another markdown file. All paths must exist or the build will fail with an error.

### Display Configuration

**`title`** (string, required)

The page title. Used in navigation, search results, and as the default heading.

**`description`** (string)

A short summary of the page content. Used as the meta description for SEO and displayed by `<SectionIndex />` for child page listings.

**`order`** (number, default: 999)

Controls sort order in the sidebar and section listings. Lower numbers appear first. Use this to create logical groupings (e.g., `0` for intro, `10` for basics, `100` for advanced).

### Aggregated Content Fields

For content aggregated from external repositories, these fields enable proper placement and "Edit on GitHub" links. For complete details on aggregation configuration, see [Documentation Aggregation Configuration Reference](configuration.md).

**`github_target_path`** (string)

Target location in the docs directory for aggregated content.

**`github_instance`** (string, default: "https://github.com")

Base URL of the GitHub instance.

**`github_org`** (string)

GitHub organization name.

**`github_repo`** (string)

Repository name.

**`github_source_path`** (string)

Original file path in the source repository.

**`github_branch`** (string, default: "main")

Branch name for edit links.

## Best Practices

### Component Usage

- Always use `<SectionIndex />` on section index pages (tutorials/, how-to/, explanation/, reference/)
- Place `<RelatedTopics />` at the end of content pages, before any closing sections
- Keep `related_topics` lists focused (3-5 items is ideal)
- Write clear, concise `description` fields for better section overviews

### Mermaid Diagrams

- Use for timelines, processes, and complex relationships
- Keep diagrams simple and focused
- Test in both light and dark mode (use the preview)
- Don't overuse — diagrams should add clarity, not replace text
- Use the five canonical class names (`decision`, `input`, `process`, `output`, `neutral`) for node colors — every node must be assigned one
- Do not write `classDef` declarations or `style X fill:` lines in diagram source

### Containers/Callouts

- Use `:::tip` for recommendations and best practices
- Use `:::warning` for important caveats that readers should know
- Use `:::danger` only for critical warnings about data loss, security, or system damage
- Use `:::info` sparingly for contextual information
- Use `:::details` for optional advanced content that most readers can skip

### Front-matter

- Always include `title` and `description` on every page
- Use `order` to control logical flow in sections
- Validate that `related_topics` links exist before committing
- Keep descriptions under 160 characters for optimal SEO

## Related Topics

<RelatedTopics />
