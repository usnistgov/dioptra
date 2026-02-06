<template>
  <PageTitle
    title="Plugins"
    caption="Containers for Tasks and Files"
    conceptType="plugin"
  />

  <TableComponent
    ref="tableRef"
    :rows="plugins"
    :columns="computedColumns"
    title="Plugins"
    v-model:selected="selected"
    :loading="isLoading"
    @request="getPlugins"
    @create="router.push('/plugins/new')"
    @edit="(row) => router.push(`/plugins/${row.id}`)"
    @delete="
      (row) => {
        selected = [row];
        showDeleteDialog = true;
      }
    "
    @editTags="
      (row) => {
        editObjTags = row;
        showTagsDialog = true;
      }
    "
  />

  <DeleteDialog
    v-model="showDeleteDialog"
    @submit="deletePlugin"
    type="Plugin"
    :name="selected[0]?.name || ''"
  />

  <AssignTagsDialog
    v-model="showTagsDialog"
    :editObj="editObjTags"
    type="plugins"
    @refreshTable="tableRef.refreshTable()"
  />
</template>

<script setup>
import { ref, computed } from "vue";
import { useRouter } from "vue-router";
import TableComponent from "@/components/table/TableComponent.vue";
import PageTitle from "@/components/PageTitle.vue";
import DeleteDialog from "@/dialogs/DeleteDialog.vue";
import AssignTagsDialog from "@/dialogs/AssignTagsDialog.vue";
import * as api from "@/services/dataApi";
import * as notify from "../notify";

const router = useRouter();
const tableRef = ref(null);

// State
const plugins = ref([]);
const isLoading = ref(false);
const selected = ref([]);
const showDeleteDialog = ref(false);
const showTagsDialog = ref(false);
const editObjTags = ref({});

// Columns
const computedColumns = computed(() => [
  {
    name: "id",
    label: "ID",
    field: "id",
    align: "left",
    styleType: "icon-id",
    conceptType: "plugin",
    includeIcon: true,
  },
  {
    name: "name",
    label: "Plugin Name",
    field: "name",
    align: "left",
    styleType: "resource-name",
    conceptType: "plugin",
    textType: "capitalize",
    maxWidth: "250px",
    sortable: true,
  },
  {
    name: "description",
    label: "Description",
    field: "description",
    align: "left",
    styleType: "long-text",
    maxWidth: "300px",
    maxLength: 100,
    useQuotes: true,
    sortable: true,
  },
  {
    name: "files",
    label: "Files",
    field: (row) => row.files?.length || 0,
    align: "left",
    styleType: "icon-badge",
    conceptType: "file",
    formatLabel: "{label} Files",
  },
  {
    name: "group",
    label: "Group",
    field: "group",
    align: "left",
    styleType: "icon-badge",
    conceptType: "group",
  },
  {
    name: "tags",
    label: "Tags",
    field: "tags",
    align: "left",
    styleType: "tag-list",
  },
]);

// API Functions
async function getPlugins(pagination) {
  isLoading.value = true;
  try {
    const minLoadTimePromise = new Promise((resolve) =>
      setTimeout(resolve, 300),
    );

    const [res] = await Promise.all([
      api.getData("plugins", pagination),
      minLoadTimePromise,
    ]);

    plugins.value = res.data.data;
    tableRef.value.updateTotalRows(res.data.totalNumResults);
  } catch (err) {
    notify.error(err.response?.data?.message || "Failed to fetch plugins");
  } finally {
    isLoading.value = false;
  }
}

async function deletePlugin() {
  try {
    const id = selected.value[0].id;
    await api.deleteItem("plugins", id);
    notify.success(`Successfully deleted '${selected.value[0].name}'`);
    showDeleteDialog.value = false;
    selected.value = [];
    tableRef.value.refreshTable();
  } catch (err) {
    notify.error(err.response?.data?.message || "Failed to delete plugin");
  }
}
</script>
