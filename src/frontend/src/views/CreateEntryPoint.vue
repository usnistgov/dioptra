<template>
  <div class="row items-center justify-between">
    <div class="row items-center">
      <PageTitle 
        :subtitle="pageSubtitle"
        conceptType="entrypoint" 
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
    <q-form ref="basicInfoForm" greedy :style="{ 'pointer-events': history ? 'auto' : '' }">
      <div class="row">
        <div :class="`${isMobile ? 'col-12' : 'col-6'} q-mr-xl`">
          
          <q-input 
            outlined 
            dense 
            v-model.trim="entryPoint.name"
            :rules="[requiredRule]"
            class="q-mb-md q-mt-md"
            aria-required="true"
            :disable="history"
            input-class="text-h6 text-weight-bold"
          >
            <template v-slot:before>
              <label class="field-label" style="width: 60px">Name:</label>
            </template>
          </q-input>

          <ResourcePicker
            v-model="entryPoint.group"
            type="group"
            :options="store.groups"
            option-value="id"
            @filter="getGroups"
            :disable="history"
            input-debounce="300"
            class="q-mb-md"
          >
            <template v-slot:before>
              <label class="field-label" style="width: 60px">Group:</label>
            </template>
          </ResourcePicker>

          <ResourcePicker
            v-if="!history"
            v-model="entryPoint.queues"
            type="queue"
            :options="queues"
            option-value="id"
            @filter="getQueues"
            :disable="history"
            input-debounce="300"
            class="q-mb-md"
            chip-outline
          >
            <template v-slot:before>
               <label class="field-label" style="width: 60px">Queues:</label>
            </template>
          </ResourcePicker>

          <div v-else class="row items-center q-mb-md">
            <label class="field-label" style="width: 60px">Queues:</label>
            <div 
              class="col" 
              style="border: 1px solid lightgray; border-radius: 4px; padding: 5px 8px; margin-left: 10px;"
            >
              <q-icon
                name="sym_o_info"
                size="1.5em"
                color="grey"
                class="q-mr-sm"
              />
              <span class="text-grey-7">Queues not available in snapshots</span>
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
            input-style="height: 173px; line-height: 1.5;"
            input-class="text-body1 text-grey-8"
          >
            <template v-slot:before>
              <label class="field-label">Description:</label>
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
                  <template #body-cell-name="props">
            <div style="font-size: 15px;">
              {{ props.row.name }}
            </div>
          </template>

          <template #body-cell-defaultValue="props">
            <q-chip
              v-if="props.row.defaultValue === null"
              label="No Default"
              color="negative"
              text-color="white"
            />
            <div v-else>
              {{ props.row.defaultValue }}
            </div>
          </template>
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
          @create="selectedArtifactParam = null; showArtifactParamDialog = true"
        >
          <template #body-cell-name="props">
            <div style="font-size: 15px;">
              {{ props.row.name }}
            </div>
          </template>
          
          <template #body-cell-actions="props">
            <q-btn 
              icon="edit"
              round size="sm"
              color="primary"
              flat
              class="q-mr-sm"
              @click="
                selectedArtifactParam = props.row;
                selectedArtifactParamIndex = props.rowIndex;
                showArtifactParamDialog = true;
              "
            />
            <q-btn 
              icon="sym_o_delete"
              round size="sm"
              color="negative"
              flat
              @click="selectedArtifactParamProps = props; showDeleteDialogArtifactParam = true"
            />
          </template>
          
          <template #body-cell-outputParams="props">
            <div class='row q-gutter-x-md justify-between'>
             <ParameterList 
                :items="props.row.outputParams" 
                type="output" 
                @click="(param, i) => { handleSelectedParam('edit', props, i, 'outputParams', 'artifacts'); showEditArtifactParamDialog = true; }"
             />
              <div>
                <q-btn
                  round
                  size="xs"
                  icon="add"
                  color="grey-5"
                  text-color="black"
                  class="q-mr-xs q-my-xs"
                  @click="handleSelectedParam('create', props, 0, 'outputParams', 'artifacts'); showEditArtifactParamDialog = true"
                />
                <q-tooltip> Add Output Parameters </q-tooltip> 
              </div>
            </div>
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
      <div :class="`${isMobile ? 'col-12 q-mb-xl' : 'col-6'} q-mr-lg`">
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
          style="min-height: 200px;"
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
        <div class="q-ma-none text-grey-8" >Attached Plugins:</div>
        <AssignPluginsDropdown
          v-model:selectedPlugins="entryPoint.plugins"
          v-model:pluginIDsToUpdate="pluginIDsToUpdate"
          v-model:pluginIDsToRemove="pluginIDsToRemove"
          class="q-mt-sm"
        />
         <div class="q-mt-md text-grey-8" >Function Tasks:</div>
        <TableComponent
          :rows="tasks"
          :columns="taskColumns"
          :hideToggleDraft="true"
          :hideSearch="true"
          :disableSelect="true"
          :hideOpenBtn="true"
          :hideDeleteBtn="true"
          :hideCreateBtn=true
          style = "margin-top:10px !important"
        >
          <template #body-cell-pluginName="props">
            <BadgeIcon :label="props.row.pluginName" type="plugin" :show-icon="true" size="sm" :mini="true" :uppercase="false" />
          </template>

          <template #body-cell-taskName="props">
            <ResourceName :text="props.row.name" concept-type="task" :minimal="true" />
          </template>

          <template #body-cell-inputParams="props">
            <ParameterList :items="props.row.inputParams" type="input" />
          </template>

          <template #body-cell-outputParams="props">
            <ParameterList :items="props.row.outputParams" type="output" />
          </template>

          <template #body-cell-add="props">
            <q-btn icon="add" round size="xs" color="grey-5" text-color="black" @click="addToTaskGraph(props.row)">
               <q-tooltip>Add to Task Graph YAML</q-tooltip>
            </q-btn>
          </template>
        </TableComponent>
      </div>
    </div>
  </fieldset>

  <fieldset class="q-px-lg q-mt-lg q-pt-lg" :class="history ? `disabled` : ``">
    <legend>Artifact Info</legend>
    <div class="row" :style="{ 'pointer-events': history ? 'none' : '' }">
      <div :class="`${isMobile ? 'col-12 q-mb-xl' : 'col-6'} q-mr-xl`">
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
          style="min-height: 200px;"
        />  
      </div>
      
      <div class="col">
        <h2>Artifact Task Plugins</h2>
        <div class="q-ma-none text-grey-8" >Attached Plugins:</div>
        <AssignPluginsDropdown
          v-model:selectedPlugins="entryPoint.artifactPlugins"
          v-model:pluginIDsToUpdate="artifactPluginIDsToUpdate"
          v-model:pluginIDsToRemove="artifactPluginIDsToRemove"
          class="q-mt-lg"
        />
         <div class="q-mt-md text-grey-8" >Artifact Tasks:</div>
        <TableComponent
          :rows="artifactTasks"
          :columns="artifactTaskColumns"
          :hideToggleDraft="true"
          :hideSearch="true"
          :disableSelect="true"
          :hideOpenBtn="true"
          :hideDeleteBtn="true"
          :hideCreateBtn=true
          style="margin-top:10px !important"
        >
          <template #body-cell-pluginName="props">
            <BadgeIcon :label="props.row.pluginName" type="plugin" :show-icon="true" :mini="true"  :uppercase="false" size="sm" />
          </template>

          <template #body-cell-taskName="props">
            <ResourceName :text="props.row.name" concept-type="task" :minimal="true" />
          </template>

          <template #body-cell-outputParams="props">
            <ParameterList :items="props.row.outputParams" type="output" />
          </template>

          <template #body-cell-add="props">
            <q-btn icon="add" round size="xs" color="grey-5" text-color="black" @click="addToArtifactGraph(props.row)">
               <q-tooltip>Add to Artifact Graph YAML</q-tooltip>
            </q-btn>
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
      @click="confirmLeave = true; store.initialPage ? router.push('/entrypoints') : router.back()"
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
    :editParam="selectedArtifactParam"
    @submit="handleArtifactParamSubmit"
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
  import TableComponent from '@/components/table/TableComponent.vue'
  import LeaveFormDialog from '@/dialogs/LeaveFormDialog.vue'
  import ReturnToFormDialog from '@/dialogs/ReturnToFormDialog.vue'
  import InfoPopupDialog from '@/dialogs/InfoPopupDialog.vue'
  import ArtifactParamDialog from '@/dialogs/ArtifactParamDialog.vue'
  import EditPluginTaskParamDialog from '@/dialogs/EditPluginTaskParamDialog.vue'
  import AssignPluginsDropdown from '@/components/AssignPluginsDropdown.vue'
  import ResourcePicker from "@/components/ResourcePicker.vue";
  

  import ResourceName from '@/components/table/cells/ResourceName.vue'
  import BadgeIcon from '@/components/table/cells/BadgeIcon.vue'
  import ParameterList from '@/components/table/cells/ParameterList.vue'

  const route = useRoute()
  
  const router = useRouter()

  const store = useLoginStore()

  const isMobile = inject('isMobile')
  const darkMode = inject('darkMode')

  const selectedArtifactParam = ref(null)
  const selectedArtifactParamIndex = ref(-1)

  function handleArtifactParamSubmit(param) {
    if (selectedArtifactParam.value) {
      // Update existing parameter
      entryPoint.value.artifactParameters[selectedArtifactParamIndex.value] = { ...param }
    } else {
      // Create new parameter
      entryPoint.value.artifactParameters.push({ ...param })
    }
    showArtifactParamDialog.value = false
  }

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

  const pageSubtitle = computed(() => {
    if (route.params.id === 'new') {
      return 'Create Entrypoint'
    }
    
    // 2. Handling History / Snapshots
    if (history.value && store.selectedSnapshot) {
      return `${entryPoint.value.name || 'Loading...'} (Snapshot ${store.selectedSnapshot.snapshot})`
    }
    
    // 3. Standard view 
    return copyAtEditStart.value?.name || entryPoint.value.name || 'Loading...'
  })

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
    { name: 'outputParams', label: 'Output Parameters', align: 'left', field: 'outputParams', sortable: false, classes: 'vertical-top' },
    { name: 'actions', label: 'Actions', align: 'center', },
  ]

  const taskColumns = [
    { name: 'pluginName', label: 'Plugin', align: 'left', field: 'pluginName', sortable: true, },
    { name: 'taskName', label: 'Task', align: 'left', field: 'name', sortable: true, },
    { name: 'inputParams', label: 'Input Params', align: 'left', field: 'inputParams', sortable: false, classes: 'vertical-top' },
    { name: 'outputParams', label: 'Output Params', align: 'left', field: 'outputParams', sortable: false, classes: 'vertical-top' },
    { name: 'add', label: 'Add to Graph', align: 'center', sortable: false, },
  ]

  const artifactTaskColumns = [
    { name: 'pluginName', label: 'Plugin', align: 'left', field: 'pluginName', sortable: true, },
    { name: 'taskName', label: 'Task', align: 'left', field: 'name', sortable: true, },
    { name: 'outputParams', label: 'Output Params', align: 'left', field: 'outputParams', sortable: false, classes: 'vertical-top' },
    { name: 'add', label: 'Add to Graph', align: 'center', sortable: false, },
  ]

  const showReturnDialog = ref(false)

  async function getEntrypoint() {
    if(route.params.id === 'new') {
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
    

    submitObject.queues = submitObject.queues.map(q => (q && typeof q === 'object') ? q.id : q)
    submitObject.plugins = submitObject.plugins.map(p => (p && typeof p === 'object') ? p.id : p)
    submitObject.artifactPlugins = submitObject.artifactPlugins.map(p => (p && typeof p === 'object') ? p.id : p)

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
          rowsPerPage: 0, 
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
    // always use Mixed Style Invocation
    let string = `<step-name>:\n  task: ${task.name}`
    if(task.inputParams.length > 0) {
      string += `\n  kwargs:`
      task.inputParams.forEach((param) => {
        string += `\n    ${param.name}: <input-value>`
      })
    }
    if(entryPoint.value.taskGraph.trim().length === 0) {
      entryPoint.value.taskGraph = string
    } else {
      entryPoint.value.taskGraph += `\n${string}`
    }
  }

  function addToArtifactGraph(task) {
    let string = `<output-name>:\n  contents: <contents>\n  task:\n    name: ${task.name}`
    if(entryPoint.value.artifactGraph.trim().length === 0) {
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
      confirmLeave.value = true
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
        parameters: entryPoint.value.parameters,
        artifacts: entryPoint.value.artifactParameters.map((param) => ({
            ...param,
            outputParams: param.outputParams.map((oParam) => ({
              ...oParam,
              parameterType: oParam.parameterType.id
            }))

          }))
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
      notify.error(err.response.data.message)
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