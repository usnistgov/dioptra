<template>
  <div class="column" style="flex: 1; width: 100%;">
    <codemirror
      v-model="code"
      :placeholder="placeholder"
      :autofocus="false"
      :indent-with-tab="true"
      :tab-size="2"
      :extensions="extensions"
      :disabled="readOnly"
      @ready="handleReady"
      @update="highlightPlaceholder"
      :style="{
        flex: 1,
        'max-height': expanded ? 'none' : (props.maxHeight || '100vh'),
        'border': `${showError ? '2px solid red' : '2px solid black'}`
      }"
    />
    <div v-if="code.split('\n').length > 10 && props.maxHeight">
      <q-btn
        :label="`${expanded ? 'Collapse' : 'Expand'}`"
        :icon="`${expanded ? 'arrow_upward' : 'arrow_downward'}`"
        color="secondary" 
        @click="expanded = !expanded"
        class="q-mt-xs"
      />
    </div>
    <div
      :class="{ visibility: showError ? 'hidden' : '' }"
      class="row text-caption q-ml-md text-negative"
      role="alert"
      style="min-height: 20px;" 
    >
      {{ showError }}
    </div>
  </div>
</template>

<script setup>
  import { computed, shallowRef, ref } from 'vue'
  import { Codemirror } from 'vue-codemirror'
  import { yaml } from '@codemirror/lang-yaml'
  import { oneDark } from '@codemirror/theme-one-dark'
  import { linter, lintGutter } from "@codemirror/lint"
  import parser from "js-yaml"
  import { python } from '@codemirror/lang-python'
  import { CompletionContext, autocompletion, startCompletion } from '@codemirror/autocomplete'
  import YAML from 'yaml'
  import { 
    Decoration, 
    ViewPlugin, 
    MatchDecorator, 
    EditorView 
  } from '@codemirror/view'
  import { useQuasar } from 'quasar'

  import { RangeSetBuilder } from '@codemirror/state'

const variableHighlighter = ViewPlugin.fromClass(class {
  constructor(view) {
    this.decorations = this.computeDecorations(view)
  }

  update(update) {
    if (update.docChanged || update.viewportChanged) {
      this.decorations = this.computeDecorations(update.view)
    }
  }

  computeDecorations(view) {
    const builder = new RangeSetBuilder()
    
    // This regex uses an optional capture group:
    // 1. \$([\w-]+)     - Captures the base name (e.g., "step_name")
    // 2. (\.[\w.-]+)?  - Optionally captures the dot-path (e.g., ".output")
    const variableRegex = /\$([\w-]+)(\.[\w.-]*)?/g;
    
    for (let { from, to } of view.visibleRanges) {
      const text = view.state.doc.sliceString(from, to)
      let match
      
      while ((match = variableRegex.exec(text))) {
        // match[0] is the full text, e.g., "$step.output"
        // match[1] is the base, e.g., "step"
        // match[2] is the dot-path, e.g., ".output" or undefined
        
        const isComplex = match[2] !== undefined // True if it has a dot-path
        const cssClass = isComplex ? "cm-yaml-variable-complex" : "cm-yaml-variable-simple"
        
        const start = from + match.index
        const end = start + match[0].length
        
        builder.add(start, end, Decoration.mark({
          class: cssClass
        }))
      }
    }
    return builder.finish()
  }
}, {
  decorations: v => v.decorations
})


