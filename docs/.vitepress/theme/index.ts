import { h, nextTick, watch } from 'vue'
import type { Theme } from 'vitepress'
import DefaultTheme from 'vitepress/theme'
import { useData } from 'vitepress'
import { createMermaidRenderer } from 'vitepress-mermaid-renderer'
import './style.css'
import SectionIndex from './components/SectionIndex.vue'
import RelatedTopics from './components/RelatedTopics.vue'
import Carousel from './components/Carousel.vue'
import VPFooter from './components/VPFooter.vue'
import LinkPreviewProvider from './components/LinkPreviewProvider.vue'

export default {
  extends: DefaultTheme,
  Layout: () => {
    const { isDark } = useData()

    const initMermaid = () => {
      createMermaidRenderer({
        // Colors are injected globally via the mermaid-classdefs markdown plugin
        theme: isDark.value ? 'dark' : 'default',
      })
    }

    nextTick(() => initMermaid())

    watch(
      () => isDark.value,
      () => {
        initMermaid()
      }
    )

    return h(LinkPreviewProvider, null, {
      default: () => h(DefaultTheme.Layout, null, {
        "layout-bottom": () => h(VPFooter),
      })
    })
  },
  enhanceApp({ app }) {
    app.component('SectionIndex', SectionIndex)
    app.component('RelatedTopics', RelatedTopics)
    app.component('Carousel', Carousel)
  },
} satisfies Theme
