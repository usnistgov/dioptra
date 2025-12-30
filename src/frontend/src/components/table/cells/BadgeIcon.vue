<template>
  <q-chip
    v-if="type"
    :color="styles.color"
    text-color="white"
    :icon="styles.icon"
    :size="size"
    :outline="chipType === 'outline'"
    square
    class="text-weight-bold q-py-md q-px-sm"
  >
    <span 
      class="font-mono ellipsis q-ml-xs" 
      :class="{ 'text-uppercase': uppercase }"
      style="font-size: 12px; font-weight:500; max-width:200px"
    > 
      {{ displayValue }} 
    </span>
    
    <q-tooltip>{{ tooltipText }}</q-tooltip>
  </q-chip>
</template>

<script setup>
import { computed } from 'vue'
import { getConceptStyle } from '@/constants/tableStyles'

const props = defineProps({
  type: String,
  label: [String, Number],
  rowId: [String, Number],
  uppercase: {
    type: Boolean,
    default: true
  },
  size: {
    type: String,
    default: 'sm'
  },
  chipType: {
    type: String,
    default: 'outline',
    validator: (value) => ['outline', 'normal'].includes(value)
  },
  formatLabel: {
    type: String,
    default: '' // e.g., "Job ID was {label}"
  }
})

// Fallback to a neutral style if the type is unknown to avoid crashes
const styles = computed(() => {
  return getConceptStyle(props.type) || { color: 'grey-7', icon: 'help' }
})

const displayValue = computed(() => {
  // Use "NA" if label is null/undefined/empty, otherwise use the label
  const labelVal = (props.label !== undefined && props.label !== null && props.label !== '') 
    ? props.label 
    : 'NA'
  
  const typeVal = props.type || ''

  // If no format string is provided, use the label or fall back to the type
  if (!props.formatLabel) {
    return labelVal !== 'NA' ? labelVal : typeVal
  }
  
  // Inject values into the format string
  // Replaces {label} with the label (or NA) and {type} with the concept type
  return props.formatLabel
    .replace(/{label}/g, labelVal)
    .replace(/{type}/g, typeVal)
})

const tooltipText = computed(() => {
  if (!props.type) return ''
  const base = `${props.type}: ${props.label || 'N/A'}`
  const idSuffix = props.rowId ? ` (ID: ${props.rowId})` : ''
  return base + idSuffix
})
</script>