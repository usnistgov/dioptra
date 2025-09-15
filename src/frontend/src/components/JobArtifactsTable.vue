<template>
  <TableComponent
    :rows="artifacts"
    :columns="columns"
    :title="`Artifacts Created by Job ${route.params.id}`"
    v-model:selected="selected"
    @edit="router.push(`/artifacts/${selected[0].id}`)"
    :hideDeleteBtn="true"
    :hideCreateBtn="true"
  >
    <template #body-cell-taskName="props">
      {{ props.row.task.name }}
    </template>
    <template #body-cell-taskOutputParams="props">
      <q-chip
        v-for="param in props.row.task.outputParams"
        color="purple"
        text-color="white"
        dense
      >
        {{ param.name }}: {{ param.parameterType.name }}
      </q-chip>
    </template>
    <template #body-cell-download="props">
      <q-btn
        :href="props.row.fileUrl"
        :download="`artifact-${props.row?.id}`"
        color="primary"
        round
        icon="download"
        size="sm"
        @click.stop
      />
    </template>
  </TableComponent>
</template>

<script setup>
import TableComponent from '@/components/TableComponent.vue'
import { ref, onMounted } from 'vue'
import * as api from '@/services/dataApi'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

const props = defineProps(['artifactIds'])
const selected = ref([])

onMounted(() => {
  getArtifacts()
})

const artifacts = ref([])

async function getArtifacts() {
  try {
    for (let id of props.artifactIds) {
      const res = await api.getItem('artifacts', id)
      artifacts.value.push(res.data)
    }
  } catch(err) {
    console.warn(err)
  }
}

const columns = [
  { name: 'description', label: 'Description', field: 'description', align: 'left', sortable: true },
  { name: 'taskName', label: 'Task Name', align: 'left' },
  { name: 'taskOutputParams', label: 'Task Output Params', align: 'left' },
  { name: 'download', label: 'Download', align: 'center' },
]
</script>