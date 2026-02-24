<template>
  <PageTitle 
    title="Queues" 
    conceptType="queue" 
  />

  <TableComponent
    ref="tableRef"
    :rows="queues"
    :columns="showDrafts ? computedDraftColumns : computedColumns"
    v-model:selected="selected"
    v-model:showDrafts="showDrafts"
    :showToggleDraft="true"
    :loading="isLoading"
    @request="getQueues"
    @create="router.push('/queues/new')"
    @edit="(row) => openQueue(false, row)"
    @open="(openTab) => openQueue(openTab)"
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
    <template #body-cell-hasDraft="props">
      <q-btn
        round
        size="sm"
        :icon="props.row.hasDraft ? 'edit' : 'add'"
        :color="props.row.hasDraft ? 'primary' : 'grey-5'"
        @click.stop="router.push(`/queues/${props.row.id}/resourceDraft/${props.row.hasDraft ? '' : 'new'}`)"
      />
    </template>
  </TableComponent>

  <DeleteDialog
    v-model="showDeleteDialog"
    @submit="deleteQueue"
    type="Queue"
    :name="selected[0]?.name || ''"
  />

  <AssignTagsDialog
    v-model="showTagsDialog"
    :editObj="editObjTags"
    type="queues"
    @refreshTable="tableRef.refreshTable()"
  />
</template>

<script setup>
const openWindow = window;
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

const queues = ref([]);
const isLoading = ref(false);
const selected = ref([]);
const showDrafts = ref(false);
const showDeleteDialog = ref(false);
const showTagsDialog = ref(false);
const editObjTags = ref({});

const computedColumns = computed(() => [
  {
    name: "id",
    label: "ID",
    field: "id",
    align: "left",
    styleType: "icon-id",
    conceptType: "queue",
    includeIcon: true,
    sortable: false,
  },
  {
    name: "name",
    label: "Name",
    field: "name",
    align: "left",
    styleType: "resource-name",
    conceptType: "queue",
    textType: "none",
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
    useQuotes: false,
    sortable: true,
  },
  {
    name: "hasDraft",
    label: "Has Draft",
    field: "hasDraft",
    align: "left",
    sortable: false,
  },
  {
    name: "createdOn",
    label: "Created On",
    field: "createdOn",
    align: "left",
    sortable: true,
    styleType: "date",
    textColor: "text-grey-10",
    sortable: true,
  },
  {
    name: "lastModifiedOn",
    label: "Last Modified",
    field: "lastModifiedOn",
    align: "left",
    sortable: true,
    styleType: "date",
    textColor: "text-grey-10",
    sortable: false,
  },
  {
    name: "tags",
    label: "Tags",
    field: "tags",
    align: "left",
    styleType: "tag-list",
    sortable: false,
  },
]);

const computedDraftColumns = computed(() => [
  {
    name: "id",
    label: "ID",
    field: "id",
    align: "left",
    styleType: "icon-id",
    conceptType: "queue",
    includeIcon: true,
    sortable: false,
  },
  {
    name: "name",
    label: "Name",
    field: "name",
    align: "left",
    styleType: "resource-name",
    conceptType: "queue",
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
    useQuotes: false,
    sortable: true,
  },
  {
    name: "createdOn",
    label: "Created On",
    field: "createdOn",
    align: "left",
    sortable: true,
  },
  {
    name: "lastModifiedOn",
    label: "Last Modified",
    field: "lastModifiedOn",
    align: "left",
    sortable: true,
  },
]);

async function getQueues(pagination, showDraftsVal) {
  isLoading.value = true;
  const minLoadTimePromise = new Promise((resolve) => setTimeout(resolve, 300));

  try {
    const [res] = await Promise.all([
      api.getData("queues", pagination, showDraftsVal),
      minLoadTimePromise,
    ]);

    queues.value = res.data.data;
    tableRef.value.updateTotalRows(res.data.totalNumResults);
  } catch (err) {
    notify.error(err.response?.data?.message || "Failed to fetch queues");
  } finally {
    isLoading.value = false;
  }
}

async function deleteQueue() {
  try {
    const id = selected.value[0].id;
    
    if (Object.hasOwn(selected.value[0], "hasDraft")) {
      await api.deleteItem("queues", id);
    } else {
      await api.deleteDraft("queues", id);
    }
    
    notify.success(`Successfully deleted '${selected.value[0].name}'`);
    showDeleteDialog.value = false;
    selected.value = [];
    tableRef.value.refreshTable();
  } catch (err) {
    notify.error(err.response?.data?.message || "Failed to delete queue");
  }
}

function openQueue(openTab, row) {
  const target = row || selected.value[0];
  if (!target) return;

  const url = target.payload
    ? `/queues/${target.id}/draft`
    : `/queues/${target.id}`;

  if (openTab) openWindow.open(url, "_blank", "noopener,noreferrer");
  else router.push(url);
}
</script>