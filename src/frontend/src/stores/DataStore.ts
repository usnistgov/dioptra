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
    { 
      name: 'Entry Point 1',
      group: 'Group 1',
      id: 1,
      parameters: [
        {name: 'data_dir', default_value: 'nfs/data', parameter_type: 'Path'},
        {name: 'image_size', default_value: '28-28-1', parameter_type: 'String'},
        {name: 'test_param', default_value: 'hello', parameter_type: 'String'},
      ],
      task_graph: `---
doe: "a deer, a female deer"
ray: "a drop of golden sun"
pi: 3.14159
xmas: true
french-hens: 3
calling-birds:
  - huey
  - dewey
  - louie
  - fred
xmas-fifth-day:
  calling-birds: four
  french-hens: 3
  golden-rings: 5
  partridges:
    count: 1
    location: "a pear tree"
  turtle-doves: two`
    },
    { 
      name: 'Entry Point 2',
      group: 'Group 2',
      id: 2,
      parameters: [
        {name: 'data_dir', default_value: 'nfs/data', parameter_type: 'Path'},
        {name: 'image_size', default_value: '28-28-1', parameter_type: 'String'},
        {name: 'test_param', default_value: 'hello', parameter_type: 'String'},
      ],
      task_graph: ''
    },
    { 
      name: 'Entry Point 3',
      group: 'Group 3',
      id: 3,
      parameters: [
        {name: 'data_dir', default_value: 'nfs/data', parameter_type: 'Path'},
        {name: 'image_size', default_value: '28-28-1', parameter_type: 'String'},
        {name: 'test_param', default_value: 'hello', parameter_type: 'String'},
      ],
      task_graph: ''
    }
  ])

  const savedExperimentForm = reactive({})

  const editEntryPoint = reactive({})

  // computed()'s are getters

  // function()'s are actions
  

  return { experiments, tags, entryPoints, savedExperimentForm, editMode, editEntryPoint }
})