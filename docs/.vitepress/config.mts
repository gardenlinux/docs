import { readdir, readFile } from "fs/promises";
import matter from "gray-matter";
import { join } from "path";
import { defineConfig } from "vitepress";
import { generateDocumentationSidebar } from "./sidebar.js";
import { mermaidClassDefs } from "./plugins/mermaid-classdefs.js";

// Get base URL from environment variable (for GitHub Pages deployment)
const base = process.env.BASE_URL || "/";

// Generate sidebar dynamically at build time
const documentationSidebar = generateDocumentationSidebar();

// Build a map of URL -> { title, description, url } for all markdown pages
async function buildPageMap(pagesDir: string): Promise<Record<string, { title: string; description: string; url: string }>> {
  const map: Record<string, { title: string; description: string; url: string }> = {};
  const skipDirs = ['.vitepress', 'node_modules', 'dist', '_build', '.venv'];

  async function scanDir(dir: string, basePath: string = "") {
    const dirName = dir.split('/').pop() || '';
    if (skipDirs.includes(dirName)) {
      return;
    }

    try {
      const entries = await readdir(dir, { withFileTypes: true });
      for (const entry of entries) {
        const fullPath = join(dir, entry.name);
        if (entry.isDirectory()) {
          await scanDir(fullPath, basePath + entry.name + "/");
        } else if (entry.name.endsWith(".md")) {
          try {
            const content = await readFile(fullPath, "utf-8");
            const { data } = matter(content);
            let url = basePath + entry.name.replace(/\.md$/, ".html");
            url = url.replace(/\/index\.html$/, "/");
            if (!url.startsWith("/")) {
              url = "/" + url;
            }
            map[url] = {
              title: data.title || entry.name.replace(/\.md$/, ""),
              description: data.description || "",
              url,
            };
          } catch (e) {
            // Skip files that can't be read
          }
        }
      }
    } catch (e) {
      // Skip directories that can't be read
    }
  }

  await scanDir(pagesDir);
  return map;
}

// Normalize a related_topics path to a URL
function normalizeUrl(ref: string): string {
  // Remove .md extension if present
  let url = ref.replace(/\.md$/, "");
  // If no extension and no trailing slash, add .html
  if (!url.endsWith("/") && !url.includes(".")) {
    url = url + ".html";
  }
  // Handle /index paths
  url = url.replace(/\/index\.html$/, "/");
  // Ensure leading slash
  if (!url.startsWith("/")) {
    url = "/" + url;
  }
  return url;
}

