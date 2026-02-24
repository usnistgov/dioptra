<template>
  <div class="row items-center justify-between">
    <PageTitle :subtitle="ORIGINAL_PLUGIN?.name" conceptType="plugin" />
    <q-btn
      color="negative"
      icon="sym_o_delete"
      label="Delete Plugin"
      @click="showDeletePluginDialog = true"
    />
  </div>

  <q-expansion-item
    v-model="showMetadata"
    class="shadow-1 overflow-hidden q-mt-lg"
    style="border-radius: 10px; width: 45%"
    header-style="font-size: 22px"
    header-class="bg-primary text-white"
    expand-icon-class="text-white"
  >
    <template #header>
      <q-item-section avatar>
        <q-icon name="terminal" color="white" size="md" />
      </q-item-section>
      <q-item-section>
        <q-item-label>
          {{ showMetadata ? "Hide" : "Show" }} "{{ ORIGINAL_PLUGIN.name }}"
          Metadata
        </q-item-label>
        <q-item-label
          caption
          class="text-white"
          v-if="ORIGINAL_PLUGIN.description"
        >
          {{ truncateString(ORIGINAL_PLUGIN.description, 100) }}
        </q-item-label>
      </q-item-section>
    </template>

    <q-card class="q-pa-md">
      <KeyValueTable :rows="pluginRows" :secondColumnFullWidth="true">
        <template #name>
          <div class="row items-center cursor-pointer">
            {{ name }}
            <q-icon name="edit" size="xs" color="primary" class="q-ml-sm" />
            <q-popup-edit
              v-model="name"
              auto-save
              v-slot="scope"
              :validate="requiredRule"
            >
              <q-input
                v-model.trim="scope.value"
                dense
                autofocus
                counter
                @keyup.enter="scope.set"
                :error="invalidName"
                :error-message="nameError"
                @update:model-value="checkName"
              />
            </q-popup-edit>
          </div>
        </template>

        <template #description>
          <div class="row items-center no-wrap cursor-pointer">
            <div style="white-space: pre-line; overflow-wrap: break-word">
              {{ description || "No description provided" }}
            </div>
            <q-icon name="edit" size="xs" color="primary" class="q-ml-sm" />
            <q-popup-edit
              v-model.trim="description"
              auto-save
              v-slot="scope"
              buttons
            >
              <q-input
                v-model="scope.value"
                dense
                autofocus
                counter
                type="textarea"
              />
            </q-popup-edit>
          </div>
        </template>
      </KeyValueTable>

      <div class="row justify-end q-mt-md q-gutter-x-md">
        <q-btn
          outline
          color="primary"
          label="Revert"
          @click="revertValues"
          :disable="!valuesChanged"
        />
        <q-btn
          color="primary"
          label="Save"
          @click="updatePlugin"
          :disable="!valuesChanged"
        >
          <q-tooltip v-if="!valuesChanged">No changes detected</q-tooltip>
        </q-btn>
      </div>
    </q-card>
  </q-expansion-item>

  <TableComponent
    ref="tableRef"
    :rows="files"
    :columns="fileColumns"
    v-model:selected="selected"
    @open="openTab => (openTab
      ? openWindow.open(`/plugins/${route.params.id}/files/${selected[0].id}`, '_blank')
      : router.push(`/plugins/${route.params.id}/files/${selected[0].id}`)
    )"
    :loading="isLoading"
    @request="getFiles"
    @create="router.push(`/plugins/${route.params.id}/files/new`)"
    @edit="(row) => router.push(`/plugins/${route.params.id}/files/${row.id}`)"
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
    @submit="deleteFile"
    type="Plugin File"
    :name="selected[0]?.filename || ''"
  />
  <DeleteDialog
    v-model="showDeletePluginDialog"
    @submit="deletePlugin"
    type="Plugin"
    :name="name"
  />
  <AssignTagsDialog
    v-model="showTagsDialog"
    :editObj="editObjTags"
    type="files"
    @refreshTable="tableRef.refreshTable()"
  />
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import * as api from "@/services/dataApi";
import * as notify from "../notify";

// Components
import PageTitle from '@/components/PageTitle.vue'
import KeyValueTable from '@/components/KeyValueTable.vue'
import TableComponent from '@/components/table/TableComponent.vue'
import DeleteDialog from '@/dialogs/DeleteDialog.vue'
import AssignTagsDialog from '@/dialogs/AssignTagsDialog.vue'

