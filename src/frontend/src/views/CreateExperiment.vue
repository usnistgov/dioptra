<template>
  <PageTitle 
    :title="title"
  />
  <div :class="`row ${isMedium ? '' : 'q-mx-xl'} q-my-lg`">
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
            >
              <template v-slot:before>
                <label :class="`field-label`">Description:</label>
              </template>
            </q-input>
          </q-form>
        </div>
      </fieldset>
    </div>
    <fieldset :class="`${isMobile ? 'col-12 q-mt-lg' : 'col'}`">
      <legend>Entrypoint</legend>
      <div class="q-ma-lg">
        <q-select
          outlined
          dense
          v-model="experiment.entrypoints"
          use-input
          use-chips
          multiple
          emit-value
          map-options
          option-label="name"
          option-value="id"
          input-debounce="300"
          :options="entrypoints"
          @filter="getEntrypoints"
          class="q-mb-md"
        >
          <template v-slot:before>
            <div class="field-label">Entrypoints:</div>
          </template>  
        </q-select>

        <q-btn 
          color="primary"
          icon="add"
          label="Create new Entry Point"
          class="q-mt-lg"
          @click="router.push('/entrypoints/new')" 
        />
      </div>
    </fieldset>
  </div>

  <div :class="`${isMobile ? '' : 'q-mx-xl'} float-right q-mb-lg`">
      <q-btn  
        to="/experiments"
        color="negative" 
        label="Cancel"
        class="q-mr-lg"
        @click="confirmLeave = true"
      />
      <q-btn  
        @click="submit()" 
        color="primary" 
        label="Submit Experiment"
      />
    </div>

    <LeaveFormDialog 
      v-model="showLeaveDialog"
      type="experiment"
      @leaveForm="confirmLeave = true; router.push(toPath)"
    />
</template>

<script setup>
  import { ref, inject, computed } from 'vue'
  import { useLoginStore } from '@/stores/LoginStore.ts'
  import { useRouter, useRoute, onBeforeRouteLeave } from 'vue-router'
  import * as api from '@/services/dataApi'
  import * as notify from '../notify'
  import PageTitle from '@/components/PageTitle.vue'
  import LeaveFormDialog from '@/dialogs/LeaveFormDialog.vue'

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
    group: '',
    description: '',
    entrypoints: [],
  })

  const isEmptyValues = computed(() => {
    return Object.values(experiment.value).every((value) => 
      (typeof value === 'string' && value === '') || 
      (Array.isArray(value) && value.length === 0)
    )
  })

  const basicInfoForm = ref(null)

  let initialCopy = ref({
    name: '',
    group: '',
    description: '',
    entrypoints: [],
  })

  const valuesChanged = computed(() => {
    for (const key in initialCopy.value) {
      if(JSON.stringify(initialCopy.value[key]) !== JSON.stringify(experiment.value[key])) {
        return true
      }
    }
    return false
  })

  const title = ref('')
  getExperiment()
  async function getExperiment() {
    if(route.params.id === 'new') {
      title.value = 'Create Experiment'
      return
    }
    try {
      const res = await api.getItem('experiments', route.params.id)
      experiment.value = res.data
      initialCopy.value = JSON.parse(JSON.stringify({
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
    try {
      if(route.params.id === 'new') {
        await api.addItem('experiments', experiment.value)
        notify.success(`Successfully created '${experiment.value.name}'`)
      } else {
        experiment.value.entrypoints.forEach((entrypoint, index, array) => {
          if(typeof entrypoint === 'object') {
            array[index] = entrypoint.id
          }
        })
        await api.updateItem('experiments', route.params.id, {
        name: experiment.value.name,
        description: experiment.value.description,
        entrypoints: experiment.value.entrypoints
      })
        notify.success(`Successfully updated '${experiment.value.name}'`)
      }
    } catch(err) {
      console.log('err = ', err)
      notify.error(err.response.data.message)
    } finally {
      router.push('/experiments')
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
    if(confirmLeave.value) {
      next(true)
    } else if(!isEmptyValues.value && valuesChanged.value) {
      showLeaveDialog.value = true
    } else {
      next(true)
    }
  })

  const showLeaveDialog = ref(false)
  const confirmLeave = ref(false)
  const toPath = ref()

</script>