// --- 2. Structural Highlighting (Indentation Logic) ---
// This scans lines to detect Step Names (indent 0) vs Plugin Names (indent 2)
const structureHighlighter = ViewPlugin.fromClass(class {
  constructor(view) {
    this.decorations = this.computeDecorations(view)
  }

  update(update) {
    if (update.docChanged || update.viewportChanged) {
      this.decorations = this.computeDecorations(update.view)
    }
  }

  computeDecorations(view) {
    const builder = new RangeSetBuilder()
    
    for (let { from, to } of view.visibleRanges) {
      for (let pos = from; pos <= to;) {
        const line = view.state.doc.lineAt(pos)
        const text = line.text
        let match
        
        // Logic 1: Step Name (Indent 0)
        // Regex captures the key text before the colon
        match = text.match(/^(\S[^:]*):/) 
        if (match) {
          const keyText = match[1] // The captured key
          const keyStart = line.from
          const keyEnd = line.from + keyText.length
          
          builder.add(keyStart, keyEnd, Decoration.mark({
            class: "cm-yaml-step-key" // Apply class directly to the key
          }))
        }
        
        // Logic 2: Plugin Name (Indent 2)
        // Regex captures the key text after the 2 spaces
        match = text.match(/^\s{2}(\S[^:]*):/)
        if (match) {
          const keyText = match[1] // The captured key
          // Start position needs to account for the 2 spaces
          const keyStart = line.from + 2 
          const keyEnd = keyStart + keyText.length
          
          builder.add(keyStart, keyEnd, Decoration.mark({
            class: "cm-yaml-plugin-key" // Apply class directly to the key
          }))
        }
        
        pos = line.to + 1
      }
    }
    return builder.finish()
  }
}, {
  decorations: v => v.decorations
})

  const $q = useQuasar()

  const expanded = ref(false)

  function myCompletions(context) {
    let word = context.matchBefore(/\$\w*/) || context.matchBefore(/\w*/)
    if (word.from == word.to && !context.explicit) {
      return null
    }

    // Get the current line from the document
    const line = context.state.doc.lineAt(context.pos)
    const lineText = line.text
    
    // Get the text before the cursor
    const textBeforeCursor = lineText.slice(0, context.pos - line.from)
    
    // Check if the cursor is typing a new key before the colon
    const isTypingBeforeColon = /^[^\s:]+$/.test(textBeforeCursor.trim())

    // If the user is typing a new key before the colon, suppress the autocompletion
    if (isTypingBeforeColon) return null

    // Determine the current top-level key
    let topLevelKeys = []
    try {
      topLevelKeys = Object.keys(YAML.parse(context.state.doc.toString()))
    } catch (error) {
      console.error("Failed to parse YAML:", error)
    }
    let currentTopLevelKey = null

    for (const key of topLevelKeys) {
      if (context.pos >= context.state.doc.toString().indexOf(key)) {
        currentTopLevelKey = key
      }
    }

    // Filter out the current top-level key from the autocompletions
    const filteredTopLevelKeys = getTopLevelKeys(code.value).filter(option => option.label !== `$${currentTopLevelKey}`)
    const additionalTopLevelKeys = getTopLevelKeys(props.additionalCode)

    return {
      from: word.from,
      options: [...props.autocompletions, ...filteredTopLevelKeys, ...additionalTopLevelKeys],
      // options: [
      //   {label: "match", type: "keyword"},
      //   {label: "hello", type: "variable", info: "(World)"},
      //   {label: "magic", type: "text", apply: "⠁⭒*.✩.*⭒⠁", detail: "macro"}
      // ]
    }
  }

  const props = defineProps(['placeholder', 'language', 'readOnly', 'showError', 'autocompletions', 'additionalCode', 'maxHeight'])

  const code = defineModel()

  // Codemirror EditorView instance ref
  const view = shallowRef()
  const handleReady = (payload) => {
    view.value = payload.view
  }

  function highlightPlaceholder(update) {
    if(!view.value || update.docChanged || props.language === 'python') return
    const from = view.value.state.selection.ranges[0].from
    const to = view.value.state.selection.ranges[0].to
    if(from !== to) return // short circut if user is dragging cursor

    const placeholders = ['<input-value>', '<step-name>', '<output-name>', '<contents>']
    placeholders.forEach((placeholder) => {
      let startIndex = code.value.indexOf(placeholder)
      while(startIndex !== -1) {
        const endIndex = startIndex + placeholder.length

        // Check if the cursor position is within the bounds of the current placeholder instance
        if(from >= startIndex && from <= endIndex && from !== startIndex && from !== endIndex) {
          console.log(`Cursor is at position ${from}, within the substring '${placeholder}' from index ${startIndex} to ${endIndex}`)
          view.value.dispatch({
            selection: { anchor: startIndex, head: endIndex }
          })
          if(placeholder === '<input-value>' || placeholder === '<contents>') {
            startCompletion(view.value)
          }
          return // Break after the first match to avoid overlapping selection conflicts
        }

        // Move to the next possible start index to continue searching
        startIndex = code.value.indexOf(placeholder, startIndex + placeholder.length)
      }
    })
  }


  const yamlLinter = linter((view) => {
    const diagnostics = []
    try {
      parser.load(view.state.doc)
    } catch (e) {
      const loc = e.mark
      const from = loc ? loc.position : 0
      const to = from
      const severity = "error"

      diagnostics.push({
        from,
        to,
        message: e.message,
        severity
      })
    } 

    return diagnostics
  })

  function getTopLevelKeys(code) {
    try {
      if(code) {
        let output = []
        const keys =  Object.keys(YAML.parse(code)).filter((key) => key !== '<step-name>')
        keys.forEach((key) => {
          output.push({
            label: `$${key}`,
            type: 'keyword'
          })
        })
        return output
      }
      return []
    } catch (error) {
      console.error('YAML Parsing Error:', error)
      return []
    }
  }

