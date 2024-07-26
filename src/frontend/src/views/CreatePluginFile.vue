<template>
  <PageTitle :title="title" />
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
        :rows="pluginParameterTypes"
        :columns="columns"
        title="Plugin Param Types"
        @request="getPluginParameterTypes"
        ref="tableRef"
        :hideToggleDraft="true"
        :hideEditBtn="true"
        :hideDeleteBtn="true"
        :disableSelect="true"
      >
      <template #body-cell-view="props">
        <q-btn
          label="View"
          color="primary"
          @click.stop="structure = JSON.stringify(props.row.structure, null, 2); displayStructure = true;"
        />
      </template>
      </TableComponent>
      <TableComponent
        :rows="tasks"
        :columns="taskColumns"
        title="Plugin Tasks"
        ref="tableRef"
        :hideToggleDraft="true"
        :hideEditBtn="true"
        :hideDeleteBtn="true"
        :hideSearch="true"
        :disableSelect="true"
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
            @remove="tasks[props.rowIndex].inputParams.splice(i, 1)"
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
              @remove="tasks[props.rowIndex].outputParams.splice(i, 1)"
              :label="`${param.name}: ${pluginParameterTypes.filter((type) => type.id === param.parameterType)[0]?.name}`"
            />
            <q-btn
              round
              size="xs"
              icon="add"
              @click="handleSelectedParam('create', props, i, 'outputParams'); showEditParamDialog = true"
            />
        </template>
        <template #body-cell-actions="props">
          <q-btn icon="sym_o_delete" round size="sm" color="negative" flat @click="selectedTaskProps = props; showDeleteDialog = true" />
        </template>
      </TableComponent>
      <q-card bordered class="q-ma-xl">
        <q-card-section>
        <div class="text-h6">Task Form</div>
      </q-card-section>
      <q-form ref="taskForm" greedy @submit.prevent="addTask" class="q-mx-xl">
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
            />
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
            />
          </div>
        </q-form>



        <q-card-actions align="right">
          <q-btn
            label="Add Task"
            color="secondary"
            icon="add"
            type="submit"
          >
            <span class="sr-only">Add Task</span>
            <q-tooltip>
              Add Task
            </q-tooltip>
          </q-btn>
        </q-card-actions>
      </q-form>
    </q-card>
    </fieldset>
  </div>

  <div :class="`${isMobile ? '' : ''} float-right q-mb-lg`">
    <q-btn  
      :to="`/plugins/${route.params.id}/files`"
      color="negative" 
      label="Cancel"
      class="q-mr-lg"
    />
    <q-btn  
      @click="submit()" 
      color="primary" 
      label="Save File"
      type="submit"
    />
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
    v-model="showDeleteDialog"
    @submit="tasks.splice(selectedTaskProps.rowIndex, 1); showDeleteDialog = false"
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
</template>

<script setup>
  import { ref, inject, watch, onMounted } from 'vue'
  import { useRoute, useRouter } from 'vue-router'
  import CodeEditor from '@/components/CodeEditor.vue'
  import * as api from '@/services/dataApi'
  import * as notify from '../notify'
  import TableComponent from '@/components/TableComponent.vue'
  import InfoPopupDialog from '@/dialogs/InfoPopupDialog.vue'
  import PageTitle from '@/components/PageTitle.vue'
  import DeleteDialog from '@/dialogs/DeleteDialog.vue'
  import EditPluginTaskParamDialog from '@/dialogs/EditPluginTaskParamDialog.vue'
  
  const route = useRoute()
  const router = useRouter()

  const isMobile = inject('isMobile')

  const pluginFile = ref({})
  const uploadedFile = ref(null)

  const selectedTaskProps = ref()
  const showDeleteDialog = ref(false)
  const showEditParamDialog = ref(false)

  const title = ref('')

  onMounted(async () => {
    if(route.params.fileId === 'new') {
      title.value = 'Create File'
      return
    }
    try {
      const res = await api.getFile(route.params.id, route.params.fileId)
      console.log('getFile = ', res)
      pluginFile.value = res.data
      title.value = `Edit ${res.data.filename}`
      tasks.value = res.data.tasks
      tasks.value.forEach((task) => {
        [...task.inputParams, ... task.outputParams].forEach((param) => {
          param.parameterType = param.parameterType.id
        })
      })
    } catch(err) {
      notify.error(err.response.data.message)
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
    contentsError.value = newVal.length > 0 ? '' : 'This field is required'
  })

  async function submit() {
    basicInfoForm.value.validate().then(success => {
      contentsError.value = pluginFile.value.contents?.length > 0 ? '' : 'This field is required'
      if (success && contentsError.value === '') {
        addOrModifyFile()
      }
      else {
        // error
      }
    })
  }

  async function addOrModifyFile() {
    const plguinFileSubmit = {
        filename: pluginFile.value.filename,
        contents: pluginFile.value.contents,
        description: pluginFile.value.description,
        tasks: tasks.value
      }
    try {
      let res
      if(route.params.fileId === 'new') {
        res = await api.addFile(route.params.id, plguinFileSubmit)
      } else {
        res = await api.updateFile(route.params.id, route.params.fileId, plguinFileSubmit)
      }
      notify.success(`Sucessfully ${route.params.fileId === 'new' ? 'created' : 'updated'} '${res.data.filename}'`)
      router.push(`/plugins/${route.params.id}/files`)
    } catch(err) {
      console.log('err = ', err)
      notify.error(err.response.data.message)
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

  const selected = ref([])
  const tableRef = ref(null)
  const pluginParameterTypes = ref([])
  const displayStructure = ref(false)
  const structure = ref('')

  const columns = [
    { name: 'name', label: 'Name', align: 'left', field: 'name', sortable: true, },
    { name: 'description', label: 'Description', field: 'description',align: 'left', sortable: false },
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

  const tasks = ref([])
  const task = ref({
  })

  const basicInfoForm = ref(null)
  const taskForm = ref(null)
  const inputParamForm = ref(null)
  const outputParamForm = ref(null)

  const taskColumns = [
    { name: 'name', label: 'Name', align: 'left', field: 'name', sortable: true, },
    { name: 'inputParams', label: 'Input Params', field: 'inputParams', align: 'left', sortable: false },
    { name: 'outputParams', label: 'Output Params', field: 'outputParams', align: 'left', sortable: false },
    { name: 'actions', label: 'Actions', align: 'center', },
  ]

  async function getPluginParameterTypes(pagination) {
    console.log('pagination = ', pagination)
    try {
      const res = await api.getData('pluginParameterTypes', pagination)
      pluginParameterTypes.value = res.data.data
      tableRef.value.updateTotalRows(res.data.totalNumResults)
    } catch(err) {
      console.log('err = ', err)
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
        tasks.value.push({
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
    tasks.value[selectedTaskProps.value.rowIndex][selectedTaskProps.value.type][selectedTaskProps.value.paramIndex] = updatedParam
  }

  function addParam(newParam) {
    tasks.value[selectedTaskProps.value.rowIndex][selectedTaskProps.value.type].push(newParam)
  }

</script>