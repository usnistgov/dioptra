<template>
  <div class="row items-center justify-between">
    <div class="row items-center">
      <PageTitle 
        :title="title"
      />
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
        label="Delete Entrypoint"
        @click="showDeleteDialogEntrypoint = true; objectForDeletion = entryPoint"
        :disable="history"
      />
    </div>
  </div>
  <fieldset class="q-px-lg q-mt-lg" :class="history ? `disabled` : ``">
    <legend>Basic Info</legend>
    <q-form ref="basicInfoForm" greedy :style="{ 'pointer-events': history ? 'none' : '' }">
      <div class="row">
        <div :class="`${isMobile ? 'col-12' : 'col-6'} q-mr-xl`">
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
            class="q-mb-sm"
          >
            <template v-slot:before>
              <div class="field-label">Group:</div>
            </template>  
          </q-select>
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
            class="q-mb-md"
            :disable="history"
          >
            <template v-slot:before>
              <div class="field-label">Queues:</div>
            </template>  
            <template v-slot:selected-item="scope">
              <q-chip
                :label="scope.opt.name"
                removable
                dense
                @remove="scope.removeAtIndex(scope.index)"
                :tabindex="scope.tabindex"
                color="primary"
                text-color="white"
              />
            </template>
          </q-select>
          <div v-else class="row items-center q-mb-md">
            <label class="field-label">Queues:</label>
            <div 
              class="col" 
              style="border: 1px solid lightgray; border-radius: 4px; padding: 5px 8px; margin-left: 6px;"
            >
              <q-icon
                name="sym_o_info"
                size="2em"
                color="grey"
                class="q-mr-sm"
              />
              Queues are not yet available in Entrypoint snapshots
            </div>
          </div>
        </div>
        <div class="col">
          <q-input 
            outlined 
            dense 
            v-model.trim="entryPoint.description"
            type="textarea"
            :disable="history"
            class="q-mt-md"
            input-style="height: 173px"
          >
            <template v-slot:before>
              <label :class="`field-label`">Description:</label>
            </template>
          </q-input>
        </div>
      </div>
    </q-form>
  </fieldset>

  <fieldset class="q-px-lg q-mt-lg q-py-lg" :class="history ? `disabled` : ``">
    <legend>Parameters</legend>
    <div class="row" :style="{ 'pointer-events': history ? 'none' : '' }">
      <div :class="`${isMobile ? 'col-12' : 'col-6'} q-mr-xl column`">
        <TableComponent
          title="Entrypoint Parameters"
          :rows="entryPoint.parameters"
          :columns="columns"
          :hideToggleDraft="true"
          :hideSearch="true"
          :disableSelect="true"
          :hideOpenBtn="true"
          :hideDeleteBtn="true"
          :hideBottom="true"
          :showAll="true"
          @create="selectedParam = null; showEntrypointParamDialog = true;"
          style="margin-top: 0;"
        >
          <template #body-cell-actions="props">
            <q-btn 
              icon="edit"
              round
              size="sm"
              color="primary"
              flat
              @click="
                selectedParam = props.row; 
                selectedParamIndex = props.rowIndex; 
                showEntrypointParamDialog = true;
                selectedParamType = 'parameters';
              " 
            />
            <q-btn
              icon="sym_o_delete"
              round
              size="sm"
              color="negative"
              flat
              @click="
                selectedParam = props.row; 
                showDeleteDialogParam = true
                selectedParamType = 'parameters'
              "
            />
          </template>
        </TableComponent>
      </div>
      <div class="col">
        <TableComponent
          :rows="entryPoint.artifactParameters"
          :columns="artifactColumns"
          title="Artifact Parameters"
          :hideToggleDraft="true"
          :hideSearch="true"
          :disableSelect="true"
          :hideOpenBtn="true"
          :hideDeleteBtn="true"
          :hideBottom="true"
          :showAll="true"
          rightCaption="*Click parameter to edit, or X to delete"
          style="margin-top: 0;"
          @create="showArtifactParamDialog = true"
        >
          <template #body-cell-name="props">
            <div style="font-size: 18px;">
              {{ props.row.name }}
              <q-btn icon="edit" round size="sm" color="primary" flat />
            </div>
            <q-popup-edit v-model="props.row.name" v-slot="scope">
              <q-input v-model="scope.value" dense autofocus counter @keyup.enter="scope.set" />
            </q-popup-edit>
          </template>
          <template #body-cell-outputParams="props">
            <div v-for="(param, i) in props.row.outputParams" :key="i">
              <q-chip
                color="purple"
                text-color="white"
                dense
                clickable
                removable
                @click="handleSelectedParam('edit', props, i, 'outputParams', 'artifacts'); showEditArtifactParamDialog = true; console.log('param = ', param)"
                @remove="entryPoint.artifactParameters[props.rowIndex].outputParams.splice(i, 1)"
                :label="`${param.name}: ${param.parameterType.name}`"
              />
              <div v-if="!param.parameterType" class="text-white q-mr-sm q-my-xs bg-red q-pa-xs rounded-borders">
                Resolve missing type above
              </div>
            </div>
            <q-btn
              round
              size="xs"
              icon="add"
              color="grey-5"
              text-color="black"
              class="q-mr-xs q-my-xs"
              @click="handleSelectedParam('create', props, i, 'outputParams', 'artifacts'); showEditArtifactParamDialog = true"
            />
          </template>
          <template #body-cell-delete="props">
            <q-btn 
              icon="sym_o_delete"
              round size="md"
              color="negative"
              flat
              @click="selectedArtifactParamProps = props; showDeleteDialogArtifactParam = true"
            />
          </template>
        </TableComponent>
      </div>
    </div>
  </fieldset>

  <fieldset class="q-px-lg q-mt-lg q-pt-lg" :class="history ? `disabled` : ``">
    <legend>Task Graph Info</legend>
    <div class="row" :style="{ 'pointer-events': history ? 'none' : '' }">
      <div :class="`${isMobile ? 'col-12 q-mb-xl' : 'col-6'} q-mr-xl column`">
        <h2>Task Graph</h2>
        <p class="text-caption q-mb-none text-grey-8 q-pl-xs">
          Use "Add to Task Graph" button in Plugin Tasks table to insert YAML, and 
          CTRL + Space or $ to trigger autocompletion.
        </p>
        <CodeEditor 
          v-model="entryPoint.taskGraph"
          language="yaml"
          placeholder="# task graph yaml file"
          :showError="taskGraphError"
          :autocompletions="autocompletions"
          :readOnly="history"
        />  
        <q-btn
          label="Validate Inputs"
          color="primary"
          @click="validateInputs()"
          class="self-start"
        />
      </div>
      
      <div class="col">
        <h2>Task Plugins</h2>
        <AssignPluginsDropdown
          v-model:selectedPlugins="entryPoint.plugins"
          v-model:pluginIDsToUpdate="pluginIDsToUpdate"
          v-model:pluginIDsToRemove="pluginIDsToRemove"
          class="q-mt-lg"
        />
        <TableComponent
          :rows="tasks"
          :columns="taskColumns"
          title="Function Tasks"
          :hideToggleDraft="true"
          :hideSearch="true"
          :disableSelect="true"
          :hideOpenBtn="true"
          :hideDeleteBtn="true"
          :hideCreateBtn=true
        >
          <template #body-cell-inputParams="props">
            <div v-for="(param, i) in props.row.inputParams" :key="i">
              <q-chip
                color="indigo"
                text-color="white"
                dense
                clickable
                class="q-mr-none"
              >
                {{ `${param.name}` }}
                <span v-if="param.required" class="text-red">*</span>
                : {{ param.parameterType.name }}
              </q-chip>
            </div>
          </template>
          <template #body-cell-outputParams="props">
            <div v-for="(param, i) in props.row.outputParams" :key="i">
              <q-chip
                color="purple"
                text-color="white"
                dense
                clickable
                class="q-mr-none"
              >
                {{ `${param.name}` }}
                <span v-if="param.required" class="text-red">*</span>
                : {{ param.parameterType.name }}
              </q-chip>
            </div>
          </template>
          <template #body-cell-add="props">
            <q-btn icon="add" round size="xs" color="grey-5" text-color="black" @click="addToTaskGraph(props.row)" />
          </template>
        </TableComponent>
      </div>
    </div>
  </fieldset>

  <fieldset class="q-px-lg q-mt-lg q-pt-lg" :class="history ? `disabled` : ``">
    <legend>Artifact Info</legend>
    <div class="row" :style="{ 'pointer-events': history ? 'none' : '' }">
      <div :class="`${isMobile ? 'col-12 q-mb-xl' : 'col-6'} q-mr-xl column`">
        <h2>Artifact Output Graph</h2>
        <p class="text-caption q-mb-none text-grey-8 q-pl-xs">
          Use "Add to Artifact Output Graph" button in Artifact Tasks table to insert YAML, and 
          CTRL + Space or $ to trigger autocompletion.
        </p>
        <CodeEditor 
          v-model="entryPoint.artifactGraph"
          :additionalCode="entryPoint.taskGraph"
          language="yaml"
          :autocompletions="autocompletions"
          placeholder="# task graph yaml file"
          :readOnly="history"
        />  
      </div>
      
      <div class="col">
        <h2>Artifact Task Plugins</h2>
        <AssignPluginsDropdown
          v-model:selectedPlugins="entryPoint.artifactPlugins"
          v-model:pluginIDsToUpdate="artifactPluginIDsToUpdate"
          v-model:pluginIDsToRemove="artifactPluginIDsToRemove"
          class="q-mt-lg"
        />
        <TableComponent
          :rows="artifactTasks"
          :columns="artifactTaskColumns"
          title="Artifact Tasks"
          :hideToggleDraft="true"
          :hideSearch="true"
          :disableSelect="true"
          :hideOpenBtn="true"
          :hideDeleteBtn="true"
          :hideCreateBtn=true
        >
          <template #body-cell-outputParams="props">
            <div v-for="(param, i) in props.row.outputParams" :key="i">
              <q-chip
                color="purple"
                text-color="white"
                dense
                clickable
                class="q-mr-none"
              >
                {{ `${param.name}` }}
                <span v-if="param.required" class="text-red">*</span>
                : {{ param.parameterType.name }}
              </q-chip>
            </div>
          </template>
          <template #body-cell-add="props">
            <q-btn icon="add" round size="xs" color="grey-5" text-color="black" @click="addToArtifactGraph(props.row)" />
          </template>
        </TableComponent>
      </div>
    </div>
  </fieldset>

  <div class="float-right q-my-lg">
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
      :disable="history || !enableSubmit"
    >
      <q-tooltip v-if="!enableSubmit">
        No changes detected — nothing to save
      </q-tooltip>
    </q-btn>
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
    :name="selectedParam?.name"
  />
  <DeleteDialog 
    v-model="showDeleteDialogArtifactParam"
    @submit="entryPoint.artifactParameters.splice(selectedArtifactParamProps.rowIndex, 1); showDeleteDialogArtifactParam = false"
    type="Artifact Parameter"
    :name="selectedArtifactParamProps?.row?.name"
  />
  <EntrypointParamDialog 
    v-model="showEntrypointParamDialog"
    :editParam="selectedParam"
    @updateParam="updateParam"
    @createParam="createParam"
  />
  <ArtifactParamDialog
    v-model="showArtifactParamDialog"
    @submit="addArtifactParam"
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

  <EditPluginTaskParamDialog 
    v-model="showEditArtifactParamDialog"
    :editParam="selectedParam"
    :pluginParameterTypes="pluginParameterTypes"
    :inputOrOutputParams="selectedTaskProps?.inputOrOutputParams"
    @updateParam="updateArtifactOutputParam"
    @addParam="addArtifactOutputParam"
  />
