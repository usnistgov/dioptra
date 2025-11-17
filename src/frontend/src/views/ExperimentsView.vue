<template>
  <PageTitle title="Experiments" />
  <TableComponent 
    :rows="experiments"
    :columns="columns"
    title="Experiments"
    v-model:selected="selected"
  @edit="openTab => (
    openTab
        ? openWindow.open(`/experiments/${selected[0].id}`, '_blank')
        : router.push(`/experiments/${selected[0].id}`)
  )"
    @delete="showDeleteDialog = true"
    @request="getExperiments"
    ref="tableRef"
    @editTags="(row) => { editObjTags = row; showTagsDialog = true }"
    @create="router.push('/experiments/new')"
  >
    <!-- <template #body-cell-name="props">
      <RouterLink :to="`/experiments/${props.row.id}/jobs`" @click.stop>
        {{ props.row.name.length < 18 ? props.row.name : props.row.name.replace(/(.{18})..+/, "$1…") }}
        <q-tooltip v-if="props.row.name.length > 18" max-width="30vw" style="overflow-wrap: break-word">
          {{ props.row.name }}
        </q-tooltip>
      </RouterLink>
    </template> -->
        <template #body-cell-id="props">
      <span class="link">
        {{ props.row.id }}
      </span>
      <q-icon
        name="open_in_new"
        size="sm"
        class="q-ml-sm"
        @click.stop="openWindow.open(`/experiments/${props.row.id}`, '_blank')"
      />
    </template>
    <template #body-cell-entrypoints="props">
      <q-chip
        v-for="(entrypoint, i) in props.row.entrypoints"
        :key="i"
        color="secondary" 
        text-color="white"
      >
        {{ entrypoint.name }}
      </q-chip>
    </template>
  </TableComponent>

  <DeleteDialog 
    v-model="showDeleteDialog"
    @submit="deleteExperiment"
    type="Experiment"
    :name="selected.length ? selected[0].name : ''"
  />
  <AssignTagsDialog 
    v-model="showTagsDialog"
    :editObj="editObjTags"
    type="experiments"
    @refreshTable="tableRef.refreshTable()"
  />
</template>

<script setup>

  import TableComponent from '@/components/TableComponent.vue'
  import { ref } from 'vue'
  import { useRouter } from 'vue-router'
  import * as api from '@/services/dataApi'
  import * as notify from '../notify'
  import DeleteDialog from '@/dialogs/DeleteDialog.vue'
  import PageTitle from '@/components/PageTitle.vue'
  import AssignTagsDialog from '@/dialogs/AssignTagsDialog.vue'

  const openWindow = window
  
  const router = useRouter()

  const showDeleteDialog = ref(false)
  const showTagsDialog = ref(false)
  const editObjTags = ref({})

  const experiments = ref([])

  const columns = [
     { name: 'id', label: 'ID', align: 'left', field: 'id', sortable: true, },
    { name: 'name', label: 'Name', align: 'left', field: 'name', sortable: true, },
    { name: 'description', label: 'Description', align: 'left', field: 'description', sortable: true },
    { name: 'entrypoints', label: 'Entry Points', align: 'left', field: 'entrypoints', sortable: false },
    { name: 'tags', label: 'Tags', align: 'left', sortable: false },
  ]

  const selected = ref([])

  async function getExperiments(pagination) {
    try {
      const res = await api.getData('experiments', pagination, false)
      experiments.value = res.data.data
      tableRef.value.updateTotalRows(res.data.totalNumResults)
    } catch(err) {
      console.log('err = ', err)
      notify.error(err.response.data.message)
    } 
  }

  const tableRef = ref(null)

  async function deleteExperiment() {
    try {
      await api.deleteItem('experiments', selected.value[0].id)
      notify.success(`Successfully deleted '${selected.value[0].name}'`)
      showDeleteDialog.value = false
      selected.value = []
      tableRef.value.refreshTable()
    } catch(err) {
      notify.error(err.response.data.message);
    }
  }


</script>
