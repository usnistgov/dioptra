export const RESOURCE_STYLES = {
  entrypoint: {
    icon: "account_tree",
    color: "orange-13",
    darkColor: "orange-5",
  },
  experiment: {
    icon: "science",
    color: "primary",
    darkColor: "blue-4", // Assuming primary is blue-ish
  },
  queue: {
    icon: "queue",
    color: "blue-grey-6",
    darkColor: "blue-grey-3",
  },
  plugin: {
    icon: "extension",
    color: "teal-7",
    darkColor: "teal-2",
  },
  file: {
    icon: "file_copy",
    color: "green-9",
    darkColor: "green-4",
  },
  job: {
    icon: "outbound",
    color: "indigo-6",
    darkColor: "indigo-3",
  },
  group: {
    icon: "person",
    color: "grey-8",
    darkColor: "grey-5",
  },
  artifact: {
    icon: "sim_card_download",
    color: "brown-6",
    darkColor: "brown-3",
  },
  task: {
    icon: "functions",
    color: "black",
    darkColor: "grey-4",
  },
  tag: {
    icon: "sell",
    color: "grey-9",
    darkColor: "grey-5",
  },
  parameterType: {
    icon: "shape_line",
    color: "red-10", // slightly darker for text/lines
    darkColor: "red-4",
  },
  default: {
    icon: "help_outline",
    color: "grey-7",
    darkColor: "grey-5",
  },
}

export function getResourceStyle(type, darkMode = false) {
  const style = RESOURCE_STYLES[type] || RESOURCE_STYLES.default

  return {
    ...style,
    color: darkMode ? style.darkColor : style.color,
  }
}
