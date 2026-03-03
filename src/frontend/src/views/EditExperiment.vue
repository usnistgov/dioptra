<template>
  <div class="row items-center justify-between">
    <div class="row items-center">
      <PageTitle
        :subtitle="pageSubtitle"
        conceptType="experiment"
      />
      <q-chip
        v-if="route.params.id !== 'new'"
        class="q-ml-lg"
        :color="`${darkMode ? 'grey-9' : ''}`"
        label="View History"
        icon="history"
        @click="store.showRightDrawer = !store.showRightDrawer"
        clickable
      >
        <q-toggle v-model="store.showRightDrawer" left-label color="orange" />
      </q-chip>
    </div>
    <q-btn
      v-if="route.params.id !== 'new'"
      :color="history ? 'red-3' : 'negative'"
      icon="sym_o_delete"
      label="Delete Experiment"
      @click="showDeleteDialog = true"
      :disable="history"
    />
  </div>

  <q-expansion-item
    v-model="showMetadata"
    class="shadow-1 overflow-hidden q-mt-lg"
    style="border-radius: 10px; min-width:400px; width: 60%; max-width: 700px"
    header-style="font-size: 22px"
    header-class="bg-primary text-white"
    expand-icon-class="text-white"
  >
    <template #header>
      <q-item-section avatar>
        <q-icon :name="styles.icon"  color="white" size="md" /> 
      </q-item-section>
      <q-item-section>
        <q-item-label>
          {{ showMetadata ? "Hide" : "Show" }} "{{ ORIGINAL_EXPERIMENT.name }}"
          Metadata
        </q-item-label>
        <q-item-label
          caption
          class="text-white"
          v-if="ORIGINAL_EXPERIMENT.description"
        >
          {{ truncateString(ORIGINAL_EXPERIMENT.description, 100) }}
        </q-item-label>
      </q-item-section>
    </template>


  <q-card class="q-pa-md" :class="history ? 'disabled' : ''">
    <KeyValueTable
      :rows="metadataRows"
      :style="{ pointerEvents: history ? 'auto' : 'auto' }"
      :secondColumnFullWidth="true"
    >
      <template #name="{}">
        <div class="row items-center cursor-pointer">
          <div class="text-h6 text-weight-bold text-primary">
            {{ experiment?.name }}
          </div>
          <q-btn icon="edit" round size="sm" color="primary" flat class="q-ml-sm" />
          
          <q-popup-edit
            v-model="experiment.name"
            auto-save
            v-slot="scope"
            :validate="requiredRule"
          >
            <q-input
              v-model="scope.value"
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

      <template #group="{}">
        <ResourcePicker

          v-model="experiment.group"
          type="group"
          :options="store.groups"
          option-value="id"
          @filter="getGroups"
          :disable="history"
          input-debounce="300"
        />
      </template>

      <template #description="{}">
        <div class="row items-center no-wrap cursor-pointer">
          <div
            class="text-body1 text-grey-8"
            style="white-space: pre-line; overflow-wrap: break-word; line-height: 1.5;"
            :class="{ 'text-grey-5': darkMode }"
          >
            {{ experiment?.description || "No description provided." }}
          </div>
          <q-btn icon="edit" round size="sm" color="grey" flat class="q-ml-xs" />

          <q-popup-edit 
            v-model="experiment.description" 
            auto-save 
            v-slot="scope" 
            buttons
          >
            <q-input
              v-model="scope.value"
              type="textarea"
              dense
              autofocus
              counter
              @keyup.enter.stop
            />
          </q-popup-edit>
        </div>
      </template>

      <template #entrypoints="{}">
        <ResourcePicker
          v-if="!history"
          v-model="experiment.entrypoints"
          type="entrypoint"
          chip-square chip-outline
          :options="entrypoints"
          option-value="id"
          @filter="getEntrypoints"
          :disable="history"
          input-debounce="300"
        />
        </template>

          <div class="row items-center" v-if="history">
            <q-icon
              name="sym_o_info"
              size="2.5em"
              color="grey"
              class="q-mr-sm"
            />
            <div style="flex: 1; white-space: normal; word-break: break-word">
              Entrypoints are not yet available in Experiment snapshots
            </div>
          </div>

      </KeyValueTable>
      <div class="float-right q-my-sm">
        <q-btn
          outline
          color="primary"
          label="Revert"
          class="q-mr-lg cancel-btn"
          @click="revertValues"
          :disable="!valuesChanged"
        />

        <q-btn
          label="Save"
          color="primary"
          @click="updateExperiment"
          :disable="!valuesChanged"
          style="min-width: 100px"
        >
          <q-tooltip v-if="!valuesChanged">
            No changes detected — nothing to save
          </q-tooltip>
        </q-btn>
      </div>
    </q-card>
  </q-expansion-item>

  <JobsView embedded />

  <DeleteDialog
    v-model="showDeleteDialog"
    @submit="deleteExperiment"
    type="Experiment"
    :name="experiment.name"
  />
</template>

