<template>
  <div class="row items-center justify-between">
      <PageTitle 
        :subtitle="route.params.id === 'new' ? 'Create Plugin Parameter' : copyAtEditStart?.name"
        conceptType="parameterType" 
      />
      <q-btn 
        v-if="route.params.id !== 'new'"
        color="negative"
        icon="sym_o_delete" 
        label="Delete Plugin Parameter" 
        @click="showDeleteDialog = true"
      />
  </div>
  <div :class="`row q-my-lg ${isMobile ? '' : 'q-gutter-x-xl'}`">
    <fieldset :class="isMobile ? 'col-12' : 'col'">
      <legend>Basic Info</legend>
      <q-form ref="basicInfoForm" class="q-ma-lg">
        <q-input 
          outlined 
          dense 
          v-model.trim="pluginParamType.name"
          :rules="[requiredRule]"
          aria-required="true"
          class="q-mb-sm"
        >
          <template v-slot:before>
            <label :class="`field-label`">Name:</label>
          </template>
        </q-input>
        <q-select
          outlined 
          v-model="pluginParamType.group" 
          :options="store.groups"
          option-label="name"
          option-value="id"
          emit-value
          map-options
          dense
          :rules="[requiredRule]"
          id="pluginGroup"
          class="q-mb-sm"
        >
          <template #before>
            <label for="pluginGroup" class="field-label">Group:</label>
          </template>
        </q-select>
        <q-input
          v-model="pluginParamType.description"
          outlined
          type="textarea"
          dense
          id="pluginDescription"
        >
          <template #before>
            <label for="pluginDescription" class="field-label">Description:</label>
          </template>
        </q-input>
      </q-form>
    </fieldset>
    <fieldset :class="isMobile ? 'col-12' : 'col'" class="q-pa-lg">
      <legend>Structure</legend>
      <q-file
        v-model="uploadedFile"
        label="Upload JSON structure"
        outlined
        use-chips
        dense
        accept=".json, text/x-json"
        @update:model-value="processFile"
        class="q-mt-xs q-mb-sm"
      >
        <template v-slot:before>
          <label :class="`field-label`">Structure:</label>
        </template>
        <template v-slot:prepend>
          <q-icon name="attach_file" />
        </template>
      </q-file>
      <CodeEditor 
        v-model="jsonString"
        language="yaml"
        placeholder="Enter plugin parameter type JSON structure"
        :showError="jsonError"
        style="min-height: 234px;"
        maxHeight="425px"
      />
    </fieldset>
  </div>

  <div class="float-right">
    <q-btn
      outline  
      color="primary" 
      label="Cancel"
      class="q-mr-lg cancel-btn"
      @click="confirmLeave = true; router.back()"
    />
    <q-btn  
      @click="submit()" 
      color="primary"
      label="Submit"
      :disable="jsonError !== '' || !valuesChangedFromEditStart"
    >
      <q-tooltip v-if="jsonError !== ''">
        Fix invalid JSON
      </q-tooltip>
      <q-tooltip v-else-if="!valuesChangedFromEditStart">
        No changes detected — nothing to save
      </q-tooltip>
    </q-btn>
  </div>

  <DeleteDialog 
    v-model="showDeleteDialog"
    @submit="deletePluginParameter()"
    type="Plugin Parameter"
    :name="copyAtEditStart?.name"
  />
  <ReturnToFormDialog
    v-model="showReturnDialog"
    @cancel="clearForm"
  />
</template>

<script setup>
import PageTitle from '@/components/PageTitle.vue'
import { ref, computed, onMounted, inject, watch } from 'vue'
import { useLoginStore } from '@/stores/LoginStore.ts'
import { useRouter, useRoute, onBeforeRouteLeave } from 'vue-router'
import * as api from '@/services/dataApi'
import * as notify from '../notify'
import ReturnToFormDialog from '@/dialogs/ReturnToFormDialog.vue'
import CodeEditor from '@/components/CodeEditor.vue'
import DeleteDialog from '@/dialogs/DeleteDialog.vue'

const store = useLoginStore()
const route = useRoute()
const router = useRouter()
const isMobile = inject('isMobile')

const pluginParamType = ref({
  name: '',
  group: store.loggedInGroup.id,
  description: '',
  structure: null
})

const ORIGINAL_COPY = {
  name: '',
  group: store.loggedInGroup.id,
  description: '',
  structure: null
}

