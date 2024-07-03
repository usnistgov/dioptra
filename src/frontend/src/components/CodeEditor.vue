<template>
  <codemirror
    v-model="code"
    :placeholder="placeholder"
    :style="{ 'min-height': '250px', 'max-height': '70vh' }"
    :autofocus="false"
    :indent-with-tab="true"
    :tab-size="2"
    :extensions="extensions"
    @ready="handleReady"
    @change="console.log('change', $event)"
    @focus="console.log('focus', $event)"
    @blur="console.log('blur', $event)"
  />
</template>

<script setup>
  import { computed, shallowRef, defineModel } from 'vue'
  import { Codemirror } from 'vue-codemirror'
  import { yaml } from '@codemirror/lang-yaml'
  import { oneDark } from '@codemirror/theme-one-dark'
  import { linter, lintGutter } from "@codemirror/lint"
  import parser from "js-yaml"
  import { python } from '@codemirror/lang-python'

  const props = defineProps(['placeholder', 'language'])

  // const code = ref('')

  const code = defineModel()

  // Codemirror EditorView instance ref
  const view = shallowRef()
  const handleReady = (payload) => {
    view.value = payload.view
  }

  const yamlLinter = linter((view) => {
    const diagnostics = [];
    try {
      parser.load(view.state.doc);
    } catch (e) {
      const loc = e.mark;
      const from = loc ? loc.position : 0;
      const to = from;
      const severity = "error";

      diagnostics.push({
        from,
        to,
        message: e.message,
        severity
      });
    } 

    return diagnostics;
  })


  const extensions = computed(() => {
    if(props.language === 'python') {
      return [python(), oneDark]
    }
    return [
      yaml(), 
      oneDark,
      yamlLinter,
      lintGutter()
    ]
  })
</script>