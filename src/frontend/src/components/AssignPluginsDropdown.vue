<template>
  <ResourcePicker
    v-model="selectedPlugins"
    :options="pluginOptions"
    resourceType="plugin"
    label="Plugins:"
    @filter="getPlugins"
    @add="(added) => addPlugin(added.value)"
    @remove="(removed) => removePlugin(removed.value)"
    :stacked-badges="true"
    @sync="(plugin, index) => syncPlugin(plugin.id, index)"
  />
</template>

<script setup>
import { ref, watch } from 'vue'
import * as api from '@/services/dataApi'
import ResourcePicker from '@/components/ResourcePicker.vue'

const selectedPlugins = defineModel('selectedPlugins')
const originalSelectedPluginIds = ref([])

watch(selectedPlugins, (newVal) => {
  originalSelectedPluginIds.value = newVal.map(p => p.id)
  },
  { once: true }
)

const pluginIDsToUpdate = defineModel('pluginIDsToUpdate')
const pluginIDsToRemove = defineModel('pluginIDsToRemove')

const pluginOptions = ref([])

async function getPlugins(val = '', update) {
  update(async () => {
    try {
      const res = await api.getData('plugins', {
        search: val,
        rowsPerPage: 0, // get all
        index: 0
      })
      pluginOptions.value = res.data.data
    } catch(err) {
      notify.error(err.response.data.message)
    } 
  })
}

async function syncPlugin(pluginId, index) {
  try {
    const res = await api.getItem('plugins', pluginId)
    selectedPlugins.value.splice(index, 1, res.data)
    pluginIDsToUpdate.value.push(pluginId)
  } catch(err) {
    console.warn(err)
  }
}

function addPlugin(plugin) {
  pluginIDsToUpdate.value.push(plugin.id)
  pluginIDsToRemove.value = pluginIDsToRemove.value.filter((id) => id !== plugin.id)
}

function removePlugin(plugin) {
  if(originalSelectedPluginIds.value.includes(plugin.id)) {
    pluginIDsToRemove.value.push(plugin.id)
  }
  pluginIDsToUpdate.value = pluginIDsToUpdate.value.filter((id) => id !== plugin.id)
}

</script>
