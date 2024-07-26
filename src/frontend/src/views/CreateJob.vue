<template>
  <PageTitle 
    title="Create Job"
  />
  <div :class="`row ${isMobile ? '' : 'q-mx-xl'} q-my-lg`">
    <div :class="`${isMobile ? 'col-12' : 'col-5'} q-mr-xl`">
      <fieldset>
        <legend>Basic Info</legend>
        <div class="q-ma-lg">
          <q-form ref="basicInfoForm" greedy>
            <q-input 
              outlined 
              dense 
              v-model.trim="job.description"
              class="q-mb-lg"
              type="textarea"
              autogrow
            >
              <template v-slot:before>
                <label :class="`field-label`">Description:</label>
              </template>
            </q-input>
            <q-select
              outlined
              dense
              v-model="job.queue"
              clearable
              use-input
              emit-value
              map-options
              option-label="name"
              option-value="id"
              input-debounce="100"
              :options="queues"
              @filter="getQueues"
              :rules="[requiredRule]"
              class="q-mb-sm"
            >
              <template v-slot:before>
                <div class="field-label">Queue:</div>
              </template>  
            </q-select>
            <q-select
              outlined
              dense
              v-model="selectedEntrypoint"
              clearable
              use-input
              map-options
              option-label="name"
              option-value="id"
              input-debounce="100"
              :options="entrypoints"
              @filter="getEntrypoints"
              :rules="[requiredRule]"
              class="q-mb-sm"
              hint="Select Entrypoint in order to edit values on the right"
            >
              <template v-slot:before>
                <div class="field-label">Entrypoint:</div>
              </template>  
            </q-select>
            <q-input
              outlined 
              v-model="job.timeout" 
              dense
              aria-required="true"
              class="q-mb-lg"
              :rules="[timeUnitRule]"
            >
              <template v-slot:before>
                <div class="field-label">Timeout:</div>
              </template>  
            </q-input>
          </q-form>
        </div>
      </fieldset>
    </div>
    <fieldset :class="`${isMobile ? 'col-12 q-mt-lg' : 'col'}`" :disabled="selectedEntrypoint === ''">
      <legend>Values</legend>
      <div class="q-px-xl">
        <BasicTable
          :columns="columns"
          :rows="parameters"
          :hideSearch="true"
          :hideEditTable="true"
          :hideDelete="true"
          @edit="(param, i) => {selectedParam = param; selectedParamIndex = i; showEditParamDialog = true}"
          @delete="(param) => {selectedParam = param; showDeleteDialog = true}"
          :inlineEditFields="['value']"
        />
      </div>
    </fieldset>
  </div>

  <div :class="`${isMobile ? '' : 'q-mx-xl'} float-right q-mb-lg`">
      <q-btn  
        :to="`/experiments/${route.params.id}/jobs`"
        color="negative" 
        label="Cancel"
        class="q-mr-lg"
      />
      <q-btn  
        @click="submit()" 
        color="primary" 
        label="Submit Job"

      />
    </div>

  <DeleteDialog 
    v-model="showDeleteDialog"
    @submit="deleteParam()"
    type="Parameter"
    :name="selectedParam.name"
  />

  <EditJobParamDialog 
    v-model="showEditParamDialog"
    :editParam="selectedParam"
    @updateParam="updateParam"
  />
</template>

<script setup>
  import { ref, inject, watch, computed } from 'vue'
  import { useRouter } from 'vue-router'
  import DeleteDialog from '@/dialogs/DeleteDialog.vue'
  import EditJobParamDialog from '@/dialogs/EditJobParamDialog.vue'
  import BasicTable from '@/components/BasicTable.vue'
  import { useRoute } from 'vue-router'
  import * as api from '@/services/dataApi'
  import * as notify from '../notify'
  import PageTitle from '@/components/PageTitle.vue'

  const route = useRoute()
  
  const router = useRouter()

  const isMobile = inject('isMobile')

  function requiredRule(val) {
    return (!!val) || "This field is required"
  }

  function timeUnitRule(val) {
    return (/^\d+[hms]$/.test(val)) || "Value must be an integer followed by 'h', 'm', or 's'";
  }


  const job = ref({
    description: '',
    timeout: '24h',
    queue: '',
    entrypoint: '',
  })

  const selectedEntrypoint = ref('')

  const parameters = ref([])
  const computedValue = computed(() => {
    let output = {}
    if(parameters.value.legnth === 0) return output
    parameters.value.forEach((param) => {
      output[param.name] = param.value
    })
    return output
  })

  watch(() => selectedEntrypoint.value, (newVal) => {
    parameters.value = []
    if(Array.isArray(newVal?.parameters)) {
      newVal.parameters.forEach((param) => {
        parameters.value.push({
          name: param.name,
          value: param.defaultValue,
          type: param.parameterType
        })
      })
    }
  })

  const basicInfoForm = ref(null)

  const columns = [
    { name: 'name', label: 'Name', align: 'left', field: 'name', sortable: true, },
    { name: 'value', label: 'Value', align: 'left', field: 'value', sortable: true, },
    { name: 'parameterType', label: 'Type', align: 'left', field: 'type', sortable: true, },
    // { name: 'actions', label: 'Actions', align: 'center',  },
  ]

  function submit() {
    basicInfoForm.value.validate().then(success => {
      if (success) {
        createJob()
      }
      else {
        // error
      }
    })
  }

  async function createJob() {
    job.value.entrypoint = selectedEntrypoint.value.id
    job.value.values = computedValue.value
    console.log('submitting job = ', JSON.parse(JSON.stringify(job.value)))
    try {
      await api.addJob(route.params.id, job.value)
      notify.success(`Sucessfully created ''`)
    } catch(err) {
      notify.error(err.response.data.message)
    } finally {
      router.push(`/experiments/${route.params.id}/jobs`)
    }
  }

  const showDeleteDialog = ref(false)
  const selectedParam = ref({})
  const selectedParamIndex = ref('')

  function deleteParam() {
    parameters.value = parameters.value.filter((param) => param.name !== selectedParam.value.name)
    showDeleteDialog.value = false
  }

  const showEditParamDialog = ref(false)

  function updateParam(parameter) {
    parameters.value[selectedParamIndex.value] = { ...parameter }
    showEditParamDialog.value = false
  }

  const queues = ref([])
  const entrypoints = ref([])

  async function getQueues(val = '', update) {
    update(async () => {
      try {
        const res = await api.getData('queues', {
          search: val,
          rowsPerPage: 100,
          index: 0
        })
        queues.value = res.data.data
      } catch(err) {
        notify.error(err.response.data.message)
      } 
    })
  }

  async function getEntrypoints(val = '', update) {
    update(async () => {
      try {
        const res = await api.getData('entrypoints', {
          search: val,
          rowsPerPage: 100,
          index: 0
        })
        entrypoints.value = res.data.data
      } catch(err) {
        notify.error(err.response.data.message)
      } 
    })
  }

</script>
