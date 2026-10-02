<template>
  <TableComponent
    v-model:selected="selected"
    :rows="artifacts"
    :columns="columns"
    :title="`Artifacts Created by Job ${route.params.id}`"
    :hideDeleteBtn="true"
    :hideCreateBtn="true"
    :loading="isLoading"
    :defaultSort="{ sortBy: 'id', descending: true }"
    @open="
      (openTab) =>
        openTab
          ? openWindow.open(`/artifacts/${selected[0].id}`, '_blank')
          : router.push(`/artifacts/${selected[0].id}`)
    "
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
        :href="cellProps.row.fileUrl"
        :download="`artifact-${cellProps.row?.id}`"
        color="primary"
        round
        icon="download"
        size="sm"
        @click.stop
      />
    </template>
  </TableComponent>
</template>

<script setup>
import TableComponent from "@/components/TableComponent.vue";
import { ref, onMounted } from "vue";
import * as api from "@/services/dataApi";
import { useRouter, useRoute } from "vue-router";
import * as notify from "../notify";

const openWindow = window;
const router = useRouter();
const route = useRoute();

const props = defineProps(["artifactIds"]);
const selected = ref([]);

onMounted(() => {
  getArtifacts();
});

const artifacts = ref([]);
const isLoading = ref(false);

async function getArtifacts() {
  isLoading.value = true;
  try {
    const responses = await Promise.all(props.artifactIds.map((id) => api.getItem("artifacts", id)));
    artifacts.value = responses.map((r) => r.data);
  } catch (err) {
    console.warn(err);
    notify.error(err.response?.data?.message || "Error loading artifacts");
  } finally {
    isLoading.value = false;
  }
}

const columns = [
  { name: "id", label: "ID", field: "id", align: "left", sortable: true },
  { name: "description", label: "Description", field: "description", align: "left", sortable: true },
  { name: "taskName", label: "Task Name", align: "left" },
  { name: "taskOutputParams", label: "Task Output Params", align: "left" },
  { name: "lastModifiedOn", label: "Last Modified", align: "left", field: "lastModifiedOn", sortable: true },
  { name: "download", label: "Download", align: "center" },
];
</script>
