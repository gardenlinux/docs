import { generateSidebar } from 'vitepress-sidebar';
import fs from 'fs';
import path from 'path';
import matter from 'gray-matter';

export function generateDocumentationSidebar(): any {
  const sidebar = generateSidebar([{
    documentRootPath: 'docs',
    scanStartPath: '',
    resolvePath: '/',
    collapsed: true,
    useTitleFromFileHeading: true,
    useTitleFromFrontmatter: true,
    useFolderLinkFromIndexFile: true,
    useFolderTitleFromIndexFile: true,
    sortMenusByFrontmatterOrder: true,
    frontmatterOrderDefaultValue: 999,
    prefixSeparator: '/',
    excludeFilesByFrontmatterFieldName: 'exclude',
  }]);
  
  // Post-process sidebar to fix folder titles and extract descriptions from frontmatter
  const fixFolderTitles = (items: any[], depth = 0): any[] => {
    return items.map((item, index) => {
      try {
        let frontmatter: Record<string, any> | undefined;

        // Recursively fix nested items first (works regardless of whether this item has a link)
        if (item.items && Array.isArray(item.items)) {
          item.items = fixFolderTitles(item.items, depth + 1);
        }

        // Skip processing if no link (section headers, collapsed groups, etc.)
        if (!item.link || typeof item.link !== 'string') {
          console.log(`[sidebar] Skipping item without link: text="${item.text}", hasItems=${!!item.items}`);
          return item;
        }

        // Fix folder links for proper active state detection
        // VitePress normalizes "/tutorials/index.md" to "/tutorials/" (WITH trailing slash)
        // The regex /(?:(^|\/)index)?\.(?:md|html)$/ captures the "/" before "index"
        // So we must ensure sidebar links for index pages also have trailing slashes
        
        // IMPORTANT: Don't add leading slash - VitePress adds base path
        // If we have "/tutorials/", VitePress makes it "//tutorials/" (external link!)
        
        if (item.link.endsWith('/index.md')) {
          // Convert "tutorials/index.md" to "tutorials/"
          item.link = item.link.replace(/\/index\.md$/, '/');
        } else if (item.link.startsWith('/')) {
          // Remove leading slash that vitepress-sidebar added
          item.link = item.link.substring(1);
        }
        
        // Now check if link needs trailing slash
        if (!item.link.endsWith('/')) {
          const possibleIndexPath = path.join('docs', item.link, 'index.md');
          if (fs.existsSync(possibleIndexPath)) {
            // Add trailing slash: "tutorials" to "tutorials/"
            item.link = item.link + '/';
          }
        }

        // Check if this is a folder with index.md to read its frontmatter
        const possibleIndexPath = path.join('docs', item.link, 'index.md');
        if (fs.existsSync(possibleIndexPath)) {
          try {
            const content = fs.readFileSync(possibleIndexPath, 'utf-8');
            frontmatter = matter(content).data;
            if (frontmatter?.title) {
              item.text = frontmatter.title;
            }
          } catch (err) {
            // Ignore errors, keep the original text
          }
        } else if (item.link.endsWith('.md')) {
          // This is a file link - read frontmatter from the page
          const pagePath = path.join('docs', item.link);
          if (fs.existsSync(pagePath)) {
            try {
              const content = fs.readFileSync(pagePath, 'utf-8');
              frontmatter = matter(content).data;
            } catch (err) {
              // Ignore errors
            }
          }
        } else if (!item.link.includes('.')) {
          // Link has no extension (vitepress-sidebar strips .md for leaf pages)
          // Try appending .md to find the source file
          const pagePath = path.join('docs', item.link + '.md');
          if (fs.existsSync(pagePath)) {
            try {
              const content = fs.readFileSync(pagePath, 'utf-8');
              frontmatter = matter(content).data;
            } catch (err) {
              // Ignore errors
            }
          }
        }

        if (frontmatter?.description) {
          item.description = frontmatter.description;
        }

        return item;
      } catch (error) {
        console.error(`Error processing sidebar item at index ${index}:`, {
          text: item.text,
          link: item.link,
          hasItems: !!item.items,
          error: error instanceof Error ? error.message : String(error)
        });
        throw error; // Re-throw after logging
      }
    });
  };
  
  const fixedSidebar: Record<string, any> = {};
  for (const [key, section] of Object.entries(sidebar)) {
    fixedSidebar[key] = {
      ...section,
      items: fixFolderTitles(section.items),
    };
  }
  
  return fixedSidebar;
}
