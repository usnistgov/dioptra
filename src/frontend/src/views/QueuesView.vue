<template>
  <PageTitle title="Groups" />
  
  <TableComponent 
    ref="tableRef"
    :rows="userGroups"
    :columns="computedColumns"
    title="Groups"
    v-model:selected="selected"
    :loading="isLoading"
    :hideCreateBtn="true"
    
    @request="getUserGroups"
    @edit="router.push('/groups/admin')"
    @delete="showDeleteDialog = true"
  />

  <DeleteDialog 
    v-model="showDeleteDialog"
    @submit="deleteGroup"
    type="Group"
    :name="selected[0]?.name || ''"
  />
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useLoginStore } from '@/stores/LoginStore'
import * as api from '@/services/dataApi'
import * as notify from '../notify'

// Components
import TableComponent from '@/components/table/TableComponent.vue'
import PageTitle from '@/components/PageTitle.vue'
import DeleteDialog from '@/dialogs/DeleteDialog.vue'

const router = useRouter()
const store = useLoginStore()
const tableRef = ref(null)

// State
const userGroups = ref([])
const selected = ref([])
const isLoading = ref(false)
const showDeleteDialog = ref(false)

// Columns
const computedColumns = computed(() => [
  { 
    name: 'id', 
    label: 'Group ID', 
    field: 'id', 
    align: 'left', 
    styleType: 'icon-badge',
    conceptType: 'group',       // Triggers the group icon
    formatLabel: '#{label}',
    includeIcon: true,
    sortable: false
  },
  { 
    name: 'name', 
    label: 'Name', 
    field: 'name', 
    align: 'left', 
    styleType: 'resource-name', // Use the standard bold/blue style
    conceptType: 'group',       // Triggers the group icon
    includeIcon: true,
    sortable: true
  },
  { 
    name: 'read', 
    label: 'Read', 
    field: 'read', 
    align: 'center', 
    sortable: true
    // TableComponent automatically renders booleans as ✅/❌
  },
  { 
    name: 'write', 
    label: 'Write', 
    field: 'write', 
    align: 'center',
  },
  { 
    name: 'shareRead', 
    label: 'Share Read', 
    field: 'shareRead', 
    align: 'center', 
    style: 'width: 150px' ,
    sortable: true
  },
  { 
    name: 'shareWrite', 
    label: 'Share Write', 
    field: 'shareWrite', 
    align: 'center', 
    style: 'width: 150px' ,
    sortable: true
  },
  { 
    name: 'admin', 
    label: 'Admin', 
    field: 'admin', 
    align: 'center',
  },
  { 
    name: 'owner', 
    label: 'Owner', 
    field: 'owner', 
    align: 'center',
  },
])

// Helpers
const userGroupsIds = computed(() => {
  if(store.loggedInUser && store.loggedInUser.groups) {
    return store.loggedInUser.groups.map((group) => group.id)
  }
  return []
})

// Actions
async function getUserGroups(pagination) {
  if(userGroupsIds.value.length === 0) {
    // Optional: Only show notification if user actually expects groups
    // notify.error('Please login to view user groups.') 
    return
  }

  isLoading.value = true
  // Reset array to avoid duplicates on refresh
  userGroups.value = [] 

  try {
    const res = await api.getData('groups', pagination)
    const groups = res.data.data
    
    // Filter logic from original code
    groups.forEach((group) => {
      group.members.forEach((member) => {
        if(member.user.id === store.loggedInUser.id) {
          userGroups.value.push({
            id: group.id, // Ensure we pass ID for routing/selection
            name: member.group.name,
            ...member.permissions
          })
        }
      })
    })
    
    // Update total rows based on filtered result
    if(tableRef.value) {
      tableRef.value.updateTotalRows(userGroups.value.length)
    }
  } catch(err) {
    notify.error(err.response?.data?.message || 'Failed to fetch groups')
  } finally {
    isLoading.value = false
  }
}

async function deleteGroup() {
  try {
    // Assuming you have an ID from the mapping above
    const id = selected.value[0].id 
    await api.deleteItem('groups', id)
    notify.success(`Successfully deleted '${selected.value[0].name}'`)
    showDeleteDialog.value = false
    selected.value = []
    tableRef.value.refreshTable()
  } catch(err) {
    notify.error(err.response?.data?.message || 'Delete failed')
  }
}
</script>