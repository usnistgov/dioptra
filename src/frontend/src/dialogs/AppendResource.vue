<template>
  <DialogComponent 
    v-model="showDialog"
    @emitSubmit="submit"
    :hideDraftBtn="true"
  >
    <template #title>
      <label id="modalTitle">
        Assign {{ childResourceType }} for '{{ parentResourceObj.name }}'
      </label>
    </template>
    <q-select
      outlined
      dense
      v-model="childResourceObjs"
      use-input
      use-chips
      multiple
      option-label="name"
      option-value="id"
      input-debounce="100"
      :options="childResourceOptions"
      @filter="getChildResources"
    >
      <template v-slot:before>
        <div class="field-label text-capitalize">{{ childResourceType }}:</div>
      </template>
      <template v-slot:selected>
        <div>
          <div
            v-for="(resource, i) in childResourceObjs"
            :key="resource.id"
            :class="i > 0 ? 'q-mt-xs' : ''"
            >
              <q-chip
                removable
                color="secondary"
                text-color="white"
                class="q-ml-xs "
                @remove="childResourceObjs.splice(i, 1)"
              >
                {{ resource.name }}
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


  const props = defineProps(['parentResourceType', 'parentResourceObj', 'childResourceType' ])
  const emit = defineEmits(['submit'])

  const showDialog = defineModel()

  const childResourceObjs = ref([])
  const selectedChildIds = computed(() => {
    return childResourceObjs.value.map((obj) => obj.id)
  })

  const childResourceOptions = ref([])
  const originalChildIds = ref()

  watch(showDialog, (newVal) => {
    if(newVal) {
      console.log('props = ', props.parentResourceObj)
      childResourceObjs.value = JSON.parse(JSON.stringify(props.parentResourceObj[props.childResourceType]))
      originalChildIds.value = JSON.parse(JSON.stringify(props.parentResourceObj[props.childResourceType].map((obj) => obj.id)))
    }
  })

  async function submit() {
    let childIdsToAdd = []
    let childIdsToRemove = []

    selectedChildIds.value.forEach((id) => {
      if (!originalChildIds.value.includes(id)) {
        childIdsToAdd.push(id)
      }
    })

    originalChildIds.value.forEach((id) => {
      if (!selectedChildIds.value.includes(id)) {
        childIdsToRemove.push(id)
      }
    })

    try {
      if(childIdsToAdd.length > 0) {
        await api.appendResource(props.parentResourceType, props.parentResourceObj.id, props.childResourceType, childIdsToAdd)
      }
      for(const id of childIdsToRemove) {
        await api.removeResourceFromResource(props.parentResourceType, props.parentResourceObj.id, props.childResourceType, id)
      }
      notify.success(`Successfully updated ${props.childResourceType} for  '${props.parentResourceObj.name}'`)
      showDialog.value = false
      emit('submit')
    } catch (err) {
      notify.error(err.message)
    }
  }

  async function getChildResources(val = '', update) {
    update(async () => {
      try {
        const res = await api.getData(props.childResourceType, {
          search: val,
          rowsPerPage: 0, // get all
          index: 0
        })
        childResourceOptions.value = res.data.data.filter((ep) => !selectedChildIds.value.includes(ep.id))
      } catch(err) {
        notify.error(err.response.data.message)
      } 
    })
  }

</script>