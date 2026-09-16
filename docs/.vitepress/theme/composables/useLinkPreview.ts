import { ref, onMounted, onUnmounted, nextTick } from 'vue'

export function useLinkPreview() {
  const targetElement = ref<HTMLElement | null>(null)
  const href = ref<string>('')
  const isVisible = ref(false)
  
  let hoverTimeout: ReturnType<typeof setTimeout> | null = null
  let isHoveringLink = false
  let isHoveringPreview = false
  
  const HOVER_DELAY = 400 // ms before showing preview
  const HIDE_DELAY = 200 // ms before hiding when mouse leaves

  function shouldShowPreview(link: HTMLAnchorElement): boolean {
    const url = link.getAttribute('href')
    if (!url) return false
    
    // Only show for internal links
    if (!url.startsWith('/')) return false
    
    // Don't show for anchor-only links (same page)
    if (url.startsWith('#')) return false
    
    // Optional: Add more filters
    // e.g., exclude external links, certain paths, etc.
    
    return true
  }

  function handleLinkMouseEnter(event: MouseEvent) {
    const target = event.currentTarget as HTMLAnchorElement
    
    if (!shouldShowPreview(target)) return
    
    isHoveringLink = true
    
    // Clear any existing timeout
    if (hoverTimeout) {
      clearTimeout(hoverTimeout)
    }
    
    // Show preview after delay
    hoverTimeout = setTimeout(() => {
      if (isHoveringLink) {
        targetElement.value = target
        href.value = target.getAttribute('href') || ''
        isVisible.value = true
      }
    }, HOVER_DELAY)
  }

  function handleLinkMouseLeave() {
    isHoveringLink = false
    
    // Clear hover timeout
    if (hoverTimeout) {
      clearTimeout(hoverTimeout)
      hoverTimeout = null
    }
    
    // Hide preview after delay (gives time to move mouse to preview)
    setTimeout(() => {
      if (!isHoveringLink && !isHoveringPreview) {
        hidePreview()
      }
    }, HIDE_DELAY)
  }

  function handlePreviewMouseEnter() {
    isHoveringPreview = true
  }

  function handlePreviewMouseLeave() {
    isHoveringPreview = false
    
    // Hide preview after delay
    setTimeout(() => {
      if (!isHoveringLink && !isHoveringPreview) {
        hidePreview()
      }
    }, HIDE_DELAY)
  }

  function hidePreview() {
    isVisible.value = false
    targetElement.value = null
    href.value = ''
  }

  function attachListeners() {
    // Find all content links
    const contentArea = document.querySelector('.vp-doc')
    if (!contentArea) return
    
    const links = contentArea.querySelectorAll('a')
    
    links.forEach((link) => {
      link.addEventListener('mouseenter', handleLinkMouseEnter as EventListener)
      link.addEventListener('mouseleave', handleLinkMouseLeave)
    })
  }

  function detachListeners() {
    const contentArea = document.querySelector('.vp-doc')
    if (!contentArea) return
    
    const links = contentArea.querySelectorAll('a')
    
    links.forEach((link) => {
      link.removeEventListener('mouseenter', handleLinkMouseEnter as EventListener)
      link.removeEventListener('mouseleave', handleLinkMouseLeave)
    })
  }

  // Watch for route changes and reattach listeners
  function setupRouteWatcher(): MutationObserver | null {
    const observer = new MutationObserver(() => {
      detachListeners()
      attachListeners()
    })
    
    const contentArea = document.querySelector('.VPContent')
    if (contentArea) {
      observer.observe(contentArea, {
        childList: true,
        subtree: true
      })
      return observer
    }
    
    return null  // Explicit return
  }

  let observer: MutationObserver | null = null

  onMounted(async () => {
    // Wait for next tick to ensure DOM is fully rendered
    await nextTick()
    
    // Small delay to ensure VitePress content has rendered
    setTimeout(() => {
      attachListeners()
    }, 100)
    
    // Watch for route changes
    observer = setupRouteWatcher()
  })

  onUnmounted(() => {
    detachListeners()
    observer?.disconnect()
    if (hoverTimeout) {
      clearTimeout(hoverTimeout)
    }
  })

  return {
    targetElement,
    href,
    isVisible,
    handlePreviewMouseEnter,
    handlePreviewMouseLeave
  }
}
