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
    <div class="row items-center">
      <label class="col-3 q-mb-lg" id="tagName">
        Tag Name:
      </label>
      <q-input 
        class="col q-mb-xs" 
        outlined 
        dense 
        v-model.trim="name"  
        autofocus 
        :rules="[requiredRule]" 
        aria-labelledby="tagName"
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
  })

  function emitAddOrEdit() {
    if(props.editTag) {
      emit('updateTag', name.value, props.editTag.id)
    } else {
      emit('addTag', name.value, group.value)
    }
  }

</script>