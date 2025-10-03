<template>
  <div class="row items-center justify-between">
    <div class="row items-center">
      <PageTitle :title="ORIGINAL_EXPERIMENT?.name" />
      <q-chip
        v-if="route.params.id !== 'new'"
        class="q-ml-lg"
        :color="`${darkMode ? 'grey-9' : ''}`"
        label="View History"
        icon="history"
        @click="store.showRightDrawer = !store.showRightDrawer"
        clickable
      >
        <q-toggle
          v-model="store.showRightDrawer"
          left-label
          color="orange"
        />
      </q-chip>
    </div>
    <q-btn 
      v-if="route.params.id !== 'new'"
      :color="history ? 'red-3' : 'negative'" 
      icon="sym_o_delete" 
      label="Delete Experiment" 
      @click="showDeleteDialog = true"
      :disable="history"
    />
  </div>

  <fieldset 
    class="q-mt-md q-pa-lg"
    style="display: inline-block; width: auto; height: auto; max-width: 50%;"
    :style="{ cursor: history ? 'not-allowed' : 'auto', }"
    :disabled="history"
  >
    <legend>Metadata</legend>
    <KeyValueTable 
      :rows="metadataRows"
      :style="{ pointerEvents: history ? 'none' : 'auto', }"
    >
      <template #name="{ }">
        {{ experiment?.name }}
        <q-btn icon="edit" round size="sm" color="primary" flat />
        <q-popup-edit
          v-model="experiment.name" 
          auto-save 
          v-slot="scope"
          :validate="requiredRule"
        >
          <q-input 
            v-model.trim="scope.value"
            dense
            autofocus
            counter
            @keyup.enter="scope.set"
            :error="invalidName"
            :error-message="nameError"
            @update:model-value="checkName"
          />
        </q-popup-edit>
      </template>
      <template #group="{ }">
        <q-select
          outlined 
          v-model="experiment.group" 
          :options="store.groups"
          option-label="name"
          option-value="id"
          emit-value
          map-options
          dense
          :rules="[requiredRule]"
          aria-required="true"
          :disable="history"
          hide-bottom-space
        />
      </template>
      <template #description="{ }">
        <div class="row items-center no-wrap">
          <div style="white-space: pre-line; overflow-wrap: break-word; ">
            {{ experiment?.description }}
          </div>
          <q-btn icon="edit" round size="sm" color="primary" flat class="q-ml-xs" />
        </div>
        <q-popup-edit v-model.trim="experiment.description" auto-save v-slot="scope" buttons>
          <q-input
            v-model="scope.value"
            dense
            autofocus
            counter
            type="textarea"
            @keyup.enter.stop
          />
        </q-popup-edit>
      </template>
      <template #entrypoints="{ }">
        <q-select
          v-if="!history"
          outlined
          dense
          v-model="experiment.entrypoints"
          use-input
          use-chips
          multiple
          map-options
          option-label="name"
          option-value="id"
          input-debounce="300"
          :options="entrypoints"
          @filter="getEntrypoints"
          class="q-mb-md"
          :disable="history"
        >
          <template v-slot:before>
            <div class="field-label">Entrypoints:</div>
          </template>
          <template v-slot:selected>
            <q-chip
              v-for="(entrypoint, i) in experiment.entrypoints"
              :key="entrypoint.id"
              color="secondary"
              :label="entrypoint.name"
              class="text-white"
              removable
              @remove="experiment.entrypoints.splice(i, 1)"
            />
          </template>  
        </q-select>
        <div class="row items-center" v-if="history">
          <q-icon
            name="sym_o_info"
            size="2.5em"
            color="grey"
            class="q-mr-sm"
          />
          <div style="flex: 1; white-space: normal; word-break: break-word;">
            Entrypoints are not yet available in Experiment snapshots
          </div>
        </div>
      </template>
    </KeyValueTable>
    <div class="float-right q-mt-md">
      <q-btn
        outline  
        color="primary" 
        label="Revert"
        class="q-mr-lg cancel-btn"
        @click="revertValues"
        :disable="!valuesChanged"
      />
      <q-btn
        label="Save"
        color="primary"
        @click="updateExperiment"
        :disable="!valuesChanged"
      />
    </div>
  </fieldset>
  <JobsView /> 

  <DeleteDialog
    v-model="showDeleteDialog"
    @submit="deleteExperiment"
    type="Experiment"
    :name="experiment.name"
  />
