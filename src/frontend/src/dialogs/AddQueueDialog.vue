<template>
  <DialogComponent 
    v-model="showDialog"
    @emitSubmit="$emit('submit', name)"
  >
    <template #title>Register Queue</template>
    <div class="row items-center">
      <div class="col-3 q-mb-lg">
        Queue Name:
      </div>
      <q-input 
        class="col" 
        outlined 
        dense 
        v-model="name" 
        autofocus 
        :rules="[rules.requiredRule]" 
      />
    </div>
    <div class="row items-center">
      <div class="col-3">
        Locked:
      </div>
      <q-toggle v-model="locked" class="q-mr-sm" />
      <q-icon :name="locked ? 'lock' : 'lock_open'" size="sm" />
    </div>
  </DialogComponent>
</template>

<script setup>
  import { ref, onUpdated } from 'vue'
  import * as rules from '@/services/validationRules'
  import DialogComponent from './DialogComponent.vue'

  defineEmits(['submit'])

  const showDialog = defineModel()

  const name = ref('')
  const locked = ref(true)

  onUpdated(() => {
    name.value = ''
    locked.value = true
  })


</script>