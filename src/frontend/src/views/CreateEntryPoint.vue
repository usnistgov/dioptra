<template>
  <PageTitle 
    :title="title"
  />
  <div :class="`row ${isMobile ? '' : 'q-mx-xl'} q-my-lg`">
    <div :class="`${isMobile ? 'col-12' : 'col-5'} q-mr-xl`">
      <fieldset>
        <legend>Basic Info</legend>
        <div style="padding: 0 5%">
          <q-form ref="basicInfoForm" greedy>
            <q-input 
              outlined 
              dense 
              v-model.trim="entryPoint.name"
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
              v-model="entryPoint.group" 
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
              v-model.trim="entryPoint.description"
              class="q-mb-sm q-mt-sm"
              type="textarea"
              autogrow
            >
              <template v-slot:before>
                <label :class="`field-label`">Description:</label>
              </template>
            </q-input>
          </q-form>
        </div>
      </fieldset>
      <fieldset class="q-mt-lg">
        <legend>Task Graph</legend>
        <div class="row q-mx-md">
          <CodeEditor 
            v-model="entryPoint.taskGraph"
            language="yaml"
            placeholder="# task graph yaml file"
            style="width: 0; flex-grow: 1;"
            :showError="taskGraphError"
          />
        </div>

      </fieldset>
    </div>
    <fieldset :class="`${isMobile ? 'col-12 q-mt-lg' : 'col'}`">
      <legend>Parameters</legend>
      <div class="q-px-xl">
        <BasicTable
          :columns="columns"
          :rows="entryPoint.parameters"
          :hideSearch="true"
          :hideEditTable="true"
          @edit="(param, i) => {selectedParam = param; selectedParamIndex = i; showEditParamDialog = true}"
          @delete="(param) => {selectedParam = param; showDeleteDialog = true}"
        >
        </BasicTable>

        <q-card
          flat
          bordered
          class="q-px-lg q-my-lg"
        >
          <q-card-section class="q-px-none">
            <label class="text-body1">Add Parameter</label>
          </q-card-section>
          <q-form ref="paramForm" greedy @submit.prevent="addParam">
            <q-input 
              outlined 
              dense 
              v-model.trim="parameter.name"
              :rules="[requiredRule]"
              class="q-mb-sm "
              label="Enter Name"
            />
            <q-select
              outlined 
              v-model="parameter.parameterType" 
              :options="typeOptions" 
              dense
              :rules="[requiredRule]"
              aria-required="true"
              class="q-mb-sm"
              label="Select Type"
            />
            <q-input 
              outlined 
              dense 
              v-model.trim="parameter.defaultValue"
              class="q-mb-sm"
              label="Enter Default Value"
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
        </q-card>

        <q-select
          outlined
          dense
          v-model="entryPoint.queues"
          use-input
          use-chips
          multiple
          emit-value
          map-options
          option-label="name"
          option-value="id"
          input-debounce="100"
          :options="queues"
          @filter="getQueues"
          class="q-mb-md"
        >
          <template v-slot:before>
            <div class="field-label">Queues:</div>
          </template>  
        </q-select>

        <q-select
          v-if="route.params.id === 'new'"
          outlined
          dense
          v-model="entryPoint.plugins"
          use-input
          use-chips
          multiple
          emit-value
          map-options
          option-label="name"
          option-value="id"
          input-debounce="100"
          :options="plugins"
          @filter="getPlugins"
        >
          <template v-slot:before>
            <div class="field-label">Plugins:</div>
          </template>  
        </q-select>
      </div>
    </fieldset>
  </div>

  <div :class="`${isMobile ? '' : 'q-mx-xl'} float-right q-mb-lg`">
      <q-btn  
        to="/entrypoints"
        color="negative" 
        label="Cancel"
        class="q-mr-lg"
      />
      <q-btn  
        @click="submit()" 
        color="primary" 
        label="Submit EntryPoint"

      />
    </div>

  <DeleteDialog 
    v-model="showDeleteDialog"
    @submit="deleteParam()"
    type="Parameter"
    :name="selectedParam.name"
  />

  <EditParamDialog 
    v-model="showEditParamDialog"
    :editParam="selectedParam"
    @updateParam="updateParam"
  />
