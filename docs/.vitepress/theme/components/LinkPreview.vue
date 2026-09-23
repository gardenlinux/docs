<template>
  <div v-if="isVisible && content" ref="floatingRef" :style="floatingStyles" class="link-preview" @mouseenter="handleMouseEnter" @mouseleave="handleMouseLeave">
    <div class="link-preview-content">
      <h3 v-if="content.title">{{ content.title }}</h3>
      <p v-if="content.description" class="description">{{ content.description }}</p>
      <div v-if="content.excerpt" class="excerpt" v-html="content.excerpt"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useFloating, offset, flip, shift } from '@floating-ui/vue'

const props = defineProps<{
  targetElement: HTMLElement | null
  href: string
  isVisible: boolean
}>()

const emit = defineEmits<{
  (e: 'mouseenter'): void
  (e: 'mouseleave'): void
}>()

const floatingRef = ref<HTMLElement | null>(null)
const content = ref<{
  title?: string
  description?: string
  excerpt?: string
} | null>(null)

// Floating UI setup
const { floatingStyles } = useFloating(
  computed(() => props.targetElement),
  floatingRef,
  {
    placement: 'top',
    middleware: [
      offset(10),
      flip(),
      shift({ padding: 8})
    ]
  }
)

const handleMouseEnter = () => {
  emit('mouseenter')
}

const handleMouseLeave = () => {
  emit('mouseleave')
}

// Fetch content when href changes and preview is visible
watch(
  () => [props.href, props.isVisible] as const,
  async ([href, visible]) => {
    if (!visible || !href) {
      content.value = null
      return
    }

    // Check if it's a glossary link (with or without .html)
    if (href.includes('/reference/glossary') && href.includes('#')) {
      const term = href.split('#')[1]
      content.value = await fetchGlossaryTerm(term)
    } else {
      content.value = await fetchPagePreview(href)
    }
  }, 
  { immediate: true }
)

async function fetchGlossaryTerm(anchor: string): Promise<any> {
  try {
    // Try fetching markdown first (works in dev)
    let response = await fetch('/reference/glossary.md', {
      headers: { 'Accept': 'text/plain, text/markdown' }
    })
    
    if (response.ok) {
      const markdown = await response.text()
      return parseGlossaryFromMarkdown(markdown, anchor)
    }
    
    // Production: fetch HTML and parse DOM
    response = await fetch('/reference/glossary.html')
    if (!response.ok) return null
    
    const html = await response.text()
    return parseGlossaryFromHtml(html, anchor)
  } catch {
    return null
  }
}

function parseGlossaryFromMarkdown(markdown: string, anchor: string): any {
  const lines = markdown.split('\n')
  let foundHeading = false
  let title = ''
  let excerpt = ''
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]
    
    if (line.startsWith('### ')) {
      const headingText = line.replace('### ', '').trim()
      const generatedAnchor = headingText
        .toLowerCase()
        .replace(/[^\w\s-]/g, '')
        .replace(/\s+/g, '-')
        .replace(/-+/g, '-')
      
      if (generatedAnchor === anchor || headingText.toLowerCase().includes(anchor.replace(/-/g, ' '))) {
        foundHeading = true
        title = headingText
        continue
      } else if (foundHeading) {
        break
      }
    }
    
    if (foundHeading && line.trim() && !line.startsWith('#')) {
      excerpt += line + ' '
    }
  }
  
  if (!title) return null
  return { title, excerpt: excerpt.trim() }
}

