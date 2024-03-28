import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'

export const useDataStore = defineStore('data', () => {
  // ref()'s are state properties

  const editMode = ref(false)

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

  const entryPoints = ref([
    'Entry Point 1',
    'Entry Point 2',
    'Entry Point 3',
    'Entry Point 4',
    'Entry Point 5',
    'Entry Point 6',
  ])

  const savedExperimentForm = reactive({})

  // computed()'s are getters

  // function()'s are actions
  

  return { experiments, tags, entryPoints, savedExperimentForm, editMode }
})