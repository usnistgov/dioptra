import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useDataStore = defineStore('data', () => {
  // ref()'s are state properties
  const experiments = ref([])
  const tags = ref([
    'Machine Learning', 
    'Adversarial Machine Learning', 
    'Tensorflow', 
    'vgg16', 
    'Image Classification', 
    'Patch Attack', 
    'Categorical Data', 
    'AI'
  ])

  // computed()'s are getters

  // function()'s are actions
  

  return { experiments, tags }
})