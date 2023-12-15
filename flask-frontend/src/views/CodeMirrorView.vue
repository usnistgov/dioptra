<template>
  <div>
    <h3 class="q-mb-lg">CodeMirror</h3>
    <p class="text-body1 q-mb-lg">
      This is an implementation of a code editor using CodeMirror
    </p>
    <div class="q-mb-sm">
      <q-btn-toggle
        v-model="language"
        toggle-color="primary"
        push
        color="blue-grey-2"
        textColor="black"
        :options="[
          {label: 'Python', value: 'python'},
          {label: 'YAML', value: 'yaml'},
        ]"
      />
      <span class="float-right">
        <q-btn outline icon="delete" label="Clear" @click="code=''" class="q-mr-md"/>
        <q-btn outline icon="file_copy" label="Copy" @click="copyToClipboard()" />
      </span>
    </div>
    <codemirror
      v-model="code"
      placeholder="Code goes here..."
      :style="{ height: '70vh' }"
      :autofocus="true"
      :indent-with-tab="true"
      :tab-size="2"
      :extensions="extensions"
      class="my-custom-codemirror text-body1"
      @ready="handleReady"
      @change="console.log('change', $event)"
      @focus="console.log('focus', $event)"
      @blur="console.log('blur', $event)"
    />
  </div>
</template>

<script setup lang="ts">
  import { ref, shallowRef, computed, watch } from 'vue';
  import { Codemirror } from 'vue-codemirror';
  import { python } from '@codemirror/lang-python';
  import { oneDark } from '@codemirror/theme-one-dark';
  import { StreamLanguage, foldGutter } from '@codemirror/language';
  import { yaml } from '@codemirror/legacy-modes/mode/yaml';
  import axios from 'axios';
  import parser from "js-yaml";
  import { linter, lintGutter, type LintSource } from "@codemirror/lint";

  import { CompletionContext, autocompletion } from '@codemirror/autocomplete';


  const code = ref(`print('Hello, world!')`);
  // const extensions = [python(), oneDark];
  const language = ref('python');

 const extensions = computed(() => {
    if (language.value === 'python') {
      return [python(), oneDark];
    } else {
      return [
        StreamLanguage.define(yaml), 
        oneDark, 
        lintGutter(), 
        yamlLinter, 
        autocompletion({ override: [myCompletions] }) 
      ];
    }
  }); 

  watch(language, async (newVal) => {
    if (newVal === 'python') {
      code.value = `print('Hello, world!')`;
    } else {
      code.value = '';
    }
  });

  const yamlLinter = linter((view) => {
    const diagnostics = [];
    try {
      parser.load(view.state.doc);
    } catch (e: any) {
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
  });

  // Codemirror EditorView instance ref
  const view = shallowRef();
  const handleReady = (payload: any) => {
    view.value = payload.view;
  };

  function copyToClipboard() {
    navigator.clipboard.writeText(code.value);
  }

  function myCompletions(context: CompletionContext) {
    let word = context.matchBefore(/\w*/);
    if (word.from == word.to && !context.explicit)
      return null;
    return {
      from: word.from,
      options: [
        { label: "Hello world example!!!!", type: "text" },
        { 
          label: "example.yaml", 
          type: "text", 
          apply: () => {
            if (view.value) {
              view.value.dispatch({
                changes: {from: word.from, to: word.to, insert: yamlAutocomplete.value}
              });
            }
          }, 
          detail: "Pull in the contents of example.yaml" 
        },
        { 
          label: "example.json", 
          type: "text", 
          apply: () => {
            if (view.value) {
              view.value.dispatch({
                changes: {from: word.from, to: word.to, insert: jsonAutocomplete.value}
              });
            }
          }, 
          detail: "Pull in the contents of example.json" 
        },
      ]
    };
  }

loadExampleYaml();

const yamlAutocomplete = ref('');
const jsonAutocomplete = ref('');

async function loadExampleYaml() {
  try {
    const yamlResponse = await axios.get('/example.yaml');
    const jsonResponse = await axios.get('/example.json');
    yamlAutocomplete.value = yamlResponse.data;
    jsonAutocomplete.value = JSON.stringify(jsonResponse.data, null, '\t');
  } catch (error) {
    console.error('Error loading YAML file', error);
  }
}




</script>

<style>
.my-custom-codemirror .cm-gutters {
  border-right: 1px solid #797979; /* Customize the color and width as needed */
}
/* .my-custom-codemirror .cm-foldGutter {
  display: none !important;
} */
</style>