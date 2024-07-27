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
    <div class="row items-center">
      <label class="col-3 q-mb-lg" id="modelName">
        Model Name:
      </label>
      <q-input 
        class="col q-mb-xs" 
        outlined 
        dense 
        v-model.trim="name"  
        autofocus 
        :rules="[requiredRule]" 
        aria-labelledby="modelName"
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