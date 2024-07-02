<template>
  <PageTitle title="Groups" />
  <TableComponent 
    :rows="userGroups"
    :columns="columns"
    title="Groups"
    @delete="showDeleteDialog = true"
    @edit="dataStore.editMode = true; router.push('/groups/admin')"
    v-model:selected="selected"
  >
    <template #body-cell="props">
      <q-td :props="props">
        <q-badge color="blue" :label="props.value" />
      </q-td>
    </template>
  </TableComponent>
  <q-btn 
    class="fixedButton"
    round
    color="primary"
    icon="add"
    size="lg"
    to="/groups/admin"
  >
    <span class="sr-only">Create a new Group</span>
    <q-tooltip>
      Create a new Group
    </q-tooltip>
  </q-btn>
</template>

<script setup>
  import * as api from '@/services/groupsApi'
  import { ref, computed } from 'vue'
  import * as notify from '../notify';
  import TableComponent from '@/components/TableComponent.vue'
  import { useLoginStore } from '@/stores/LoginStore'
  import { useDataStore } from '@/stores/DataStore'
  import { useRouter } from 'vue-router'
  import PageTitle from '@/components/PageTitle.vue'


  const router = useRouter()

  const store = useLoginStore()
  const dataStore = useDataStore()

  const columns = [
    { name: 'name', label: 'Name', align: 'left', field: 'name', sortable: true },
    { name: 'read', label: 'Read', align: 'left', field: 'read', sortable: true },
    { name: 'write', label: 'Write', align: 'left', field: 'write', sortable: true },
    { name: 'shareRead', label: 'Share Read', align: 'left', field: 'shareRead', sortable: true, style: 'width: 200px' },
    { name: 'shareWrite', label: 'Share Write', align: 'left', field: 'shareWrite', sortable: true, style: 'width: 200px' },
    { name: 'admin', label: 'Admin', align: 'left', field: 'admin', sortable: true },
    { name: 'owner', label: 'Owner', align: 'left', field: 'owner', sortable: true },
  ]

  // getGroups()
  // async function getGroups() {
  //   try {
  //     const res = await api.getGroups()
  //     console.log('getGroups = ', res)
  //   } catch(err) {
  //     notify.error(err.response.data.message)
  //   } 
  // }

  const userGroupsIds = computed(() => {
    if(store.loggedInUser) {
      return store.loggedInUser.groups.map((group) => group.id)
    }
    return []
  })

  const userGroups = ref([])

  getUserGroups()

  async function getUserGroups() {
    if(userGroupsIds.value.length === 0) {
      notify.error('Please login to view user groups.')
      return
    }
    for (const id of userGroupsIds.value) {
      const res = await api.getGroup(id)
      console.log('getGroup res = ', res)
      res.data.members.forEach((member) => {
        if(member.user.username === store.loggedInUser.username) {
          userGroups.value.push({
            name: member.group.name,
            ...member.permissions
          })
        }
      })
    }
  }

  const selected = ref([])

</script>
