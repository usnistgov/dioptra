<template>
  <DialogComponent 
    v-model="showDialog"
    @emitSubmit="emitAdd"
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
        :rules="[requiredRule]" 
        aria-labelledby="pluginName"
        aria-required="true"
      />
    </div>
    <div class="row items-center">
      <label class="col-3 q-mb-lg" id="pluginGroup">
        Group:
      </label>
      <q-select
      class="col"
        outlined 
        v-model="plugin.group" 
        :options="store.groups.map((group) => group.name)" 
        dense
        :rules="[requiredRule]"
        aria-labelledby="pluginGroup"
        aria-required="true"
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
    tags: [],
    files: []
  })

  function requiredRule(val) {
    return (val && val.length > 0) || "This field is required"
  }

  const emit = defineEmits(['addPlugin'])

  function emitAdd() {
    const copy = JSON.parse(JSON.stringify(plugin.value))
    copy.id = String(Math.floor(Math.random()*90000) + 10000)
    emit('addPlugin', copy)
    showDialog.value = false
  }

  watch(showDialog, (newVal) => {
    if(!newVal) {
      plugin.value.name = ''
      plugin.value.group = ''
    }
  })

</script>