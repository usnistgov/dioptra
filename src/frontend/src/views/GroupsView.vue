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
    Warning: All users can read and write resources in every group as permissions are not yet implemented.
  </q-banner>
  <TableComponent
    ref="tableRef"
    v-model:selected="selected"
    v-model:showDeleted="showDeleted"
    :rows="userGroups"
    :columns="columns"
    :highlightedRowKeys="activeGroupIds"
    title="Groups"
    :showDeletedToggle="true"
    :hideCreateBtn="false"
    @open="openGroup"
    @request="getUserGroups"
    @create="router.push('/groups/new')"
  >
    <template #body-cell-name="props">
      <span>{{ props.row.qualifiedName }}</span>
      <q-chip
        v-if="props.row.deleted"
        label="Deleted"
        outline
        color="red"
        dense
      />
    </template>
    <template #body-cell-context="props">
      <q-btn
        :label="props.row.id === store.loggedInGroup.id ? 'Active Context' : 'Set Context'"
        :color="props.row.id === store.loggedInGroup.id ? 'secondary' : 'primary'"
        :outline="props.row.id !== store.loggedInGroup.id"
        :disable="props.row.id === store.loggedInGroup.id || props.row.deleted"
        dense
        no-caps
        @click.stop="store.setLoggedInGroup(props.row.id)"
      />
    </template>
    <template #body-cell-delete="props">
      <q-btn
        v-if="!props.row.deleted"
        round
        :color="props.row.owner ? 'negative' : 'grey-5'"
        :disable="!props.row.owner"
        icon="sym_o_delete"
        size="sm"
        aria-label="Delete group"
        @click.stop="requestDelete(props.row)"
      />
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
import { computed, ref } from "vue";
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
  { name: "id", label: "ID", align: "left", field: "id", sortable: true },
  { name: "name", label: "Name", align: "left", field: "qualifiedName", sortable: true },
  { name: "read", label: "Read", align: "left", field: "read", sortable: true },
  { name: "write", label: "Write", align: "left", field: "write", sortable: true },
  { name: "admin", label: "Admin", align: "left", field: "admin", sortable: true },
  { name: "owner", label: "Owner", align: "left", field: "owner", sortable: true },
  { name: "context", label: "Context", align: "center", field: "id", sortable: false },
];

const userGroups = ref([]);
const showDeleteDialog = ref(false);
const showDeleted = ref(false);
const activeGroupIds = computed(() => (store.loggedInGroup ? [store.loggedInGroup.id] : []));

async function getUserGroups(pagination) {
  userGroups.value = [];
  const res = await api.getData("groups", pagination, false, showDeleted.value);
  const groups = res.data.data;
  groups.forEach((group) => {
    const member = group.members.find((m) => Number(m.user.id) === Number(store.loggedInUser?.id));
    userGroups.value.push({
      id: group.id,
      name: group.name,
      qualifiedName: `${group.user.username}/${group.name}`,
      deleted: group.deleted,
      read: group.public || (member?.permissions.read ?? false),
      write: group.public || (member?.permissions.write ?? false),
      admin: member?.permissions.admin ?? false,
      owner: member?.permissions.owner ?? false,
    });
  });

  tableRef.value.updateTotalRows(res.data.totalNumResults);
}

const selected = ref([]);

function requestDelete(group) {
  selected.value = [group];
  showDeleteDialog.value = true;
}

function openGroup(openInNewTab = false) {
  if (selected.value.length === 0) {
    return;
  }

  const route = router.resolve(`/groups/${selected.value[0].id}/admin`);
  if (openInNewTab) {
    window.open(route.href, "_blank");
    return;
  }
  router.push(route);
}

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
