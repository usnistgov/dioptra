<template>
  <PageTitle title="Tags" />
  <TableComponent 
    :rows="tags"
    :columns="columns"
    title="Tags"
    @delete="showDeleteDialog = true"
    @edit="editing = true; showAddDialog = true"
    v-model:selected="selected"
    @request="getTags"
    ref="tableRef"
    @create="showAddDialog = true"
    :loading="isLoading"
  >
    <template #body-cell-name="props">
      <q-chip color="primary" text-color="white">
        {{ props.row.name }}
      </q-chip>
    </template>
  </TableComponent>

  <AddTagsDialog 
    v-model="showAddDialog"
    @addTag="addTag"
    @updateTag="updateTag"
    :editTag="selected.length && editing ? selected[0] : ''"
  />
  <DeleteDialog 
    v-model="showDeleteDialog"
    @submit="deleteTag"
    type="Tag"
    :name="selected.length ? selected[0].name : ''"
  />
</template>

<script setup>
  import * as api from '@/services/dataApi'
  import { ref, watch } from 'vue'
  import * as notify from '../notify'
  import TableComponent from '@/components/TableComponent.vue'
  import AddTagsDialog from '@/dialogs/AddTagsDialog.vue'
  import DeleteDialog from '@/dialogs/DeleteDialog.vue'
  import PageTitle from '@/components/PageTitle.vue'
  import { useLoginStore } from '@/stores/LoginStore'

  const store = useLoginStore()

  const showAddDialog = ref(false)
  const showDeleteDialog = ref(false)

  const tags = ref([])

  const isLoading = ref(false)

  const tableRef = ref(null)

  const columns = [
    { name: 'name', label: 'Name', align: 'left', field: 'name', sortable: true },
    { name: 'id', label: 'Tag ID', align: 'left', field: 'id', sortable: false },
    { name: 'createdOn', label: 'Created On', align: 'left', field: 'createdOn', sortable: true },
    { name: 'lastModifiedOn', label: 'Last Modified', align: 'left', field: 'lastModifiedOn', sortable: true },
  ]

  async function getTags(pagination) {
    isLoading.value = true
    const minLoadTimePromise = new Promise(resolve => setTimeout(resolve, 300)); 

    try {
      const [res] = await Promise.all([
        api.getData('tags', pagination),
        minLoadTimePromise
      ]);
      
      tags.value = res.data.data;
      tableRef.value.updateTotalRows(res.data.totalNumResults);
    } catch(err) {
      console.log('err = ', err);
      notify.error(err.response.data.message);
    } finally {
      isLoading.value = false;
    }
  }

  async function addTag(name, group) {
    try {
      await api.addItem('tags', {
        name,
        group
      })
      notify.success(`Successfully created tag '${name}'`)
      showAddDialog.value = false
      tableRef.value.refreshTable()
    } catch(err) {
      notify.error(err.response.data.message)
    }
  }

  async function updateTag(name, id) {
    try {
      await api.updateItem('tags', id, { name })
      notify.success(`Successfully edited Tag '${name}'`)
      showAddDialog.value = false
      selected.value = []
      tableRef.value.refreshTable()
    } catch(err) {
      notify.error(err.response.data.message)
    }
  }

  const selected = ref([])
  const editing = ref(false)

  watch(showAddDialog, (newVal) => {
    if(!newVal) editing.value = false
  })

  async function deleteTag() {
    try {
      await api.deleteItem('tags', selected.value[0].id)
      notify.success(`Successfully deleted Tag '${selected.value[0].name}'`)
      showDeleteDialog.value = false
      selected.value = []
      tableRef.value.refreshTable()
    } catch(err) {
      notify.error(err.response.data.message);
    }
  }

  watch(() => store.triggerPopup, (newVal) => {
    if(newVal) {
      showAddDialog.value = true
      store.triggerPopup = false
    }
  })

</script>
