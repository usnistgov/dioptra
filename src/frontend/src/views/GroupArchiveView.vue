<template>
  <h1>Deleted Group Archive</h1>
  <q-banner
    class="bg-orange-2 text-dark q-mb-lg"
    rounded
  >
    Read-only archive for {{ group ? `${group.user.username}/${group.name}` : "deleted group" }}. Browsing this archive
    does not change your active group.
  </q-banner>
  <template v-if="group">
    <q-select
      v-model="resourceType"
      :options="resourceTypes"
      emit-value
      map-options
      label="Resource type"
      outlined
    />
    <q-toggle
      v-if="supportsDrafts"
      v-model="drafts"
      label="My retained drafts"
    />
    <p v-if="drafts">Only your own retained drafts are shown, including new-resource and modification drafts.</p>
    <p v-else-if="resourceType === 'tags'">
      Tags are retained records; they do not have individual soft-delete markers.
    </p>
    <q-table
      v-model:pagination="pagination"
      :rows="rows"
      :columns="columns"
      :loading="loading"
      :rows-per-page-options="[15]"
      row-key="id"
      flat
      bordered
      @request="loadPage"
    >
      <template #body-cell-details="props">
        <q-td :props="props">
          <q-btn
            label="View record"
            flat
            color="primary"
            @click="record = props.row"
          />
        </q-td>
      </template>
    </q-table>
  </template>
  <q-dialog
    :model-value="record !== null"
    @update:model-value="record = null"
  >
    <q-card style="width: 900px; max-width: 90vw">
      <q-card-section class="text-h6">Archived record (read-only)</q-card-section>
      <q-card-section>
        <pre class="archive-record">{{ JSON.stringify(record, null, 2) }}</pre>
      </q-card-section>
      <q-card-actions align="right"
        ><q-btn
          v-close-popup
          label="Close"
          flat
      /></q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import * as api from "@/services/dataApi";
import * as notify from "@/notify";

const route = useRoute();
const router = useRouter();
const groupId = Number(route.params.id);
const group = ref(null);
const resourceType = ref("experiments");
const drafts = ref(false);
const rows = ref([]);
const record = ref(null);
const loading = ref(false);
const pagination = ref({ page: 1, rowsPerPage: 15, rowsNumber: 0 });
const resourceTypes = [
  { label: "Experiments", value: "experiments" },
  { label: "Queues", value: "queues" },
  { label: "Entrypoints", value: "entrypoints" },
  { label: "Plugins", value: "plugins" },
  { label: "Plugin parameter types", value: "pluginParameterTypes" },
  { label: "Jobs", value: "jobs" },
  { label: "Artifacts", value: "artifacts" },
  { label: "Models", value: "models" },
  { label: "Tags", value: "tags" },
];
const supportsDrafts = computed(() =>
  ["experiments", "queues", "entrypoints", "plugins", "pluginParameterTypes"].includes(resourceType.value),
);
const columns = [
  { name: "id", label: "ID", field: "id", align: "left" },
  {
    name: "name",
    label: "Name / Description",
    field: (row) => row.name || row.description || row.payload?.name || "",
    align: "left",
  },
  { name: "details", label: "Details", align: "right" },
];
let latestRequest = 0;

async function loadPage({ pagination: requested } = { pagination: pagination.value }) {
  if (!group.value) return;
  const request = ++latestRequest;
  loading.value = true;
  rows.value = [];
  try {
    const response = await api.getArchivedResources(
      resourceType.value,
      groupId,
      (requested.page - 1) * 15,
      drafts.value && supportsDrafts.value,
    );
    if (request !== latestRequest) return;
    rows.value = response.data.data;
    pagination.value = { ...requested, rowsNumber: response.data.totalNumResults };
  } catch (error) {
    if (request === latestRequest) notify.error(error.response?.data?.message || "Failed to load archived resources");
  } finally {
    if (request === latestRequest) loading.value = false;
  }
}

watch([resourceType, drafts], () => {
  record.value = null;
  loadPage({ pagination: { page: 1, rowsPerPage: 15, rowsNumber: 0 } });
});

onMounted(async () => {
  try {
    const response = await api.getArchivedGroup(groupId);
    if (!response.data.deleted) {
      await router.replace(`/groups/${groupId}/admin`);
      return;
    }
    group.value = response.data;
    await loadPage();
  } catch (error) {
    notify.error(error.response?.data?.message || "Failed to load deleted group");
  }
});
</script>

<style scoped>
.archive-record {
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}
</style>
