<template>
  <DialogComponent 
    v-model="showDialog"
    @emitSubmit="submitTags"
    :hideDraftBtn="true"
  >
    <template #title>
      <label id="modalTitle">
        Assign Tags for '{{ editObj.name || editObj.description }}'
      </label>
    </template>
    <q-chip 
      v-for="(tag, i) in tags"
      :key="i"
      :label="tag.name"
      clickable
      no-caps
      class="q-ma-sm"
      @click="toggleTag(tag.id)"
      :color="selectedTagIDs.includes(tag.id) ? 'primary' : 'grey-4'"
      :textColor="selectedTagIDs.includes(tag.id) ? 'white' : 'black'"
    />

    <q-input 
      v-model="newTag" 
      outlined 
      dense 
      label="Add new Tag option" 
      class="q-mt-lg" 
      style="width: 250px"
      @keydown.enter.prevent="addNewTag"
    >
      <template v-slot:before>
        <q-icon name="sell" />
      </template>
      <template v-slot:append>
        <q-btn round dense size="sm" icon="add" color="primary" @click="addNewTag()" />
      </template>
    </q-input>
  </DialogComponent>
</template>

<script setup>
  import { ref, watch } from 'vue'
  import DialogComponent from './DialogComponent.vue'
  import { useLoginStore } from '@/stores/LoginStore.ts'
  import * as api from '@/services/dataApi'
  import * as notify from '../notify'

  const store = useLoginStore()

  const props = defineProps(['editObj', 'type', ])
  const emit = defineEmits(['refreshTable'])

  const showDialog = defineModel()

  const tags = ref([])
  const selectedTagIDs = ref([])

  async function getTags() {
    try {
      const res = await api.getData('tags', {index: 0, rowsPerPage: 50, search: ''})
      tags.value = res.data.data
      if(props.editObj.tags.length > 0) {
        props.editObj.tags.forEach((tag) => {
          selectedTagIDs.value.push(tag.id)
        })
      }
    } catch(err) {
      notify.error(err.response.data.message)
    } 
  }

  watch(showDialog, (newVal) => {
    if(newVal) {
      getTags()
    }
    selectedTagIDs.value = []
    newTag.value = ''
  })

  function toggleTag(id) {
    if(!selectedTagIDs.value.includes(id)) {
      selectedTagIDs.value.push(id)
    } else {
      selectedTagIDs.value.forEach((selectedTagId, i) => {
        if(selectedTagId === id) {
          selectedTagIDs.value.splice(i, 1)
        }
      })
    }
  }

  const newTag = ref('')

  async function addNewTag() {
    if(!newTag.value.trim().length) return
    try {
      await api.addItem('tags', {
        name: newTag.value,
        group: store.loggedInGroup.id
      })
      notify.success(`Sucessfully created tag '${newTag.value}'`)
      newTag.value = ''
      getTags()
    } catch(err) {
      notify.error(err.response.data.message)
    }
  }

  async function submitTags() {
    showDialog.value = false
    try {
      if(props.type ===  'files') {
        await api.updateTags(props.type, props.editObj.plugin.id, selectedTagIDs.value, props.editObj.id)
      } else {
        await api.updateTags(props.type, props.editObj.id, selectedTagIDs.value)
      }
      notify.success(`Sucessfully updated Tags for '${props.editObj.name || props.editObj.description}'`)
      emit('refreshTable')
    } catch(err) {
      notify.error(err.response.data.message);
    }
  }

</script>