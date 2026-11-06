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
    :refresh-on-group-change="false"
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
        v-if="props.row.deleted"
        label="Browse Deleted Resources"
        color="primary"
        dense
        no-caps
        :to="`/groups/${props.row.id}/archive`"
        @click.stop
      />
      <q-btn
        v-else
        :label="props.row.id === store.loggedInGroup.id ? 'Active Context' : 'Set Context'"
        :color="props.row.id === store.loggedInGroup.id ? 'secondary' : 'primary'"
        :outline="props.row.id !== store.loggedInGroup.id"
        :disable="props.row.id === store.loggedInGroup.id || props.row.deleted"
        dense
        no-caps
        @click.stop="setGroupContext(props.row.id)"
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
import { openInNewTab as openRouteInNewTab } from "@/services/navigation";

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
let latestGroupsRequest = 0;

async function getUserGroups(pagination) {
  const requestId = ++latestGroupsRequest;
  const res = await api.getData("groups", pagination, false, showDeleted.value);
  if (requestId !== latestGroupsRequest) {
    return;
  }

  userGroups.value = res.data.data.map((group) => {
    const member = group.members.find((m) => Number(m.user.id) === Number(store.loggedInUser?.id));
    return {
      id: group.id,
      name: group.name,
      qualifiedName: `${group.user.username}/${group.name}`,
      deleted: group.deleted,
      read: group.public || (member?.permissions.read ?? false),
      write: group.public || (member?.permissions.write ?? false),
      admin: member?.permissions.admin ?? false,
      owner: member?.permissions.owner ?? false,
    };
  });

  tableRef.value.updateTotalRows(res.data.totalNumResults);
}

const selected = ref([]);

function requestDelete(group) {
  selected.value = [group];
  showDeleteDialog.value = true;
}

async function setGroupContext(groupId) {
  if (store.setLoggedInGroup(groupId)) {
    return;
  }

  try {
    await api.refreshLoginState();
    if (!store.setLoggedInGroup(groupId)) {
      throw new Error(`Group ${groupId} is not available to the current user.`);
    }
  } catch (err) {
    notify.error(err.response?.data?.message || err.message || "Failed to refresh available groups");
  }
}

function openGroup(openInNewTab = false) {
  if (selected.value.length === 0) {
    return;
  }

  const group = selected.value[0];
  const route = router.resolve(`/groups/${group.id}/${group.deleted ? "archive" : "admin"}`);
  if (openInNewTab) {
    openRouteInNewTab(route.href);
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

  try {
    await api.deleteItem("groups", deletedGroupId);

    await api.refreshLoginState();

    notify.success(`Successfully deleted '${deletedGroupName}'`);
    showDeleteDialog.value = false;
    selected.value = [];
    tableRef.value.refreshTable();
  } catch (err) {
    notify.error(err.response?.data?.message || "Failed to delete group");
  }
}
</script>
