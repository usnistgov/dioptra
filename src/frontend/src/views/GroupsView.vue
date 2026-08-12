<template>
  <PageTitle
    title="Groups"
    resourceType="group"
    subtitle="Controls access to shared resources"
  />
  <q-banner
    rounded
    class="bg-orange-2 text-dark q-mt-md"
  >
    Warning: all future users have access to groups created in this phase.
  </q-banner>
  <TableComponent
    ref="tableRef"
    v-model:selected="selected"
    v-model:showDeleted="showDeleted"
    :rows="userGroups"
    :columns="columns"
    title="Groups"
    :showDeletedToggle="true"
    :hideCreateBtn="false"
    @delete="showDeleteDialog = true"
    @edit="router.push('/groups/admin')"
    @request="getUserGroups"
    @create="router.push('/groups/new')"
  >
    <template #body-cell="props">
      <q-td :props="props">
        <q-badge
          color="blue"
          :label="props.value"
        />
      </q-td>
    </template>
  </TableComponent>

  <DeleteDialog
    v-model="showDeleteDialog"
    type="Group"
    :name="selected.length ? selected[0].name : ''"
    @submit="deleteGroup"
  />
</template>

<script setup>
import * as api from "@/services/dataApi";
import { ref } from "vue";
import * as notify from "../notify";
import TableComponent from "@/components/TableComponent.vue";
import { useLoginStore } from "@/stores/LoginStore";
import { useRouter } from "vue-router";
import PageTitle from "@/components/PageTitle.vue";
import DeleteDialog from "@/dialogs/DeleteDialog.vue";

const router = useRouter();

const store = useLoginStore();

const tableRef = ref(null);

const columns = [
  { name: "name", label: "Name", align: "left", field: "name", sortable: true },
  { name: "read", label: "Read", align: "left", field: "read", sortable: true },
  { name: "write", label: "Write", align: "left", field: "write", sortable: true },
  { name: "shareRead", label: "Share Read", align: "left", field: "shareRead", sortable: true, style: "width: 200px" },
  {
    name: "shareWrite",
    label: "Share Write",
    align: "left",
    field: "shareWrite",
    sortable: true,
    style: "width: 200px",
  },
  { name: "admin", label: "Admin", align: "left", field: "admin", sortable: true },
  { name: "owner", label: "Owner", align: "left", field: "owner", sortable: true },
];

const userGroups = ref([]);
const showDeleteDialog = ref(false);
const showDeleted = ref(false);

async function getUserGroups(pagination) {
  userGroups.value = [];
  const res = await api.getData("groups", pagination, false, showDeleted.value);
  const groups = res.data.data;
  groups.forEach((group) => {
    if (group.public) {
      userGroups.value.push({
        id: group.id,
        name: group.name,
        deleted: group.deleted,
        read: true,
        write: true,
        shareRead: true,
        shareWrite: true,
        admin: true,
        owner: true,
      });
      return;
    }

    const member = group.members.find((m) => m.user.id === store.loggedInUser?.id);
    userGroups.value.push({
      id: group.id,
      name: group.name,
      deleted: group.deleted,
      read: member?.permissions.read ?? false,
      write: member?.permissions.write ?? false,
      shareRead: member?.permissions.share_read ?? false,
      shareWrite: member?.permissions.share_write ?? false,
      admin: member?.permissions.admin ?? false,
      owner: member?.permissions.owner ?? false,
    });
  });

  tableRef.value.updateTotalRows(res.data.totalNumResults);
}

const selected = ref([]);

async function deleteGroup() {
  if (selected.value.length === 0) {
    return;
  }

  const deletedGroupId = selected.value[0].id;
  const deletedGroupName = selected.value[0].name;
  const wasActiveGroup = store.loggedInGroup?.id === deletedGroupId;

  try {
    await api.deleteItem("groups", deletedGroupId);

    const userInfoRes = await api.getLoginStatus();
    store.loggedInUser = userInfoRes.data;
    store.setGroups(userInfoRes.data.groups);

    if (wasActiveGroup && store.groups.length > 0) {
      store.setLoggedInGroup(store.groups[0].id);
    }

    notify.success(`Successfully deleted '${deletedGroupName}'`);
    showDeleteDialog.value = false;
    selected.value = [];
    tableRef.value.refreshTable();
  } catch (err) {
    notify.error(err.response?.data?.message || "Failed to delete group");
  }
}
</script>
