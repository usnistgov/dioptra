<template>
  <DialogComponent 
    v-model="showDialog"
    @emitSubmit="emitAddOrEdit"
    :hideDraftBtn="true"
  >
    <template #title>
      <label id="modalTitle">
        {{ queueToDraft.hasDraft ? 'Edit Draft' : `Create Draft for "${queueToDraft.name}"` }}
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
  import * as api from '@/services/dataApi'
  import * as notify from '../notify'

  const store = useLoginStore()

  const props = defineProps(['queueToDraft'])
  const emit = defineEmits(['addQueue', 'updateQueue', 'updateDraftLinkedToQueue'])

  function requiredRule(val) {
    return (!!val) || "This field is required"
  }

  const showDialog = defineModel()

  const name = ref('')
  const group = ref('')
  const description = ref('')

  const queue = ref({})

  watch(showDialog, async (newVal) => {
    if(newVal && props.queueToDraft.hasDraft) {
      await getDraft()
      name.value = queue.value.name
      description.value = queue.value.description
      group.value = queue.value.group
    }
    else {
      name.value = ''
      description.value = ''
    }
  })

  async function getDraft() {
    try {
      const res = await api.getItem('queues', props.queueToDraft.id, true)
      queue.value = res.data
    } catch(err) {
      console.log('err = ', err)
      notify.error(err.response.data.message)
    }
  }

  function emitAddOrEdit() {
    if(props.queueToDraft.hasDraft) {
      emit('updateDraftLinkedToQueue', props.queueToDraft.id, name.value, description.value)
    } else {
      emit('addQueue', name.value, description.value, props.queueToDraft.id)
    }
  }

</script>