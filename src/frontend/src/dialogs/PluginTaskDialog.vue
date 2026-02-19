<template>
  <q-dialog v-model="showDialog" :persistent="true">
    <q-card>
      <q-card-section class="bg-primary text-white text-h6">
        <div class="text-h6">Create {{ taskType === 'functions' ? 'Function' : 'Artifact' }} Task</div>
      </q-card-section>
      <q-card-section>
        <q-form ref="taskForm" @submit.prevent="addTask" id="taskForm">
          <q-input 
            outlined 
            dense 
            v-model.trim="task.name"
            :rules="[requiredRule]"
            class="q-mt-sm"
          >
            <template v-slot:before>
              <label :class="`field-label`">Task Name:</label>
            </template>
          </q-input>
          <div class="row items-end" style="min-height: 30px;" v-if="taskType === 'functions'">
            <label>
              Input Parameters:
            </label>
            <q-chip
              v-for="(param, i) in inputParams"
              :key="i"
              color="indigo"
              text-color="white"
              removable
              dense
              @remove="inputParams.splice(i, 1)"
            >
              {{ `${param.name}` }}
              <span v-if="param.required" class="text-red">*</span>
              {{ `: ${param.parameterType.name}` }}
            </q-chip>
          </div>
          <q-form ref="inputParamForm" greedy @submit.prevent="addInputParam" v-if="taskType === 'functions'">
            <div class="row">
              <q-input
                v-model.trim="inputParam.name"
                label="Name"
                :rules="[requiredRule]"
                dense
                outlined
                class="col q-mr-sm"
                style="width: 300px;"
              />
              <q-select 
                v-model="inputParam.parameterType"
                emit-value
                option-value="id"
                option-label="name"
                map-options
                label="Type"
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
                <span class="sr-only">Add Input Parameter</span>
                <q-tooltip>
                  Add Input Parameter
                </q-tooltip>
              </q-btn>
            </div>
          </q-form>
          
          <div class="row items-end" style="min-height: 30px;">
            <label>
              Output Parameters:
            </label>
            <q-chip
              v-for="(param, i) in outputParams"
              :key="i"
              color="purple"
              text-color="white"
              removable
              dense
              @remove="outputParams.splice(i, 1)"
              :label="`${param.name}: ${param.parameterType.name}`"
            />
          </div>
          <q-form ref="outputParamForm" greedy @submit.prevent="addOutputParam">
            <div class="row">
              <q-input
                v-model.trim="outputParam.name"
                label="Name"
                :rules="[requiredRule]"
                dense
                outlined
                class="col q-mr-sm"
                style="width: 370px;"
              />
              <q-select 
                v-model="outputParam.parameterType"
                emit-value
                option-value="id"
                option-label="name"
                map-options
                label="Type"
                :options="pluginParameterTypes"
                class="col q-mr-xl"
                outlined
                dense
                :rules="[requiredRule]"
              />
              <div class="col" v-if="taskType==='functions'"></div>
              <q-btn
                round
                icon="add"
                color="purple"
                style="height: 10px"
                class="q-mr-sm"
                @click="addOutputParam()"
              >
                <span class="sr-only">Add Output Parameter</span>
                <q-tooltip>
                  Add Output Parameter
                </q-tooltip>
              </q-btn>
            </div>
          </q-form>
        </q-form>
      </q-card-section>

      <q-separator />

      <q-card-actions align="right">
        <q-btn 
          outline
          color="primary cancel-btn" 
          label="Cancel" 
          v-close-popup 
          class="q-mr-xs"
        />
        <q-btn
          label="Confirm"
          color="primary"
          type="submit"
          form="taskForm"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps(['taskType', 'pluginParameterTypes'])

const emit = defineEmits(['submit'])

const showDialog = defineModel()

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

const task = ref({})

const taskForm = ref(null)
const inputParamForm = ref(null)
const outputParamForm = ref(null)


function requiredRule(val) {
  return (!!val) || "This field is required"
}

function addTask() {
  taskForm.value.validate().then(success => {
    if(success) {
      emit('submit', {
        name: task.value.name,
        inputParams: inputParams.value,
        outputParams: outputParams.value
      })
      showDialog.value = false
    }
  })
}

function addInputParam() {
  inputParamForm.value.validate().then(success => {
    if (success) {
      const type = props.pluginParameterTypes.find((paramType) => paramType.id === inputParam.value.parameterType)
      inputParam.value.parameterType = {
        name: type.name,
        id: type.id
      }
      inputParams.value.push(inputParam.value)
      inputParam.value = {}
      inputParam.value.required = true
      inputParamForm.value.reset()
    }
  })
}

function addOutputParam() {
  outputParamForm.value.validate().then(success => {
    if (success) {
      const type = props.pluginParameterTypes.find((paramType) => paramType.id === outputParam.value.parameterType)
      outputParam.value.parameterType = {
        name: type.name,
        id: type.id
      }
      outputParams.value.push(outputParam.value)
      outputParam.value = {}
      outputParamForm.value.reset()
    }
  })
}

function resetTaskForm() {
  task.value ={}
  taskForm.value.reset()
  inputParam.value = { required: true }
  outputParam.value = {}
  inputParams.value = []
  outputParams.value = []
  inputParamForm.value?.reset()
  outputParamForm.value?.reset()
}


watch(showDialog, (newVal) => {
  if(!newVal) {
    resetTaskForm()
  }
})

</script>