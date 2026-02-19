<template>
  <div class="row items-center justify-between">
    <div class="row items-center">
      <PageTitle 
        :title="title"
        :draftLabel="resourceDraft ? 'Resource Draft' : 'Draft'"
      />
    </div>
    <div>
      <q-btn 
        v-if="route.params.id !== 'new'"
        color="negative"
        icon="sym_o_delete" 
        label="Delete Queue"
        @click="showDeleteDialog = true"
      />
    </div>
  </div>
  <div :style="{ width: isMobile ? '100%' : isMedium ? '60%' : '50%' }">
    <fieldset class="q-mt-lg">
      <legend>Basic Info</legend>
        <q-form ref="form" class="q-ma-lg">
          <q-input 
            outlined 
            dense 
            v-model.trim="queue.name"
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
            v-model="queue.group" 
            :options="store.groups"
            option-label="name"
            option-value="id"
            emit-value
            map-options
            dense
            :rules="[requiredRule]"
            id="queueGroup"
            class="q-mb-sm"
          >
            <template #before>
              <label for="queueGroup" class="field-label">Group:</label>
            </template>
          </q-select>
          <q-input
            v-model="queue.description"
            outlined
            type="textarea"
            dense
            id="queueDescription"
          >
            <template #before>
              <label for="queueDescription" class="field-label">Description:</label>
            </template>
          </q-input>
        </q-form>
    </fieldset>

    <div class="q-mt-lg">
      <q-btn
        v-show="(resourceDraft && !newResourceDraft) || route.params.draftType === 'draft'"
        label="Convert to Resource"
        color="secondary"
        @click="convertToResource()"
      />
      <div class="float-right">
        <q-btn
          outline  
          color="primary" 
          label="Cancel"
          class="q-mr-lg cancel-btn"
          @click="confirmLeave = true; store.initialPage ? router.push('/queues') : router.back()"
        />
        <q-btn  
          @click="submit()" 
          color="primary"
          label="Submit"
          :disable="!valuesChangedFromEditStart"
        >
          <q-tooltip v-if="!valuesChangedFromEditStart">
            No changes detected — nothing to save
          </q-tooltip>
        </q-btn>
      </div>
    </div>
  </div>

  <ReturnToFormDialog
    v-model="showReturnDialog"
    @cancel="clearForm"
  />
  <DeleteDialog 
    v-model="showDeleteDialog"
    @submit="deleteDraft()"
    type="Queue"
    :name="copyAtEditStart?.name"
  />
</template>

<script setup>
import PageTitle from '@/components/PageTitle.vue'
import { ref, computed, onMounted, inject, watch } from 'vue'
import { useLoginStore } from '@/stores/LoginStore.ts'
import { useRoute, useRouter, onBeforeRouteLeave } from 'vue-router'
import * as api from '@/services/dataApi'
import * as notify from '../notify'
import ReturnToFormDialog from '@/dialogs/ReturnToFormDialog.vue'
import DeleteDialog from '@/dialogs/DeleteDialog.vue'

const store = useLoginStore()
const route = useRoute()
const router = useRouter()
const isMobile = inject('isMobile')
const isMedium = inject('isMedium')
const darkMode = inject('darkMode')

const queue = ref({
  name: '',
  group: store.loggedInGroup.id,
  description: ''
})

const ORIGINAL_COPY = {
  name: '',
  group: store.loggedInGroup.id,
  description: ''
}

const copyAtEditStart = ref()

const valuesChangedFromEditStart = computed(() => {
  for (const key in copyAtEditStart.value) {
    if(JSON.stringify(copyAtEditStart.value[key]) !== JSON.stringify(queue.value[key])) {
      return true
    }
  }
  return false
})


onMounted(async () => {
  if(store.savedForms?.queue && route.params.id === 'new') {
    copyAtEditStart.value = JSON.parse(JSON.stringify(queue.value))
    showReturnDialog.value = true
    queue.value = store.savedForms.queue
  } else if(route.params.id !== 'new' && !resourceDraft.value) {
    // edit draft
    await getDraft()
    copyAtEditStart.value = JSON.parse(JSON.stringify(queue.value))
  } else if(newResourceDraft.value) {
    // crate new resource draft
    copyAtEditStart.value = JSON.parse(JSON.stringify(queue.value))
  } else if(resourceDraft.value) {
    // edit resource draft
    await getResourceDraft()
    copyAtEditStart.value = JSON.parse(JSON.stringify(queue.value))
  }
})