const openWindow = window
const route = useRoute();
const router = useRouter();
const tableRef = ref(null);

// Plugin State
const name = ref("");
const description = ref("");
const ORIGINAL_PLUGIN = ref({ name: "", description: "" });
const showMetadata = ref(false);

// Files Table State
const files = ref([]);
const isLoading = ref(false);
const selected = ref([]);
const showDeleteDialog = ref(false);
const showDeletePluginDialog = ref(false);
const showTagsDialog = ref(false);
const editObjTags = ref({});

const fileColumns = computed(() => [
  {
    name: "id",
    label: "File ID",
    field: "id",
    align: "left",
    styleType: "icon-id",
    conceptType: "file",
    includeIcon: true,
  },
  {
    name: "filename",
    label: "Filename",
    field: "filename",
    align: "left",
    styleType: "resource-name",
    conceptType: "file",
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
    maxLength: 80,
    sortable: true,
  },
  {
    name: "functionTasks",
    label: "Function Tasks",
    field: (row) => row.tasks?.functions?.length || 0,
    align: "left",
    styleType: "icon-badge",
    conceptType: "task",
    formatLabel: "{label} Tasks",
  },
  {
    name: "artifactTasks",
    label: "Artifact Tasks",
    field: (row) => row.tasks?.artifacts?.length || 0,
    align: "left",
    styleType: "icon-badge",
    conceptType: "task",
    formatLabel: "{label} Tasks",
  },
  {
    name: "tags",
    label: "Tags",
    field: "tags",
    align: "left",
    styleType: "tag-list",
  },
]);

onMounted(() => {
  getPlugin();
});

async function getPlugin() {
  try {
    const res = await api.getItem("plugins", route.params.id);
    name.value = res.data.name;
    description.value = res.data.description;
    ORIGINAL_PLUGIN.value = JSON.parse(JSON.stringify(res.data));
  } catch (err) {
    notify.error("Failed to load plugin details");
  }
}

async function getFiles(pagination) {
  isLoading.value = true;
  try {
    const res = await api.getFiles(route.params.id, pagination);
    files.value = res.data.data;
    tableRef.value.updateTotalRows(res.data.totalNumResults);
  } catch (err) {
    notify.error("Failed to load plugin files");
  } finally {
    isLoading.value = false;
  }
}

// Logic helpers
const valuesChanged = computed(() => {
  return (
    name.value !== ORIGINAL_PLUGIN.value?.name ||
    description.value !== ORIGINAL_PLUGIN.value?.description
  );
});

const pluginRows = [
  { label: "Name", slot: "name" },
  { label: "Description", slot: "description" },
];

const invalidName = ref(false);
const nameError = ref("");

function requiredRule(val) {
  invalidName.value = !val || val.length === 0;
  nameError.value = invalidName.value ? "Name is required" : "";
  return !invalidName.value;
}

function checkName(val) {
  requiredRule(val);
}

function revertValues() {
  name.value = ORIGINAL_PLUGIN.value.name;
  description.value = ORIGINAL_PLUGIN.value.description;
}

async function updatePlugin() {
  try {
    const res = await api.updateItem("plugins", route.params.id, {
      name: name.value,
      description: description.value,
    });
    getPlugin();
    notify.success(`Successfully updated '${res.data.name}'`);
  } catch (err) {
    notify.error(err.response?.data?.message || "Update failed");
  }
}

async function deleteFile() {
  try {
    await api.deleteFile(route.params.id, selected.value[0].id);
    notify.success(`Successfully deleted '${selected.value[0].filename}'`);
    showDeleteDialog.value = false;
    selected.value = [];
    tableRef.value.refreshTable();
  } catch (err) {
    notify.error(err.response?.data?.message || "Delete failed");
  }
}

async function deletePlugin() {
  try {
    await api.deleteItem("plugins", route.params.id);
    notify.success(`Successfully deleted plugin`);
    router.push(`/plugins`);
  } catch (err) {
    notify.error(err.response?.data?.message || "Delete failed");
  }
}

function truncateString(str, limit) {
  if (!str) return "";
  return str.length > limit ? str.slice(0, limit - 3) + "..." : str;
}
</script>