const dollarTriggerExtension = EditorView.updateListener.of((update) => {
  if (!view.value) return

  let insertedText = ""
  let isSingleCharInsertion = false

  update.changes.iterChanges((fromA, toA, fromB, toB, inserted) => {
    insertedText = inserted.sliceString(0)

    // Check if exactly one character was inserted
    isSingleCharInsertion = (inserted.length === 1) && (insertedText === "$")
  })

  if (isSingleCharInsertion) {
    startCompletion(view.value)
  }
})

  const noActiveLine = EditorView.theme({
    '.cm-activeLine': { backgroundColor: 'transparent' },
    '.cm-activeLineGutter': { backgroundColor: 'transparent' }
  })

  const extensions = computed(() => {
    const baseExtensions = []

    if($q.dark.isActive) {
      baseExtensions.push(oneDark)
    }

    if (props.language === 'python') {
      return [python(), ...baseExtensions]
    }

    if (props.language === 'text') {
      return [
        EditorView.lineWrapping,
        noActiveLine,  
        ...baseExtensions,
      ]
    }

    return [
      yaml(),
      yamlLinter,
      lintGutter(),
      autocompletion({ override: [myCompletions] }),
      dollarTriggerExtension,
      EditorView.lineWrapping,
      variableHighlighter,
      structureHighlighter,

      ...baseExtensions,
    ]
  })
</script>

<style>
  /* .cm-scroller { 
    overflow: auto; 
    min-height: 250px;
  } */

.cm-editor {
  width: 100% !important;
}

/* Existing styles... */



/* 1. The $variable Badge */
/* (This usually works because regex matches often happen on text nodes, 
    but we can bulletproof it too just in case) */
.cm-yaml-variable,
.cm-yaml-variable * {
  background-color: #e0f7fa;
  color: #006064 !important;
  border-radius: 4px;
  padding: 0px 4px;
  font-family: monospace;
  font-weight: bold;
  font-size: 0.9em;
  border: 1px solid #b2ebf2;
  display: inline-block;
  line-height: normal;
}

/* Dark Mode Badge */
body.body--dark .cm-yaml-variable,
body.body--dark .cm-yaml-variable * {
  background-color: #2c3e50;
  color: #56c6eb !important;
  border-color: #34495e;
}

/* 1a. The $variable Badge (Simple - BLUE) */
.cm-yaml-variable-simple,
.cm-yaml-variable-simple * {
  background-color: #e0f7fa; /* Light Cyan */
  color: #006064 !important;    /* Dark Cyan Text */
  border-radius: 4px;
  padding: 0px 4px;
  font-family: monospace;
  font-weight: bold;
  font-size: 0.9em;
  border: 1px solid #b2ebf2;
  display: inline-block;
  line-height: normal;
}

/* Dark Mode Badge (Simple - BLUE) */
body.body--dark .cm-yaml-variable-simple,
body.body--dark .cm-yaml-variable-simple * {
  background-color: #2c3e50;
  color: #56c6eb !important;
  border-color: #34495e;
}

/* 1b. The $variable Badge (Complex - PURPLE) */
.cm-yaml-variable-complex,
.cm-yaml-variable-complex * {
  background-color: #f3e5f5; /* Light Purple */
  color: #6a1b9a !important;   /* Dark Purple */
  border-radius: 4px;
  padding: 0px 4px;
  font-family: monospace;
  font-weight: bold;
  font-size: 0.9em;
  border: 1px solid #e1bee7;
  display: inline-block;
  line-height: normal;
}

/* Dark Mode Badge (Complex - PURPLE) */
body.body--dark .cm-yaml-variable-complex,
body.body--dark .cm-yaml-variable-complex * {
  background-color: #3e2753; /* Darker Purple */
  color: #ce93d8 !important;    /* Lighter Purple */
  border-color: #4a148c;
}

/* 2. Step Name (Indent 0) */
.cm-yaml-step-key,
.cm-yaml-step-key * { /* <--- The * targets the inner .ͼl span */
  font-weight: 900;
  color: #1976d2 !important; 
  font-size: 1.1em;
  text-decoration: underline;
  text-decoration-color: rgba(25, 118, 210, 0.3);
}

/* 3. Plugin Name (Indent 2) */
.cm-yaml-plugin-key{
/* Box styles */
  background-color: transparent;
  border: 1px solid #9c27b0; /* Purple border */
  border-radius: 4px;         /* Rounded edges */
  padding: 0px 4px;           /* Add some space */
  display: inline-block;
  line-height: normal;
  
  /* Text styles for the wrapper */
  font-weight: 900;
  font-size: 1.1em;
  color: #9c27b0 !important; /* Purple text */
}

.cm-yaml-plugin-key * { /* <--- The * targets the inner .ͼl span */
font-weight: inherit;
  font-size: inherit;
  color: #9c27b0 !important;
  text-decoration: none !important;
}

/* Dark Mode Adjustment for Step Name */
body.body--dark .cm-yaml-plugin-key {
  border-color: #ce93d8; /* Lighter purple border */
  color: #ce93d8 !important;
}

body.body--dark .cm-yaml-plugin-key * {
   color: #ce93d8 !important;
}

</style>