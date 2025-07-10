<template>
  <div class="row items-center justify-between">
    <div class="row items-center">
      <PageTitle 
        :title="title"
      />
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
    <div>
      <q-btn 
        v-if="route.params.id !== 'new'"
        :color="history ? 'red-3' : 'negative'" 
        icon="sym_o_delete" 
        label="Delete Entrypoint"
        @click="showDeleteDialogEntrypoint = true; objectForDeletion = entryPoint"
        :disable="history"
      />
    </div>
  </div>
  <div class="row q-my-lg">
    <div :class="`${isMobile ? 'col-12' : 'col-5'} q-mr-xl`" style="display: flex; flex-direction: column;">
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
              :disable="history"
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
              :disable="history"
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
              :disable="history"
            >
              <template v-slot:before>
                <label :class="`field-label`">Description:</label>
              </template>
            </q-input>
          </q-form>
        </div>
      </fieldset>
      <fieldset class="q-mt-lg full-height">
        <legend>Task Graph</legend>
        <p class="text-caption q-mb-none text-grey-8 q-pl-xs">
          Use "Add to Task Graph" button in Plugin Tasks table to insert YAML, and 
          CTRL + Space to trigger autocompletion.
        </p>
        <CodeEditor 
          v-model="entryPoint.taskGraph"
          language="yaml"
          placeholder="# task graph yaml file"
          :showError="taskGraphError"
          :autocompletions="autocompletions"
          :readOnly="history"
          :style="history ? 'cursor: not-allowed; opacity: 0.9;' : ''"
        />
        <q-btn
          label="Validate Inputs"
          color="primary"
          @click="validateInputs()"
        />
      </fieldset>
    </div>
    <fieldset :class="`${isMobile ? 'col-12 q-mt-lg' : 'col'}`">
      <legend>Parameters</legend>
      <div class="q-px-xl" :style="history ? 'cursor: not-allowed;' : ''">
        <TableComponent
          :rows="entryPoint.parameters"
          :columns="columns"
          :hideToggleDraft="true"
          :hideSearch="true"
          :disableSelect="true"
          :hideCreateBtn=true
          :hideOpenBtn="true"
          :hideDeleteBtn="true"
          :style="history ? 'pointer-events: none; opacity: 0.5;' : ''"
        >
          <template #body-cell-actions="props">
            <q-btn 
              icon="edit"
              round
              size="sm"
              color="primary"
              flat
              @click="selectedParam = props.row; selectedParamIndex = props.rowIndex; showEditParamDialog = true" 
            />
            <q-btn
              icon="sym_o_delete"
              round
              size="sm"
              color="negative"
              flat
              @click="selectedParam = props.row; showDeleteDialogParam = true"
            />
          </template>
        </TableComponent>
        <q-card
          v-if="!history"
          flat
          bordered
          class="q-px-lg q-mt-lg"
        >
          <q-card-section class="q-px-none">
            <label class="text-body1" :style="history ? 'opacity: 0.5;' : ''">Add Parameter</label>
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
          v-if="!history"
          outlined
          dense
          v-model="entryPoint.queues"
          use-input
          use-chips
          multiple
          map-options
          option-label="name"
          option-value="id"
          input-debounce="100"
          :options="queues"
          @filter="getQueues"
          class="q-mt-lg q-mb-md"
          :disable="history"
        >
          <template v-slot:before>
            <div class="field-label">Queues:</div>
          </template>  
          <template v-slot:selected-item="scope">
            <q-chip
              :label="scope.opt.name"
              removable
              @remove="scope.removeAtIndex(scope.index)"
              :tabindex="scope.tabindex"
              color="primary"
              text-color="white"
            />
          </template>
        </q-select>
        <div v-else class="row items-center q-mt-lg q-mb-md">
          <label class="field-label">Queues:</label>
          <div 
            class="col" 
            style="border: 1px solid lightgray; border-radius: 4px; padding: 10px 8px; margin-left: 6px;"
            :style="history ? 'opacity: 0.5; pointer-events: none;' : ''"
          >
            <q-icon
              name="sym_o_info"
              size="2em"
              color="grey"
              class="q-mr-sm"
            />
            Queues are not yet avaiable in Entrypoint snapshots
          </div>
        </div>
        <q-select
          v-if="route.params.id === 'new'"
          outlined
          dense
          v-model="entryPoint.plugins"
          use-input
          use-chips
          multiple
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
          <template v-slot:selected-item="scope">
            <q-chip
              :label="scope.opt.name"
              removable
              @remove="scope.removeAtIndex(scope.index)"
              :tabindex="scope.tabindex"
              color="secondary"
              text-color="white"
            />
          </template>
        </q-select>
        <div 
          class="row items-center" 
          v-if="route.params.id !== 'new' && entryPoint.plugins.length > 0"
        >
          <label class="field-label">Plugins:</label>
          <div 
            class="col" 
            style="border: 1px solid lightgray; border-radius: 4px; padding: 5px 8px; margin-left: 6px;"
            :style="history ? 'opacity: 0.5; pointer-events: none;' : ''"
          >
            <div
              v-for="(plugin, i) in entryPoint.plugins"
              :key="i"
            >
              <q-chip
                :label="plugin.name"
                color="secondary"
                text-color="white"
              >
                <q-badge
                  v-if="!plugin.latestSnapshot" 
                  color="red" 
                  label="outdated" 
                  rounded
                  class="q-ml-xs"
                />
              </q-chip>
              <q-btn
                v-if="!plugin.latestSnapshot"
                round 
                color="red" 
                icon="sync"
                size="sm"
                @click="syncPlugin(plugin.id, i)"
              >
                <q-tooltip>
                  Sync to latest version of plugin
                </q-tooltip>
              </q-btn>
            </div>
          </div>
        </div>
      </div>
      
      <TableComponent
        :rows="tasks"
        :columns="taskColumns"
        title="Plugin Tasks"
        :hideToggleDraft="true"
        :hideSearch="true"
        :disableSelect="true"
        :hideOpenBtn="true"
        :hideDeleteBtn="true"
        :hideCreateBtn=true
        :style="history ? 'opacity: 0.5; pointer-events: none;' : ''"
      >
        <template #body-cell-inputParams="props">
          <q-chip
            v-for="(param, i) in props.row.inputParams"
            :key="i"
            color="indigo"
            class="q-mr-sm"
            text-color="white"
            dense
            clickable
          >
            {{ `${param.name}` }}
            <span v-if="param.required" class="text-red">*</span>
            : {{ param.parameterType.name }}
          </q-chip>
        </template>
        <template #body-cell-outputParams="props">
          <q-chip
            v-for="(param, i) in props.row.outputParams"
            :key="i"
            color="purple"
            text-color="white"
            dense
            clickable
          >
            {{ `${param.name}` }}
            <span v-if="param.required" class="text-red">*</span>
            : {{ param.parameterType.name }}
          </q-chip>
        </template>
        <template #body-cell-add="props">
          <q-btn icon="add" round size="xs" color="grey-5" text-color="black" @click="addToTaskGraph(props.row)" />
        </template>
      </TableComponent>
    </fieldset>
  </div>

  <div class="float-right q-mb-lg">
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
      label="Submit EntryPoint"
      :disable="history"
    />
  </div>

  <DeleteDialog 
    v-model="showDeleteDialogEntrypoint"
    @submit="deleteEntrypoint()"
    type="Entrypoint"
    :name="entryPoint.name"
    @click=""
  />
  <DeleteDialog 
    v-model="showDeleteDialogParam"
    @submit="deleteParam()"
    type="Parameter"
    :name="selectedParam.name"
  />
  <EditParamDialog 
    v-model="showEditParamDialog"
    :editParam="selectedParam"
    @updateParam="updateParam"
  />
  <LeaveFormDialog 
    v-model="showLeaveDialog"
    type="entrypoint"
    @leaveForm="leaveForm"
  />
  <ReturnToFormDialog
    v-model="showReturnDialog"
    @cancel="clearForm"
  />
  <InfoPopupDialog
    v-model="displayErrorDialog"
  >
    <template #title>
      <label id="modalTitle">
        Entrypoint Input Errors
      </label>
    </template>
    Errors found: {{ inputErrors.length }}
    <ul>
      <li v-for="error in inputErrors">
        {{ error.message }}
      </li>
    </ul>
  </InfoPopupDialog>
