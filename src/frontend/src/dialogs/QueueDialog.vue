<template>
  <DialogComponent 
    v-model="showDialog"
    @emitSubmit="emitAddOrEdit"
    @emitSaveDraft="saveDraft"
    :hideDraftBtn="editQueue ? true : false"
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
        v-model.trim="name"  
        autofocus 
        :rules="[requiredRule]" 
        aria-labelledby="queueName"
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
        v-model="group" 
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
      <label class="col-3" id="description">
        Description:
      </label>
      <q-input
        class="col"
        v-model.trim="description"
        outlined
        type="textarea"
        aria-labelledby="description"
      />
    </div>
  </DialogComponent>
</template>

<script setup>
  import { ref, watch } from 'vue'
  import DialogComponent from './DialogComponent.vue'
  import { useLoginStore } from '@/stores/LoginStore.ts'

  const store = useLoginStore()

  const props = defineProps(['editQueue'])
  const emit = defineEmits(['addQueue', 'updateQueue', 'saveDraft'])

  function requiredRule(val) {
    return (!!val) || "This field is required"
  }

  const showDialog = defineModel()

  const name = ref('')
  const group = ref('')
  const description = ref('')

  watch(showDialog, (newVal) => {
    if(newVal) {
      name.value = props.editQueue.name
      description.value = props.editQueue.description
      group.value = props.editQueue.group
    }
    else {
      name.value = ''
      description.value = ''
    }
  })

  function emitAddOrEdit() {
    if(props.editQueue) {
      emit(
        'updateQueue', 
        name.value, 
        props.editQueue.id, 
        description.value, 
        Object.hasOwn(props.editQueue, 'payload') ? true : false
      )
    } else {
      emit('addQueue', name.value, description.value)
    }
  }

  function saveDraft() {
    emit('saveDraft', name.value, description.value, props.editQueue.id)
  }


</script>