<template>
  <DialogComponent 
    v-model="showDialog"
    @emitSubmit="emitAddOrEdit"
    :hideDraftBtn="true"
  >
    <template #title>
      <label id="modalTitle">
        {{ props.editParam ? `Edit Param '${editParam.name}'` : 'Create Param' }}
      </label>
    </template>
    <q-input
      v-model.trim="name"
      :rules="[requiredRule]"
      dense
      outlined
      id="name"
      class="q-mb-xs"
    >
      <template #before>
        <label for="name" class="field-label">Name:</label>
      </template>
    </q-input>
    <q-select 
      v-model="parameterType"
      emit-value
      option-value="id"
      option-label="name"
      map-options
      :options="pluginParameterTypes"
      outlined
      dense
      :rules="[requiredRule]"
      id="type"
    >
      <template #before>
        <label for="type" class="field-label">Type:</label>
      </template>
    </q-select>
    <div v-if="paramType === 'inputParams'" class="row items-center">
      <label class="col-3" for="required">
        Required:
      </label>
      <q-checkbox
        v-model="required"
        id="required"
      />
    </div>
  </DialogComponent>
</template>

<script setup>
  import { ref, watch } from 'vue'
  import DialogComponent from './DialogComponent.vue'

  const props = defineProps(['editParam', 'pluginParameterTypes', 'paramType'])
  const emit = defineEmits(['addParam', 'updateParam'])

  function requiredRule(val) {
    return (!!val) || "This field is required"
  }

  const showDialog = defineModel()

  const name = ref('')
  const parameterType = ref('')
  const required = ref(true)

  watch(showDialog, (newVal) => {
    if(newVal) {
      name.value = props.editParam.name
      parameterType.value = props.editParam.parameterType
      required.value = props.editParam && Object.hasOwn(props.editParam, 'required') ? props.editParam.required : true
    }
    else {
      name.value = ''
      parameterType.value = ''
    }
  })

  function emitAddOrEdit() {
    let param = {name: name.value, parameterType: parameterType.value}
    if(props.paramType === 'inputParams') {
      param.required = required.value
    }
    if(props.editParam) {
      emit('updateParam', param)
    } else {
      emit('addParam', param)
    }
    showDialog.value = false
  }


</script>