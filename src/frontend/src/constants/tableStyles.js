export const CONCEPT_STYLES = {
  entrypoint: { 
    icon: 'account_tree', 
    color: 'orange-8', 
    basePath: 'entrypoints' 
  },
    experiment: { 
    icon: 'science', 
    color: 'primary', 
    basePath: 'experiments' 
  },
  queue: { 
    icon: 'queue', 
    color: 'blue-grey-6', 
    basePath: 'queues' 
  },
  plugin: { 
    icon: 'extension', 
    color: 'teal-7', 
    basePath: 'plugins' 
  },
  file: {
    icon: 'file_copy',
    color: 'green-9',
    basePath: 'plugins'
  },

  job: { 
    icon: 'outbound', 
    color: 'indigo-6', 
    basePath: 'jobs' 
  },  
  group: { 
    icon: 'person', 
    color: 'grey-7', 
    basePath: 'group' 
  },
  artifact: { 
    icon: 'sim_card_download', 
    color: 'brown-5', 
    basePath: 'artifact' 
  },
  task:{
    icon: 'functions', //brick ? function?
    color: 'black',
    basePath: 'plugin',
  },
  tag:{
    icon: 'tag', //brick ? function?
    color: 'grey-9',
    basePath: 'tags',
  },
  parameterType:{
    icon: 'shape_line',
    color: 'red-11',
    basePath: 'pluginParams'
  },
  default: { 
    icon: 'help_outline', 
    color: 'grey-7', 
    basePath: 'home' 
  }
}

export function getConceptStyle(type) {
  return CONCEPT_STYLES[type] || CONCEPT_STYLES.default
}