<template>
  <q-card bordered class="q-mt-lg">
    <q-card-section>
      <div class="text-h6">Add Artifact Param</div>
    </q-card-section>
    <q-form ref="artifactParamForm" greedy @submit.prevent="addArtifactParam" class="q-mx-lg">
      <q-input 
        outlined 
        dense 
        v-model.trim="artifactParam.name"
        :rules="[requiredRule]"
        class="q-mt-sm"
      >
        <template v-slot:before>
          <label :class="`field-label`">Param Name:</label>
        </template>
      </q-input>

      <label>
        Output Params:
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
            option-label="name"
            map-options
            label="Param Type"
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
            <span class="sr-only">Add Output Param</span>
            <q-tooltip>
              Add Output Param
            </q-tooltip>
          </q-btn>
        </div>
      </q-form>

      <q-card-actions align="right">
        <q-btn
          label="Add Artifact Param"
          color="secondary"
          icon="add"
          type="submit"
        />
      </q-card-actions>
    </q-form>
  </q-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import * as api from '@/services/dataApi'
import * as notify from '../notify'

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

onMounted(() => {
  getPluginParameterTypes()
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
    else {
      // error
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
    else {
      // error
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