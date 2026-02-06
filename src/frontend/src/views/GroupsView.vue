<template>
  <PageTitle title="Groups" conceptType="group" />

  <TableComponent
    ref="tableRef"
    :rows="userGroups"
    :columns="computedColumns"
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
import { ref, computed } from "vue";
import { useRouter } from "vue-router";
import { useLoginStore } from "@/stores/LoginStore";
import * as api from "@/services/dataApi";
import * as notify from "../notify";

import TableComponent from "@/components/table/TableComponent.vue";
import PageTitle from "@/components/PageTitle.vue";
import DeleteDialog from "@/dialogs/DeleteDialog.vue";

const router = useRouter();
const store = useLoginStore();
const tableRef = ref(null);

const userGroups = ref([]);
const selected = ref([]);
const isLoading = ref(false);
const showDeleteDialog = ref(false);

// Columns
const computedColumns = computed(() => [
  {
    name: "name",
    label: "Name",
    field: "name",
    align: "left",
    styleType: "resource-name",
    conceptType: "group", 
    includeIcon: true,
  },
  {
    name: "read",
    label: "Read",
    field: "read",
    align: "center",
  },
  {
    name: "write",
    label: "Write",
    field: "write",
    align: "center",
  },
  {
    name: "shareRead",
    label: "Share Read",
    field: "shareRead",
    align: "center",
    style: "width: 150px",
  },
  {
    name: "shareWrite",
    label: "Share Write",
    field: "shareWrite",
    align: "center",
    style: "width: 150px",
  },
  {
    name: "admin",
    label: "Admin",
    field: "admin",
    align: "center",
  },
  {
    name: "owner",
    label: "Owner",
    field: "owner",
    align: "center",
  },
]);

const userGroupsIds = computed(() => {
  if (store.loggedInUser && store.loggedInUser.groups) {
    return store.loggedInUser.groups.map((group) => group.id);
  }
  return [];
});

async function getUserGroups(pagination) {
  if (userGroupsIds.value.length === 0) {
    return;
  }

  isLoading.value = true;
  // Reset array to avoid duplicates on refresh
  userGroups.value = [];

  try {
    const res = await api.getData("groups", pagination);
    const groups = res.data.data;

    groups.forEach((group) => {
      group.members.forEach((member) => {
        if (member.user.id === store.loggedInUser.id) {
          userGroups.value.push({
            id: group.id, 
            name: member.group.name,
            ...member.permissions,
          });
        }
      });
    });

    if (tableRef.value) {
      tableRef.value.updateTotalRows(userGroups.value.length);
    }
  } catch (err) {
    notify.error(err.response?.data?.message || "Failed to fetch groups");
  } finally {
    isLoading.value = false;
  }
}

async function deleteGroup() {
  try {
    const id = selected.value[0].id;
    await api.deleteItem("groups", id);
    notify.success(`Successfully deleted '${selected.value[0].name}'`);
    showDeleteDialog.value = false;
    selected.value = [];
    tableRef.value.refreshTable();
  } catch (err) {
    notify.error(err.response?.data?.message || "Delete failed");
  }
}
</script>
