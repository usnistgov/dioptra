<template>
  <div 
    :class="[textColor, textTypeClass, 'text-wrap-style']"
    :style="{ maxWidth: maxWidth, width: 'fit-content' }"
  >
    {{ formattedDisplayValue }}
    
    <q-tooltip v-if="isTruncated || useQuotes" max-width="400px" style="font-size: 13px">
      {{ formattedFullText }}
    </q-tooltip>
  </div>
</template>

<script setup>
import { computed } from 'vue'


const props = defineProps({
  text: [String, Number],
  maxLength: {
    type: Number,
    default: 150
  },
  maxWidth: {
    type: String,
    default: '250px'
  },
  useQuotes: {
    type: Boolean, 
    default: false
  },
  textType: {
    type: String, 
    default: "none" 
  },
  // NEW PROP: Allows overriding the default grey color
  textColor: {
    type: String,
    default: 'text-grey-8' 
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
  /* Allows text to wrap to multiple lines */
  white-space: normal;
  /* Ensures long URLs or words don't spill out */
  word-break: break-word; 
  /* Ensures the line height is comfortable for multi-line text */
  line-height: 1.4;
  /* Optional: align text to the top of the cell */
  display: inline-block;
  vertical-align: top;
}
</style>