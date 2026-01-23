<template>
  <DialogComponent 
    v-model="showDialog"
    @emitSubmit="emitSubmit()"
    :hideDraftBtn="true"
  >
    <template #title>
      <label id="modalTitle">
        {{ props.editParam ? 'Edit' : 'Create' }} Parameter
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
    <div v-if="parameter.defaultValue === null">
      Default Value:
      <q-chip
        label="Null"
        color="negative"
        text-color="white"
        class="q-ml-md"
      />
    </div>
    <q-input
      v-else
      outlined 
      dense 
      v-model.trim="parameter.defaultValue"
      class="q-mb-sm"
      aria-required="false"
      hint="Optional"
      :disable="parameter.defaultValue === null"
    >
      <template v-slot:before>
        <label
          class="field-label"
          :class="{ 'text-grey-6': parameter.defaultValue === null }"
        >
          Default Value:
        </label>
      </template>
    </q-input>
    <div class="q-mt-md">
      Null Value:
      <q-checkbox
        class="q-ml-lg"
        :model-value="parameter.defaultValue === null"
        @update:model-value="(val) => {
          parameter.defaultValue = val ? null : ''
        }"
      />
    </div>
  </DialogComponent>
</template>

<script setup>
  import DialogComponent from './DialogComponent.vue'
  import { ref, watch } from 'vue'

  const emit = defineEmits(['updateParam', 'createParam'])

  const requiredRule = (val) => (val && val.length > 0) || "This field is required"

  const showDialog = defineModel()
  const props = defineProps(['editParam'])

  let parameter = ref({
    name: '',
    parameterType: '',
    defaultValue: '',
  })

  const typeOptions = ref([
    'string',
    'float',
    'integer',
    'boolean',
    'list',
    'mapping',
  ])

  watch(showDialog, (newVal) => {
    if(newVal && props.editParam) {
      // edit param
      parameter.value.name = props.editParam.name
      parameter.value.parameterType = props.editParam.parameterType
      parameter.value.defaultValue = props.editParam.defaultValue
    } else {
      // close dialog
      parameter.value.name = ''
      parameter.value.parameterType = ''
      parameter.value.defaultValue = ''
    }
  })

  function emitSubmit() {
    if(props.editParam) {
      emit('updateParam', parameter.value)
    } else {
      emit('createParam', parameter.value)
    }
  }

</script>
