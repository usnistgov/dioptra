<template>
  <div class="row items-center justify-between">
    <PageTitle :title="title" />
    <q-btn 
      v-if="route.params.fileId !== 'new' && route.params.draftType !== 'newResourceDraft'"
      color="negative"
      icon="sym_o_delete" 
      label="Delete Plugin File" 
      @click="showDeleteFileDialog = true"
    />
  </div>
  <div class="row q-my-lg">
    <fieldset :class="`${isMobile ? 'col-12 q-mb-lg' : 'col q-mr-md'}`">
      <legend>Basic Info</legend>
      <div style="padding: 0 5%">
        <q-form @submit.prevent="submit" ref="basicInfoForm" greedy>
          <q-input 
            outlined 
            dense 
            v-model.trim="pluginFile.filename"
            :rules="[requiredRule, pythonFilenameRule]"
            class="q-mb-sm q-mt-md"
            aria-required="true"
          >
            <template v-slot:before>
              <label :class="`field-label`">Filename:</label>
            </template>
          </q-input>

          <q-input 
            outlined 
            dense 
            v-model.trim="pluginFile.description"
            class="q-mb-lg "
            type="textarea"
            autogrow
          >
            <template v-slot:before>
              <label :class="`field-label`">Description:</label>
            </template>
          </q-input>
        </q-form>

        <q-file
          v-model="uploadedFile"
          label="Upload Python File"
          outlined
          use-chips
          dense
          accept=".py, text/x-python"
          @update:model-value="processFile"
          class="q-mb-sm"
        >
          <template v-slot:before>
            <label :class="`field-label`">File Contents:</label>
          </template>
          <template v-slot:prepend>
            <q-icon name="attach_file" />
          </template>
        </q-file>

        <CodeEditor 
          v-model="pluginFile.contents"
          language="python"
          :placeholder="'#Enter plugin file code here...'"
          style="max-height: 50vh; margin-bottom: 15px;"
          :showError="contentsError"
        />
      </div>
    </fieldset>
    <fieldset :class="`${isMobile ? 'col-12' : 'col q-ml-md'}`">
      <legend>Plugin Tasks</legend>
      <TableComponent
        :rows="pluginFile.tasks"
        :columns="taskColumns"
        title="Plugin Tasks"
        ref="tableRef"
        :hideToggleDraft="true"
        :hideCreateBtn="true"
        :hideSearch="true"
        :disableSelect="true"
        :hideOpenBtn="true"
        :hideDeleteBtn="true"
        rightCaption="*Click param to edit, or X to delete"
      >
        <template #body-cell-name="props">
          {{ props.row.name }}
          <q-btn icon="edit" round size="sm" color="primary" flat />
          <q-popup-edit v-model="props.row.name" v-slot="scope">
            <q-input v-model="scope.value" dense autofocus counter @keyup.enter="scope.set" />
          </q-popup-edit>
        </template>
        <template #body-cell-inputParams="props">
          <q-chip
            v-for="(param, i) in props.row.inputParams"
            :key="i"
            color="indigo"
            class="q-mr-sm"
            text-color="white"
            dense
            clickable
            removable
            @remove="pluginFile.tasks[props.rowIndex].inputParams.splice(i, 1)"
            @click="handleSelectedParam('edit', props, i, 'inputParams'); showEditParamDialog = true"
          >
            {{ `${param.name}` }}
            <span v-if="param.required" class="text-red">*</span>
            {{ `: ${pluginParameterTypes.filter((type) => type.id === param.parameterType)[0]?.name}` }}
          </q-chip>
          <q-btn
            round
            size="xs"
            icon="add"
            color="grey-5"
            text-color="black"
            @click="handleSelectedParam('create', props, i, 'inputParams'); showEditParamDialog = true"
          />
        </template>
        <template #body-cell-outputParams="props">
          <q-chip
              v-for="(param, i) in props.row.outputParams"
              :key="i"
              color="purple"
              class="q-mr-sm"
              text-color="white"
              dense
              clickable
              removable
              @click="handleSelectedParam('edit', props, i, 'outputParams'); showEditParamDialog = true"
              @remove="pluginFile.tasks[props.rowIndex].outputParams.splice(i, 1)"
              :label="`${param.name}: ${pluginParameterTypes.filter((type) => type.id === param.parameterType)[0]?.name}`"
            />
            <q-btn
              round
              size="xs"
              icon="add"
              color="grey-5"
              text-color="black"
              @click="handleSelectedParam('create', props, i, 'outputParams'); showEditParamDialog = true"
            />
        </template>
        <template #body-cell-actions="props">
          <q-btn icon="sym_o_delete" round size="sm" color="negative" flat @click="selectedTaskProps = props; showDeleteDialog = true" />
        </template>
      </TableComponent>
      <q-card bordered class="q-ma-lg">
        <q-card-section>
          <div class="text-h6">Task Form</div>
        </q-card-section>
        <q-form ref="taskForm" greedy @submit.prevent="addTask" class="q-mx-lg">
          <q-input 
            outlined 
            dense 
            v-model.trim="task.name"
            :rules="[requiredRule]"
            class="q-mb-sm"
            label="Task Name"
          />
          <label>
            Input Params:
          </label>
          <q-chip
            v-for="(param, i) in inputParams"
            :key="i"
            color="indigo"
            text-color="white"
            removable
            @remove="inputParams.splice(i, 1)"
          >
            {{ `${param.name}` }}
            <span v-if="param.required" class="text-red">*</span>
            {{ `: ${pluginParameterTypes.filter((type) => type.id === param.parameterType)[0]?.name}` }}
          </q-chip>
          <q-form ref="inputParamForm" greedy @submit.prevent="addInputParam">
            <div class="row">
              <q-input
                v-model.trim="inputParam.name"
                label="Input Param Name"
                :rules="[requiredRule]"
                dense
                outlined
                class="col q-mr-sm"
              />
              <q-select 
                v-model="inputParam.parameterType"
                emit-value
                option-value="id"
                option-label="name"
                map-options
                label="Param Type"
                :options="pluginParameterTypes"
                class="col q-mr-xl"
                outlined
                dense
                :rules="[requiredRule]"
              />
              <div class="col">
                <q-checkbox
                  label="Required"
                  left-label
                  v-model="inputParam.required"
                />
              </div>
              <q-btn
                round
                icon="add"
                color="indigo"
                style="height: 10px"
                class="q-mr-sm"
                @click="addInputParam()"
              >
                <span class="sr-only">Add Input Param</span>
                <q-tooltip>
                  Add Input Param
                </q-tooltip>
              </q-btn>
            </div>
          </q-form>

          <label>
            Output Params:
          </label>
          <q-chip
            v-for="(param, i) in outputParams"
            :key="i"
            color="purple"
            text-color="white"
            removable
            @remove="outputParams.splice(i, 1)"
            :label="`${param.name}: ${pluginParameterTypes.filter((type) => type.id === param.parameterType)[0].name}`"
          />
          <q-form ref="outputParamForm" greedy @submit.prevent="addOutputParam">
            <div class="row">
              <q-input
                v-model.trim="outputParam.name"
                label="Output Param Name"
                :rules="[requiredRule]"
                dense
                outlined
                class="col q-mr-sm"
              />
              <q-select 
                v-model="outputParam.parameterType"
                emit-value
                option-value="id"
                option-label="name"
                map-options
                label="Param Type"
                :options="pluginParameterTypes"
                class="col q-mr-xl"
                outlined
                dense
                :rules="[requiredRule]"
              />
              <div class="col"></div>
              <q-btn
                round
                icon="add"
                color="purple"
                style="height: 10px"
                class="q-mr-sm"
                @click="addOutputParam()"
              >
                <span class="sr-only">Add Output Param</span>
                <q-tooltip>
                  Add Output Param
                </q-tooltip>
              </q-btn>
            </div>
          </q-form>

          <q-card-actions align="right">
            <q-btn
              label="Add Task"
              color="secondary"
              icon="add"
              type="submit"
            />
          </q-card-actions>
        </q-form>
      </q-card>

      <q-expansion-item
        :label="`${showParamTypes ? 'Hide' : 'Show'} Plugin Param Types`"
        v-model="showParamTypes"
        header-class="text-bold shadow-2"
        class="q-mb-md"
        ref="expansionItem"
        @after-show="scroll"
      >
        <TableComponent
          :rows="pluginParameterTypes"
          :columns="columns"
          title="Plugin Param Types"
          @request="getPluginParameterTypes"
          :hideToggleDraft="true"
          :hideCreateBtn="true"
          :disableSelect="true"
          style="margin-top: 0"
          :hideOpenBtn="true"
          :hideDeleteBtn="true"
        >
          <template #body-cell-view="props">
            <q-btn
              label="View"
              color="primary"
              @click.stop="structure = JSON.stringify(props.row.structure, null, 2); displayStructure = true;"
            />
          </template>
        </TableComponent>
      </q-expansion-item>
    </fieldset>
  </div>

  <div class="row justify-between">
    <!--       :style="{ visibility: route.params.fileId === 'new' ? 'visible' : 'hidden' }" -->
    <q-btn
      label="Save As Draft"
      color="orange-5"
      @click="submitDraft('newDraft')"
      :style="{ 
        visibility: route.params.draftType ? 'hidden' : 'visible' 
      }"
    />
    <div>
      <q-btn
        outline
        color="primary" 
        label="Cancel"
        class="q-mr-lg cancel-btn"
        @click="confirmLeave = true; router.back()"
      />
      <q-btn  
        @click="triggerSubmit()"  
        color="primary" 
        :label="!route.params.draftType ? 'Save File' : 
          route.params.draftType === 'draft' ? 'Save File Draft' : 'Save File Resource Draft'"
        type="submit"
      />
    </div>
  </div>

  <InfoPopupDialog
    v-model="displayStructure"
  >
    <template #title>
      <label id="modalTitle">
        Plugin Param Structure
      </label>
    </template>
    <CodeEditor 
      v-model="structure"
      style="height: auto;"
      :readOnly="true"
    />
  </InfoPopupDialog>
  <DeleteDialog 
    v-model="showDeleteFileDialog"
    @submit="deleteFile(); showDeleteFileDialog = false"
    type="Plugin File"
    :name="pluginFile.filename"
  />
  <DeleteDialog 
    v-model="showDeleteDialog"
    @submit="pluginFile.tasks.splice(selectedTaskProps.rowIndex, 1); showDeleteDialog = false"
    type="Plugin Task"
    :name="selectedTaskProps?.row?.name"
  />
  <EditPluginTaskParamDialog 
    v-model="showEditParamDialog"
    :editParam="selectedParam"
    :pluginParameterTypes="pluginParameterTypes"
    :paramType="selectedTaskProps?.type"
    @updateParam="updateParam"
    @addParam="addParam"
  />
  <LeaveFormDialog 
    v-model="showLeaveDialog"
    type="plugin file"
    @leaveForm="leaveForm"
  />
  <ReturnToFormDialog
    v-model="showReturnDialog"
    @cancel="clearForm"
  />
