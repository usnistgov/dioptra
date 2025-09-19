<template>
  <q-dialog v-model="showDialog">
    <q-card>
      <q-card-section class="bg-primary text-white text-h6">
        Import Plugin Tasks
      </q-card-section>

      <q-card-section style="max-height: 75vh" class="scroll">
        <p class="text-body2">
          The plugin tasks below have been inferred from your python code.  
          Select the tasks you would like to import.  Duplicate tasks will
          be overwritten.
        </p>
        <p v-if="errorMessage" class="text-negative" style="max-width: 500px;">
          Error: {{ errorMessage }}
        </p>
        <TableComponent
          :rows="tasks"
          :columns="taskColumns"
          title="Plugin Tasks"
          ref="tableRef"
          :hideToggleDraft="true"
          :hideCreateBtn="true"
          :hideSearch="true"
          :hideOpenBtn="true"
          :hideDeleteBtn="true"
          :highlightRow="true"
          :disabledRowKeys="disabledRowKeys"
          v-model:selected="selectedTasks"
          selection="multiple"
          row-key="name"
        >
          <template #body-cell-name="props">
            <div style="font-size: 18px;">
              {{ props.row.name }}
              <!-- <p v-if="props.row.missing_types.length > 0" class="text-caption text-negative">
                Missing Types:
                <div v-for="type in props.row.missing_types">
                  {{ type.name }}
                </div>
              </p> -->
            </div>
          </template>
          <template #body-cell-inputParams="props">
            <div class="column items-end fit q-mt-sm">
              <q-chip
                v-for="(param, i) in props.row.inputParams"
                :key="i"
                color="indigo"
                text-color="white"
                dense
              >
                {{ `${param.name}` }}
                <span v-if="param.required" class="text-red">*</span>
                {{ `: ${param.type}` }}
              </q-chip>
              <q-chip
                v-if="props.row.inputParams.length === 0"
                dense
                color="orange"
                text-color="white"
                label="No params listed"
              />
            </div>
          </template>
          <template #body-cell-outputParams="props">
            <div class="column items-end fit q-mt-sm">
              <q-chip
                v-for="(param, i) in props.row.outputParams"
                :key="i"
                color="purple"
                text-color="white"
                dense
                :label="`${param.name}: ${param.type}`"
              />
              <q-chip
                v-if="props.row.outputParams.length === 0"
                dense
                color="orange"
                text-color="white"
                label="No params listed"
              />
            </div>
          </template>
          <template #body-cell-select="props">
            <q-checkbox
              v-model="selectedTasks"
              :val="props.row"
            />
          </template>
          <template #expandedSlot="{ row, rowProps }">
            <div class="row" v-if="Object.hasOwn(dupliateIdenticalTasks, row.name)" @vue:mounted="expandRow(row, rowProps)">
              Duplicate task with identical params already exist in your plugin file.
            </div>
            <div v-if="Object.hasOwn(dupliateTasksWithDifferentParams, row.name)" @vue:mounted="expandRow(row, rowProps)">
              <div class="row">
                Duplicate task.  Importing will overwrite the existing params below.
              </div>
              <div class="row justify-end">
                <div class="column items-end">
                  <q-chip
                    v-for="(param, i) in dupliateTasksWithDifferentParams[row.name].inputParams"
                    :key="i"
                    color="indigo"
                    text-color="white"
                    dense
                  >
                    {{ `${param.name}` }}
                    <span v-if="param.required" class="text-red">*</span>
                    {{ `: ${param.type}` }}
                  </q-chip>
                  <q-chip
                    v-if="dupliateTasksWithDifferentParams[row.name].inputParams.length === 0"
                    dense
                    color="orange"
                    text-color="white"
                    label="No params listed"
                  />
                </div>
                <div class="column items-end" style="width: 142px; padding-left: 0; padding-right: 0;">
                  <q-chip
                    v-for="(param, i) in dupliateTasksWithDifferentParams[row.name].outputParams"
                    :key="i"
                    color="purple"
                    text-color="white"
                    dense
                    :label="`${param.name}: ${param.type}`"
                  />
                  <q-chip
                    v-if="dupliateTasksWithDifferentParams[row.name].outputParams.length === 0"
                    dense
                    color="orange"
                    text-color="white"
                    label="No params listed"
                  />
                </div>
              </div>
            </div>
          </template>
        </TableComponent>
      </q-card-section>

      <q-separator />

      <q-card-actions align="right" class="text-primary">
        <q-form @submit="submit()" >
          <q-btn 
            outline
            color="primary cancel-btn" 
            label="Cancel" 
            v-close-popup 
            class="q-mr-md"
          />
          <q-btn
            color="primary"
            type="submit"
            >
              Import
          </q-btn>
        </q-form>
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import * as api from '@/services/dataApi'
import TableComponent from '@/components/TableComponent.vue'
import * as notify from '../notify'

const props = defineProps(['pythonCode', 'pluginParameterTypes', 'existingTasks'])
const emit = defineEmits(['importTasks'])

const showDialog = defineModel()

const existingTasksCopy = ref([])

