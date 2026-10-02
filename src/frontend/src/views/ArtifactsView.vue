<template>
  <PageTitle
    title="Artifacts"
    resourceType="artifact"
    subtitle="Stored output objects from Jobs"
  />
  <TableComponent
    ref="tableRef"
    v-model:selected="selected"
    :rows="rows"
    :columns="columns"
    title="Artifacts"
    :hideCreateBtn="true"
    :hideDeleteBtn="true"
    :loading="isLoading"
    :defaultSort="{ sortBy: 'id', descending: true }"
    @open="
      (openTab) =>
        openTab
          ? openWindow.open(`/artifacts/${selected[0].id}`, '_blank')
          : router.push(`/artifacts/${selected[0].id}`)
    "
    @delete="showDeleteDialog = true"
    @request="getData"
  >
    <template #body-cell-taskName="cellProps">
      {{ cellProps.row.task.name }}
    </template>
    <template #body-cell-taskOutputParams="cellProps">
      <q-chip
        v-for="(param, i) in cellProps.row.task.outputParams"
        :key="i"
        color="purple"
        text-color="white"
        dense
      >
        {{ param.name }}: {{ param.parameterType.name }}
      </q-chip>
    </template>
    <template #body-cell-download="cellProps">
      <q-btn
        color="primary"
        round
        icon="download"
        size="sm"
        :loading="downloadingId === cellProps.row.id"
        @click.stop="downloadFile(cellProps.row.fileUrl, `artifact-${cellProps.row?.id}`, cellProps.row.id)"
      />
    </template>
  </TableComponent>

  <ArtifactsDialog
    v-model="showAddEditDialog"
    :editArtifact="selected.length && editing ? selected[0] : ''"
    @addArtifact="addArtifact"
    @updateArtifact="updateArtifact"
  />
  <DeleteDialog
    v-model="showDeleteDialog"
    type="Model"
    :name="selected.length ? selected[0].description : ''"
    @submit="deleteModel"
  />
  <AssignTagsDialog
    v-model="showTagsDialog"
    :editObj="editObjTags"
    @submitTags="submitTags"
  />
</template>

<script setup>
import TableComponent from "@/components/TableComponent.vue";
import ArtifactsDialog from "@/dialogs/ArtifactsDialog.vue";
import DeleteDialog from "@/dialogs/DeleteDialog.vue";
import { ref, watch } from "vue";
import * as api from "@/services/dataApi";
import * as notify from "../notify";
import PageTitle from "@/components/PageTitle.vue";
import AssignTagsDialog from "@/dialogs/AssignTagsDialog.vue";
import { useRouter } from "vue-router";
import { useTableUtils } from "@/services/useTableUtils";

const openWindow = window;
const router = useRouter();

const editing = ref(false);

const showAddEditDialog = ref(false);
const showTagsDialog = ref(false);

watch(showAddEditDialog, (newVal) => {
  if (!newVal) editing.value = false;
});

const { rows, isLoading, tableRef, selected, showDeleteDialog, getData } = useTableUtils("artifacts");

const columns = [
  { name: "id", label: "ID", align: "left", field: "id", sortable: true },
  { name: "description", label: "Description", field: "description", align: "left", sortable: true },
  {
    name: "job",
    label: "Job",
    align: "left",
    resourceType: "job",
    field: (row) => ({
      name: `Job ${row.job}`,
      url: `/jobs/${row.job}`,
      id: row.job,
    }),
  },
  { name: "taskName", label: "Task Name", align: "left" },
  { name: "taskOutputParams", label: "Task Output Params", align: "left" },
  { name: "lastModifiedOn", label: "Last Modified", align: "left", field: "lastModifiedOn", sortable: true },
  { name: "download", label: "Download", align: "center" },
];

async function addArtifact(name, group, description) {
  try {
    const res = await api.addItem("models", {
      name,
      description,
      group,
    });
    showAddEditDialog.value = false;
    notify.success(`Successfully created '${res.data.name}'`);
    tableRef.value.refreshTable();
  } catch (err) {
    notify.error(err.response.data.message);
  }
}

async function deleteModel() {
  try {
    await api.deleteItem("models", selected.value[0].id);
    notify.success(`Successfully deleted '${selected.value[0].description}'`);
    showDeleteDialog.value = false;
    selected.value = [];
    tableRef.value.refreshTable();
  } catch (err) {
    notify.error(err.response.data.message);
  }
}

async function updateArtifact(id, description) {
  try {
    await api.updateItem("artifacts", id, { description });
    notify.success(`Successfully updated artifact`);
    showAddEditDialog.value = false;
    selected.value = [];
    tableRef.value.refreshTable();
  } catch (err) {
    notify.error(err.response.data.message);
  }
}

const editObjTags = ref({});

async function submitTags(selectedTagIDs) {
  showTagsDialog.value = false;
  try {
    await api.updateTags("artifacts", editObjTags.value.id, selectedTagIDs);
    notify.success(`Successfully updated Tags for '${editObjTags.value.name}'`);
    tableRef.value.refreshTable();
  } catch (err) {
    console.log("err = ", err);
    notify.error(err.response.data.message);
  }
}

const downloadingId = ref(null);

async function downloadFile(url, filename, id) {
  downloadingId.value = id;
  try {
    await api.downloadFile(url, filename);
    notify.success(`Successfully downloaded file: ${filename}`);
  } catch (err) {
    console.warn(err);
    notify.error(`Error downloading file ${filename}`);
  } finally {
    downloadingId.value = null;
  }
}
</script>
