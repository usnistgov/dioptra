<template>
  <q-dialog v-model="showDialog" :persistent="true">
    <q-card>
      <q-card-section class="bg-primary text-white text-h6">
        <div class="text-h6">Create Artifact Parameter</div>
      </q-card-section>
      <q-card-section>
        <q-form ref="artifactParamForm" greedy @submit.prevent="addArtifactParam" id="artifactForm">
          <q-input 
            outlined 
            dense 
            v-model.trim="artifactParam.name"
            :rules="[requiredRule]"
            class="q-mt-sm"
          >
            <template v-slot:before>
              <label :class="`field-label`">Name:</label>
            </template>
          </q-input>
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
                label="Output Parameter Name"
                :rules="[requiredRule]"
                dense
                outlined
                class="col q-mr-sm"
                style="width: 395px;"
              />
              <q-select 
                v-model="outputParam.parameterType"
                option-label="name"
                map-options
                label="Parameter Type"
                :options="pluginParameterTypes"
                class="col q-mr-lg"
                outlined
                dense
                :rules="[requiredRule]"
              />
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
          form="artifactForm"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import * as api from '@/services/dataApi'
import * as notify from '../notify'

const showDialog = defineModel()

const emit = defineEmits(['submit'])

const outputParams = ref([])
const outputParam = ref({
  name: '',
  parameterType: ''
})
const artifactParam = ref({
  name: '',
  outputParams: []
})
const pluginParameterTypes = ref([])
const artifactParamForm = ref(null)
const outputParamForm = ref(null)

function requiredRule(val) {
  return (!!val) || "This field is required"
}

watch(showDialog, (newVal) => {
  getPluginParameterTypes()
  if(!newVal) {
    artifactParam.value = {
      name: '',
      outputParams: []
    }
    outputParam.value = {
      name: '',
      parameterType: ''
    }
    resetForm()
  }
})

async function getPluginParameterTypes() {
  try {
    const res = await api.getData('pluginParameterTypes', { rowsPerPage: 0 })
    pluginParameterTypes.value = res.data.data
  } catch(err) {
    notify.error(err.response.data.message)
  } 
}


function addOutputParam() {
  outputParamForm.value.validate().then(success => {
    if (success) {
      const type = pluginParameterTypes.value.find((paramType) => paramType.id === outputParam.value.parameterType.id)
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

function addArtifactParam() {
  artifactParamForm.value.validate().then(success => {
    if(success) {
      const submitArtifactParam = {
        name: artifactParam.value.name,
        outputParams: outputParams.value
      }
      emit('submit', submitArtifactParam)
      resetForm()
    }
  })
}

function resetForm() {
  artifactParam.value ={}
  artifactParamForm.value.reset()
  outputParam.value = {}
  outputParams.value = []
  outputParamForm.value?.reset()
}

</script>