<template>
  <DialogComponent 
    v-model="showDialog"
    @emitSubmit="emitAddOrEdit"
  >
    <template #title>
      <label id="modalTitle">
        {{editQueue ? 'Edit Queue' : 'Register Queue'}}
      </label>
    </template>
    <div class="row items-center">
      <label class="col-3 q-mb-lg" id="queueName">
        Queue Name:
      </label>
      <q-input 
        class="col q-mb-xs" 
        outlined 
        dense 
        v-model="name" 
        autofocus 
        :rules="[rules.requiredRule]" 
        aria-labelledby="queueName"
        aria-required="true"
      />
    </div>
    <!-- <div class="row items-center">
      <label class="col-3" id="locked">
        Locked:
      </label>
      <q-toggle v-model="locked" class="q-mr-sm" aria-labelledby="locked" />
      <q-icon :name="locked ? 'lock' : 'lock_open'" size="sm" />
    </div> -->
    <div class="row items-center">
      <label class="col-3" id="locked">
        Description:
      </label>
      <q-input
        class="col"
        v-model="description"
        outlined
        type="textarea"
      />
    </div>
  </DialogComponent>
</template>

<script setup>
  import { ref, watch } from 'vue'
  import * as rules from '@/services/validationRules'
  import DialogComponent from './DialogComponent.vue'

  const props = defineProps(['editQueue'])
  const emit = defineEmits(['addQueue', 'updateQueue'])

  const showDialog = defineModel()

  const name = ref('')
  const locked = ref(true)
  const description = ref('')

  watch(showDialog, (newVal) => {
    if(newVal) {
      name.value = props.editQueue.name
      description.value = props.editQueue.description
    }
    else {
      name.value = ''
      locked.value = true
      description.value = ''
    }
  })

  function emitAddOrEdit() {
    if(props.editQueue) {
      emit('updateQueue', name.value, props.editQueue.id, description.value)
    } else {
      emit('addQueue', name.value, description.value)
    }
  }


</script>