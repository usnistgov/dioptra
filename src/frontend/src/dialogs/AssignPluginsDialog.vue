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
        <div >
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
                @remove="selectedPlugins.splice(i, 1)"
              >
                {{ plugin.name }}
                <q-badge
                  v-if="!plugin.latestSnapshot" 
                  color="red" 
                  label="Outdated" 
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
                @click="syncPlugin(plugin.id, i)"
              >
                <q-tooltip>
                  Sync to latest version of plugin
                </q-tooltip>
              </q-btn>
          </div>
        </div>
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
    let pluginsToAdd = [...pluginsToUpdate.value]
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
      if(pluginsToAdd.length > 0) {
        await api.addPluginsToEntrypoint(props.editObj.id, pluginsToAdd) 
      }
      for(const plugin of pluginsToRemove) {
        await api.removePluginFromEntrypoint(props.editObj.id, plugin)
      }
      notify.success(`Successfully updated plugins for  '${props.editObj.name}'`)
      showDialog.value = false
      emit('refreshTable')
    } catch (err) {
      notify.error("Error in processing plugins: " + err.message);
    }
  }

  async function getPlugins(val = '', update) {
    update(async () => {
      try {
        const res = await api.getData('plugins', {
          search: val,
          rowsPerPage: 0, // get all
          index: 0
        })
        console.log('res = ', res)
        pluginOptions.value = res.data.data.filter((plugin) => !selectedPluginIds.value.includes(plugin.id))
      } catch(err) {
        notify.error(err.response.data.message)
      } 
    })
  }

  const pluginsToUpdate = ref([])

  async function syncPlugin(pluginID, index) {
    try {
      const res = await api.getItem('plugins', pluginID)
      selectedPlugins.value.splice(index, 1, res.data)
      pluginsToUpdate.value.push(pluginID)
    } catch(err) {
      console.warn(err)
    }
  }

</script>