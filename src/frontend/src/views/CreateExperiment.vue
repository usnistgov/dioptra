<template>
  <div class="row items-center justify-between">
    <div class="row items-center">
      <PageTitle :title="title" />
      <q-chip
        v-if="route.params.id !== 'new'"
        class="q-ml-lg"
      >
        <q-toggle
          v-model="store.showRightDrawer"
          left-label
          label="View History"
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

  <div :class="`row q-my-lg`">
    <div :class="`${isMobile ? 'col-12' : 'col-5'} q-mr-xl`">
      <fieldset>
        <legend>Basic Info</legend>
        <div class="q-ma-lg">
          <q-form ref="basicInfoForm" greedy>
            <q-input 
              outlined 
              dense 
              v-model.trim="experiment.name"
              :rules="[requiredRule]"
              class="q-mb-sm q-mt-md"
              aria-required="true"
              :disable="history"
            >
              <template v-slot:before>
                <label :class="`field-label`">Name:</label>
              </template>
            </q-input>
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
            >
              <template v-slot:before>
                <div class="field-label">Group:</div>
              </template>  
            </q-select>
            <q-input 
              outlined 
              dense 
              v-model.trim="experiment.description"
              class="q-mb-sm q-mt-sm"
              type="textarea"
              :disable="history"
            >
              <template v-slot:before>
                <label :class="`field-label`">Description:</label>
              </template>
            </q-input>
          </q-form>
        </div>
      </fieldset>
    </div>
    <fieldset :class="`${isMobile ? 'col-12 q-mt-lg' : 'col'}`" :disabled="history">
      <legend>Entrypoint</legend>
      <div class="q-ma-lg">
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

        <q-btn
          v-if="!history"
          color="primary"
          icon="add"
          label="Create new Entry Point"
          class="q-mt-lg"
          @click="router.push('/entrypoints/new')" 
        />

        <div class="row items-center" v-if="history">
          <q-icon
            name="sym_o_info"
            size="2.5em"
            color="grey"
            class="q-mr-sm"
          />
          <div>Entrypoints are not part of Experiment snapshots</div>
        </div>
      </div>
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
        :color="history ? 'blue-2' : 'primary'" 
        label="Submit Experiment"
        :disable="history"
      />
    </div>

    <LeaveFormDialog 
      v-model="showLeaveDialog"
      type="experiment"
      @leaveForm="leaveForm"
    />
    <ReturnToFormDialog
      v-model="showReturnDialog"
      @cancel="clearForm"
    />
    <DeleteDialog
      v-model="showDeleteDialog"
      @submit="deleteExperiment"
      type="Experiment"
      :name="experiment.name"
    />
</template>