</template>

<script setup>
  import { ref, inject, watch, onMounted, computed } from 'vue'
  import { useRoute, useRouter, onBeforeRouteLeave } from 'vue-router'
  import CodeEditor from '@/components/CodeEditor.vue'
  import * as api from '@/services/dataApi'
  import * as notify from '../notify'
  import TableComponent from '@/components/TableComponent.vue'
  import InfoPopupDialog from '@/dialogs/InfoPopupDialog.vue'
  import PageTitle from '@/components/PageTitle.vue'
  import DeleteDialog from '@/dialogs/DeleteDialog.vue'
  import EditPluginTaskParamDialog from '@/dialogs/EditPluginTaskParamDialog.vue'
  import LeaveFormDialog from '@/dialogs/LeaveFormDialog.vue'
  import ReturnToFormDialog from '@/dialogs/ReturnToFormDialog.vue'
  import { useLoginStore } from '@/stores/LoginStore'

  const store = useLoginStore()
  
  const route = useRoute()
  const router = useRouter()

  const isMobile = inject('isMobile')

  const pluginFile = ref({
    filename: '',
    description: '',
    contents: '',
    tasks: []
  })
  const initialCopy = ref({
    filename: '',
    description: '',
    contents: '',
    tasks: [],
  })

  const valuesChanged = computed(() => {
    for (const key in initialCopy.value) {
      if(JSON.stringify(initialCopy.value[key]) !== JSON.stringify(pluginFile.value[key])) {
        return true
      }
    }
    return false
  })

  const uploadedFile = ref(null)

  const selectedTaskProps = ref()
  const showDeleteFileDialog = ref(false)
  const showDeleteDialog = ref(false)
  const showEditParamDialog = ref(false)

  const expansionItem = ref(null)
  const showParamTypes = ref(false)

  function scroll() {
    expansionItem.value.$el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  const title = ref('')

  onMounted(async () => {
    if(route.params.fileId === 'new') {
      title.value = 'Create File'
      if(store.savedForms.files[route.params.id]) {
        pluginFile.value = JSON.parse(JSON.stringify(store.savedForms.files[route.params.id]))
        initialCopy.value = JSON.parse(JSON.stringify(store.savedForms.files[route.params.id]))
        showReturnDialog.value = true
      }
      return
    }
    if(route.params.draftType === 'newResourceDraft') {
      let parentPluginName
      try {
        const res = await api.getFile(route.params.id, route.params.fileId)
        parentPluginName = res.data.filename
        pluginFile.value = {
          filename: res.data.filename,
          contents: res.data.contents,
          tasks: res.data.tasks,
          description: res.data.description
        }
        initialCopy.value = JSON.parse(JSON.stringify(pluginFile.value))
      } catch(err) {
        console.log(err)
      }
      title.value = `Create ${parentPluginName} Resource Draft`
      return
    }
    try {
      let res
      if(route.params.draftType === 'draft') {
        res = await api.getFile(route.params.id, route.params.fileId, 'draft')
      } else if(route.params.draftType === 'resourceDraft') {
        res = await api.getFile(route.params.id, route.params.fileId, 'resourceDraft')
      } else {
        res = await api.getFile(route.params.id, route.params.fileId)
      }
      pluginFile.value = {
        filename: res.data.filename,
        contents: res.data.contents,
        tasks: res.data.tasks,
        description: res.data.description,
        ...(res.data.resourceSnapshot && { resourceSnapshot: res.data.resourceSnapshot })
      }
      title.value = `Edit ${res.data.filename}`
      console.log('plugin tasks not containing pluginParamType?', pluginFile.value)
      pluginFile.value.tasks.forEach((task) => {
        [...task.inputParams, ...task.outputParams].forEach((param) => {
          param.parameterType = param.parameterType.id
        })
      })
      initialCopy.value = JSON.parse(JSON.stringify(pluginFile.value))
    } catch(err) {
      notify.error(err.response.data.message)
      console.log('err = ', err)
    } 
  })

  function requiredRule(val) {
    return (!!val) || "This field is required"
  }

  function pythonFilenameRule(val) {
    const regex = /^[a-zA-Z_][a-zA-Z0-9_]*\.py$/
    if (!regex.test(val)) {
      return "Invalid Python filename"
    }
    if (val === '_.py') {
      return "_.py is not a valid Python filename"
    }
    return true
  }

  const contentsError = ref('')

  watch(() => pluginFile.value.contents, (newVal) => {
    if(clearFormExecuted.value) {
      clearFormExecuted.value = false
    } else {
      contentsError.value = newVal.length > 0 ? '' : 'This field is required'
    }
  })

  function triggerSubmit() {
      //   @click="!route.params.draftType ? submit() : 
      // route.params.draftType === 'draft' ? submitDraft('draft') : submitDraft('newResourceDraft')"
    if(!route.params.draftType) {
      submit()
    } else if(route.params.draftType === 'draft') {
      submitDraft(route.params.draftType)
    } else {
      submitResourceDraft()
    }
  }

  async function submit() {
    const isValid = await basicInfoForm.value.validate()
    contentsError.value = pluginFile.value.contents?.length > 0 ? '' : 'This field is required'
    if (!isValid || contentsError.value !== '') return

    try {
      let res
      if (route.params.fileId === 'new') {
        res = await api.addFile(route.params.id, pluginFile.value)
      } else {
        res = await api.updateFile(route.params.id, route.params.fileId, pluginFile.value)
      }

      store.savedForms.files[route.params.id] = null
      notify.success(`Successfully ${route.params.fileId === 'new' ? 'created' : 'updated'} '${res.data.filename}'`)
      confirmLeave.value = true
      router.push(`/plugins/${route.params.id}/files`)
    } catch (err) {
      notify.error(err.response?.data?.message || 'An error occurred')
    }
  }

  async function submitResourceDraft() {
    const isValid = await basicInfoForm.value.validate()
    contentsError.value = pluginFile.value.contents?.length > 0 ? '' : 'This field is required'
    if (!isValid || contentsError.value !== '') return

    try {
      let res
      if(route.params.draftType === 'newResourceDraft') {
        // create new resource draft
        res = await api.addFile(route.params.id, pluginFile.value, 'resourceDraft', route.params.fileId)
        notify.success(`Successfully created resource draft '${res.data.payload.filename}'`)
      } else if(route.params.draftType === 'resourceDraft') {
        // update resource draft
        console.log('pluginFile = ', pluginFile.value)
        res = await api.updateFile(route.params.id, route.params.fileId, pluginFile.value, 'resourceDraft')
        notify.success(`Successfully updated resource draft '${res.data.payload.filename}'`)
      }
      confirmLeave.value = true
      router.push(`/plugins/${route.params.id}/files`)
    } catch(err) {
      notify.error(err.response?.data?.message || 'An error occurred')
    }
  }

  async function submitDraft(type) {
    const isValid = await basicInfoForm.value.validate()
    contentsError.value = pluginFile.value.contents?.length > 0 ? '' : 'This field is required'
    if (!isValid || contentsError.value !== '') return
    try {
      let res
      if(type === 'newDraft') {
        // create new draft
        res = await api.addFile(route.params.id, pluginFile.value, 'draft')
        notify.success(`Successfully created draft '${res.data.payload.filename}'`)
      } else if(route.params.draftType === 'draft') {
        // update draft
        res = await api.updateFile(route.params.id, route.params.fileId, pluginFile.value, 'draft')
        notify.success(`Successfully updated draft '${res.data.payload.filename}'`)
      }
      confirmLeave.value = true
      router.push({
        path: `/plugins/${route.params.id}/files`,
        state: { showDrafts: true } 
      })
    } catch(err) {
      console.log('err = ', err)
      notify.error(err.response?.data?.message || 'An error occurred')
    }
  }

  function processFile() {
    const file = uploadedFile.value
    if (!file) {
      pluginFile.value.contents = ''
      return
    }
    const reader = new FileReader()
    reader.onload = (e) => {
      pluginFile.value.contents = e.target.result;
    }
    reader.onerror = (e) => {
      console.log('error = ', e)
    }
    reader.readAsText(file); // Reads the file as text
  }

  const tableRef = ref(null)
  const pluginParameterTypes = ref([])
  const displayStructure = ref(false)
  const structure = ref('')

  const columns = [
    { name: 'name', label: 'Name', align: 'left', field: 'name', sortable: true, },
    { name: 'description', label: 'Description', field: 'description',align: 'left', sortable: true },
    { name: 'view', label: 'Structure', align: 'left', sortable: false },
  ]

  const inputParam = ref({
    name: '',
    parameterType: '',
    required: true
  })
  const outputParam = ref({
    name: '',
    parameterType: ''
  })

  const inputParams = ref([])
  const outputParams = ref([])

  const task = ref({
  })

  const basicInfoForm = ref(null)
  const taskForm = ref(null)
  const inputParamForm = ref(null)
  const outputParamForm = ref(null)

  const taskColumns = [
    { name: 'name', label: 'Name', align: 'left', field: 'name', sortable: false, },
    { name: 'inputParams', label: 'Input Params', field: 'inputParams', align: 'left', sortable: false },
    { name: 'outputParams', label: 'Output Params', field: 'outputParams', align: 'left', sortable: false },
    { name: 'actions', label: 'Actions', align: 'center', },
  ]

  async function getPluginParameterTypes(pagination) {
    pagination.rowsPerPage = 0 // get all
    try {
      const res = await api.getData('pluginParameterTypes', pagination)
      pluginParameterTypes.value = res.data.data
      tableRef.value.updateTotalRows(res.data.totalNumResults)
    } catch(err) {
      notify.error(err.response.data.message)
    } 
  }

  function addInputParam() {
    inputParamForm.value.validate().then(success => {
      if (success) {
        inputParams.value.push(inputParam.value)
        inputParam.value = {}
        inputParam.value.required = true
        inputParamForm.value.reset()
      }
      else {
        // error
      }
    })
  }

  function addOutputParam() {
    outputParamForm.value.validate().then(success => {
      if (success) {
        outputParams.value.push(outputParam.value)
        outputParam.value = {}
        outputParamForm.value.reset()
      }
      else {
        // error
      }
    })
  }

  function addTask() {
    taskForm.value.validate().then(success => {
      if (success) {
        pluginFile.value.tasks.push({
          name: task.value.name,
          inputParams: inputParams.value,
          outputParams: outputParams.value
        })
        task.value ={}
        inputParams.value = []
        outputParams.value = []
        taskForm.value.reset()
      }
      else {
        // error
      }
    })
  }

  const selectedParam = ref()

  function handleSelectedParam(action, paramProps, paramIndex, type) {
    selectedTaskProps.value = paramProps
    selectedTaskProps.value.paramIndex = paramIndex
    selectedTaskProps.value.type = type
    if(action === 'create') {
      selectedParam.value = ''
      return
    }
    selectedParam.value = selectedTaskProps.value.row[selectedTaskProps.value.type][selectedTaskProps.value.paramIndex]
  }

  function updateParam(updatedParam) {
    pluginFile.value.tasks[selectedTaskProps.value.rowIndex][selectedTaskProps.value.type][selectedTaskProps.value.paramIndex] = updatedParam
  }

  function addParam(newParam) {
    pluginFile.value.tasks[selectedTaskProps.value.rowIndex][selectedTaskProps.value.type].push(newParam)
  }

  onBeforeRouteLeave((to, from, next) => {
    toPath.value = to.path
    if(confirmLeave.value || !valuesChanged.value) {
      next(true)
    } else if(route.params.fileId === 'new') {
      leaveForm()
    } else {
      showLeaveDialog.value = true
    }
  })

  const showLeaveDialog = ref(false)
  const showReturnDialog = ref(false)
  const confirmLeave = ref(false)
  const toPath = ref()

  const isEmptyValues = computed(() => {
    return Object.values(pluginFile.value).every((value) => 
      (typeof value === 'string' && value === '') || 
      (Array.isArray(value) && value.length === 0)
    )
  })

  function leaveForm() {
    if(isEmptyValues.value) {
      store.savedForms.files[route.params.id] = null
    } else if(route.params.fileId === 'new') {
      store.savedForms.files[route.params.id] = pluginFile.value
    }
    confirmLeave.value = true
    router.push(toPath.value)
  }

  const clearFormExecuted = ref(false)

  function clearForm() {
    pluginFile.value = {
      filename: '',
      description: '',
      contents: '',
      tasks: [],
    }
    basicInfoForm.value.reset()
    clearFormExecuted.value = true
    store.savedForms.files[route.params.id] = null
  }

  async function deleteFile() {
    try {
      if(!route.params.draftType) {
        await api.deleteFile(route.params.id, route.params.fileId)
      } else if(route.params.draftType === 'draft') {
        await api.deleteFile(route.params.id, route.params.fileId, 'draft')
      } else if(route.params.draftType === 'resourceDraft') {
        await api.deleteFile(route.params.id, route.params.fileId, 'resourceDraft')
      }
      notify.success(`Successfully deleted '${pluginFile.value.filename}'`)
      router.push({
        path: `/plugins/${route.params.id}/files`,
        ...(route.params.draftType === 'draft' && { state: { showDrafts: true } })
      })
    } catch(err) {
      notify.error(err.response.data.message);
    }
  }

</script>