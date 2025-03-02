<template>
  <DialogComponent 
    v-model="showDialog"
    @emitSubmit="emitAddOrEdit"
    :hideDraftBtn="true"
  >
    <template #title>
      <label id="modalTitle">
        {{ editPlugin ? 'Edit Plugin' : 'Register Plugin'}}
      </label>
    </template>
    <q-input
      outlined 
      dense 
      v-model="plugin.name" 
      autofocus 
      :rules="[requiredRule, pythonModuleNameRule]" 
      class="q-mb-xs"
      id="pluginName"
    >
      <template #before>
        <label for="pluginName" class="field-label">Name:</label>
      </template>
    </q-input>
    <q-select
      v-if="!editPlugin"
      outlined 
      v-model="plugin.group" 
      :options="store.groups"
      option-label="name"
      option-value="id"
      emit-value
      map-options
      dense
      :rules="[requiredRule]"
      id="pluginGroup"
    >
      <template #before>
        <label for="pluginGroup" class="field-label">Group:</label>
      </template>
    </q-select>
    <q-input
      v-model="plugin.description"
      outlined
      type="textarea"
      dense
      id="pluginDescription"
    >
      <template #before>
        <label for="pluginDescription" class="field-label">Description:</label>
      </template>
    </q-input>
  </DialogComponent>
</template>

<script setup>
  import DialogComponent from './DialogComponent.vue'
  import { ref, watch } from 'vue'
  import { useLoginStore } from '@/stores/LoginStore.ts'

  const store = useLoginStore()

  const props = defineProps(['editPlugin'])

  const showDialog = defineModel()

  const plugin = ref({
    name: '',
    group: '',
    description: '',
  })

  function requiredRule(val) {
    return (!!val) || "This field is required"
  }

  function pythonModuleNameRule(val) {
    if (/\s/.test(val)) {
      return "A Python module name cannot contain spaces."
    }
    if (!/^[A-Za-z_]/.test(val)) {
      return "A Python module name must start with a letter or underscore."
    }
    if (!/^[A-Za-z_][A-Za-z0-9_]*$/.test(val)) {
      return "A Python module name can only contain letters, numbers, and underscores."
    }
    if (val === "_") {
      return "A Python module name cannot be '_' with no other characters."
    }
    return true
  }


  const emit = defineEmits(['addPlugin', 'updatePlugin'])

  function emitAddOrEdit() {
    if(props.editPlugin) {
      emit('updatePlugin', plugin.value, props.editPlugin.id)
    } else {
      emit('addPlugin', plugin.value)
    }
    showDialog.value = false
  }

  watch(showDialog, (newVal) => {
    if(newVal) {
      plugin.value.name = props.editPlugin.name
      plugin.value.description = props.editPlugin.description
    }
    else {
      plugin.value.name = ''
      plugin.value.group = ''
      plugin.value.description = ''
    }
    if (!plugin.value.group) {
      plugin.value.group = store.loggedInGroup.id
    }
  })

</script>