<script setup>
  import { ref, inject, computed, watch } from 'vue'
  import { useLoginStore } from '@/stores/LoginStore.ts'
  import { useRouter, useRoute, onBeforeRouteLeave } from 'vue-router'
  import * as api from '@/services/dataApi'
  import * as notify from '../notify'
  import PageTitle from '@/components/PageTitle.vue'
  import LeaveFormDialog from '@/dialogs/LeaveFormDialog.vue'
  import ReturnToFormDialog from '@/dialogs/ReturnToFormDialog.vue'
  import DeleteDialog from '@/dialogs/DeleteDialog.vue'

  const route = useRoute()
  
  const router = useRouter()

  const store = useLoginStore()

  const isMobile = inject('isMobile')
  const isMedium = inject('isMedium')

  function requiredRule(val) {
    return (!!val) || "This field is required"
  }

  let experiment = ref({
    name: '',
    group: store.loggedInGroup.id,
    description: '',
    entrypoints: [],
  })

  function clearForm() {
    experiment.value = {
      name: '',
      group: store.loggedInGroup.id,
      description: '',
      entrypoints: [],
    }
    basicInfoForm.value.reset()
    store.savedForms.experiment = null
  }

  async function checkIfStillValid() {
    for(let index = store.savedForms.experiment.entrypoints.length - 1; index >= 0; index--) {
      let id = store.savedForms.experiment.entrypoints[index].id
      try {
        const res =  await api.getItem('entrypoints', id)
      } catch(err) {
        await store.savedForms.experiment.entrypoints.splice(index, 1)
        console.warn(err)
      } 
    }
  }

  const basicInfoForm = ref(null)

  let copyAtEditStart = ref({
    name: '',
    group: store.loggedInGroup.id,
    description: '',
    entrypoints: [],
  })

  const valuesChangedFromEditStart = computed(() => {
    for (const key in copyAtEditStart.value) {
      if(JSON.stringify(copyAtEditStart.value[key]) !== JSON.stringify(experiment.value[key])) {
        return true
      }
    }
    return false
  })

  const ORIGINAL_COPY = {
    name: '',
    group: store.loggedInGroup.id,
    description: '',
    entrypoints: [],
  }

  const valuesChangedFromOriginal = computed(() => {
    for (const key in ORIGINAL_COPY) {
      if(JSON.stringify(ORIGINAL_COPY[key]) !== JSON.stringify(experiment.value[key])) {
        return true
      }
    }
    return false
  })

  const title = ref('')
  const showReturnDialog = ref(false)

  getExperiment()
  async function getExperiment() {
    if(route.params.id === 'new') {
      title.value = 'Create Experiment'
      if(store.savedForms?.experiment) {
        showReturnDialog.value = true
        await checkIfStillValid()
        copyAtEditStart.value = JSON.parse(JSON.stringify({
          name: store.savedForms.experiment.name,
          group: store.savedForms.experiment.group,
          description: store.savedForms.experiment.description,
          entrypoints: store.savedForms.experiment.entrypoints,
        }))
        experiment.value = store.savedForms.experiment
      }
      return
    }
    try {
      const res = await api.getItem('experiments', route.params.id)
      experiment.value = res.data
      copyAtEditStart.value = JSON.parse(JSON.stringify({
        name: res.data.name,
        group: res.data.group,
        description: res.data.description,
        entrypoints: res.data.entrypoints,
      }))
      title.value = `Edit ${res.data.name}`
      console.log('experiment = ', experiment.value)
    } catch(err) {
      console.log('err = ', err)
      notify.error(err.response.data.message)
    } 
  }

  function submit() {
    basicInfoForm.value.validate().then(success => {
      if(success) {
        confirmLeave.value = true
        addorModifyExperiment()
      }
    })
  }

  async function addorModifyExperiment() {
    experiment.value.entrypoints.forEach((entrypoint, index, array) => {
      if(typeof entrypoint === 'object') {
        array[index] = entrypoint.id
      }
    })
    try {
      if(route.params.id === 'new') {
        await api.addItem('experiments', experiment.value)
        store.savedForms.experiment = null
        notify.success(`Successfully created '${experiment.value.name}'`)
      } else {
        await api.updateItem('experiments', route.params.id, {
        name: experiment.value.name,
        description: experiment.value.description,
        entrypoints: experiment.value.entrypoints
      })
        notify.success(`Successfully updated '${experiment.value.name}'`)
      }
      router.push('/experiments')
    } catch(err) {
      console.log('err = ', err)
      notify.error(err.response.data.message)
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

  onBeforeRouteLeave((to, from, next) => {
    toPath.value = to.path
    if(confirmLeave.value || !valuesChangedFromEditStart.value || history.value) {
      next(true)
    } else if(route.params.id === 'new') {
      leaveForm()
    } else {
      showLeaveDialog.value = true
    }
  })

  const showLeaveDialog = ref(false)
  const confirmLeave = ref(false)
  const toPath = ref()

  function leaveForm() {
    if(route.params.id === 'new' && valuesChangedFromEditStart.value && valuesChangedFromOriginal.value) {
      store.savedForms.experiment = experiment.value
    } else {
      store.savedForms.experiment = null
    }
    confirmLeave.value = true
    router.push(toPath.value)
  }

  const history = computed(() => {
    return store.showRightDrawer
  })

  watch(() => store.selectedSnapshot, (newVal) => {
    if(newVal) {
      experiment.value = {
        name: newVal.name,
        group: newVal.group,
        description: newVal.description
      }
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