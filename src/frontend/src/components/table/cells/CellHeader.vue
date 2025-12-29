<template>
  <div :class="`row items-center ${alignClass}`">
    <span 
      style="font-weight: 600;
            color: #546e7a;
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;"
    >
      {{ col.label }}
    </span>
    
    </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  col: Object
})

// Map Quasar column alignment ('left', 'center', 'right') to Flex classes
const alignClass = computed(() => {
  const align = props.col.align || 'left'
  if (align === 'center') return 'justify-center'
  if (align === 'right') return 'justify-end'
  return 'justify-start'
})
</script>