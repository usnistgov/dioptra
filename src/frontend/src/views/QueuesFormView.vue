<template>
  <div class="row items-center justify-between">
    <div class="row items-center">
      <PageTitle :title="route.params.id === 'new' ? 'Create Queue' : copyAtEditStart?.name" />
        <q-chip
          v-if="route.params.id !== 'new'"
          class="q-ml-md"
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
    <div>
      <q-btn 
        v-if="route.params.id !== 'new'"
        :color="history ? 'red-3' : 'negative'" 
        icon="sym_o_delete" 
        label="Delete Queue"
        @click="showDeleteDialog = true"
        :disable="history"
      />
    </div>
  </div>
  <div :style="{ width: isMobile ? '100%' : isMedium ? '60%' : '50%' }" :class="history ? `disabled` : ``">
    <fieldset class="q-mt-lg" :style="{ 'pointer-events': history ? 'none' : '' }">
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
        v-if="route.params.id === 'new'"
        @click="submitDraft()"
        label="Save As Draft"
        color="secondary"
        :disable="!valuesChangedFromEditStart || history"
      />
      <div class="float-right">
        <q-btn
          outline  
          color="primary" 
          label="Cancel"
          class="q-mr-lg cancel-btn"
          @click="confirmLeave = true; store.initialPage ? router.push('/queues') : router.back()"
          :disable="history"
        />
        <q-btn  
          @click="submit()" 
          color="primary"
          label="Submit"
          :disable="!valuesChangedFromEditStart || history"
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
    @submit="deleteQueue()"
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
  } else if(route.params.id === 'new') {
    copyAtEditStart.value = JSON.parse(JSON.stringify(queue.value))
  } else if(route.params.id !== 'new') {
    await getQueue()
    copyAtEditStart.value = JSON.parse(JSON.stringify(queue.value))
  }
})

async function getQueue() {
  try {
    const res = await api.getItem('queues', route.params.id)
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
    if(route.params.id === 'new') {
      createQueue()
    }
    else if(route.params.id !== 'new') {
      updateQueue()
    }
  })
}

function submitDraft() {
  form.value.validate().then(success => {
    if(!success) return
    confirmLeave.value = true
    if(route.params.id === 'new') {
      createDraft()
    }
  })
}

async function createQueue() {
  try {
    const res = await api.addItem('queues', queue.value)
    notify.success(`Successfully created '${res.data.name}'`)
    store.savedForms.queue = null
    router.push('/queues')
  } catch(err) {
    notify.error(err.response.data.message)
  } 
}

async function createDraft() {
  try {
    const params = {
      name: queue.value.name,
      description: queue.value.description,
      group: queue.value.group
    }
    const res = await api.addDraft('queues', params)
    notify.success(`Successfully created '${res.data.payload.name}'`)
    store.savedForms.queue = null
    router.push('/queues')
  } catch(err) {
    notify.error(err.response.data.message)
  } 
}

async function updateQueue() {
  try {
    const res = await api.updateItem('queues', route.params.id, 
      {
        name: queue.value.name,
        description: queue.value.description, 
      }
    )
    notify.success(`Successfully updated '${res.data.name}'`)
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

const history = computed(() => {
  return store.showRightDrawer
})

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

async function deleteQueue() {
  try {
    await api.deleteItem('queues', route.params.id)
    notify.success(`Successfully deleted '${copyAtEditStart.value.name}'`)
    store.savedForms.queue = null
    showDeleteDialog.value = false
    router.push('/queues')
  } catch(err) {
    notify.error(err.response.data.message);
  }
}

</script>