const valuesChangedFromOriginal = computed(() => {
  for (const key in ORIGINAL_COPY) {
    if(JSON.stringify(ORIGINAL_COPY[key]) !== JSON.stringify(pluginParamType.value[key])) {
      return true
    }
  }
  return false
})

const copyAtEditStart = ref()

const valuesChangedFromEditStart = computed(() => {
  for (const key in copyAtEditStart.value) {
    if(JSON.stringify(copyAtEditStart.value[key]) !== JSON.stringify(pluginParamType.value[key])) {
      return true
    }
  }
  return false
})

onMounted(async () => {
  if(store.savedForms?.pluginParamType && route.params.id === 'new') {
    copyAtEditStart.value = JSON.parse(JSON.stringify(pluginParamType.value))
    showReturnDialog.value = true
    pluginParamType.value = store.savedForms.pluginParamType
    if(pluginParamType.value.structure && Object.keys(pluginParamType.value.structure).length > 0) {
      jsonString.value = JSON.stringify(pluginParamType.value.structure, null, 2)
    }
  } else if(route.params.id === 'new') {
    copyAtEditStart.value = JSON.parse(JSON.stringify(pluginParamType.value))
  } else if(route.params.id !== 'new') {
    await getPluginParamType()
    copyAtEditStart.value = JSON.parse(JSON.stringify(pluginParamType.value))
  }
})

async function getPluginParamType() {
  try {
    const res = await api.getItem('pluginParameterTypes', route.params.id)
    pluginParamType.value = res.data
    if(pluginParamType.value.structure) {
      jsonString.value = JSON.stringify(pluginParamType.value.structure, null, 2)
    }
    if(pluginParamType.value.description === null) {
      // the default description is null, not empty string
      pluginParamType.value.description = ''
    }
  } catch(err) {
    notify.error(err.response.data.message)
  }
}

function requiredRule(val) {
  return (!!val) || "This field is required"
}

const jsonString = ref('')
const jsonError = ref('')

watch(() => jsonString.value, (newVal) => {
  validJsonRule(newVal)
  if(newVal.length > 0 && jsonError.value === '') {
    pluginParamType.value.structure = JSON.parse(newVal)
  } else {
    pluginParamType.value.structure = null
  }
})

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

const showReturnDialog = ref(false)
const confirmLeave = ref(false)
const toPath = ref()

onBeforeRouteLeave((to, from, next) => {
  toPath.value = to.path
  if(confirmLeave.value) {
    next(true)
  } else if(valuesChangedFromOriginal.value && route.params.id === 'new') {
    store.savedForms.pluginParamType = pluginParamType.value
    next(true)
  } else {
    store.savedForms.pluginParamType = null
    next(true)
  }
})

function clearForm() {
  pluginParamType.value = ORIGINAL_COPY
  jsonString.value = ''
  basicInfoForm.value.reset()
  store.savedForms.pluginParamType = null
}

const basicInfoForm = ref()

async function submit() {
  basicInfoForm.value.validate().then(success => {
    if(jsonError.value) return
    if(route.params.id === 'new') {
      createPluginParamType()
    } else {
      updatePluginParamType()
    }
  })
}

async function createPluginParamType() {
  try {
    const res = await api.addItem('pluginParameterTypes', pluginParamType.value)
    notify.success(`Successfully created '${res.data.name}'`)
    store.savedForms.pluginParamType = null
    confirmLeave.value = true
    router.push('/pluginParams')
  } catch(err) {
    notify.error(err.response.data.message)
  }
}

async function updatePluginParamType() {
  try {
    const res = await api.updateItem('pluginParameterTypes', route.params.id, 
      {
        name: pluginParamType.value.name,
        description: pluginParamType.value.description, 
        structure: pluginParamType.value.structure
      }
    )
    confirmLeave.value = true
    notify.success(`Successfully updated '${res.data.name}'`)
    router.push('/pluginParams')
  } catch(err) {
    notify.error(err.response.data.message)
  } 
}

const showDeleteDialog = ref(false)

async function deletePluginParameter() {
  try {
    await api.deleteItem('pluginParameterTypes', route.params.id)
    notify.success(`Successfully deleted '${copyAtEditStart.value.name}'`)
    store.savedForms.pluginParamType = null
    showDeleteDialog.value = false
    router.push('/pluginParams')
  } catch(err) {
    notify.error(err.response.data.message);
  }
}

</script>