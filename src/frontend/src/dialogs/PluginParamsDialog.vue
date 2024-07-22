<template>
  <DialogComponent 
    v-model="showDialog"
    @emitSubmit="emitAddOrEdit"
    :hideDraftBtn="true"
  >
    <template #title>
      <label id="modalTitle">
        Register Plugin Parameter Type
      </label>
    </template>
    <div class="row items-center q-mb-xs">
      <label class="col-3 q-mb-lg" id="pluginName">
        Name:
      </label>
      <q-input 
        class="col" 
        outlined 
        dense 
        v-model="plugin.name" 
        autofocus 
        :rules="[requiredRule]" 
        aria-labelledby="pluginName"
        aria-required="true"
      />
    </div>
    <div v-if="!editPluginParamType" class="row items-center q-mb-xs">
      <label class="col-3 q-mb-lg" id="pluginGroup">
        Group:
      </label>
      <q-select
        class="col"
        outlined 
        v-model="plugin.group" 
        :options="store.groups"
        option-label="name"
        option-value="id"
        emit-value
        map-options
        dense
        :rules="[requiredRule]"
        aria-labelledby="pluginGroup"
        aria-required="true"
      />
    </div>
    <div class="row items-center">
      <label class="col-3 " id="description">
        Description:
      </label>
      <q-input
      	class="col"
        v-model="plugin.description"
        outlined
        type="textarea"
        aria-labelledby="description"
        autogrow
        dense
      />
    </div>
    <q-file
      v-model="uploadedFile"
      label="Upload JSON structure"
      outlined
      use-chips
      dense
      accept=".json, text/x-json"
      @update:model-value="processFile"
      class="q-mt-md q-mb-sm"
    >
      <template v-slot:before>
        <label :class="`field-label`">Structure:</label>
        <q-icon name="attach_file" />
      </template>
    </q-file>
    <div style="padding: 0 2%" class="row">
      <CodeEditor 
        v-model="jsonString"
        language="yaml"
        placeholder="Enter Plugin Parameter Type JSON structure..."
        style="width: 0; flex-grow: 1;"
        :showError="jsonError"
      />
    </div>
  </DialogComponent>
</template>

<script setup>
  import DialogComponent from './DialogComponent.vue'
  import { ref, watch } from 'vue'
  import { useLoginStore } from '@/stores/LoginStore.ts'
  import CodeEditor from '@/components/CodeEditor.vue'

  const props = defineProps(['editPluginParamType'])

  const store = useLoginStore()

  const showDialog = defineModel()

  const jsonString = ref('')

  watch(() => jsonString.value, (newVal) => {
    validJsonRule(newVal)
  })

  const plugin = ref({
    name: '',
    group: '',
    description: '',
  })

  function requiredRule(val) {
    return (!!val) || "This field is required"
  }

  const jsonError = ref('')

  function validJsonRule(val) {
    if(val.length === 0) {
      jsonError.value = ''
      return
    }
    try {
      JSON.parse(val)
      jsonError.value = ''
    } catch (e) {
      jsonError.value = 'Invalid JSON format'
    }
  }

  const emit = defineEmits(['addPluginParamType', 'updatePluginParamType'])

  function emitAddOrEdit() {
    if(jsonError.value !== '') return
    if(jsonString.value.length > 0) {
      plugin.value.structure = JSON.parse(jsonString.value)
    } else {
      plugin.value.structure = {}
    }
    if(props.editPluginParamType) {
      emit('updatePluginParamType', props.editPluginParamType.id, plugin.value.name, plugin.value.description, plugin.value.structure)
    } else {
      emit('addPluginParamType', plugin.value)
    }
    showDialog.value = false
  }

  watch(showDialog, (newVal) => {
    if(newVal) {
      plugin.value.name = props.editPluginParamType.name
      plugin.value.description = props.editPluginParamType.description
      if(props.editPluginParamType.structure && Object.keys(props.editPluginParamType.structure).length > 0) {
        jsonString.value = JSON.stringify(props.editPluginParamType.structure, null, 2)
      }
    }
    else {
      plugin.value.name = ''
      plugin.value.group = ''
      plugin.value.description = ''
      jsonString.value = ''
      uploadedFile.value = null
    }
  })

  const uploadedFile = ref(null)

  function processFile() {
    const file = uploadedFile.value
    if (!file) {
      jsonString.value = '{}'
      return
    }
    const reader = new FileReader()
    reader.onload = (e) => {
      jsonString.value = e.target.result;
    }
    reader.onerror = (e) => {
      console.log('error = ', e)
    }
    reader.readAsText(file) // Reads the file as text
  }

</script>