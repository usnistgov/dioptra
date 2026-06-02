<template>
  <PageTitle
    v-if="route.name !== 'experimentJobs'"
    :title="title"
    resourceType="job"
    subtitle="Parameterized executions of Entrypoints"
  />
  <TableComponent
    ref="tableRef"
    v-model:selected="selected"
    :rows="rows"
    :columns="columns"
    title="Jobs"
    :hideOpenBtn="true"
    :loading="isLoading"
    :hideCreateBtn="route.name === 'experimentJobs' && experiment?.deleted"
    :defaultSort="{ sortBy: 'id', descending: true }"
    @request="getJobs"
    @delete="showDeleteDialog = true"
    @editTags="
      (row) => {
        editObjTags = row;
        showTagsDialog = true;
      }
    "
    @create="pushToJobRoute"
    @open="
      (openTab) =>
        openTab ? openWindow.open(`/jobs/${selected[0].id}`, '_blank') : router.push(`/jobs/${selected[0].id}`)
    "
  >
    <template #body-cell-status="cellProps">
      <JobStatus :status="cellProps.row.status" />
    </template>
  </TableComponent>

  <DeleteDialog
    v-model="showDeleteDialog"
    type="Job"
    :name="selected[0]?.description || `Job ID: ${selected[0]?.id}`"
    @submit="deleteRow"
  />

  <ArtifactsDialog
    v-model="showArtifactsDialog"
    :editArtifact="''"
    :expId="route.params.id"
    :jobId="jobId"
  />

  <AssignTagsDialog
    v-model="showTagsDialog"
    :editObj="editObjTags"
    type="jobs"
    @refreshTable="tableRef.refreshTable()"
  />
</template>

<script setup>
import TableComponent from "@/components/TableComponent.vue";
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import PageTitle from "@/components/PageTitle.vue";
import * as api from "@/services/dataApi";
import * as notify from "../notify";
import DeleteDialog from "@/dialogs/DeleteDialog.vue";
import ArtifactsDialog from "@/dialogs/ArtifactsDialog.vue";
import AssignTagsDialog from "@/dialogs/AssignTagsDialog.vue";
import JobStatus from "@/components/JobStatus.vue";
import { useTableUtils } from "@/services/useTableUtils";

const openWindow = window;
const route = useRoute();
const router = useRouter();

const columns = [
  { name: "id", label: "ID", align: "left", field: "id", sortable: true },
  {
    name: "entrypoint",
    label: "Entrypoint",
    align: "left",
    field: "entrypoint",
    sortable: true,
    resourceType: "entrypoint",
  },
  { name: "queue", label: "Queue", align: "left", field: "queue", sortable: true, resourceType: "queue" },
  {
    name: "description",
    label: "Description",
    align: "left",
    field: "description",
    sortable: true,
    style: "width: 275px",
  },
  { name: "status", label: "Status", align: "left", field: "status", sortable: true },
  { name: "tags", label: "Tags", align: "left", field: "tags", sortable: false },
  { name: "lastModifiedOn", label: "Last Modified", align: "left", field: "lastModifiedOn", sortable: true },
];

if (route.name === "allJobs") {
  columns.splice(2, 0, {
    name: "experiment",
    label: "Experiment",
    align: "left",
    field: "experiment",
    sortable: true,
    resourceType: "experiment",
  });
}

const title = ref("");

if (route.name === "experimentJobs") {
  getExperiment();
} else if (route.name === "allJobs") {
  title.value = "Jobs";
}

const experiment = ref();

async function getExperiment() {
  try {
    const res = await api.getItem("experiments", route.params.id);
    experiment.value = res.data;
  } catch (err) {
    console.log("err = ", err);
  }
}

const { rows, isLoading, tableRef, selected, showDeleteDialog, getData, deleteRow } = useTableUtils("jobs");

async function getJobs(pagination, showDrafts) {
  try {
    if (route.name === "experimentJobs") {
      isLoading.value = true;
      const res = await api.getJobs(route.params.id, pagination, showDrafts);
      rows.value = res.data.data;
      tableRef.value?.updateTotalRows(res.data.totalNumResults);
      isLoading.value = false;
    } else if (route.name === "allJobs") {
      await getData(pagination, showDrafts);
    }
  } catch (err) {
    console.log("err = ", err);
    notify.error(err.response.data.message);
  }
}

const showArtifactsDialog = ref(false);
const showTagsDialog = ref(false);
const editObjTags = ref({});

const jobId = ref("");

function pushToJobRoute() {
  if (route.name === "experimentJobs") {
    router.push(`/experiments/${route.params.id}/jobs/new`);
  } else if (route.name === "allJobs") {
    router.push("/jobs/new");
  }
}
</script>
