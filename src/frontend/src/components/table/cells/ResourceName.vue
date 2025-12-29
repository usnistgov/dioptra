<template>
  <div class="resource-item-container row items-center no-wrap",
        style="min-width:150px; height:100%;">
    
    <div v-if="conceptType" class="shrink-0 flex flex-center" style="width: 24px;">
      <q-icon 
        v-if="includeIcon" 
        :name="styles.icon" 
        :color="styles.color" 
        size="xs" 
      />
      <div 
        v-else 
        :style="{ 
          width: '8px', 
          height: '8px', 
          borderRadius: '50%', 
          backgroundColor: styles.hexColor || 'black'
        }"
      ></div>
    </div>

    <div 
      class="resource-name-text text-weight-bold text-blue-grey-10 text-wrap-style q-ml-xs"
      :class="textTypeClass"
      :style="{
        maxWidth: maxWidth,
        letterSpacing: '.5px',
        '--hover-color': styles.hexColor || '#000'
      }"
    >
      {{ formattedDisplayValue }}
      
      <q-tooltip v-if="isTruncated || useQuotes" style="font-size: 13px">
        {{ formattedFullText }}
      </q-tooltip>
    </div>
  </div>
</template>

<style scoped>
/* Ensure the container defines the hover area */
.resource-item-container {
  cursor: pointer;
  width: fit-content;
}

.resource-name-text {
  white-space: normal;
  word-break: break-word; 
  line-height: 1.2;
  position: relative;
  display: inline-block;
  transition: color 0.2s ease;
}

/* Create the line */
.resource-name-text::after {
  content: '';
  position: absolute;
  left: 0;
  bottom: -2px;      /* Offset from text */
  width: 100%;
  height: 2px;
  background-color: var(--hover-color);
  transform: scaleX(0);
  transition: transform 0.15s ease-out;
}

.resource-item-container:hover .resource-name-text::after {
  transform: scaleX(1);
}


</style>

<script setup>
import { computed } from 'vue'
import { getConceptStyle } from '@/constants/tableStyles'
import { colors } from 'quasar'

const { getPaletteColor } = colors

const props = defineProps({
  text: [String, Number],
  conceptType: {
    type: String,
    default: null // If null, no icon is shown
  },
  maxLength: {
    type: Number,
    default: 35
  },
  maxWidth: {
    type: String,
    default: '200px'
  },
  useQuotes: {
    type: Boolean, 
    default: false
  },
  textType: {
    type: String, 
    default: "none" 
  },
  includeIcon: {
    type: Boolean, 
    default: false 
  }
})

const styles = computed(() => {
  if (!props.conceptType) return { icon: '', color: '' }
  const style = getConceptStyle(props.conceptType)
  try {
    return {
      ...style,
      hexColor: getPaletteColor(style.color)
    }
  } catch (e) {
    return { ...style, hexColor: style.color }
  }
})

const applyTransformation = (val) => {
  if (!val || typeof val !== 'string') return val
  const type = (props.textType || "none").toLowerCase()
  if (type === 'capitalize') return val.charAt(0).toUpperCase() + val.slice(1)
  if (type === 'uppercase') return val.toUpperCase()
  if (type === 'lowercase') return val.toLowerCase()
  return val
}

const wrapInQuotes = (val) => {
  if (!props.useQuotes || val === '-' || val === '') return val
  return `"${val}"`
}

const isTruncated = computed(() => {
  if (!props.text) return false
  return props.text.toString().length > props.maxLength
})

const formattedDisplayValue = computed(() => {
  if (props.text === undefined || props.text === null || props.text === '') return '-'
  
  let str = props.text.toString()

  if (str.length > props.maxLength) {
    str = str.slice(0, props.maxLength).trim() + '...'
  }

  str = applyTransformation(str)
  return wrapInQuotes(str)
})

const formattedFullText = computed(() => {
  if (!props.text) return ''
  return wrapInQuotes(applyTransformation(props.text.toString()))
})

const textTypeClass = computed(() => {
  const type = (props.textType || "none").toLowerCase()
  if (type === 'uppercase') return 'text-uppercase'
  if (type === 'lowercase') return 'text-lowercase'
  if (type === 'capitalize') return 'text-capitalize'
  return ''
})
</script>

<style scoped>
.text-wrap-style {
  white-space: normal;
  word-break: break-word; 
  line-height: 1.2; 
}
</style>