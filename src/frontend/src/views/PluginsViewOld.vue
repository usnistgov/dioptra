<template>
  <PageTitle title="Plugins" />

  <TableComponent
    :rows="plugins"
    :columns="columns"
    title="Plugins"
    v-model:selected="selected"  
    @edit="router.push(`/plugins/${selected[0].id}`)"
    @delete="showDeleteDialog = true"
    @request="getPlugins"
    ref="tableRef"
    @editTags="(row) => { editObjTags = row; showTagsDialog = true }"
    @create="router.push('/plugins/new')"
    :loading="isLoading"
  >

    <template #body-cell-group="props">
      <div>{{ props.row.group.name }}</div>
    </template>
    <template #body-cell-files="props">
      {{ props.row.files?.length }}
    </template>
  </TableComponent>

  <DeleteDialog 
    v-model="showDeleteDialog"
    @submit="deletePlugin"
    type="Plugin"
    :name="selected.length ? selected[0].name : ''"
  />
  <AssignTagsDialog 
    v-model="showTagsDialog"
    :editObj="editObjTags"
    type="plugins"
    @refreshTable="tableRef.refreshTable()"
  />
</template>

<script setup>
  import TableComponent from '@/components/TableComponent.vue'
  import DeleteDialog from '@/dialogs/DeleteDialog.vue'
  import { ref } from 'vue'
  import { useRouter } from 'vue-router'
  import * as api from '@/services/dataApi'
  import * as notify from '../notify'
  import PageTitle from '@/components/PageTitle.vue'
  import AssignTagsDialog from '@/dialogs/AssignTagsDialog.vue'
  import { useLoginStore } from '@/stores/LoginStore.ts'

  const store = useLoginStore()

  const router = useRouter()

  const selected = ref([])

  const showDeleteDialog = ref(false)
  const showTagsDialog = ref(false)
  const editObjTags = ref({})

  const plugins = ref([])

  const isLoading = ref(false)

  async function getPlugins(pagination) {
    isLoading.value = true
    const minLoadTimePromise = new Promise(resolve => setTimeout(resolve, 300)); 

    try {
      const [res] = await Promise.all([
        api.getData('plugins', pagination),
        minLoadTimePromise
      ]);
      
      plugins.value = res.data.data;
      tableRef.value.updateTotalRows(res.data.totalNumResults);
    } catch(err) {
      console.log('err = ', err);
      notify.error(err.response.data.message);
    } finally {
      isLoading.value = false;
    }
  }

  const columns = [
    { name: 'id', label: 'ID', align: 'left', field: 'id', sortable: false, },
    { name: 'name', label: 'Name', align: 'left', field: 'name', sortable: true },
    { name: 'description', label: 'Description', field: 'description',align: 'left', sortable: true },
    { name: 'files', label: 'Number of Files', align: 'left', field: 'files', sortable: false },
    { name: 'tags', label: 'Tags', align: 'left', sortable: false },
  ]

  async function deletePlugin() {
    try {
      await api.deleteItem('plugins', selected.value[0].id)
      notify.success(`Successfully deleted '${selected.value[0].name}'`)
      showDeleteDialog.value = false
      selected.value = []
      tableRef.value.refreshTable()
    } catch(err) {
      notify.error(err.response.data.message);
    }
  }

  const tableRef = ref(null)

</script>