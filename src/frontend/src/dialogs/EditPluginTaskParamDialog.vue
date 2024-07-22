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
    <div class="row items-center">
      <label class="col-3 q-mb-lg" id="paramName">
        Param Name:
      </label>
      <q-input
        v-model.trim="name"
        :rules="[requiredRule]"
        dense
        outlined
        class="col q-mr-sm"
        aria-labelledby="paramName"
        aria-required="true"
      />
    </div>
    <div class="row items-center q-mb-xs">
      <label class="col-3 q-mb-lg" id="paramType">
        Param Type:
      </label>
        <q-select 
          v-model="parameterType"
          emit-value
          option-value="id"
          option-label="name"
          map-options
          label="Param Type"
          :options="pluginParameterTypes"
          class="col q-mr-sm"
          outlined
          dense
          :rules="[requiredRule]"
          aria-labelledby="paramType"
          aria-required="true"
        />
    </div>
    <div v-if="paramType === 'inputParams'" class="row items-center">
      <label class="col-3" id="paramType">
        Required:
      </label>
      <q-checkbox
        v-model="required"
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