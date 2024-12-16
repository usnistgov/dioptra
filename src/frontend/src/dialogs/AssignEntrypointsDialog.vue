<template>
  <DialogComponent 
    v-model="showDialog"
    @emitSubmit="submit"
    :hideDraftBtn="true"
  >
    <template #title>
      <label id="modalTitle">
        Assign Entrypoints for '{{ experiment.name }}'
      </label>
    </template>
    <q-select
      outlined
      dense
      v-model="selectedEntrypoints"
      use-input
      use-chips
      multiple
      option-label="name"
      option-value="id"
      input-debounce="100"
      :options="entrypointOptions"
      @filter="getEntrypoints"
    >
      <template v-slot:before>
        <div class="field-label">Entrypoints:</div>
      </template>
      <template v-slot:selected>
        <div>
          <div
            v-for="(entrypoint, i) in selectedEntrypoints"
            :key="entrypoint.id"
            :class="i > 0 ? 'q-mt-xs' : ''"
            >
              <q-chip
                removable
                color="secondary"
                text-color="white"
                class="q-ml-xs "
                @remove="selectedEntrypoints.splice(i, 1)"
              >
                {{ entrypoint.name }}
              </q-chip>
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


  const props = defineProps(['experiment' ])
  const emit = defineEmits(['getExperiment'])

  const showDialog = defineModel()

  const selectedEntrypoints = ref([])
  const selectedEntrypointIds = computed(() => {
    return selectedEntrypoints.value.map((ep) => ep.id)
  })

  const entrypointOptions = ref([])
  const originalEntrypoints = ref()

  watch(showDialog, (newVal) => {
    if(newVal) {
      selectedEntrypoints.value = JSON.parse(JSON.stringify(props.experiment.entrypoints))
      originalEntrypoints.value = JSON.parse(JSON.stringify(props.experiment.entrypoints.map((obj) => obj.id)))
    }
  })

  async function submit() {
    let entrypointsToAdd = [...entrypointsToUpdate.value]
    let entrypointsToRemove = []

    selectedEntrypointIds.value.forEach((ep) => {
      if (!originalEntrypoints.value.includes(ep)) {
        entrypointsToAdd.push(ep)
      }
    })

    originalEntrypoints.value.forEach((ep) => {
      if (!selectedEntrypointIds.value.includes(ep)) {
        entrypointsToRemove.push(ep)
      }
    })

    try {
      if(entrypointsToAdd.length > 0) {
        await api.addEntrypointsToExperiment(props.experiment.id, entrypointsToAdd) 
      }
      for(const entrypointId of entrypointsToRemove) {
        await api.removeEntrypointFromExperiment(props.experiment.id, entrypointId)
      }
      notify.success(`Successfully updated entrypoints for  '${props.experiment.name}'`)
      showDialog.value = false
      emit('getExperiment')
    } catch (err) {
      notify.error("Error in processing entrypoints: " + err.message);
    }
  }

  async function getEntrypoints(val = '', update) {
    update(async () => {
      try {
        const res = await api.getData('entrypoints', {
          search: val,
          rowsPerPage: 0, // get all
          index: 0
        })
        entrypointOptions.value = res.data.data.filter((ep) => !selectedEntrypointIds.value.includes(ep.id))
      } catch(err) {
        notify.error(err.response.data.message)
      } 
    })
  }

  const entrypointsToUpdate = ref([])

</script>