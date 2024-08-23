<template>
  <DialogComponent 
    v-model="showDialog"
    @emitSubmit="emitAdd"
    :hideDraftBtn="true"
  >
    <template #title>
      <label id="modalTitle">
        Register Plugin
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
    <div class="row items-center q-mb-xs">
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

  const showDialog = defineModel()

  const plugin = ref({
    name: '',
    group: '',
    description: '',
    tags: [],
    files: []
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


  const emit = defineEmits(['addPlugin'])

  function emitAdd() {
    const copy = JSON.parse(JSON.stringify(plugin.value))
    emit('addPlugin', copy)
    showDialog.value = false
  }

  watch(showDialog, (newVal) => {
    if(!newVal) {
      plugin.value.name = ''
      plugin.value.group = ''
      plugin.value.description = ''
    }
  })

</script>