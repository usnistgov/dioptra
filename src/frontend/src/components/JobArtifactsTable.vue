<template>
  <TableComponent
    :rows="artifacts"
    :columns="columns"
    :title="`Artifacts Created by Job ${route.params.id}`"
    v-model:selected="selected"
    @open="openTab => (openTab
      ? openWindow.open(`/artifacts/${selected[0].id}`, '_blank')
      : router.push(`/artifacts/${selected[0].id}`)
    )"
    :hideDeleteBtn="true"
    :hideCreateBtn="true"
    :loading="isLoading"
  >
    <template #body-cell-download="props">
      <q-btn
        :href="props.row.fileUrl"
        :download="`artifact-${props.row?.id}`"
        color="primary"
        round dense flat
        icon="download"
        size="md"
        @click.stop
      >
        <q-tooltip>Download Artifact</q-tooltip>
      </q-btn>
    </template>
  </TableComponent>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import * as api from '@/services/dataApi'
import * as notify from '../notify'
import TableComponent from '@/components/table/TableComponent.vue'

const openWindow = window
const router = useRouter()
const route = useRoute()

const props = defineProps(['artifactIds'])
const selected = ref([])
const artifacts = ref([])
const isLoading = ref(false)

// Column Definitions using Standard Styles
const columns = [
  { 
    name: 'id', 
    label: 'Artifact ID', 
    field: 'id', 
    align: 'left', 
    styleType: 'icon-badge', 
    conceptType: 'artifact',
    includeIcon: true,
    size: 'md',
    uppercase: false,
    formatLabel: 'Artifact #{label}'
  },
  { 
    name: 'description', 
    label: 'Description', 
    field: 'description', 
    align: 'left', 
    styleType: 'long-text',
    maxWidth: '250px' 
  },
  { 
    name: 'taskName', 
    label: 'Task Name', 
    // Access nested property directly in field function
    field: row => row.task?.name, 
    align: 'left',
    styleType: 'icon-badge',
    conceptType: 'task',
    chipType: 'outline',
    uppercase: false
  },
  { 
    name: 'taskOutputParams', 
    label: 'Task Output Params', 
    // Pass the array directly to the component
    field: row => row.task?.outputParams || [], 
    align: 'left',
    styleType: 'parameter-list', // Uses your new ParameterList component automatically
    parameterType: 'output',
    style: 'min-width: 250px'
  },
  { 
    name: 'download', 
    label: 'Download', 
    align: 'center',
    headerStyle: 'width: 50px'
  },
]

onMounted(() => {
  if (props.artifactIds && props.artifactIds.length) {
    getArtifacts()
  }
})

async function getArtifacts() {
  isLoading.value = true
  const minLoadTimePromise = new Promise(resolve => setTimeout(resolve, 300))

  try {
    const artifactsPromise = Promise.all(
      props.artifactIds.map(id => api.getItem('artifacts', id))
    )

    const [responses] = await Promise.all([
      artifactsPromise,
      minLoadTimePromise
    ])

    artifacts.value = responses.map(r => r.data)

  } catch (err) {
    console.warn(err)
    notify.error(err.response?.data?.message || 'Error loading artifacts')
  } finally {
    isLoading.value = false
  }
}


</script>