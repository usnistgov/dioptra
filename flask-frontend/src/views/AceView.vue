<template>
  <div>
    <h3 class="q-mb-lg">Ace</h3>
    <p class="text-body1 q-mb-lg">
      This is an implementation of a code editor using Ace
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
    <v-ace-editor
      v-model:value="code"
      :lang="language"
      theme="one_dark"
      style="min-height: 70vh"
      :printMargin="false"
      :options="{ 
        placeholder: 'Enter code here...',
        useWorker: true,
      }"
      class="text-body1"
    />
  </div>
</template>

<script setup lang="ts">
  import { ref, watch } from 'vue';
  import { VAceEditor } from 'vue3-ace-editor';
  import ace from 'ace-builds';
  import 'ace-builds/src-noconflict/mode-python';
  import 'ace-builds/src-noconflict/mode-yaml';
  import 'ace-builds/src-noconflict/theme-one_dark';
  import axios from 'axios';

  const code = ref(`print('Hello, world!')`);
  const language = ref('python');

  import workerYaml from 'ace-builds/src-noconflict/worker-yaml?url';
  ace.config.setModuleUrl('ace/mode/yaml_worker', workerYaml);

  watch(language, async (newVal) => {
    if (newVal === 'python') {
      code.value = `print('Hello, world!')`;
    } else {
      try {
          const response = await axios.get('/example-yaml.yaml');
          code.value = response.data;
      } catch (error) {
        console.error('Error loading YAML file', error);
      }
    }
  });

  function copyToClipboard() {
    navigator.clipboard.writeText(code.value);
  }

</script>

