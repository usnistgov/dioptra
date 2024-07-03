<template>
  <DialogComponent 
    v-model="showDialog"
    @emitSubmit="$emit('updateParam', parameter)"
    :hideDraftBtn="true"
  >
    <template #title>
      <label id="modalTitle">
        Edit Parameter
      </label>
    </template>
    <q-input 
      outlined 
      dense 
      v-model.trim="parameter.name"
      :rules="[requiredRule]"
      class="q-mb-sm"
      aria-required="true"
    >
      <template v-slot:before>
        <label :class="`field-label`">Name:</label>
      </template>
    </q-input>
    <q-select
      outlined 
      v-model="parameter.parameterType" 
      :options="typeOptions" 
      dense
      :rules="[requiredRule]"
      aria-required="true"
      class="q-mb-sm"
    >
    <template v-slot:before>
      <label :class="`field-label`">Type:</label>
    </template>
    </q-select>
    <q-input 
      outlined 
      dense 
      v-model.trim="parameter.defaultValue"
      class="q-mb-sm"
      aria-required="false"
      hint="Optional"
    >
      <template v-slot:before>
        <label :class="`field-label`">Default Value:</label>
      </template>
    </q-input>
  </DialogComponent>
</template>

<script setup>
  import DialogComponent from './DialogComponent.vue'
  import { reactive, watch } from 'vue'

  defineEmits(['updateParam'])

  const requiredRule = (val) => (val && val.length > 0) || "This field is required"

  const showDialog = defineModel()
  const props = defineProps(['editParam'])

  let parameter = reactive({
    name: '',
    parameterType: '',
    defaultValue: '',
  })

  const typeOptions = reactive([
    'string',
    'float',
    'path',
    'url',
  ])

  watch(showDialog, (newVal) => {
    if(newVal) {
      parameter.name = props.editParam.name
      parameter.parameterType = props.editParam.parameterType
      parameter.defaultValue = props.editParam.defaultValue

    }
    else {
      parameter.name = ''
      parameter.parameterType = ''
      parameter.defaultValue = ''
    }
  })



</script>