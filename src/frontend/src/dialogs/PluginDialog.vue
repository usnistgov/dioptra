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
    <div class="row items-center q-mb-xs">
      <label class="col-3 q-mb-lg" id="pluginName">
        Name:
      </label>
      <q-input 
        class="col" 
        outlined 
        dense 
        v-model="plugin.name" 
        autofocus 
        :rules="[requiredRule, pythonModuleNameRule]" 
        aria-labelledby="pluginName"
        aria-required="true"
      />
    </div>
    <div class="row items-center q-mb-xs" v-if="!editPlugin">
      <label class="col-3 q-mb-lg" id="pluginGroup">
        Group:
      </label>
      <q-select
        class="col"
        outlined 
        v-model="plugin.group" 
        :options="store.groups"
        option-label="name"
        option-value="id"
        emit-value
        map-options
        dense
        :rules="[requiredRule]"
        aria-labelledby="pluginGroup"
        aria-required="true"
      />
    </div>
    <div class="row items-center">
      <label class="col-3 q-mb-lg" id="pluginGroup">
        Description:
      </label>
      <q-input
      	class="col"
        v-model="plugin.description"
        outlined
        type="textarea"
      />
    </div>
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