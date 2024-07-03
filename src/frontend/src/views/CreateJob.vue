<template>
  <PageTitle 
    :title="title"
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
              v-model="job.entrypoint"
              clearable
              use-input
              
              map-options
              option-label="name"
              option-value="id"
              input-debounce="100"
              :options="queues"
              @filter="getEndpoint"
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
    <fieldset :class="`${isMobile ? 'col-12 q-mt-lg' : 'col'}`" :disabled="job.entrypoint === ''">
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
        >
        <template #body-cell-value="props">
          heyyyy
        </template>
        </BasicTable>

        <!-- <q-card
          flat
          bordered
          class="q-px-lg q-my-lg"
        >
          <q-card-section class="q-px-none">
            <label class="text-body1">Add Parameter</label>
          </q-card-section>
          <q-form ref="paramForm" greedy @submit.prevent="addParam">
            <q-select
              outlined 
              v-model="parameter.name" 
              :options="paramNames" 
              dense
              :rules="[requiredRule]"
              aria-required="true"
              class="q-mb-md"
              label="Select Param Name"
            />
            <q-input 
              outlined 
              dense 
              v-model.trim="parameter.value"
              label="Enter Value"
              :rules="[requiredRule]"
            />
            <q-card-actions align="right">
              <q-btn
                round
                color="secondary"
                icon="add"
                type="submit"
              >
                <span class="sr-only">Add Parameter</span>
                <q-tooltip>
                  Add Parameter
                </q-tooltip>
              </q-btn>
            </q-card-actions>
          </q-form>
        </q-card> -->
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
  import { ref, inject, reactive, watch, computed } from 'vue'
  import { useLoginStore } from '@/stores/LoginStore.ts'
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

  const store = useLoginStore()

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

  const paramNames = computed(() => {
    if(!job.value.entrypoint) return []
    return job.value.entrypoint.parameters.map((obj) => obj.name)
  })

  let entryPoint = ref({
    name: '',
    group: '',
    description: '',
    parameters: [],
    taskGraph: '',
    queues: [],
    plugins: []
  })

  const parameter = reactive({
    name: '',
    value: '',
  })

  const parameters = ref([])
  const computedValue = computed(() => {
    let output = {}
    if(parameters.value.legnth === 0) return output
    parameters.value.forEach((param) => {
      output[param.name] = param.value
    })
    return output
  })

  watch(() => job.value.entrypoint, (newVal) => {
    parameters.value = []
    console.log('entrypoint = ', newVal)
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
  const paramForm = ref(null)


  const columns = [
    { name: 'name', label: 'Name', align: 'left', field: 'name', sortable: true, },
    { name: 'value', label: 'Value', align: 'left', field: 'value', sortable: true, },
    { name: 'parameterType', label: 'Type', align: 'left', field: 'type', sortable: true, },
    // { name: 'actions', label: 'Actions', align: 'center',  },
  ]

  const title = ref('')
  getJob()
  async function getJob() {
    if(route.params.jobId === 'new') {
      title.value = 'Create Job'
      return
    }
    try {
      const res = await api.getItem('entrypoints', route.params.id)
      entryPoint.value = res.data
      title.value = `Edit ${res.data.name}`
      console.log('entryPoint = ', entryPoint.value)
    } catch(err) {
      console.log('err = ', err)
      notify.error(err.response.data.message)
    } 
  }


  function addParam() {
    parameters.value.push(JSON.parse(JSON.stringify(parameter)))
    parameter.name = ''
    parameter.value = ''
    paramForm.value.reset()
  }


  function submit() {
    basicInfoForm.value.validate().then(success => {
      if (success) {
        addOrModifyEntrypoint()
      }
      else {
        // error
      }
    })
  }

  async function addOrModifyEntrypoint() {
    job.value.entrypoint = job.value.entrypoint.id
    job.value.values = computedValue.value
    try {
      if (route.params.jobId === 'new') {
        await api.addJob(route.params.id, job.value)
        notify.success(`Sucessfully created '${entryPoint.value.name}'`)
      } else {
        await api.updateItem('entrypoints', route.params.id, {
          name: entryPoint.value.name,
          description: entryPoint.value.description,
          taskGraph: entryPoint.value.taskGraph,
          parameters: parameters.value,
          queues: entryPoint.value.queues,
        })
        notify.success(`Sucessfully updated '${entryPoint.value.name}'`)
      }
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

  async function getEndpoint(val = '', update) {
    update(async () => {
      try {
        const res = await api.getData('entrypoints', {
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

</script>
