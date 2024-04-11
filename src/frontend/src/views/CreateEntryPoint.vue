<template>
  <div :class="`row q-mt-lg ${isMobile ? '' : 'q-mx-xl'} q-mb-lg`">
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
                <label :class="`field-label`">Entry Point Name:</label>
              </template>
            </q-input>
            <q-select
              outlined 
              v-model="entryPoint.group" 
              :options="groupOptions" 
              dense
              :rules="[requiredRule]"
              aria-required="true"
            >
              <template v-slot:before>
                <div class="field-label">Group Name:</div>
              </template>  
            </q-select>
          </q-form>
        </div>
      </fieldset>
      <fieldset class="q-mt-lg">
        <legend>Task Graph</legend>
        <div style="padding: 0 2%" class="row">
          <CodeEditor v-model="entryPoint.task_graph" style="width: 0; flex-grow: 1;" />
        </div>
      </fieldset>
    </div>
    <fieldset :class="`${isMobile ? 'col-12 q-mt-lg' : 'col'}`">
      <legend>Parameters</legend>
      <div style="padding: 0 5%">
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
              v-model="parameter.parameter_type" 
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
              v-model.trim="parameter.default_value"
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
        label="Submit Entry Point"

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
  import { ref, inject, reactive } from 'vue'
  import { useDataStore } from '@/stores/DataStore.ts'
  import { useRouter } from 'vue-router'
  import DeleteDialog from '@/dialogs/DeleteDialog.vue'
  import CodeEditor from '@/components/CodeEditor.vue'
  import EditParamDialog from '@/dialogs/EditParamDialog.vue'
  import BasicTable from '@/components/BasicTable.vue'
  
  const router = useRouter()

  const store = useDataStore()

  const isMobile = inject('isMobile')

  const requiredRule = (val) => (val && val.length > 0) || "This field is required"

  let entryPoint = reactive({
    name: '',
    group: '',
    parameters: [],
    task_graph: ''
  })

  const parameter = reactive({
    name: '',
    parameter_type: '',
    default_value: '',
  })

  const groupOptions = ref([
    'Group 1',
    'Group 2',
    'Group 3',
  ])

  const typeOptions = ref([
    'String',
    'Float',
    'Path',
    'URI',
  ])

  const basicInfoForm = ref(null)
  const paramForm = ref(null)


  const columns = [
    { name: 'name', label: 'Name', align: 'left', field: 'name', sortable: true, },
    { name: 'type', label: 'Type', align: 'left', field: 'parameter_type', sortable: true, },
    { name: 'defaultValue', label: 'Default Value (optional)', align: 'left', field: 'default_value', sortable: true, },
    { name: 'actions', label: 'Actions', align: 'center',  },
  ]

  if(Object.keys(store.editEntryPoint).length !== 0) {
    // entryPoint = JSON.parse(JSON.stringify(store.editEntryPoint))
    entryPoint = Object.assign(entryPoint, JSON.parse(JSON.stringify(store.editEntryPoint)))
    store.editMode = true
    store.editEntryPoint = {}
  }


  function addParam() {
    entryPoint.parameters.push({
      name: parameter.name,
      parameter_type: parameter.parameter_type,
      default_value: parameter.default_value,
    })
    parameter.name = ''
    parameter.parameter_type = ''
    parameter.default_value = ''
    paramForm.value.reset()
  }

  function submit() {
    basicInfoForm.value.validate().then(success => {
      if (success) {
        if(!store.editMode) {
          entryPoint.id = new Date().getTime().toString()
          store.entryPoints.push(entryPoint)
        } else {
          const editIndex = store.entryPoints.findIndex((storedentryPoint) => storedentryPoint.id === entryPoint.id)
          store.entryPoints[editIndex] = entryPoint
        }
        router.push('/entrypoints')
      }
      else {
        // error
      }
    })
  }

  const showDeleteDialog = ref(false)
  const selectedParam = ref({})
  const selectedParamIndex = ref('')

  function deleteParam() {
    entryPoint.parameters = entryPoint.parameters.filter((param) => param.name !== selectedParam.value.name)
    showDeleteDialog.value = false
  }

  const showEditParamDialog = ref(false)

  function updateParam(parameter) {
    entryPoint.parameters[selectedParamIndex.value] = { ...parameter }
    showEditParamDialog.value = false
  }

</script>