// https://vitepress.dev/reference/site-config
export default defineConfig({
  base,
  title: "Garden Linux",
  description: "Purpose-built Linux for cloud-native workloads",
  markdown: {
    config: (md) => md.use(mermaidClassDefs),
  },
  ignoreDeadLinks: [
    // Ignore dead links in legacy documentation
    /\/how-to\/troubleshooting\//,
    /localhost/,
    // Ignore section index links without trailing slash (VitePress internal)
    /\/tutorials\/index$/,
    /\/how-to\/index$/,
    /\/explanation\/index$/,
    /\/reference\/index$/,
    /\/contributing\/index$/,
    // Ignore specific release notes pages that don't exist
    /release-notes\/archived\/1592-17/,
    /release-notes\/archived\/1877-11/,
    /release-notes\/archived\/1877-12/,
    // Ignore LICENSE files (e.g. from aggregated repos)
    /LICENSE$/,
    // Ignore broken links inside features for now
    /features\/_ephemeral/,
    /features\/_tpm2/,
    /features\/bare/,
    /features\/libc/,
    /test\//,
    /tests\//,
    /samples\//,
    /boot_modes/,
    /cis\//,
    /firewall\//,
  ],
  head: [
    [
      "link",
      {
        rel: "icon",
        type: "image/svg+xml",
        href: `/gardenlinux-logo.svg`,
      },
    ],
    ["meta", { name: "theme-color", content: "#009f76" }],
    ["meta", { property: "og:type", content: "website" }],
    ["meta", { property: "og:site_name", content: "Garden Linux" }],
    [
      "meta",
      {
        property: "og:image",
        content:
          "https://raw.githubusercontent.com/gardenlinux/gardenlinux/main/logo/gardenlinux-logo-black-text.svg",
      },
    ],
    ["meta", { property: "og:url", content: "https://gardenlinux.io/" }],
  ],
  themeConfig: {
    // https://vitepress.dev/reference/default-theme-config
    outline: {
      level: [2, 3],
      label: 'On this page'
    },
    logo: {
      light: `/gardenlinux-logo.svg`,
      dark: `/gardenlinux-logo.svg`,
    },
    nav: [
      { text: "Start Here", link: "/" },
      {
        text: "Documentation",
        items: [
          {
            text: "Introduction",
            link: "/introduction/",
          },
          {
            text: "Tutorials",
            link: "/tutorials/",
          },
          {
            text: "How-to Guides",
            link: "/how-to/",
          },
          {
            text: "Explanation",
            link: "/explanation/",
          },
          {
            text: "Reference",
            link: "/reference/",
          },
          {
            text: "Contributing",
            link: "/contributing/",
          },
        ],
      },
      // {
      //   text: "Legacy Docs",
      //   items: [
      //     {
      //       text: "Garden Linux",
      //       link: "/projects/gardenlinux/introduction/index",
      //     },
      //     { text: "Builder", link: "/projects/builder/getting_started" },
      //     {
      //       text: "Python Library",
      //       link: "/projects/python-gardenlinux-lib/index",
      //     },
      //   ],
      // },
      // { text: "Contributing", link: "/contributing/" },
    ],

    // footer: {
    //   message: "Built with 💚 by the Gardenlinux Team.",
    //   copyright: "Copyright © 2026-present",
    // },

    sidebar: documentationSidebar,

    socialLinks: [
      { icon: "github", link: "https://github.com/gardenlinux", ariaLabel: "Source Code" },
      { icon: {
        svg:
            `
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-bug" viewBox="0 0 16 16">
                <path d="M4.355.522a.5.5 0 0 1 .623.333l.291.956A5 5 0 0 1 8 1c1.007 0 1.946.298 2.731.811l.29-.956a.5.5 0 1 1 .957.29l-.41 1.352A5 5 0 0 1 13 6h.5a.5.5 0 0 0 .5-.5V5a.5.5 0 0 1 1 0v.5A1.5 1.5 0 0 1 13.5 7H13v1h1.5a.5.5 0 0 1 0 1H13v1h.5a1.5 1.5 0 0 1 1.5 1.5v.5a.5.5 0 1 1-1 0v-.5a.5.5 0 0 0-.5-.5H13a5 5 0 0 1-10 0h-.5a.5.5 0 0 0-.5.5v.5a.5.5 0 1 1-1 0v-.5A1.5 1.5 0 0 1 2.5 10H3V9H1.5a.5.5 0 0 1 0-1H3V7h-.5A1.5 1.5 0 0 1 1 5.5V5a.5.5 0 0 1 1 0v.5a.5.5 0 0 0 .5.5H3c0-1.364.547-2.601 1.432-3.503l-.41-1.352a.5.5 0 0 1 .333-.623M4 7v4a4 4 0 0 0 3.5 3.97V7zm4.5 0v7.97A4 4 0 0 0 12 11V7zM12 6a4 4 0 0 0-1.334-2.982A3.98 3.98 0 0 0 8 2a3.98 3.98 0 0 0-2.667 1.018A4 4 0 0 0 4 6z"/>
            </svg>
            `
      }, link: "https://github.com/gardenlinux/gardenlinux/issues/new/choose", ariaLabel: "Report a Bug" }
    ],

    editLink: {
      pattern: ({ filePath, frontmatter }) => {
        // If page has GitHub metadata from aggregated content, use it
        const instance = ((frontmatter.github_instance as string | undefined) || "https://github.com").replace(/\/$/, "");
        const github_org = frontmatter.github_org || "gardenlinux";
        const github_repo = frontmatter.github_repo || "docs";
        const branch = frontmatter.github_branch || "main";
        const github_source_path = frontmatter.github_source_path || `docs/${filePath}`;
        return `${instance}/${github_org}/${github_repo}/edit/${branch}/${github_source_path}`;
      },
      text: "Edit this page on GitHub",
    },

    search: {
      provider: "local",
    },
  },
  async transformPageData(pageData, { siteConfig }) {
    // Build page map - NOT cached globally due to VitePress config execution issues
    const pagesDir = siteConfig.root;
    const pageMap = await buildPageMap(pagesDir);

    // Resolve related_topics if present
    const relatedTopics = pageData.frontmatter?.related_topics;
    if (relatedTopics && Array.isArray(relatedTopics)) {
      // Get current page URL
      let currentPageUrl = "/" + pageData.relativePath.replace(/\.md$/, ".html");
      currentPageUrl = currentPageUrl.replace(/\/index\.html$/, "/");

      pageData.frontmatter.resolvedRelated = relatedTopics
        .map((ref: string) => {
          // Normalize the file path to URL
          const url = normalizeUrl(ref);
          const page = pageMap[url];

          // ERROR: File not found
          if (!page) {
            throw new Error(
              `RelatedTopics: File not found "${ref}" (resolved to "${url}") in ${pageData.relativePath}`
            );
          }

          // ERROR: Title missing in frontmatter
          if (!page.title) {
            throw new Error(
              `RelatedTopics: File "${ref}" has no title in frontmatter (in ${pageData.relativePath})`
            );
          }

          // OK: Description is optional
          return {
            url,
            title: page.title,
            description: page.description || "",
          };
        })
        .filter((page) => page.url !== currentPageUrl); // Remove self-references
    }
  },
});