async function getDraft() {
  try {
    const res = await api.getItem('queues', route.params.id, true)
    queue.value = res.data
  } catch(err) {
    notify.error(err.response.data.message)
  }
}

async function getResourceDraft() {
  try {
    const res = await api.getResourceDraft('queues', route.params.id)
    console.log('getResourceDraft = ', res)
    queue.value = res.data
  } catch(err) {
    notify.error(err.response.data.message)
  }
}

const valuesChangedFromOriginal = computed(() => {
  for (const key in ORIGINAL_COPY) {
    if(JSON.stringify(ORIGINAL_COPY[key]) !== JSON.stringify(queue.value[key])) {
      return true
    }
  }
  return false
})

function requiredRule(val) {
  return (!!val) || "This field is required"
}

const form = ref(null)

function submit() {
  form.value.validate().then(success => {
    if(!success) return
    confirmLeave.value = true
    if(newResourceDraft.value) {
      createResourceDraft()
    } else if(resourceDraft.value) {
      updateResourceDraft()
    } else if(route.params.id !== 'new') {
      updateDraft()
    }
  })
}

async function createResourceDraft() {
  const params = {
    name: queue.value.name,
    description: queue.value.description,
  }
  try {
    const res = await api.addDraft('queues', params, route.params.id)
    notify.success(`Successfully created '${res.data.payload.name}'`)
    store.savedForms.queue = null
    router.push('/queues')
  } catch(err) {
    notify.error(err.response.data.message)
  } 
}

async function updateResourceDraft() {
  const params = {
    name: queue.value.name,
    description: queue.value.description,
  }
  try {
    const res = await api.updateDraftLinkedtoQueue(route.params.id, queue.value.name, queue.value.description, queue.value.resourceSnapshot)
    notify.success(`Successfully updated '${res.data.payload.name}'`)
    store.savedForms.queue = null
    router.push('/queues')
  } catch(err) {
    notify.error(err.response.data.message)
  } 
}

async function updateDraft() {
  try {
    const res = await api.updateDraft('queues', route.params.id, 
      {
        name: queue.value.name,
        description: queue.value.description, 
      }
    )
    notify.success(`Successfully updated '${res.data.payload.name}'`)
    router.push('/queues')
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
  } else if(valuesChangedFromEditStart.value && route.params.id === 'new') {
    store.savedForms.queue = queue.value
    next(true)
  } else {
    store.savedForms.queue = null
    next(true)
  }
})

function clearForm() {
  queue.value = {
    name: '',
    group: store.loggedInGroup.id,
    description: '',
  }
  form.value.reset()
  store.savedForms.queue = null
}

watch(() => store.selectedSnapshot, (q) => {
  if(q) {
    queue.value = {
      name: q.name,
      group: q.group.id,
      description: q.description,
    }
  } else {
    getQueue()
  }
})

const showDeleteDialog = ref(false)

async function deleteDraft() {
  try {
    const name = JSON.parse(JSON.stringify(queue.value.name))
    if(resourceDraft.value) {
      await api.deleteResourceDraft('queues', route.params.id)
    } else {
      await api.deleteDraft('queues', route.params.id)
    }
    notify.success(`Successfully deleted '${name}'`)
    store.savedForms.queue = null
    showDeleteDialog.value = false
    router.push('/queues')
  } catch(err) {
    notify.error(err.response.data.message)
  }
}

async function convertToResource() {
  try {
    const name = JSON.parse(JSON.stringify(queue.value.name))
    if(resourceDraft.value) {
      await api.updateDraftLinkedtoQueue(
        route.params.id, 
        queue.value.name, 
        queue.value.description, 
        queue.value.resourceSnapshot
      )
    } else {
      await api.updateDraft('queues', route.params.id, 
        { name: queue.value.name, description: queue.value.description }
      )
    }
    await api.convertToResource(queue.value.id)
    store.savedForms.queue = null
    router.push('/queues')
    notify.success(`Successfully converted '${name}'`)
  } catch(err) {
    notify.error(err.response.data.message);
  }
}

const title = computed(() => {
  if(newResourceDraft.value) return 'Create Resource Draft'
  else return copyAtEditStart.value?.name
})

const newResourceDraft = computed(() => {
  return route.params.newResourceDraft === 'new'
})

const resourceDraft = computed(() => {
  return route.params.draftType === 'resourceDraft'
})

</script>