function parseGlossaryFromHtml(html: string, anchor: string): any {
  const parser = new DOMParser()
  const doc = parser.parseFromString(html, 'text/html')
  
  // Find the heading with matching id
  const heading = doc.querySelector(`h3#${anchor}`)
  if (!heading) return null
  
  // Extract title (remove the anchor link if present)
  const title = heading.textContent?.replace(/\s*#$/, '').trim() || ''
  
  // Get content until next heading
  let excerpt = ''
  let nextElement = heading.nextElementSibling
  while (nextElement && !nextElement.tagName.match(/^H[1-3]$/)) {
    if (nextElement.tagName === 'P') {
      excerpt += nextElement.textContent + ' '
    }
    nextElement = nextElement.nextElementSibling
  }
  
  if (!title) return null
  return { title, excerpt: excerpt.trim() }
}

async function fetchPagePreview(href: string): Promise<any> {
  try {
    let cleanHref = href.split('#')[0]
    
    if (cleanHref.endsWith('.html')) {
      cleanHref = cleanHref.slice(0, -5)
    }
    
    // Try fetching markdown first (works in dev)
    const mdPath = cleanHref.endsWith('/') 
      ? `${cleanHref}index.md` 
      : `${cleanHref}.md`
    
    let response = await fetch(mdPath, {
      headers: { 'Accept': 'text/plain, text/markdown' }
    })
    
    if (response.ok) {
      const markdown = await response.text()
      return parsePageFromMarkdown(markdown)
    }
    
    // Production: fetch HTML and parse DOM
    const htmlPath = cleanHref.endsWith('/') 
      ? `${cleanHref}index.html` 
      : `${cleanHref}.html`
    
    response = await fetch(htmlPath)
    if (!response.ok) return null
    
    const html = await response.text()
    return parsePageFromHtml(html)
  } catch {
    return null
  }
}

function parsePageFromMarkdown(markdown: string): any {
  // Parse frontmatter (between --- and ---)
  const frontmatterMatch = markdown.match(/^---\n([\s\S]*?)\n---/)
  let title = ''
  let description = ''
  
  if (frontmatterMatch) {
    const frontmatter = frontmatterMatch[1]
    const titleMatch = frontmatter.match(/^title:\s*(.+)$/m)
    const descMatch = frontmatter.match(/^description:\s*(.+)$/m)
    if (titleMatch) title = titleMatch[1].replace(/^["']|["']$/g, '')
    if (descMatch) description = descMatch[1].replace(/^["']|["']$/g, '')
  }
  
  // Extract first paragraph after frontmatter
  const contentStart = frontmatterMatch 
    ? markdown.indexOf('---', 4) + 3 
    : 0
  const content = markdown.slice(contentStart).trim()
  
  // Find first paragraph (skip headings)
  const lines = content.split('\n')
  let excerpt = ''
  for (const line of lines) {
    const trimmed = line.trim()
    if (trimmed && !trimmed.startsWith('#') && !trimmed.startsWith('```') && !trimmed.startsWith(':::')) {
      excerpt = trimmed
      break
    }
  }
  
  // If no title from frontmatter, try to get from first h1
  if (!title) {
    const h1Match = content.match(/^#\s+(.+)$/m)
    if (h1Match) title = h1Match[1]
  }
  
  return { title, description, excerpt }
}

function parsePageFromHtml(html: string): any {
  const parser = new DOMParser()
  const doc = parser.parseFromString(html, 'text/html')
  
  // Extract title from h1 or title tag
  const h1 = doc.querySelector('h1')
  const title = h1?.textContent?.replace(/\s*#$/, '').trim() || 
                doc.querySelector('title')?.textContent || ''
  
  // Try to find description from meta tag
  const metaDescription = doc.querySelector('meta[name="description"]')
  const description = metaDescription?.getAttribute('content') || ''
  
  // Extract first paragraph from content
  const contentDiv = doc.querySelector('.vp-doc')
  const firstP = contentDiv?.querySelector('p')
  const excerpt = firstP?.textContent || ''
  
  return { title, description, excerpt }
}
</script>

<style scoped>
.link-preview {
  position: fixed;
  z-index: 1000;
  max-width: 400px;
  background: var(--vp-c-bg-soft);
  border: 1px solid var(--vp-c-border);
  border-radius: 8px;
  box-shadow: var(--vp-shadow-3);
  padding: 16px;
  pointer-events: auto;
}

.link-preview-content h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--vp-c-text-1);
}

.link-preview-content .description {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: var(--vp-c-text-2);
  font-style: italic;
}

.link-preview-content .excerpt {
  margin: 0;
  font-size: 14px;
  color: var(--vp-c-text-2);
  line-height: 1.5;
}

.link-preview-content .excerpt :deep(p) {
  margin: 0;
}

/* Hide on mobile/touch devices */
@media (hover: none) {
  .link-preview {
    display: none;
  }
}
</style>
