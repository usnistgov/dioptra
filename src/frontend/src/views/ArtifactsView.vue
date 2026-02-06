<template>
  <PageTitle
    title="Artifacts"
    caption="Objects saved from Jobs"
    conceptType="artifact"
  />

  <TableComponent
    ref="tableRef"
    :rows="artifacts"
    :columns="computedColumns"
    v-model:selected="selected"
    :loading="isLoading"
    :hideCreateBtn="true"
    :hideDeleteBtn="true"
    @request="getArtifacts"
    @edit="(row) => router.push(`/artifacts/${row.id}`)"
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
  >
    <template #body-cell-taskOutputParams="props">
      <ParameterList
        :items="props.row.task?.outputParams || []"
        type="output"
      />
    </template>

    <template #body-cell-download="props">
      <q-btn
        :href="props.row.fileUrl"
        :download="`artifact-${props.row?.id}`"
        round
        dense
        color="primary"
        icon="download"
        size="md"
        @click.stop
      >
        <q-tooltip>Download Artifact</q-tooltip>
      </q-btn>
    </template>
  </TableComponent>

  <ArtifactsDialog
    v-model="showAddEditDialog"
    @addArtifact="addArtifact"
    @updateArtifact="updateArtifact"
    :editArtifact="selected.length && editing ? selected[0] : ''"
  />

  <DeleteDialog
    v-model="showDeleteDialog"
    @submit="deleteModel"
    type="Artifact"
    :name="selected[0]?.description || ''"
  />

  <AssignTagsDialog
    v-model="showTagsDialog"
    :editObj="editObjTags"
    type="artifacts"
    @submitTags="submitTags"
  />
</template>

<script setup>
import { ref, computed, watch } from "vue";
import { useRouter } from "vue-router";
import TableComponent from "@/components/table/TableComponent.vue";
import ParameterList from "@/components/table/cells/ParameterList.vue";
import PageTitle from "@/components/PageTitle.vue";
import ArtifactsDialog from "@/dialogs/ArtifactsDialog.vue";
import DeleteDialog from "@/dialogs/DeleteDialog.vue";
import AssignTagsDialog from "@/dialogs/AssignTagsDialog.vue";
import * as api from "@/services/dataApi";
import * as notify from "../notify";

const router = useRouter();
const tableRef = ref(null);

const artifacts = ref([]);
const isLoading = ref(false);
const selected = ref([]);
const editing = ref(false);

const showAddEditDialog = ref(false);
const showDeleteDialog = ref(false);
const showTagsDialog = ref(false);
const editObjTags = ref({});

watch(showAddEditDialog, (newVal) => {
  if (!newVal) editing.value = false;
});

// Column Definitions
const computedColumns = computed(() => [
  {
    name: "id",
    label: "Artifact ID",
    field: "id",
    align: "left",
    styleType: "icon-badge",
    conceptType: "artifact",
    includeIcon: true,
    size: "md",
    uppercase: false,
    formatLabel: "Artifact #{label}",
  },
  {
    name: "description",
    label: "Description",
    field: "description",
    align: "left",
    styleType: "long-text",
    maxWidth: "250px",
    maxLength: 80,
    useQuotes: true,
    sortable: true,
  },
  {
    name: "job",
    label: "Job",
    field: "job",
    align: "left",
    styleType: "icon-badge", 
    conceptType: "job",
    size: "md",
    sortable: true,
  },
  {
    name: "taskName",
    label: "Task Name",
    field: (row) => row.task?.name,
    align: "left",
    styleType: "icon-badge",
    conceptType: "task",
    uppercase: false,
    chipType: "outline",
  },
  {
    name: "taskOutputParams",
    label: "Output Params",
    field: "taskOutputParams",
    align: "left",
    style: "min-width: 200px; width: 300px; white-space: normal;",
  },
  {
    name: "download",
    label: "Download",
    align: "center",
    style: "width: 50px",
  },
]);


async function getArtifacts(pagination) {
  isLoading.value = true;
  const minLoadTimePromise = new Promise((resolve) => setTimeout(resolve, 300));

  if (!pagination.sortBy) {
    pagination.sortBy = "job";
    pagination.descending = true;
  }

  try {
    const [res] = await Promise.all([
      api.getData("artifacts", pagination),
      minLoadTimePromise,
    ]);

    artifacts.value = res.data.data;
    tableRef.value.updateTotalRows(res.data.totalNumResults);
  } catch (err) {
    console.error(err);
    notify.error(err.response?.data?.message || "Failed to fetch artifacts");
  } finally {
    isLoading.value = false;
  }
}

async function addArtifact(name, group, description) {
  try {
    const res = await api.addItem("models", { name, description, group });
    showAddEditDialog.value = false;
    notify.success(`Successfully created '${res.data.name}'`);
    tableRef.value.refreshTable();
  } catch (err) {
    notify.error(err.response?.data?.message);
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
    notify.error(err.response?.data?.message);
  }
}

async function deleteModel() {
  try {
    const id = selected.value[0].id;
    await api.deleteItem("models", id);
    notify.success(`Successfully deleted artifact`);
    showDeleteDialog.value = false;
    selected.value = [];
    tableRef.value.refreshTable();
  } catch (err) {
    notify.error(err.response?.data?.message);
  }
}

async function submitTags(selectedTagIDs) {
  showTagsDialog.value = false;
  try {
    await api.updateTags("artifacts", editObjTags.value.id, selectedTagIDs);
    notify.success(`Successfully updated Tags`);
    tableRef.value.refreshTable();
  } catch (err) {
    console.error(err);
    notify.error(err.response?.data?.message);
  }
}
</script>
