<template>
  <div>
    <slot />
    <LinkPreview
      :target-element="targetElement"
      :href="href"
      :is-visible="isVisible"
      @mouseenter="handlePreviewMouseEnter"
      @mouseleave="handlePreviewMouseLeave"
    />
  </div>
</template>

<script setup lang="ts">
import { useLinkPreview } from '../composables/useLinkPreview'
import LinkPreview from './LinkPreview.vue'

const {
  targetElement,
  href,
  isVisible,
  handlePreviewMouseEnter,
  handlePreviewMouseLeave
} = useLinkPreview()
</script>