watch(() => showDialog.value, (newVal) => {
  if(newVal) {
    tasks.value = []
    errorMessage.value = ""
    disabledRowKeys.value = []
    existingTasksCopy.value = JSON.parse(JSON.stringify(props.existingTasks))
    suggestPluginTasks()
  }
})

const tasks = ref([])
const selectedTasks = ref([])
const errorMessage = ref('')

async function suggestPluginTasks() {
  try {
    const res = await api.suggestPluginTasks(props.pythonCode)
    /*
      endpoint task:
        inputs: [{ name: "name", required: true, type: "string" }],
        outputs: [{ name: "output", type: "string" }],
        missing_types: []
      existing task:
        inputParams: [{ name: "name", required: true, parameterType: {id, name} }],
        outputParams: [{ name: "output", parameterType: {id, name} }],
    */

    // endpoint tasks, change inputs/outputs keys to inputParams/outputParams
    tasks.value = res.data.tasks.map(({ inputs, outputs, ...rest }) => ({
      ...rest,
      inputParams: inputs,
      outputParams: outputs,
    }))
    console.log('infered tasks = ', tasks.value)
    console.log('existing tasks = ', existingTasksCopy.value)

    // endpoint tasks, add parameterType id
    tasks.value.forEach((task) => {
      [...task.inputParams, ...task.outputParams].forEach((param) => {
        param.parameterType = props.pluginParameterTypes.find((type) => type.name === param.type)?.id
      })
    })

    // existing tasks, add type string
    existingTasksCopy.value.forEach((task) => {
      [...task.inputParams, ...task.outputParams].forEach((param) => {
        param.parameterType = param.parameterType.id
        param.type = props.pluginParameterTypes.find((type) => type.id === param.parameterType)?.name
      })
    })

    // auto select all tasks except for exact duplicates
    selectedTasks.value = tasks.value.filter(
      task => !Object.keys(dupliateIdenticalTasks.value).includes(task.name)
    )
  } catch(err) {
    console.warn(err)
    notify.error(err.response.data.message)
    errorMessage.value = err.response.data.message
  }
}

const taskColumns = [
  { name: 'select', label: 'Select', align: 'center', },
  { name: 'name', label: 'Name', align: 'left', field: 'name', sortable: false,  },
  { name: 'inputParams', label: 'Input Parameters', field: 'inputParams', align: 'right', sortable: false, style: 'width: 150px', },
  { name: 'outputParams', label: 'Output Parameters', field: 'outputParams', align: 'right', sortable: false, style: 'width: 150px' },
]

async function submit() {
  selectedTasks.value.forEach((task) => {
    delete task.missing_types;
    [...task.inputParams, ...task.outputParams].forEach((param) => {
      param.parameterType = {
        id: param.parameterType,
        name: param.type,
      }
      delete param.type
    })
  })
  emit('importTasks', selectedTasks.value)
  showDialog.value = false
}

const dupliateTasksWithDifferentParams = computed(() => {
  let returnObject = {}
  if(tasks.value.length === 0 || existingTasksCopy.value.length === 0) return returnObject
  tasks.value.forEach((task) => {
    const duplicate = existingTasksCopy.value.find((existingTask) => existingTask.name === task.name)
    if(!duplicate) return
    const areEqual = deepEqual(task, duplicate, ['missing_types', 'id'])
    if(areEqual) return
    else {
      returnObject[`${task.name}`] = {
        inputParams: duplicate.inputParams,
        outputParams: duplicate.outputParams,
      }
    }
  })
  return returnObject
})

const dupliateIdenticalTasks = computed(() => {
  let returnObject = {}
  if(tasks.value.length === 0 || existingTasksCopy.value.length === 0) return returnObject
  tasks.value.forEach((task) => {
    const duplicate = existingTasksCopy.value.find((existingTask) => existingTask.name === task.name)
    if(!duplicate) return
    const areEqual = deepEqual(task, duplicate, ['missing_types', 'id'])
    if(!areEqual) return
    else {
      returnObject[`${task.name}`] = {
        inputParams: duplicate.inputParams,
        outputParams: duplicate.outputParams,
      }
    }
  })
  return returnObject
})

const disabledRowKeys = ref([])

// expand row only if duplicate with different param exists
function expandRow(row, rowProps) {
  const duplicate = existingTasksCopy.value.find((task) => task.name === row.name)
  if(!duplicate) return null
  rowProps.expand = true
  if(row.name in dupliateIdenticalTasks.value) {
    disabledRowKeys.value.push(row.name)
  }
}

function deepEqual(obj1, obj2, ignoreKeys = []) {
  const isObject = (obj) => obj && typeof obj === 'object'

  if (!isObject(obj1) || !isObject(obj2)) return obj1 === obj2

  const keys1 = Object.keys(obj1).filter(k => !ignoreKeys.includes(k))
  const keys2 = Object.keys(obj2).filter(k => !ignoreKeys.includes(k))

  if (keys1.length !== keys2.length) return false;

  return keys1.every(key =>
    keys2.includes(key) &&
    deepEqual(obj1[key], obj2[key], ignoreKeys)
  );
}


</script>