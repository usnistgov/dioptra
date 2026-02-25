import { colors } from 'quasar'

// We define a Quasar class for Light mode, and a lighter variant for Dark mode
export const CONCEPT_STYLES = {
  entrypoint: { 
    icon: 'account_tree', 
    color: 'orange-13',
    darkColor: 'orange-5', 
    basePath: 'entrypoints' 
  },
  experiment: { 
    icon: 'science', 
    color: 'primary', 
    darkColor: 'blue-4', // Assuming primary is blue-ish
    basePath: 'experiments' 
  },
  queue: { 
    icon: 'queue', 
    color: 'blue-grey-6', 
    darkColor: 'blue-grey-3', 
    basePath: 'queues' 
  },
  plugin: { 
    icon: 'extension', 
    color: 'teal-7', 
    darkColor: 'teal-4', 
    basePath: 'plugins' 
  },
  file: {
    icon: 'file_copy',
    color: 'green-9',
    darkColor: 'green-4',
    basePath: 'plugins'
  },
  job: { 
    icon: 'outbound', 
    color: 'indigo-6', 
    darkColor: 'indigo-3',
    basePath: 'jobs' 
  },  
  group: { 
    icon: 'person', 
    color: 'grey-8', 
    darkColor: 'grey-5', 
    basePath: 'groups' 
  },
  artifact: { 
    icon: 'sim_card_download', 
    color: 'brown-6', 
    darkColor: 'brown-4', 
    basePath: 'artifact' 
  },
  task: {
    icon: 'functions', 
    color: 'black', 
    darkColor: 'grey-4', 
    basePath: 'plugin',
  },
  tag: {
    icon: 'tag', 
    color: 'grey-9', 
    darkColor: 'grey-5',
    basePath: 'tags',
  },
  parameterType: {
    icon: 'shape_line',
    color: 'red-10', // slightly darker for text/lines
    darkColor: 'red-4',
    basePath: 'pluginParams'
  },
  default: { 
    icon: 'help_outline', 
    color: 'grey-7', 
    darkColor: 'grey-5',
    basePath: '' 
  }
}

/**
 * Returns the style object.
 * NOTE: The 'color' property returned here is still the CLASS NAME string.
 */
export function getConceptStyle(type) {
  return CONCEPT_STYLES[type] || CONCEPT_STYLES.default
}

/**
 * Returns the HEX CODE for use in :style bindings.
 * Automatically handles Dark Mode toggle.
 */
export function getConceptColorHex(type, isDarkMode = false) {
  const style = getConceptStyle(type)
  
  // 1. Pick the correct Quasar class name based on mode
  const colorClass = isDarkMode && style.darkColor ? style.darkColor : style.color
  
  // 2. Handle Edge Case: "black" or "white" are standard CSS, not Palette names
  if (['black', 'white', 'transparent'].includes(colorClass)) {
    return colorClass
  }
  
  // 3. Convert Quasar class (e.g. 'orange-8') to Hex (e.g. '#ef6c00')
  try {
    return colors.getPaletteColor(colorClass)
  } catch (e) {
    // Fallback if Quasar can't parse it
    return '#808080' 
  }
}