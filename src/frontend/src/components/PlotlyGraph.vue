<template>
  <div
    ref="chart"
    style="
      height: 400px; 
      border: 1px solid #d1d9e1;
      border-radius: 8px; 
      overflow: hidden
    "
  >
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed, nextTick } from 'vue'
import Plotly from 'plotly.js-dist-min'
import { useQuasar } from 'quasar'

const $q = useQuasar()

const props = defineProps({
  data: Array,
  title: String,
  graphClass: String
})

/*
  Plotly expects this data format
  TODO: include type
  data = [{
    x: [1999, 2000, 2001, 2002],
    y: [10, 15, 13, 17],
    type: 'scatter'
  }]
*/

const layout = computed(() => {
  const isDark = $q.dark.isActive
  return {
    paper_bgcolor: isDark ? '#121212' : '#ffffff',
    plot_bgcolor: isDark ? '#121212' : '#ffffff',
    font: {
      color: isDark ? '#e0e0e0' : '#000000'
    },
    title: {
      text: props.title,
      x: 0.05,
      xanchor: 'left'
    },
    xaxis: {
      title: {
        text: 'Step'
      },
      gridcolor: isDark ? '#444' : '#ccc',
      zerolinecolor: isDark ? '#666' : '#aaa'
    },
    yaxis: {
      gridcolor: isDark ? '#444' : '#ccc',
      zerolinecolor: isDark ? '#666' : '#aaa'
    },
    margin: { t: 50, r: 30, l: 50 },
  }
})

const chart = ref(null)

onMounted(() => {
  Plotly.newPlot(chart.value, props.data, layout.value, { responsive: true })
})

watch(() => props.data, (newVal) => {
  const copy = JSON.parse(JSON.stringify(newVal))
    Plotly.react(chart.value, copy, layout.value, { responsive: true })
  },
  { deep: true }
)

watch(() => props.graphClass, () => {
  // allow DOM to apply new class layout before resizing
  nextTick(() => {
    Plotly.Plots.resize(chart.value)
  })
})

watch(() => $q.dark.isActive, () => {
  Plotly.purge(chart.value)
  const copy = JSON.parse(JSON.stringify(props.data))
  Plotly.react(chart.value, copy, layout.value, { responsive: true })
})

</script>

<style scopped>
body.body--dark .js-plotly-plot .modebar-btn {
  color: #e0e0e0 !important;
  fill: #e0e0e0 !important;
}

body.body--dark .js-plotly-plot .modebar-btn:hover {
  background-color: rgba(255, 255, 255, 0.1) !important;
  color: #fff !important;
  fill: #fff !important;
}
</style>