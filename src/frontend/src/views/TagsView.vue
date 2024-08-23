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
  >
    <template #body-cell-name="props">
      <q-chip color="primary" text-color="white">
        {{ props.row.name }}
      </q-chip>
    </template>
  </TableComponent>
  <q-btn 
    class="fixedButton"
    round
    color="primary"
    icon="add"
    size="lg"
    @click="showAddDialog = true"
  >
    <span class="sr-only">Register a new Tag</span>
    <q-tooltip>
      Register a new Tag
    </q-tooltip>
  </q-btn>
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

  const showAddDialog = ref(false)
  const showDeleteDialog = ref(false)

  const tags = ref([])

  const tableRef = ref(null)

  const columns = [
    { name: 'name', label: 'Name', align: 'left', field: 'name', sortable: true },
    { name: 'id', label: 'Tag ID', align: 'left', field: 'id', sortable: true },
    { name: 'createdOn', label: 'Created On', align: 'left', field: 'createdOn', format: val => `${formatDate(val)}`, sortable: true },
    { name: 'lastModifiedOn', label: 'Last Modified', align: 'left', field: 'lastModifiedOn', format: val => `${formatDate(val)}`, sortable: true },
    // { name: 'chips', label: 'Custom Column Example',align: 'left', sortable: false },
  ]

  async function getTags(pagination) {
    try {
      const res = await api.getData('tags', pagination)
      tags.value = res.data.data
      tableRef.value.updateTotalRows(res.data.totalNumResults)
    } catch(err) {
      console.log('err = ', err)
      notify.error(err.response.data.message)
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

  function formatDate(dateString) {
    const options = { year: '2-digit', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: true };
    return new Date(dateString).toLocaleString('en-US', options);
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

</script>
