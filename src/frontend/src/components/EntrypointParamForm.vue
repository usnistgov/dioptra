<template>
  <q-card
    bordered
    class="q-px-lg q-mt-lg"
  >
    <q-card-section class="q-px-none">
      <label class="text-h6">Add Entrypoint Param</label>
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
          label="Add Entrypoint Param"
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
</template>

<script setup>
import { ref } from 'vue'

const emit = defineEmits(['submit'])

const paramForm = ref(null)

const parameter = ref({
  name: '',
  parameterType: '',
  defaultValue: '',
})

const typeOptions = [
  'string',
  'float',
  'integer',
  'boolean',
  'list',
  'mapping',
]

function addParam() {
  emit('submit', JSON.parse(JSON.stringify(parameter.value)))
  parameter.value.name = ''
  parameter.value.parameterType = ''
  parameter.value.defaultValue = ''
  paramForm.value.reset()
}

function requiredRule(val) {
  return (!!val) || "This field is required"
}

</script>