</template>

<script setup>
  import { ref, inject, reactive, watch } from 'vue'
  import { useLoginStore } from '@/stores/LoginStore.ts'
  import { useRouter } from 'vue-router'
  import DeleteDialog from '@/dialogs/DeleteDialog.vue'
  import CodeEditor from '@/components/CodeEditor.vue'
  import EditParamDialog from '@/dialogs/EditParamDialog.vue'
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
    parameterType: '',
    defaultValue: '',
  })

  const typeOptions = ref([
    'string',
    'float',
    'path',
    'uri',
  ])

  const basicInfoForm = ref(null)
  const paramForm = ref(null)


  const columns = [
    { name: 'name', label: 'Name', align: 'left', field: 'name', sortable: true, },
    { name: 'type', label: 'Type', align: 'left', field: 'parameterType', sortable: true, },
    { name: 'defaultValue', label: 'Default Value (optional)', align: 'left', field: 'defaultValue', sortable: true, },
    { name: 'actions', label: 'Actions', align: 'center',  },
  ]

  const title = ref('')
  getEntrypoint()
  async function getEntrypoint() {
    if(route.params.id === 'new') {
      title.value = 'Create Entrypoint'
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
    entryPoint.value.parameters.push({
      name: parameter.name,
      parameterType: parameter.parameterType,
      defaultValue: parameter.defaultValue,
    })
    parameter.name = ''
    parameter.parameterType = ''
    parameter.defaultValue = ''
    paramForm.value.reset()
  }

  const taskGraphError = ref('')

  function submit() {
    basicInfoForm.value.validate().then(success => {
      taskGraphError.value = entryPoint.value.taskGraph.length > 0 ? '' : 'This field is required'
      if (success && taskGraphError.value === '') {
        addOrModifyEntrypoint()
      }
      else {
        // error
      }
    })
  }

  async function addOrModifyEntrypoint() {
    entryPoint.value.queues.forEach((queue, index, array) => {
      if(typeof queue === 'object') {
        array[index] = queue.id
      }
    })
    try {
      if (route.params.id === 'new') {
        await api.addItem('entrypoints', entryPoint.value)
        notify.success(`Successfully created '${entryPoint.value.name}'`)
      } else {
        await api.updateItem('entrypoints', route.params.id, {
          name: entryPoint.value.name,
          description: entryPoint.value.description,
          taskGraph: entryPoint.value.taskGraph,
          parameters: entryPoint.value.parameters,
          queues: entryPoint.value.queues,
        })
        notify.success(`Successfully updated '${entryPoint.value.name}'`)
      }
    } catch(err) {
      notify.error(err.response.data.message)
    } finally {
      router.push('/entrypoints')
    }
  }

  watch(() => entryPoint.value.taskGraph, (newVal) => {
    taskGraphError.value = newVal.length > 0 ? '' : 'This field is required'
  })

  const showDeleteDialog = ref(false)
  const selectedParam = ref({})
  const selectedParamIndex = ref('')

  function deleteParam() {
    entryPoint.value.parameters = entryPoint.value.parameters.filter((param) => param.name !== selectedParam.value.name)
    showDeleteDialog.value = false
  }

  const showEditParamDialog = ref(false)

  function updateParam(parameter) {
    entryPoint.value.parameters[selectedParamIndex.value] = { ...parameter }
    showEditParamDialog.value = false
  }

  const queues = ref([])
  const plugins = ref([])

  async function getQueues(val = '', update) {
    update(async () => {
      try {
        const res = await api.getData('queues', {
          search: val,
          rowsPerPage: 100,
          index: 0
        })
        console.log('ressss = ', res)
        queues.value = res.data.data
      } catch(err) {
        notify.error(err.response.data.message)
      } 
    })
  }

  async function getPlugins(val = '', update) {
    update(async () => {
      try {
        const res = await api.getData('plugins', {
          search: val,
          rowsPerPage: 100,
          index: 0
        })
        console.log('ressss = ', res)
        plugins.value = res.data.data
      } catch(err) {
        notify.error(err.response.data.message)
      } 
    })
  }

</script>
