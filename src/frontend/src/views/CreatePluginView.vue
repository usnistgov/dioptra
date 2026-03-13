<template>
  <PageTitle title="Create Plugin" resourceType="plugin" />
  <div :style="{ width: isMobile ? '100%' : isMedium ? '60%' : '50%' }">
    <fieldset class="q-mt-lg">
      <legend>Basic Info</legend>
        <q-form ref="form" class="q-ma-lg">
          <q-input 
            outlined 
            dense 
            v-model.trim="plugin.name"
            :rules="[requiredRule, pythonModuleNameRule]"
            aria-required="true"
            class="q-mb-sm"
          >
            <template v-slot:before>
              <label :class="`field-label`">Name:</label>
            </template>
          </q-input>
          <q-select
            outlined 
            v-model="plugin.group" 
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
            v-model="plugin.description"
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

    <div class="float-right q-mt-lg">
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
        :disable="!valuesChangedFromOriginal"
      >
        <q-tooltip v-if="!valuesChangedFromOriginal">
          No changes detected — nothing to save
        </q-tooltip>
      </q-btn>
    </div>
  </div>


  <ReturnToFormDialog
    v-model="showReturnDialog"
    @cancel="clearForm"
  />
</template>

<script setup>
import PageTitle from '@/components/PageTitle.vue'
import { ref, computed, onMounted, inject } from 'vue'
import { useLoginStore } from '@/stores/LoginStore.ts'
import { useRouter, onBeforeRouteLeave } from 'vue-router'
import * as api from '@/services/dataApi'
import * as notify from '../notify'
import ReturnToFormDialog from '@/dialogs/ReturnToFormDialog.vue'

const store = useLoginStore()
const router = useRouter()
const isMobile = inject('isMobile')
const isMedium = inject('isMedium')

const plugin = ref({
  name: '',
  group: store.loggedInGroup.id,
  description: ''
})

const ORIGINAL_COPY = {
  name: '',
  group: store.loggedInGroup.id,
  description: ''
}

onMounted(() => {
  if(store.savedForms?.plugin) {
    showReturnDialog.value = true
    plugin.value = store.savedForms.plugin
  }
})

const valuesChangedFromOriginal = computed(() => {
  for (const key in ORIGINAL_COPY) {
    if(JSON.stringify(ORIGINAL_COPY[key]) !== JSON.stringify(plugin.value[key])) {
      return true
    }
  }
  return false
})

function requiredRule(val) {
  return (!!val) || "This field is required"
}

function pythonModuleNameRule(val) {
  if (/\s/.test(val)) {
    return "A Python module name cannot contain spaces."
  }
  if (!/^[A-Za-z_]/.test(val)) {
    return "A Python module name must start with a letter or underscore."
  }
  if (!/^[A-Za-z_][A-Za-z0-9_]*$/.test(val)) {
    return "A Python module name can only contain letters, numbers, and underscores."
  }
  if (val === "_") {
    return "A Python module name cannot be '_' with no other characters."
  }
  return true
}

const form = ref(null)

function submit() {
  form.value.validate().then(success => {
    if(success) {
      confirmLeave.value = true
      addPlugin()
    }
  })
}

async function addPlugin() {
  try {
    const res = await api.addItem('plugins', plugin.value)
    notify.success(`Successfully created '${res.data.name}'`)
    store.savedForms.plugin = null
    router.push('/plugins')
  } catch(err) {
    notify.error(err.response.data.message)
  } 
}

const showReturnDialog = ref(false)
const confirmLeave = ref(false)
const toPath = ref()

onBeforeRouteLeave((to, from, next) => {
  toPath.value = to.path
  if(confirmLeave.value) {
    next(true)
  } else if(valuesChangedFromOriginal.value) {
    store.savedForms.plugin = plugin.value
    next(true)
  } else {
    store.savedForms.plugin = null
    next(true)
  }
})

function clearForm() {
  plugin.value = {
    name: '',
    group: store.loggedInGroup.id,
    description: '',
  }
  form.value.reset()
  store.savedForms.plugin = null
}

</script>