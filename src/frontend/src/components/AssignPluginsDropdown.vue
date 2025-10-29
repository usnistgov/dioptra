<template>
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
    @add="(added) => addPlugin(added.value)"
    @remove="(removed) => removePlugin(removed.value)"
  >
    <template v-slot:before>
      <div class="field-label">Plugins:</div>
    </template>
    <template v-slot:selected>
      <div>
        <div
          v-for="(plugin, i) in selectedPlugins"
          :key="plugin.id"
          :class="i > 0 ? 'q-mt-xs' : ''"
          >
            <q-chip
              removable
              color="secondary"
              text-color="white"
              class="q-ml-xs "
              @remove="selectedPlugins.splice(i, 1); removePlugin(plugin)"
            >
              {{ plugin.name }}
              <q-badge
                v-if="!plugin.latestSnapshot" 
                color="red" 
                label="outdated" 
                rounded
                class="q-ml-xs"
              />
            </q-chip>
            <q-btn
              v-if="!plugin.latestSnapshot"
              round 
              color="red" 
              icon="sync"
              size="sm"
              @click.stop="syncPlugin(plugin.id, i)"
            >
              <q-tooltip>
                Sync to latest version of plugin
              </q-tooltip>
            </q-btn>
        </div>
      </div>
    </template>
  </q-select>
</template>

<script setup>
import { ref, watch } from 'vue'
import * as api from '@/services/dataApi'

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