</template>

<script setup>
  import { ref, inject, reactive, watch, computed, onMounted, nextTick } from 'vue'
  import { useLoginStore } from '@/stores/LoginStore.ts'
  import { useRouter, onBeforeRouteLeave } from 'vue-router'
  import DeleteDialog from '@/dialogs/DeleteDialog.vue'
  import CodeEditor from '@/components/CodeEditor.vue'
  import EntrypointParamDialog from '@/dialogs/EntrypointParamDialog.vue'
  import { useRoute } from 'vue-router'
  import * as api from '@/services/dataApi'
  import * as notify from '../notify'
  import PageTitle from '@/components/PageTitle.vue'
  import TableComponent from '@/components/TableComponent.vue'
  import LeaveFormDialog from '@/dialogs/LeaveFormDialog.vue'
  import ReturnToFormDialog from '@/dialogs/ReturnToFormDialog.vue'
  import InfoPopupDialog from '@/dialogs/InfoPopupDialog.vue'
  import ArtifactParamDialog from '@/dialogs/ArtifactParamDialog.vue'
  import EditPluginTaskParamDialog from '@/dialogs/EditPluginTaskParamDialog.vue'
  import AssignPluginsDropdown from '@/components/AssignPluginsDropdown.vue'

  const route = useRoute()
  
  const router = useRouter()

  const store = useLoginStore()

  const isMobile = inject('isMobile')
  const darkMode = inject('darkMode')

  const history = computed(() => {
    return store.showRightDrawer
  })

  function requiredRule(val) {
    return (!!val) || "This field is required"
  }

  const entryPoint = ref({
    name: '',
    group: store.loggedInGroup.id,
    description: '',
    parameters: [],
    artifactParameters: [],
    taskGraph: '',
    artifactGraph: '',
    queues: [],
    plugins: [],
    artifactPlugins: [],
  })

  const ORIGINAL_COPY = {
    name: '',
    group: store.loggedInGroup.id,
    description: '',
    parameters: [],
    artifactParameters: [],
    taskGraph: '',
    artifactGraph: '',
    queues: [],
    plugins: [],
    artifactPlugins: [],
  }

  const valuesChangedFromOriginal = computed(() => {
    for (const key in ORIGINAL_COPY) {
      if(JSON.stringify(ORIGINAL_COPY[key]) !== JSON.stringify(entryPoint.value[key])) {
        return true
      }
    }
    return false
  })

  const enableSubmit = computed(() => {
    if(route.params.id === 'new' && valuesChangedFromOriginal.value) {
      return true
    } else if(route.params.id !== 'new' && valuesChangedFromEditStart.value) {
      return true
    } else {
      return false
    }
  })

  const copyAtEditStart = ref({})

  onMounted(() => {
    if(route.query.snapshotId && !store.showRightDrawer) {
      store.showRightDrawer = true
    } else {
      getEntrypoint()
      getPluginParameterTypes()
    }
  })

  const pluginParameterTypes = ref([])

  async function getPluginParameterTypes() {
    try {
      const res = await api.getData('pluginParameterTypes', { rowsPerPage: 0 })
      pluginParameterTypes.value = res.data.data
    } catch(err) {
      notify.error(err.response.data.message)
    } 
  }

  watch(() => store.selectedSnapshot, (ep) => {
    if(ep) {
      entryPoint.value = {
        name: ep.name,
        group: ep.group.id,
        description: ep.description,
        parameters: ep.parameters,
        artifactParameters: ep.artifactParameters,
        taskGraph: ep.taskGraph,
        artifactGraph: ep.artifactGraph,
        queues: ep.queues,
        plugins: ep.plugins,
        artifactPlugins: ep.artifactPlugins
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

  const valuesChangedFromEditStartBesidesPlugins = computed(() => {
    const { plugins: _1, artifactPlugins: _2, ...copyRest } = copyAtEditStart.value
    const { plugins: _3, artifactPlugins: _4, ...entryRest } = entryPoint.value
    return JSON.stringify(copyRest) !== JSON.stringify(entryRest)
  })

  const tasks = ref([])
  const artifactTasks = ref([])

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

  watch(() => entryPoint.value.artifactPlugins, () => {
    artifactTasks.value = []
    entryPoint.value.artifactPlugins.forEach((plugin) => {
      if(typeof plugin === 'number') return
      const pluginName = plugin.name
      plugin.files.forEach((file) => {
        file.tasks.artifacts.forEach((fTask) => {
          artifactTasks.value.push({ ...fTask, pluginName: pluginName })
        })
      })
    })
  }, { deep: true })

  const autocompletions = computed(() => {
    return [...entryPoint.value.parameters, ...entryPoint.value.artifactParameters].map((param) => {
      return {
        label: `$${param.name}`,
        type: 'variable'
      }
    })
  })

  const autocompletionsArtifacts = computed(() => {
    if(entryPoint.value.artifactParameters.length === 0) return []
    return entryPoint.value.artifactParameters.map((param) => {
      return {
        label: `$${param.name}`,
        type: 'variable'
      }
    })
  })

  const basicInfoForm = ref(null)

  const columns = [
    { name: 'name', label: 'Name', align: 'left', field: 'name', sortable: true, },
    { name: 'type', label: 'Type', align: 'left', field: 'parameterType', sortable: true, },
    { name: 'defaultValue', label: 'Default Value (optional)', align: 'left', field: 'defaultValue', sortable: true, },
    { name: 'actions', label: 'Actions', align: 'center', },
  ]

  const artifactColumns = [
    { name: 'name', label: 'Name', align: 'left', field: 'name', sortable: true, },
    { name: 'outputParams', label: 'Output Parameters', align: 'right', field: 'outputParams', sortable: false, classes: 'vertical-top' },
    { name: 'delete', label: 'Delete', align: 'center', },
  ]

  const taskColumns = [
    { name: 'pluginName', label: 'Plugin', align: 'left', field: 'pluginName', sortable: true, },
    { name: 'taskName', label: 'Task', align: 'left', field: 'name', sortable: true, },
    { name: 'inputParams', label: 'Input Parameters', align: 'right', field: 'inputParams', sortable: false, classes: 'vertical-top' },
    { name: 'outputParams', label: 'Output Parameters', align: 'right', field: 'outputParams', sortable: false, classes: 'vertical-top' },
    { name: 'add', label: 'Add to Task Graph', align: 'center', sortable: false, },
  ]

  const artifactTaskColumns = [
    { name: 'pluginName', label: 'Plugin', align: 'left', field: 'pluginName', sortable: true, },
    { name: 'taskName', label: 'Task', align: 'left', field: 'name', sortable: true, },
    { name: 'outputParams', label: 'Output Parameters', align: 'right', field: 'outputParams', sortable: false, classes: 'vertical-top' },
    { name: 'add', label: 'Add to Artifact Output Graph', align: 'center', sortable: false, },
  ]

  const title = ref('')
  const showReturnDialog = ref(false)

  async function getEntrypoint() {
    if(route.params.id === 'new') {
      title.value = 'Create Entrypoint'
      if(store.savedForms?.entryPoint) {
        showReturnDialog.value = true
        await checkIfStillValid('queues')
        await checkIfStillValid('plugins')
        entryPoint.value = store.savedForms.entryPoint
        copyAtEditStart.value = JSON.parse(JSON.stringify(store.savedForms.entryPoint))
      } else {
        copyAtEditStart.value = JSON.parse(JSON.stringify(entryPoint.value))
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
    let submitObject = JSON.parse(JSON.stringify(entryPoint.value))
    const keysToKeep = [
      'group', 
      'name', 
      'description', 
      'taskGraph', 
      'artifactGraph', 
      'parameters', 
      'artifactParameters', 
      'queues', 
      'plugins', 
      'artifactPlugins'
    ]
    for (const key of Object.keys(submitObject)) {
      if (!keysToKeep.includes(key)) {
        delete submitObject[key]
      }
    }
    // turn objects into ids
    submitObject.queues = submitObject.queues.map(q => q.id)
    submitObject.plugins = submitObject.plugins.map(p => p.id)
    submitObject.artifactPlugins = submitObject.artifactPlugins.map(p => p.id)

    submitObject.artifactParameters = submitObject.artifactParameters.map((param) => ({
      ...param,
      outputParams: param.outputParams.map((oParam) => ({
        ...oParam,
        parameterType: oParam.parameterType.id
      }))
    }))
    try {
      if (route.params.id === 'new') {
        await api.addItem('entrypoints', submitObject)
        store.savedForms.entryPoint = null
        notify.success(`Successfully created '${entryPoint.value.name}'`)
      } else {
        if(valuesChangedFromEditStartBesidesPlugins.value) {
          const keysToRemove = ['group', 'plugins', 'artifactPlugins']
          keysToRemove.forEach((key) => delete submitObject[key])
          await api.updateItem('entrypoints', route.params.id, submitObject)
        }
        if(pluginIDsToUpdate.value.length > 0) {
          await api.addPluginsToEntrypoint(route.params.id, pluginIDsToUpdate.value, "plugins")
        }
        if(artifactPluginIDsToUpdate.value.length > 0) {
          await api.addPluginsToEntrypoint(route.params.id, artifactPluginIDsToUpdate.value, "artifactPlugins")
        }
        for(const pluginId of pluginIDsToRemove.value) {
          await api.removePluginFromEntrypoint(route.params.id, pluginId, 'plugins')
        }
        for(const pluginId of artifactPluginIDsToRemove.value) {
          await api.removePluginFromEntrypoint(route.params.id, pluginId, 'artifactPlugins')
        }
        notify.success(`Successfully updated '${entryPoint.value.name}'`)
      }
      router.push('/entrypoints')
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
  const showDeleteDialogArtifactParam = ref(false)
  const selectedParam = ref({})
  const selectedParamIndex = ref('')
  const selectedParamType = ref('')
  const selectedArtifactParamProps = ref('')

  function deleteParam() {
    console.log('selectedParamType.value = ', selectedParamType.value)
    entryPoint.value[selectedParamType.value] = entryPoint.value[selectedParamType.value].filter((param) => param.name !== selectedParam.value.name)
    showDeleteDialogParam.value = false
  }

  const showEntrypointParamDialog = ref(false)
  const showArtifactParamDialog = ref(false)

  function updateParam(parameter) {
    entryPoint.value.parameters[selectedParamIndex.value] = { ...parameter }
    showEntrypointParamDialog.value = false
  }

  function createParam(parameter) {
    entryPoint.value.parameters.push({...parameter})
    showEntrypointParamDialog.value = false
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

  function addToArtifactGraph(task) {
    let string = `<output-name>:\n  contents: <contents>\n  task:\n    args:\n    name: ${task.name}`
    if(entryPoint.value.artifactGraph.trim().length === 0) {
      entryPoint.value.artifactGraph = ''
      entryPoint.value.artifactGraph = string
    } else {
      entryPoint.value.artifactGraph += `\n${string}`
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

  const clearFormExecuted = ref(false)

  function clearForm() {
    entryPoint.value = {
      name: '',
      group: store.loggedInGroup.id,
      description: '',
      parameters: [],
      artifactParameters: [],
      taskGraph: '',
      artifactGraph: '',
      queues: [],
      plugins: [],
      artifactPlugins: [],
    }
    basicInfoForm.value.reset()
    clearFormExecuted.value = true
    taskGraphError.value = ''
    store.savedForms.entryPoint = null
    copyAtEditStart.value = JSON.parse(JSON.stringify(entryPoint.value))
  }

  const isEmptyValues = computed(() => {
    return Object.values(entryPoint.value).every((value) => 
      (typeof value === 'string' && value === '') || 
      (Array.isArray(value) && value.length === 0)
    )
  })

  function leaveForm() {
    if(route.params.id === 'new' && valuesChangedFromOriginal.value) {
      store.savedForms.entryPoint = entryPoint.value
    } else {
      store.savedForms.entryPoint = null
    }
    confirmLeave.value = true
    router.push(toPath.value)
  }

  const pluginIDsToUpdate = ref([])
  const artifactPluginIDsToUpdate = ref([])
  const pluginIDsToRemove = ref([])
  const artifactPluginIDsToRemove = ref([])

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

  function addArtifactParam(param) {
    entryPoint.value.artifactParameters.push(param)
    showArtifactParamDialog.value = false
  }

  const showEditArtifactParamDialog = ref(false)
  const selectedTaskProps = ref()

  function handleSelectedParam(action, paramProps, paramIndex, inputOrOutputParams, functionsOrArtifacts) {
    selectedTaskProps.value = paramProps
    selectedTaskProps.value.paramIndex = paramIndex
    selectedTaskProps.value.inputOrOutputParams = inputOrOutputParams
    selectedTaskProps.value.functionsOrArtifacts = functionsOrArtifacts
    if(action === 'create') {
      selectedParam.value = ''
      return
    }
    selectedParam.value = selectedTaskProps.value.row[selectedTaskProps.value.inputOrOutputParams][selectedTaskProps.value.paramIndex]
  }

  function updateArtifactOutputParam(updatedParam) {
    entryPoint.value.artifactParameters[selectedTaskProps.value.rowIndex][selectedTaskProps.value.inputOrOutputParams][selectedTaskProps.value.paramIndex] = updatedParam
  }

  function addArtifactOutputParam(newParam) {
    entryPoint.value.artifactParameters[selectedTaskProps.value.rowIndex][selectedTaskProps.value.inputOrOutputParams].push(newParam)
  }

</script>
