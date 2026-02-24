<template>
  <PageTitle
    title="Plugin Parameter Types"
    caption="Used for type validation in Entrypoints and Artifacts"
    conceptType="parameterType"
  />

  <TableComponent
    ref="tableRef"
    :rows="pluginParameterTypes"
    :columns="computedColumns"
    v-model:selected="selected"
    @open="openTab => (openTab
      ? openWindow.open(`/pluginParams/${selected[0].id}`, '_blank')
      : router.push(`/pluginParams/${selected[0].id}`)
    )"
    @request="getPluginParameterTypes"
    @editTags="(row) => { editObjTags = row; showTagsDialog = true }"
    @create="router.push('/pluginParams/new')"
    :loading="isLoading"
    :hideToggleDraft="true"
    @delete="
      (row) => {
        selected = [row];
        showDeleteDialog = true;
      }
    "
  />

  <DeleteDialog
    v-model="showDeleteDialog"
    @submit="deletePluginParamType"
    type="Plugin Parameter Type"
    :name="selected[0]?.name || ''"
  />

  <AssignTagsDialog
    v-model="showTagsDialog"
    :editObj="editObjTags"
    type="pluginParameterTypes"
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
const pluginParameterTypes = ref([]);
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
    conceptType: "parameterType",
    includeIcon: true,
  },
  {
    name: "name",
    label: "Name",
    field: "name",
    align: "left",
    styleType: "resource-name",
    conceptType: "parameterType",
    textType: "capitalize",
    maxWidth: "200px",
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
    sortable: true,
  },
  {
    name: "createdOn",
    label: "Created On",
    field: "createdOn",
    align: "left",
    styleType: "date",
    textColor: "text-grey-10",
    sortable: true,
  },
  {
    name: "lastModifiedOn",
    label: "Last Modified",
    field: "lastModifiedOn",
    align: "left",
    styleType: "date",
    textColor: "text-grey-10",
  },
  {
    name: "tags",
    label: "Tags",
    field: "tags",
    align: "left",
    styleType: "tag-list",
  },
]);

// Actions
async function getPluginParameterTypes(pagination) {
  isLoading.value = true;
  try {
    const minLoadTimePromise = new Promise((resolve) =>
      setTimeout(resolve, 300),
    );

    const [res] = await Promise.all([
      api.getData("pluginParameterTypes", pagination),
      minLoadTimePromise,
    ]);

    pluginParameterTypes.value = res.data.data;
    tableRef.value.updateTotalRows(res.data.totalNumResults);
  } catch (err) {
    notify.error(err.response?.data?.message || "Failed to fetch parameters");
  } finally {
    isLoading.value = false;
  }
}

async function deletePluginParamType() {
  try {
    const id = selected.value[0].id;
    await api.deleteItem("pluginParameterTypes", id);
    notify.success(`Successfully deleted '${selected.value[0].name}'`);
    showDeleteDialog.value = false;
    selected.value = [];
    tableRef.value.refreshTable();
  } catch (err) {
    notify.error(err.response?.data?.message || "Delete failed");
  }
}
</script>
