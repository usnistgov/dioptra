<template>
  <div class="row q-my-lg">
    <fieldset :class="`${isMobile ? 'col-12 q-mb-lg' : 'col q-mr-md'}`">
      <legend>Basic Info</legend>
      <div style="padding: 0 5%">
        <q-form @submit.prevent="submit" ref="form" greedy>
          <q-input 
            outlined 
            dense 
            v-model.trim="pluginFile.filename"
            :rules="[requiredRule, pythonFilenameRule]"
            class="q-mb-sm q-mt-md"
            aria-required="true"
          >
            <template v-slot:before>
              <label :class="`field-label`">Filename:</label>
            </template>
          </q-input>

          <q-input 
            outlined 
            dense 
            v-model.trim="pluginFile.description"
            class="q-mb-lg "
            type="textarea"
            autogrow
          >
            <template v-slot:before>
              <label :class="`field-label`">Description:</label>
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
      <legend>Plugin Parameter Types</legend>
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
  import { useRoute, useRouter } from 'vue-router'
  import { useDataStore } from '@/stores/DataStore.ts'
  import CodeEditor from '@/components/CodeEditor.vue'
  import * as api from '@/services/dataApi'
  import * as notify from '../notify'
  
  const store = useDataStore()
  const route = useRoute()
  const router = useRouter()

  const isMobile = inject('isMobile')

  const pluginFile = ref({})
  const uploadedFile = ref(null)

  onMounted(async () => {
    if(route.params.fileId === 'new') return
    try {
      const res = await api.getFile(route.params.id, route.params.fileId)
      console.log('getFile = ', res)
      pluginFile.value = res.data
    } catch(err) {
      notify.error(err.response.data.message)
    } 
  })

  function requiredRule(val) {
    return (!!val) || "This field is required"
  }

  function pythonFilenameRule(val) {
  const regex = /^[a-zA-Z_][a-zA-Z0-9_]*\.py$/
  if (!regex.test(val)) {
    return "Invalid Python filename"
  }
  if (val === '_.py') {
    return "_.py is not a valid Python filename"
  }
  return true
}

  async function submit() {
    const plguinFileSubmit = {
        filename: pluginFile.value.filename,
        contents: pluginFile.value.contents,
        description: pluginFile.value.description
      }
    try {
      let res
      if(route.params.fileId === 'new') {
        res = await api.addFile(route.params.id, plguinFileSubmit)
      } else {
        res = await api.updateFile(route.params.id, route.params.fileId, plguinFileSubmit)
      }
      notify.success(`Sucessfully ${route.params.fileId === 'new' ? 'created' : 'updated'} Plugin File '${res.data.name}'`)
      router.push(`/plugins/${route.params.id}/files`)
    } catch(err) {
      console.log('err = ', err)
      notify.error(err.response.data.message)
    } 
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