</template>

<script setup>
  import { ref, inject, reactive, watch, computed, onMounted } from 'vue'
  import { useLoginStore } from '@/stores/LoginStore.ts'
  import { useRouter, onBeforeRouteLeave } from 'vue-router'
  import DeleteDialog from '@/dialogs/DeleteDialog.vue'
  import CodeEditor from '@/components/CodeEditor.vue'
  import EditParamDialog from '@/dialogs/EditParamDialog.vue'
  import { useRoute } from 'vue-router'
  import * as api from '@/services/dataApi'
  import * as notify from '../notify'
  import PageTitle from '@/components/PageTitle.vue'
  import TableComponent from '@/components/TableComponent.vue'
  import LeaveFormDialog from '@/dialogs/LeaveFormDialog.vue'
  import ReturnToFormDialog from '@/dialogs/ReturnToFormDialog.vue'
  import InfoPopupDialog from '@/dialogs/InfoPopupDialog.vue'

  const route = useRoute()
  
  const router = useRouter()

  const store = useLoginStore()

  const isMobile = inject('isMobile')

  const history = computed(() => {
    return store.showRightDrawer
  })

  function requiredRule(val) {
    return (!!val) || "This field is required"
  }

  let entryPoint = ref({
    name: '',
    group: store.loggedInGroup.id,
    description: '',
    parameters: [],
    taskGraph: '',
    queues: [],
    plugins: []
  })

  const copyAtEditStart = ref({
    name: '',
    group: store.loggedInGroup.id,
    description: '',
    parameters: [],
    taskGraph: '',
    queues: [],
    plugins: []
  })

  onMounted(() => {
    if(route.query.snapshotId && !store.showRightDrawer) {
      store.showRightDrawer = true
    } else {
      getEntrypoint()
    }
  })

  watch(() => store.selectedSnapshot, (ep) => {
    if(ep) {
      entryPoint.value = {
        name: ep.name,
        group: ep.group.id,
        description: ep.description,
        parameters: ep.parameters,
        taskGraph: ep.taskGraph,
        queues: ep.queues,
        plugins: ep.plugins
      }
      title.value = `View ${entryPoint.value.name}`
    } else {
      getEntrypoint()
    }
  })

  const valuesChangedFromEditStart = computed(() => {
    for (const key in copyAtEditStart.value) {
      if(JSON.stringify(copyAtEditStart.value[key]) !== JSON.stringify(entryPoint.value[key])) {
        return true
      }
    }
    return false
  })

  const ORIGINAL_COPY = {
    name: '',
    group: store.loggedInGroup.id,
    description: '',
    parameters: [],
    taskGraph: '',
    queues: [],
    plugins: []
  }

  const valuesChangedFromOriginal = computed(() => {
    for (const key in ORIGINAL_COPY) {
      if(JSON.stringify(ORIGINAL_COPY[key]) !== JSON.stringify(entryPoint.value[key])) {
        return true
      }
    }
    return false
  })

  const tasks = ref([])

  watch(() => entryPoint.value.plugins, () => {
    tasks.value = []
    entryPoint.value.plugins.forEach((plugin) => {
      if(typeof plugin === 'number') return
      const pluginName = plugin.name
      plugin.files.forEach((file) => {
        file.tasks.functions.forEach((fTask) => {
          tasks.value.push({ ...fTask, pluginName: pluginName })
        })
      })
    })
  }, { deep: true })

  const parameter = reactive({
    name: '',
    parameterType: '',
    defaultValue: '',
  })

  const typeOptions = ref([
    'string',
    'float',
    'integer',
    'boolean',
    'list',
    'mapping',
  ])

  const autocompletions = computed(() => {
    if(entryPoint.value.parameters.length === 0) return []
    return entryPoint.value.parameters.map((param) => {
      return {
        label: `$${param.name}`,
        type: 'variable'
      }
    })
  })

  const basicInfoForm = ref(null)
  const paramForm = ref(null)


  const columns = [
    { name: 'name', label: 'Name', align: 'left', field: 'name', sortable: true, },
    { name: 'type', label: 'Type', align: 'left', field: 'parameterType', sortable: true, },
    { name: 'defaultValue', label: 'Default Value (optional)', align: 'left', field: 'defaultValue', sortable: true, },
    { name: 'actions', label: 'Actions', align: 'center',  },
  ]

  const taskColumns = [
    { name: 'pluginName', label: 'Plugin', align: 'left', field: 'pluginName', sortable: true, },
    { name: 'taskName', label: 'Task', align: 'left', field: 'name', sortable: true, },
    { name: 'inputParams', label: 'Input Params', align: 'left', field: 'inputParams', sortable: false, },
    { name: 'outputParams', label: 'Output Params', align: 'left', field: 'outputParams', sortable: false, },
    { name: 'add', label: 'Add to Task Graph', align: 'left', sortable: false, },
  ]

  const title = ref('')
  const showReturnDialog = ref(false)

  getEntrypoint()

  async function getEntrypoint() {
    if(route.params.id === 'new') {
      title.value = 'Create Entrypoint'
      if(store.savedForms?.entryPoint) {
        showReturnDialog.value = true
        await checkIfStillValid('queues')
        await checkIfStillValid('plugins')
        entryPoint.value = store.savedForms.entryPoint
        copyAtEditStart.value = JSON.parse(JSON.stringify(store.savedForms.entryPoint))
      }
      return
    }
    try {
      const res = await api.getItem('entrypoints', route.params.id)
      entryPoint.value = res.data
      copyAtEditStart.value = JSON.parse(JSON.stringify(entryPoint.value))
      title.value = `Edit ${res.data.name}`
      console.log('entryPoint = ', entryPoint.value)
    } catch(err) {
      notify.error(err.response.data.message)
    } 
  }

  async function checkIfStillValid(type) {
    for(let index = store.savedForms.entryPoint[type].length - 1; index >= 0; index--) {
      let id = store.savedForms.entryPoint[type][index].id
      try {
        const res =  await api.getItem(type, id)
      } catch(err) {
        await store.savedForms.entryPoint[type].splice(index, 1)
        console.warn(err)
      } 
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

  const taskGraphPlaceholderError = computed(() => {
    if(entryPoint.value.taskGraph.includes('<step-name>') && entryPoint.value.taskGraph.includes('<input-value>')) {
      return 'Replace <step-name> and <input-value> placeholders'
    } else if(entryPoint.value.taskGraph.includes('<step-name>')) {
      return 'Replace <step-name> placeholders'
    } else if(entryPoint.value.taskGraph.includes('<input-value>')) {
      return 'Replace <input-value> placeholders'
    }
    return ''
  })

  function submit() {
    if(entryPoint.value.taskGraph.length === 0) {
      taskGraphError.value = 'This field is required'
    }
    basicInfoForm.value.validate().then(success => {
      if (success && taskGraphError.value === '') {
        confirmLeave.value = true
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
    entryPoint.value.plugins.forEach((plugin, index, array) => {
      if(typeof plugin === 'object') {
        array[index] = plugin.id
      }
    })
    try {
      if (route.params.id === 'new') {
        await api.addItem('entrypoints', entryPoint.value)
        store.savedForms.entryPoint = null
        router.push('/entrypoints')
        notify.success(`Successfully created '${entryPoint.value.name}'`)
      } else {
        await api.updateItem('entrypoints', route.params.id, {
          name: entryPoint.value.name,
          description: entryPoint.value.description,
          taskGraph: entryPoint.value.taskGraph,
          artifactGraph: '',
          parameters: entryPoint.value.parameters,
          artifactParameters: [],
          queues: entryPoint.value.queues,
        })
        console.log('pluginsToUpdate = ', pluginsToUpdate.value)
        if(pluginsToUpdate.value.length > 0) {
          await api.addPluginsToEntrypoint(route.params.id, pluginsToUpdate.value)
        }
        router.push('/entrypoints')
        notify.success(`Successfully updated '${entryPoint.value.name}'`)
      }
    } catch(err) {
      notify.error(err.response.data.message)
    }
  }

  watch(() => entryPoint.value.taskGraph, (newVal) => {
    if(clearFormExecuted.value) {
      clearFormExecuted.value = false
    } else {
      taskGraphError.value = newVal.length > 0 ? '' : 'This field is required'
      if(taskGraphPlaceholderError.value) {
        taskGraphError.value = taskGraphPlaceholderError.value
      }
    }
  })

  const showDeleteDialogEntrypoint = ref(false)
  const showDeleteDialogParam = ref(false)
  const selectedParam = ref({})
  const selectedParamIndex = ref('')

  function deleteParam() {
    entryPoint.value.parameters = entryPoint.value.parameters.filter((param) => param.name !== selectedParam.value.name)
    showDeleteDialogParam.value = false
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
          rowsPerPage: 0, // get all
          index: 0
        })
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
          rowsPerPage: 0, // get all
          index: 0
        })
        plugins.value = res.data.data
      } catch(err) {
        notify.error(err.response.data.message)
      } 
    })
  }

  function addToTaskGraph(task) {
    console.log('task = ', task)
    let string = `<step-name>:\n  ${task.name}:`
    task.inputParams.forEach((param) => {
      string += `\n    ${param.name}: <input-value>`
    })
    if(entryPoint.value.taskGraph.trim().length === 0) {
      entryPoint.value.taskGraph = ''
      entryPoint.value.taskGraph = string
    } else {
      entryPoint.value.taskGraph += `\n${string}`
    }
  }

  const showLeaveDialog = ref(false)
  const confirmLeave = ref(false)
  const toPath = ref()

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

  const clearFormExecuted= ref(false)

  function clearForm() {
    entryPoint.value = {
      name: '',
      group: store.loggedInGroup.id,
      description: '',
      parameters: [],
      taskGraph: '',
      queues: [],
      plugins: []
    }
    basicInfoForm.value.reset()
    clearFormExecuted.value = true
    store.savedForms.entryPoint = null
  }

  const isEmptyValues = computed(() => {
    return Object.values(entryPoint.value).every((value) => 
      (typeof value === 'string' && value === '') || 
      (Array.isArray(value) && value.length === 0)
    )
  })

  function leaveForm() {
    if(route.params.id === 'new' && valuesChangedFromEditStart.value && valuesChangedFromOriginal.value) {
      store.savedForms.entryPoint = entryPoint.value
    } else {
      store.savedForms.entryPoint = null
    }
    confirmLeave.value = true
    router.push(toPath.value)
  }

  const pluginsToUpdate = ref([])

  async function syncPlugin(pluginID, index) {
    try {
      const res = await api.getItem('plugins', pluginID)
      console.log('res = ', res)
      entryPoint.value.plugins.splice(index, 1, res.data)
      pluginsToUpdate.value.push(pluginID)
    } catch(err) {
      console.warn(err)
    }
  }
  const objectForDeletion = ref()

  async function deleteEntrypoint() {
    try {
      await api.deleteItem('entrypoints', objectForDeletion.value.id)
      notify.success(`Successfully deleted '${objectForDeletion.value.name}'`)
      showDeleteDialogEntrypoint.value = false
      router.push(`/entrypoints`)
    } catch(err) {
      notify.error(err.response.data.message);
    }
  }

  const inputErrors = ref([])
  const displayErrorDialog = ref(false)

  async function validateInputs() {
    try {
      const res = await api.validateEntrypoint({
        group: entryPoint.value.group.id || entryPoint.value.group,
        taskGraph: entryPoint.value.taskGraph,
        pluginSnapshots: entryPoint.value.plugins.map(plugin => plugin.snapshotId || plugin.snapshot),
        parameters: entryPoint.value.parameters
      })
      if(res?.data?.schemaValid && !taskGraphPlaceholderError.value) {
        notify.success(`Entrypoint inputs are valid!`)
      } else if(res?.data?.schemaIssues.length > 0 || taskGraphPlaceholderError.value) {
        inputErrors.value = res.data.schemaIssues
        if(taskGraphPlaceholderError.value) {
          inputErrors.value.push({message: taskGraphPlaceholderError.value})
        }
        displayErrorDialog.value = true
      }
    } catch(err) {
      console.warn(err)
    }
  }

</script>
