<template>
  <DialogComponent 
    v-model="showDialog"
    @emitSubmit="emitAddOrEdit"
    :hideDraftBtn="true"
  >
    <template #title>
      <label id="modalTitle">
        {{editModel ? 'Edit Model' : 'Register Model'}}
      </label>
    </template>
    <q-input 
      class="col q-mb-xs" 
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
    <q-input
      class="col"
      v-model.trim="description"
      outlined
      type="textarea"
      dense
      id="description"
    >
      <template #before>
        <label for="description" class="field-label">Description:</label>
      </template>
    </q-input>
  </DialogComponent>
</template>

<script setup>
  import { ref, watch } from 'vue'
  import DialogComponent from './DialogComponent.vue'
  import { useLoginStore } from '@/stores/LoginStore.ts'

  const store = useLoginStore()

  const props = defineProps(['editModel'])
  const emit = defineEmits(['addModel', 'updateModel'])

  function requiredRule(val) {
    return (!!val) || "This field is required"
  }

  const showDialog = defineModel()

  const name = ref('')
  const group = ref('')
  const description = ref('')

  watch(showDialog, (newVal) => {
    if(newVal) {
      name.value = props.editModel.name
      description.value = props.editModel.description
      group.value = props.editModel.group
    }
    else {
      name.value = ''
      description.value = ''
    }
    if (!group.value) {
      group.value = store.loggedInGroup.id
    }
  })

  function emitAddOrEdit() {
    if(props.editModel) {
      emit(
        'updateModel', 
        name.value, 
        props.editModel.id, 
        description.value
      )
    } else {
      emit('addModel', name.value, group.value, description.value)
    }
  }


</script>