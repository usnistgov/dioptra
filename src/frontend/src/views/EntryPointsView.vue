<template>
  <PageTitle
    title="Entrypoints"
    resourceType="entrypoint"
    subtitle="Reusable workflows composed of Tasks"
  />
  <TableComponent
    ref="tableRef"
    v-model:selected="selected"
    v-model:showDeleted="showDeleted"
    :rows="rows"
    :columns="columns"
    title="Entrypoints"
    :showDeletedToggle="true"
    :loading="isLoading"
    @open="
      (openTab) =>
        openTab
          ? openWindow.open(`/entrypoints/${selected[0].id}`, '_blank')
          : router.push(`/entrypoints/${selected[0].id}`)
    "
    @delete="showDeleteDialog = true"
    @request="getData"
    @editTags="
      (row) => {
        editObjTags = row;
        showTagsDialog = true;
      }
    "
    @create="router.push('/entrypoints/new')"
    @syncResource="({ row, col, resource }) => syncPlugin(row.id, resource.id, resource.name, col.name)"
    @addResource="
      ({ row, col }) => {
        editEntrypoint = row;
        pluginType = col.name;
        showAssignPluginsDialog = true;
      }
    "
  >
    <template #body-cell-group="cellProps">
      <div>{{ cellProps.row.group.name }}</div>
    </template>
    <template #body-cell-taskGraph="cellProps">
      <q-btn
        v-if="cellProps.row.taskGraph.length"
        label="View YAML"
        color="primary"
        @click.stop="
          displayYaml = cellProps.row.taskGraph;
          showTaskGraphDialog = true;
        "
      />
      <span
        v-else
        class="text-negative"
      >
        EMPTY
      </span>
    </template>
  </TableComponent>

  <InfoPopupDialog v-model="showTaskGraphDialog">
    <template #title>
      <label id="modalTitle"> Task Graph YAML </label>
    </template>
    <CodeEditor
      v-model="displayYaml"
      style="height: auto"
      :readOnly="true"
    />
  </InfoPopupDialog>
  <DeleteDialog
    v-model="showDeleteDialog"
    type="Entry Point"
    :name="selected.length ? selected[0].name : ''"
    @submit="deleteRow"
  />
  <AssignTagsDialog
    v-model="showTagsDialog"
    :editObj="editObjTags"
    type="entrypoints"
    @refreshTable="tableRef.refreshTable()"
  />
  <AssignPluginsDialog
    v-model="showAssignPluginsDialog"
    :pluginType="pluginType"
    :editObj="editEntrypoint"
    @refreshTable="(id) => updateSingleEntrypoint(id)"
  />
</template>

<script setup>
import TableComponent from "@/components/TableComponent.vue";
import { ref } from "vue";
import { useRouter } from "vue-router";
import CodeEditor from "@/components/CodeEditor.vue";
import InfoPopupDialog from "@/dialogs/InfoPopupDialog.vue";
import * as api from "@/services/dataApi";
import * as notify from "../notify";
import DeleteDialog from "@/dialogs/DeleteDialog.vue";
import PageTitle from "@/components/PageTitle.vue";
import AssignTagsDialog from "@/dialogs/AssignTagsDialog.vue";
import AssignPluginsDialog from "@/dialogs/AssignPluginsDialog.vue";
import { useTableUtils } from "@/services/useTableUtils";

const openWindow = window;
const router = useRouter();

const columns = [
  { name: "id", label: "ID", align: "left", field: "id", sortable: false },
  { name: "name", label: "Name", align: "left", field: "name", sortable: true },
  { name: "description", label: "Description", align: "left", field: "description", sortable: true },
  { name: "taskGraph", label: "Task Graph", align: "left", field: "taskGraph", sortable: false },
  {
    name: "plugins",
    label: "Plugins",
    align: "left",
    field: "plugins",
    sortable: false,
    resourceType: "plugin",
    showResourceAdd: true,
  },
  {
    name: "artifactPlugins",
    label: "Artifact Plugins",
    align: "left",
    field: "artifactPlugins",
    sortable: false,
    resourceType: "plugin",
    showResourceAdd: true,
  },
  { name: "tags", label: "Tags", align: "left", field: "tags", sortable: false },
  { name: "lastModifiedOn", label: "Last Modified", align: "left", field: "lastModifiedOn", sortable: true },
];

const showTaskGraphDialog = ref(false);
const displayYaml = ref("");

const showAssignPluginsDialog = ref(false);
const editEntrypoint = ref("");
const pluginType = ref("");

const { rows, isLoading, showDeleted, tableRef, selected, showDeleteDialog, getData, deleteRow } =
  useTableUtils("entrypoints");

const editObjTags = ref({});
const showTagsDialog = ref(false);

async function syncPlugin(entrypointId, pluginId, pluginName, pluginType) {
  try {
    await api.addPluginsToEntrypoint(entrypointId, [pluginId], pluginType);
    await updateSingleEntrypoint(entrypointId);
    notify.success(`Successfully updated plugin '${pluginName}' to latest version`);
  } catch (err) {
    console.warn(err);
    notify.error(err.response.data.message);
  }
}

async function updateSingleEntrypoint(entrypointId) {
  try {
    const res = await api.getItem("entrypoints", entrypointId);
    const idx = rows.value.findIndex((e) => e.id === entrypointId);
    rows.value[idx] = res.data;
  } catch (err) {
    console.warn(err);
    notify.error(err.response.data.message);
  }
}
</script>
