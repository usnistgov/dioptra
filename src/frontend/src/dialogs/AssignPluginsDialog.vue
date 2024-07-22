<template>
  <DialogComponent 
    v-model="showDialog"
    @emitSubmit="submitPlugins"
    :hideDraftBtn="true"
  >
    <template #title>
      <label id="modalTitle">
        Assign Plugins for '{{ editObj.name || editObj.description }}'
      </label>
    </template>
    <q-select
      outlined
      dense
      v-model="selectedPlugins"
      use-input
      use-chips
      multiple
      option-label="name"
      option-value="id"
      input-debounce="100"
      :options="pluginOptions"
      @filter="getPlugins"
    >
      <template v-slot:before>
        <div class="field-label">Plugins:</div>
      </template>
      <template v-slot:selected>
        <q-chip
          v-for="(plugin, i) in selectedPlugins"
          :key="plugin.id"
          removable
          color="secondary"
          text-color="white"
          class="q-my-none q-ml-xs q-mr-none"
          @remove="selectedPlugins.splice(i, 1)"
        >
          {{ plugin.name }}
        </q-chip>
      </template>
    </q-select>
  </DialogComponent>
</template>

<script setup>
  import { ref, watch, computed } from 'vue'
  import DialogComponent from './DialogComponent.vue'
  import * as api from '@/services/dataApi'
  import * as notify from '../notify'


  const props = defineProps(['editObj' ])
  const emit = defineEmits(['refreshTable'])

  const showDialog = defineModel()

  const selectedPlugins = ref([])
  const selectedPluginIds = computed(() => {
    return selectedPlugins.value.map((plugin) => plugin.id)
  })

  const pluginOptions = ref([])
  const originalPlugins = ref()

  watch(showDialog, (newVal) => {
    if(newVal) {
      selectedPlugins.value = JSON.parse(JSON.stringify(props.editObj.plugins))
      originalPlugins.value = JSON.parse(JSON.stringify(props.editObj.plugins.map((obj) => obj.id)))
    }
  })

  async function submitPlugins() {
    let pluginsToAdd = []
    let pluginsToRemove = []

    selectedPluginIds.value.forEach((plugin) => {
      if (!originalPlugins.value.includes(plugin)) {
        pluginsToAdd.push(plugin)
      }
    })

    originalPlugins.value.forEach((plugin) => {
      if (!selectedPluginIds.value.includes(plugin)) {
        pluginsToRemove.push(plugin)
      }
    })

    try {
      // Wait for all add and remove operations to finish
      const addPromise = (pluginsToAdd.length > 0) ? addPlugins(pluginsToAdd) : Promise.resolve()
      const removePromises = pluginsToRemove.map(plugin => removePlugin(plugin))
      await Promise.all([addPromise, ...removePromises]);

      // Log after both operations are complete
      emit('refreshTable')
      notify.success(`Sucessfully updated plugins for  '${props.editObj.name}'`)
      showDialog.value = false
    } catch (err) {
      notify.error("Error in processing plugins: " + err.message);
    }
  }


  async function addPlugins(pluginsToAdd) {
    try {
      await api.addPluginsToEntrypoint(props.editObj.id, pluginsToAdd)
    } catch(err) {
      console.log('err =  ', err)
      notify.error(err.response.data.message);
    }
  }

  async function removePlugin(plugin) {
    try {
      await api.removePluginFromEntrypoint(props.editObj.id, plugin)
    } catch(err) {
      notify.error(err.response.data.message);
    }
  }


  async function getPlugins(val = '', update) {
    update(async () => {
      try {
        const res = await api.getData('plugins', {
          search: val,
          rowsPerPage: 100,
          index: 0
        })
        pluginOptions.value = res.data.data
      } catch(err) {
        notify.error(err.response.data.message)
      } 
    })
  }

</script>