<template>
  <DialogComponent 
    v-model="showDialog"
    @emitSubmit="submit"
    :hideDraftBtn="true"
  >
    <template #title>
      <label id="modalTitle">
        Assign <span class="text-capitalize">{{ childResourceType }}</span> for '{{ parentResourceObj.name }}'
      </label>
    </template>
    <ResourcePicker
      v-model="childResourceObjs"
      :options="childResourceOptions"
      :resourceType="childResourceTypeSingular"
      :label="childLabel"
      @filter="getChildResources"
    />
  </DialogComponent>
</template>

<script setup>
  import { ref, watch, computed } from 'vue'
  import DialogComponent from './DialogComponent.vue'
  import * as api from '@/services/dataApi'
  import * as notify from '../notify'
  import ResourcePicker from '@/components/ResourcePicker.vue'


  const props = defineProps(['parentResourceType', 'parentResourceObj', 'childResourceType' ])
  const emit = defineEmits(['submit'])

  const showDialog = defineModel()

  const childResourceObjs = ref([])
  const selectedChildIds = computed(() => {
    return childResourceObjs.value.map((obj) => obj.id)
  })

  const childResourceOptions = ref([])
  const originalChildIds = ref()

  const childResourceTypeSingular = computed(() => {
    const t = props.childResourceType || ''
    return t.endsWith('s') ? t.slice(0, -1) : t
  })

  const childLabel = computed(() => {
    const t = props.childResourceType || ''
    return `${t.charAt(0).toUpperCase()}${t.slice(1)}:`
  })

  watch(showDialog, (newVal) => {
    if(newVal) {
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
        childResourceOptions.value = res.data.data
      } catch(err) {
        notify.error(err.response.data.message)
      } 
    })
  }

</script>
