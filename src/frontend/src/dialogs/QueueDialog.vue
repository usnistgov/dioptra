<template>
  <DialogComponent 
    v-model:showDialog="showDialog"
    v-model:history="history"
    @emitSubmit="emitAddOrEdit"
    @emitSaveDraft="saveDraft"
    :hideDraftBtn="editQueue ? true : false"
    :showHistoryToggle="editQueue && !Object.hasOwn(editQueue, 'payload')"
    :disableConfirm="history"
  >
    <template #title>
      <label id="modalTitle">
        {{editQueue ? 'Edit Queue' : 'Register Queue'}}
      </label>
    </template>
    <div class="row">
      <!-- this is the form col -->
      <div
        :class="`${isExtraSmall ? 'col-12 q-mb-md' : 'col'}`"
        :style="{ 
          pointerEvents: history ? 'none' : 'auto', 
          opacity: history ? .65 : 1, 
          cursor: history ? 'not-allowed' : 'default' 
        }"
        ref="formCol"
      >
        <q-input 
          class="q-mb-xs" 
          outlined 
          dense 
          v-model.trim="name"  
          autofocus 
          :rules="[requiredRule]" 
          id="queueName"
        >
          <template #before>
            <label for="queueName" class="field-label">Name:</label>
          </template>
        </q-input>
        <q-select
          class="q-mb-xs"
          outlined 
          v-model="group" 
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
          v-model.trim="description"
          outlined
          type="textarea"
          id="description"
          dense
        >
          <template #before>
            <label for="description" class="field-label">Description:</label>
          </template>
        </q-input>
      </div>
      <!-- this is the history col -->
      <SnapshotList 
        v-show="history"
        :showDialogHistory="history"
        type="queues"
        :id="props.editQueue.id"
        :maxHeight="formCol?.clientHeight"
        :class="`${isExtraSmall ? 'col-12' : 'col-sm-auto q-ml-md'}`"
      />
    </div>
  </DialogComponent>
</template>

<script setup>
  import { ref, watch, inject } from 'vue'
  import DialogComponent from './DialogComponent.vue'
  import { useLoginStore } from '@/stores/LoginStore.ts'
  import SnapshotList from '../components/SnapshotList.vue'

  const store = useLoginStore()

  const isExtraSmall = inject('isExtraSmall')

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
      history.value = false
    }
    if (!group.value) {
      group.value = store.loggedInGroup.id
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

  const history = ref(false)

  watch(() => store.selectedSnapshot, (newVal) => {
    if(newVal) {
      name.value = newVal.name
      group.value = newVal.group
      description.value = newVal.description
    } else {
      name.value = props.editQueue.name
      group.value = props.editQueue.group
      description.value = props.editQueue.description
    }
  })

  const formCol = ref()

</script>