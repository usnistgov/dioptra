<template>
  <DialogComponent 
    v-model="showDialog"
    @emitSubmit="submitPlugins"
    :hideDraftBtn="true"
  >
    <template #title>
      <label id="modalTitle">
        Assign {{ pluginType === 'plugins' ? 'Plugins' : 'Artifact Plugins' }} for '{{ editObj.name }}'
      </label>
    </template>
    <AssignPluginsDropdown
      v-model:selectedPlugins="selectedPlugins"
      v-model:pluginIDsToUpdate="pluginIDsToUpdate"
      v-model:pluginIDsToRemove="pluginIDsToRemove"
    />
  </DialogComponent>
</template>

<script setup>
  import { ref, onUpdated } from 'vue'
  import DialogComponent from './DialogComponent.vue'
  import * as api from '@/services/dataApi'
  import * as notify from '../notify'
  import AssignPluginsDropdown from '@/components/AssignPluginsDropdown.vue'

  const props = defineProps(['editObj', 'pluginType'])
  const emit = defineEmits(['refreshTable'])

  const showDialog = defineModel()

  onUpdated(() => {
    pluginIDsToUpdate.value = []
    pluginIDsToRemove.value = []
    if(props.pluginType === 'plugins') {
      selectedPlugins.value = JSON.parse(JSON.stringify(props.editObj.plugins))
    } else {
      selectedPlugins.value = JSON.parse(JSON.stringify(props.editObj.artifactPlugins))
    }
  })

  const selectedPlugins = ref([])
  const pluginIDsToUpdate = ref([])
  const pluginIDsToRemove = ref([])

  async function submitPlugins() {
    try {
      if(pluginIDsToUpdate.value.length > 0) {
        await api.addPluginsToEntrypoint(props.editObj.id, pluginIDsToUpdate.value, props.pluginType)
      }
      for(const pluginId of pluginIDsToRemove.value) {
        await api.removePluginFromEntrypoint(props.editObj.id, pluginId, props.pluginType)
      }
      notify.success(`Successfully updated plugins for '${props.editObj.name}'`)
      emit('refreshTable')
      showDialog.value = false
    } catch (err) {
      notify.error(err.response.data.message);
    }
  }

</script>
