<template>
  <div class="row q-my-lg">
    <fieldset :class="`${isMobile ? 'col-12 q-mb-lg' : 'col q-mr-md'}`">
      <legend>Basic Info</legend>
      <div style="padding: 0 5%">
        <q-form @submit.prevent="submitFile" ref="form" greedy>
          <q-input 
            outlined 
            dense 
            v-model.trim="pluginFile.name"
            :rules="[requiredRule]"
            class="q-mb-sm q-mt-md"
            aria-required="true"
          >
            <template v-slot:before>
              <label :class="`field-label`">Filename:</label>
            </template>
          </q-input>
        </q-form>

        <q-file
          v-model="uploadedFile"
          label="Upload Python File"
          outlined
          use-chips
          dense
          accept=".py, text/x-python"
          @update:model-value="processFile"
          class="q-mb-sm"
        >
          <template v-slot:before>
            <label :class="`field-label`">File Contents:</label>
          </template>
          <template v-slot:prepend>
            <q-icon name="attach_file" />
          </template>
        </q-file>

        <CodeEditor 
          v-model="pluginFile.contents"
          language="python"
          :placeholder="'#Enter plugin file code here...'"
          style="max-height: 50vh; margin-bottom: 15px;"
        />
      </div>
    </fieldset>
    <fieldset :class="`${isMobile ? 'col-12' : 'col q-ml-md'}`">
      <legend>Plugin Tasks</legend>
    </fieldset>
  </div>

  <div :class="`${isMobile ? '' : ''} float-right`">
    <q-btn  
      :to="`/plugins/${route.params.id}/files`"
      color="negative" 
      label="Cancel"
      class="q-mr-lg"
    />
    <q-btn  
      @click="submit()" 
      color="primary" 
      label="Save File"
      type="submit"
    />
  </div>
</template>

<script setup>
  import { ref, inject, reactive, computed, watch, onMounted } from 'vue'
  import { useRoute } from 'vue-router'
  import { useDataStore } from '@/stores/DataStore.ts'
  import CodeEditor from '@/components/CodeEditor.vue'
  
  const store = useDataStore()
  const route = useRoute()

  const isMobile = inject('isMobile')

  const pluginFile = ref({})
  const uploadedFile = ref(null)

  onMounted(() => {
    if(route.params.fileId === 'new') return
    const plugin = store.plugins.find((plugin) => plugin.id === route.params.id)
    pluginFile.value = JSON.parse(JSON.stringify(plugin.files.find((file) => file.id === route.params.fileId)))
  })

  function requiredRule(val) {
    return (val && val.length > 0) || "This field is required"
  }

  function submitFile() {
    console.log('submitting file')
  }

  function processFile() {
    const file = uploadedFile.value
    if (!file) {
      pluginFile.value.contents = ''
      return
    }
    const reader = new FileReader()
    reader.onload = (e) => {
      pluginFile.value.contents = e.target.result;
    }
    reader.onerror = (e) => {
      console.log('error = ', e)
    }
    reader.readAsText(file); // Reads the file as text
  }

</script>