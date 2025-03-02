<template>
  <DialogComponent 
    v-model="showDialog"
    @emitSubmit="emitAddOrEdit"
    :hideDraftBtn="true"
  >
    <template #title>
      <label id="modalTitle">
        {{editTag ? 'Edit Tag' : 'Register Tag'}}
      </label>
    </template>
    <q-input 
      class="q-mb-xs" 
      outlined 
      dense 
      v-model.trim="name"  
      autofocus 
      :rules="[requiredRule]"
      id="name"
    >
      <template #before>
        <label for="name" class="field-label">Name:</label>
      </template>
    </q-input>
    <q-select
      outlined 
      v-model="group" 
      :options="store.groups"
      option-label="name"
      option-value="id"
      emit-value
      map-options
      dense
      :rules="[requiredRule]"
      id="group"
    >
      <template #before>
        <label for="group" class="field-label">Group:</label>
      </template>
    </q-select>
  </DialogComponent>
</template>

<script setup>
  import { ref, watch } from 'vue'
  import DialogComponent from './DialogComponent.vue'
  import { useLoginStore } from '@/stores/LoginStore.ts'

  const store = useLoginStore()

  const props = defineProps(['editTag'])
  const emit = defineEmits(['addTag', 'updateTag'])

  function requiredRule(val) {
    return (!!val) || "This field is required"
  }

  const showDialog = defineModel()

  const name = ref('')
  const locked = ref(true)
  const group = ref('')

  watch(showDialog, (newVal) => {
    if(newVal) {
      name.value = props.editTag.name
      group.value = props.editTag.group
    }
    else {
      name.value = ''
      locked.value = true
    }
    if (!group.value) {
      group.value = store.loggedInGroup.id
    }
  })

  function emitAddOrEdit() {
    if(props.editTag) {
      emit('updateTag', name.value, props.editTag.id)
    } else {
      emit('addTag', name.value, group.value)
    }
  }

</script>