</template>

<script setup>
import { ref, inject, computed, watch, onMounted } from 'vue'
import { useLoginStore } from '@/stores/LoginStore.ts'
import { useRouter, useRoute } from 'vue-router'
import * as api from '@/services/dataApi'
import * as notify from '../notify'
import PageTitle from '@/components/PageTitle.vue'
import DeleteDialog from '@/dialogs/DeleteDialog.vue'
import KeyValueTable from '@/components/KeyValueTable.vue'
import JobsView from './JobsView.vue'

const route = useRoute()

const router = useRouter()

const store = useLoginStore()
const isMobile = inject('isMobile')
const isMedium = inject('isMedium')
const darkMode = inject('darkMode')

const experiment = ref({
  name: '',
  group: store.loggedInGroup.id,
  description: '',
  entrypoints: [],
})
const ORIGINAL_EXPERIMENT = ref()

const history = computed(() => {
  return store.showRightDrawer
})

onMounted(() => {
  getExperiment()
})

async function getExperiment() {
  try {
    const res = await api.getItem('experiments', route.params.id)
    experiment.value = res.data
    ORIGINAL_EXPERIMENT.value = JSON.parse(JSON.stringify(experiment.value))
    // copyAtEditStart.value = JSON.parse(JSON.stringify({
    //   name: res.data.name,
    //   group: res.data.group,
    //   description: res.data.description,
    //   entrypoints: res.data.entrypoints,
    // }))
  } catch(err) {
    console.log('err = ', err)
    notify.error(err.response.data.message)
  } 
}

const metadataRows = computed(() => [
  { label: 'Name', slot: 'name' },
  { label: 'Group', slot: 'group' },
  { label: 'Description', slot: 'description' },
  { label: 'Entrypoints', slot: 'entrypoints' },
])

const invalidName = ref(false)
const nameError = ref('')

function requiredRule(val) {
  if(!val || val.length === 0) {
    invalidName.value = true
    nameError.value = 'Name is required'
    return false
  }
  invalidName.value = false
  nameError.value = ''
  return true
}

function checkName(val) {
  if(val.length === 0) {
    invalidName.value = true
    nameError.value = 'Name is required'
  } else {
    invalidName.value = false
    nameError.value = ''
  }
}

const entrypoints = ref([])

async function getEntrypoints(val = '', update) {
  update(async () => {
    try {
      const res = await api.getData('entrypoints', {
        search: val,
        rowsPerPage: 0, // get all
        index: 0
      })
      entrypoints.value = res.data.data
    } catch(err) {
      notify.error(err.response.data.message)
    } 
  })
}

const valuesChanged = computed(() => {
  return JSON.stringify(ORIGINAL_EXPERIMENT.value) !== JSON.stringify(experiment.value)
})

function revertValues() {
  experiment.value = JSON.parse(JSON.stringify(ORIGINAL_EXPERIMENT.value))
}

async function updateExperiment() {
  experiment.value.entrypoints.forEach((entrypoint, index, array) => {
    if(typeof entrypoint === 'object') {
      array[index] = entrypoint.id
    }
  })
  try {
    const res = await api.updateItem('experiments', route.params.id, {
      name: experiment.value.name,
      description: experiment.value.description,
      entrypoints: experiment.value.entrypoints
    })
    getExperiment()
    notify.success(`Successfully updated '${res.data.name}'`)
  } catch(err) {
    notify.error(err.response.data.message)
  }  
}

watch(() => store.selectedSnapshot, (newVal) => {
  if(newVal) {
    experiment.value = newVal
  } else {
    getExperiment()
  }
})

const showDeleteDialog = ref(false)

async function deleteExperiment() {
  try {
    await api.deleteItem('experiments', experiment.value.id)
    notify.success(`Successfully deleted '${experiment.value.name}'`)
    router.push(`/experiments`)
  } catch(err) {
    notify.error(err.response.data.message);
  }
}

</script>