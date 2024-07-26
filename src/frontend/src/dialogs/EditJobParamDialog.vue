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
      disable
      aria-disabled="true"
    >
      <template v-slot:before>
        <label :class="`field-label`">Param Name:</label>
      </template>
    </q-input>
    <q-input 
      outlined 
      dense 
      v-model.trim="parameter.value"
      class="q-mb-sm"
      aria-required="false"
      :rules="[requiredRule]"
    >
      <template v-slot:before>
        <label :class="`field-label`">Param Value:</label>
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
    value: '',
  })

  watch(showDialog, (newVal) => {
    if(newVal) {
      parameter.name = props.editParam.name
      parameter.value = props.editParam.value

    }
    else {
      parameter.name = ''
      parameter.value = ''
    }
  })



</script>