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
        'max-height': '100vh',
        'border': `${showError ? '2px solid red' : '2px solid black'}`
      }"
    />
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
  import { computed, shallowRef } from 'vue'
  import { Codemirror } from 'vue-codemirror'
  import { yaml } from '@codemirror/lang-yaml'
  import { oneDark } from '@codemirror/theme-one-dark'
  import { linter, lintGutter } from "@codemirror/lint"
  import parser from "js-yaml"
  import { python } from '@codemirror/lang-python'
  import { CompletionContext, autocompletion, startCompletion } from '@codemirror/autocomplete'
  import YAML from 'yaml'
  import { EditorView } from '@codemirror/view'

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

  const props = defineProps(['placeholder', 'language', 'readOnly', 'showError', 'autocompletions', 'additionalCode'])

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

  const extensions = computed(() => {
    const baseExtensions = [
      oneDark,
    ]

    if (props.language === 'python') {
      return [python(), ...baseExtensions]
    }

    return [
      yaml(),
      yamlLinter,
      lintGutter(),
      autocompletion({ override: [myCompletions] }),
      dollarTriggerExtension,
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
</style>