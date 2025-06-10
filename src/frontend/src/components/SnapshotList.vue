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
      <div :data-snapshot-id="props.row.snapshot">
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
      </div>
    </template>
  </TableComponent>
</template>

<script setup>
import { useLoginStore } from '@/stores/LoginStore'
import { useRoute, useRouter } from 'vue-router'
import TableComponent from '@/components/TableComponent.vue'
import { ref, watch, nextTick } from 'vue'
import * as api from '@/services/dataApi'

const props = defineProps(['showDialogHistory', 'type', 'id', 'maxHeight'])

const store = useLoginStore()
const route = useRoute()
const router = useRouter()

const snapshots = ref([])
const selected = ref([])

async function getSnapshots() {
  try {
    const res = await api.getSnapshots(route.meta.type, route.params.id)
    snapshots.value = res.data.data.reverse()
    if(res.data.data.length > 0) {
      if(route.query.snapshotId) {
        // if snapshotId is provided in url, auto select it
        let index = res.data.data.findIndex(
          obj => obj.snapshot === Number(route.query.snapshotId)
        )
        selected.value = [snapshots.value[index]]
      } else {
        // else auto select the latest snapshot
        selected.value = [snapshots.value[0]]
      }
      // scroll to selected snapshot if needed
      await nextTick()
      const el = document.querySelector(
        `[data-snapshot-id="${selected.value[0]?.snapshot}"]`
      )
      el?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
    console.log('snapshots = ', snapshots.value)
  } catch(err) {
    console.warn(err)
  }
}

async function getDialogSnapshots() {
  try {
    const res = await api.getSnapshots(props.type, props.id)
    snapshots.value = res.data.data.reverse()
    if(res.data.data.length > 0) {
      // when viewing history, auto select first (latest) row
      selected.value = [snapshots.value[0]]
    }
    console.log('snapshots = ', snapshots.value)
  } catch(err) {
    console.warn(err)
  }
}

watch(() => store.showRightDrawer, (drawerOpen) => {
  if(drawerOpen) {
    getSnapshots()
  } else {
    store.selectedSnapshot = null
    history.replaceState({}, null, route.path)
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
    history.replaceState(
      {},
      null,
      route.path + '?snapshotId=' + encodeURIComponent(selected.value[0].snapshot)
    )
  }
})

const columns = [
  { name: 'timestamp', label: 'Created On', align: 'left', field: 'snapshotCreatedOn', sortable: true, },
]



</script>