<template>
  <TableComponent
    :rows="snapshots"
    :columns="columns"
    v-model:selected="selected"
    :title="props.maxHeight ? '' : 'Snapshots'"
    :hideCreateBtn="true"
    :hideSearch="true"
    rowKey="snapshot"
    :showAll="true"
    :style="{ 
      marginTop: '0', 
      maxHeight: props.maxHeight ? props.maxHeight + 'px' : '',
      height: props.maxHeight ? '' : 'calc(100vh - 50px)'
    }"
    :hideOpenBtn="true"
    :hideDeleteBtn="true"
    :disableUnselect="true"
  >
    <template #body-cell-timestamp="props">
      {{
        new Intl.DateTimeFormat('en-US', { 
          year: '2-digit', 
          month: '2-digit', 
          day: '2-digit', 
          hour: 'numeric', 
          minute: 'numeric', 
          hour12: true 
        }).format(new Date(props.row.snapshotCreatedOn))
      }}
      <q-chip
        v-if="props.row.latestSnapshot"
        label="latest"
        size="md"
        dense
        color="orange"
        text-color="white"
      />
    </template>
  </TableComponent>
</template>

<script setup>
import { useLoginStore } from '@/stores/LoginStore'
import { useRoute } from 'vue-router'
import TableComponent from '@/components/TableComponent.vue'
import { ref, watch } from 'vue'
import * as api from '@/services/dataApi'

const props = defineProps(['showDialogHistory', 'type', 'id', 'maxHeight'])

const store = useLoginStore()
const route = useRoute()

const snapshots = ref([])
const selected = ref([])

async function getSnapshots() {
  try {
    const res = await api.getSnapshots(route.meta.type, route.params.id)
    snapshots.value = res.data.data.reverse()
    console.log('snapshots = ', snapshots.value)
  } catch(err) {
    console.warn(err)
  }
}

async function getDialogSnapshots() {
  try {
    const res = await api.getSnapshots(props.type, props.id)
    snapshots.value = res.data.data.reverse()
    console.log('snapshots = ', snapshots.value)
  } catch(err) {
    console.warn(err)
  }
}

watch(() => store.showRightDrawer, (history) => {
  if(history) {
    getSnapshots()
  } else {
    store.selectedSnapshot = null
  }
})

watch(() => props.showDialogHistory, (history) => {
  if(history) {
    getDialogSnapshots()
  } else {
    store.selectedSnapshot = null
  }
})

watch(selected, (newVal) => {
  if(newVal.length > 0) {
    store.selectedSnapshot = newVal[0]
  }
})

const columns = [
  { name: 'timestamp', label: 'Created On', align: 'left', field: 'snapshotCreatedOn', sortable: true, },
]



</script>