<script setup>
import { ref, inject, computed, watch, onMounted } from "vue";
import { useLoginStore } from "@/stores/LoginStore.ts";
import { useRouter, useRoute } from "vue-router";
import * as api from "@/services/dataApi";
import * as notify from "../notify";
import PageTitle from "@/components/PageTitle.vue";
import DeleteDialog from "@/dialogs/DeleteDialog.vue";
import KeyValueTable from "@/components/KeyValueTable.vue";
import JobsView from "./JobsView.vue";
import ResourcePicker from "@/components/ResourcePicker.vue";
import { getConceptStyle } from "@/constants/tableStyles";

const route = useRoute();

const router = useRouter();

const store = useLoginStore();
const isMobile = inject("isMobile");
const isMedium = inject("isMedium");
const darkMode = inject("darkMode");

const styles = computed(() => {
  return getConceptStyle('experiment') || { color: "grey-7", icon: "help" };
});

const experiment = ref({
  name: "",
  group: store.loggedInGroup.id,
  description: "",
  entrypoints: [],
});
const ORIGINAL_EXPERIMENT = ref({
  name: "",
  group: store.loggedInGroup.id,
  description: "",
  entrypoints: [],
});

const history = computed(() => {
  return store.showRightDrawer;
});

const pageSubtitle = computed(() => {
  if (route.params.id === 'new') {
    return 'Create Experiment'
  }
  if (store.showRightDrawer && store.selectedSnapshot) {
    return `${experiment.value?.name || 'Loading...'} (Snapshot ${store.selectedSnapshot.snapshot})`
  }
  if (route.query.snapshotId && store.showRightDrawer) {
    return `${experiment.value?.name || 'Loading...'} (Snapshot ${route.query.snapshotId})`
  }
  return ORIGINAL_EXPERIMENT.value?.name || experiment.value?.name || 'Loading...'
})

onMounted(() => {
  if (route.query.snapshotId && !store.showRightDrawer) {
    store.showRightDrawer = true
  }
  
  getExperiment();
});

async function getExperiment() {
  try {
    const res = await api.getItem("experiments", route.params.id);
    experiment.value = res.data;
    ORIGINAL_EXPERIMENT.value = JSON.parse(JSON.stringify(experiment.value));
    // copyAtEditStart.value = JSON.parse(JSON.stringify({
    //   name: res.data.name,
    //   group: res.data.group,
    //   description: res.data.description,
    //   entrypoints: res.data.entrypoints,
    // }))
  } catch (err) {
    console.log("err = ", err);
    notify.error(err.response.data.message);
  }
}

const metadataRows = computed(() => [
  { label: "Name", slot: "name" },
  { label: "Group", slot: "group" },
  { label: "Description", slot: "description" },
  { label: "Entrypoints", slot: "entrypoints" },
]);

const invalidName = ref(false);
const nameError = ref("");

function requiredRule(val) {
  if (!val || val.length === 0) {
    invalidName.value = true;
    nameError.value = "Name is required";
    return false;
  }
  invalidName.value = false;
  nameError.value = "";
  return true;
}

function checkName(val) {
  if (val.length === 0) {
    invalidName.value = true;
    nameError.value = "Name is required";
  } else {
    invalidName.value = false;
    nameError.value = "";
  }
}

const entrypoints = ref([]);

async function getEntrypoints(val = "", update) {
  update(async () => {
    try {
      const res = await api.getData("entrypoints", {
        search: val,
        rowsPerPage: 0, // get all
        index: 0,
      });
      entrypoints.value = res.data.data;
    } catch (err) {
      notify.error(err.response.data.message);
    }
  });
}

const valuesChanged = computed(() => {
  return (
    JSON.stringify(ORIGINAL_EXPERIMENT.value) !==
    JSON.stringify(experiment.value)
  );
});

function revertValues() {
  experiment.value = JSON.parse(JSON.stringify(ORIGINAL_EXPERIMENT.value));
}

async function updateExperiment() {
  experiment.value.entrypoints.forEach((entrypoint, index, array) => {
    if (typeof entrypoint === "object") {
      array[index] = entrypoint.id;
    }
  });
  try {
    const res = await api.updateItem("experiments", route.params.id, {
      name: experiment.value.name,
      description: experiment.value.description,
      entrypoints: experiment.value.entrypoints,
    });
    getExperiment();
    notify.success(`Successfully updated '${res.data.name}'`);
  } catch (err) {
    notify.error(err.response.data.message);
  }
}

watch(
  () => history.value,
  (newVal) => {
    if (newVal) {
      showMetadata.value = true;
    }
  },
);

watch(
  () => store.selectedSnapshot,
  (newVal) => {
    if (newVal) {
      experiment.value = newVal;
    } else {
      getExperiment();
    }
  },
);

const showDeleteDialog = ref(false);

async function deleteExperiment() {
  try {
    await api.deleteItem("experiments", experiment.value.id);
    notify.success(`Successfully deleted '${experiment.value.name}'`);
    router.push(`/experiments`);
  } catch (err) {
    notify.error(err.response.data.message);
  }
}

const showMetadata = ref(false);

function truncateString(str, limit) {
  if (!str) return "";
  if (str?.length < limit) return str;
  return str?.slice(0, limit > 3 ? limit - 3 : limit) + "...";
}
</script>
