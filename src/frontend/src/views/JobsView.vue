<template>
  <PageTitle
    v-if="!embedded"
    :title="title"
    conceptType="job"
    caption="Runs of Entrypoints"
  />
  <div v-else class="q-mt-lg"></div>

  <TableComponent
    ref="tableRef"
    :rows="jobs"
    :columns="computedColumns"
    :title="embedded ? 'Experiment Jobs' : ''"
    v-model:selected="selected"
    :hideOpenBtn="true"
    @open="openTab => (openTab
      ? openWindow.open(`/jobs/${selected[0].id}`, '_blank')
      : router.push(`/jobs/${selected[0].id}`)
    )"
    :loading="isLoading"
    @request="getJobs"
    @create="pushToJobRoute"
    @delete="
      (row) => {
        selected = [row];
        showDeleteDialog = true;
      }
    "
    @edit="(row) => router.push(`/jobs/${row.id}`)"
    @editTags="
      (row) => {
        editObjTags = row;
        showTagsDialog = true;
      }
    "
  >
    <template #body-cell-status="props">
      <JobStatus :status="props.row.status" />
    </template>
  </TableComponent>

  <DeleteDialog
    v-model="showDeleteDialog"
    @submit="deleteJob"
    type="Job"
    :name="selected[0]?.description || `Job ID: ${selected[0]?.id}`"
  />
  <AssignTagsDialog
    v-model="showTagsDialog"
    :editObj="editObjTags"
    type="jobs"
    @refreshTable="tableRef.refreshTable()"
  />
</template>

<script setup>
import { ref, computed } from "vue"; 
import { useRoute, useRouter } from "vue-router";
import TableComponent from "@/components/table/TableComponent.vue";
import PageTitle from "@/components/PageTitle.vue";
import * as api from "@/services/dataApi";
import * as notify from "../notify";
import DeleteDialog from "@/dialogs/DeleteDialog.vue";
import AssignTagsDialog from "@/dialogs/AssignTagsDialog.vue";
import JobStatus from "@/components/JobStatus.vue";
import BadgeIcon from "@/components/table/cells/BadgeIcon.vue";

const openWindow = window
const route = useRoute();
const router = useRouter();

const title = ref("Jobs");
const jobs = ref([]);
const isLoading = ref(false);
const selected = ref([]); 
const showDeleteDialog = ref(false);
const showTagsDialog = ref(false);
const editObjTags = ref({});
const tableRef = ref(null);

if (route.name === "experimentJobs") {
  getExperiment();
}

async function getExperiment() {
  try {
    const res = await api.getItem("experiments", route.params.id);
    title.value = `${res.data.name} Jobs`;
  } catch (err) {
    console.error("Failed to fetch experiment info", err);
  }
}

const props = defineProps({
  embedded: {
    type: Boolean,
    default: false,
  },
});

const computedColumns = computed(() => {
  const baseCols = [
    {
      name: "id",
      label: "Job ID",
      field: "id",
      align: "left",
      styleType: "icon-badge",
      conceptType: "job",
      showIcon: true,
      size: "md",
      uppercase: false,
      formatLabel: "Job #{label}",
      sortable: true,
    },
    {
      name: "description",
      label: "Description",
      field: "description",
      align: "left",
      styleType: "long-text",
      maxLength: 150,
      maxWidth: "300px",
      useQuotes: true,
      textType: "capitalize",
      sortable: true,
    },
    {
      name: "entrypoint",
      label: "Entrypoint",
      field: "entrypoint",
      styleType: "icon-badge",
      conceptType: "entrypoint",
      align: "left",
      sortable: true,
      clickable: true, // Errors out currently if entrypoint was deleted - need to add functionality to view deleted snapshots
    },
    {
      name: "queue",
      label: "Queue",
      field: "queue",
      styleType: "icon-badge",
      conceptType: "queue",
      align: "left",
      sortable: true,
      clickable: true,
    },
    {
      name: "status",
      label: "Status",
      field: "status",
      align: "left",
      sortable: true,
    },
    {
      name: "tags",
      label: "Tags",
      field: "tags",
      styleType: "tag-list",
      align: "left",
    },
  ];

  if (route.name === "allJobs") {
    baseCols.splice(3, 0, {
      name: "experiment",
      label: "Experiment",
      field: "experiment",
      styleType: "icon-badge",
      conceptType: "experiment",
      align: "left",
      sortable: true,
      clickable: true,
    });
  }
  return baseCols;
});

// API functions
async function getJobs(pagination, showDrafts) {
  isLoading.value = true;
  
  // Restore default sorting by ID descending if no sort is specified
  if (!pagination.sortBy) {
    pagination.sortBy = 'id';
    pagination.descending = true;
  }

  try {
    let res;
    if (route.name === "experimentJobs") {
      res = await api.getJobs(route.params.id, pagination, showDrafts);
    } else {
      res = await api.getData("jobs", pagination, false);
    }
    jobs.value = res.data.data;
    tableRef.value.updateTotalRows(res.data.totalNumResults);
  } catch (err) {
    notify.error(err.response?.data?.message || "Failed to fetch jobs");
  } finally {
    isLoading.value = false;
  }
}

async function deleteJob() {
  try {
    const id = selected.value[0].id;
    await api.deleteItem("jobs", id);
    notify.success(`Deleted job ${id}`);
    showDeleteDialog.value = false;
    selected.value = [];
    tableRef.value.refreshTable();
  } catch (err) {
    notify.error(err.response?.data?.message);
  }
}

function pushToJobRoute() {
  const path =
    route.name === "experimentJobs"
      ? `/experiments/${route.params.id}/jobs/new`
      : "/jobs/new";
  router.push(path);
}
</script>