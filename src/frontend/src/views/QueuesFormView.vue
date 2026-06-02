<template>
  <div class="row items-center justify-between">
    <div class="row items-center">
      <PageTitle
        :title="route.params.id === 'new' ? 'Create Queue' : copyAtEditStart?.name"
        resourceType="queue"
        :deleted="queue.deleted"
      />
      <q-chip
        v-if="route.params.id !== 'new'"
        class="q-ml-md"
        :color="`${darkMode ? 'grey-9' : ''}`"
        label="View History"
        icon="history"
        clickable
        @click="store.showRightDrawer = !store.showRightDrawer"
      >
        <q-toggle
          v-model="store.showRightDrawer"
          left-label
          color="orange"
        />
      </q-chip>
    </div>
    <div>
      <q-btn
        v-if="route.params.id !== 'new' && !queue.deleted"
        :color="history ? 'red-3' : 'negative'"
        icon="sym_o_delete"
        label="Delete Queue"
        :disable="history"
        @click="showDeleteDialog = true"
      />
    </div>
  </div>
  <q-banner
    v-if="queue.deleted"
    dense
    class="text-white bg-red q-mt-md"
  >
    <template #avatar>
      <q-icon name="error" />
    </template>
    <span class="text-bold">This Queue has been deleted. Info is read only.</span>
  </q-banner>
  <div :style="{ width: isMobile ? '100%' : isMedium ? '60%' : '50%' }">
    <fieldset class="q-mt-lg">
      <legend>Basic Info</legend>
      <q-form
        ref="form"
        class="q-ma-lg"
      >
        <q-input
          v-model.trim="queue.name"
          outlined
          dense
          :rules="[requiredRule]"
          aria-required="true"
          class="q-mb-sm"
          :disable="queue.deleted || history"
        >
          <template #before>
            <label :class="`field-label`">Name:</label>
          </template>
        </q-input>
        <q-select
          id="queueGroup"
          v-model="queue.group"
          outlined
          :options="store.groups"
          option-label="name"
          option-value="id"
          emit-value
          map-options
          dense
          :rules="[requiredRule]"
          class="q-mb-sm"
          :disable="queue.deleted || history"
        >
          <template #before>
            <label
              for="queueGroup"
              class="field-label"
              >Group:</label
            >
          </template>
        </q-select>
        <q-input
          id="queueDescription"
          v-model="queue.description"
          outlined
          type="textarea"
          dense
          :disable="queue.deleted || history"
        >
          <template #before>
            <label
              for="queueDescription"
              class="field-label"
              >Description:</label
            >
          </template>
        </q-input>
      </q-form>
    </fieldset>

    <div class="q-mt-lg">
      <q-btn
        v-if="route.params.id === 'new'"
        label="Save As Draft"
        color="secondary"
        :disable="!valuesChangedFromEditStart || history"
        @click="submitDraft()"
      />
      <div class="float-right">
        <q-btn
          outline
          color="primary"
          label="Cancel"
          class="q-mr-lg cancel-btn"
          :disable="history"
          @click="
            confirmLeave = true;
            store.initialPage ? router.push('/queues') : router.back();
          "
        />
        <q-btn
          color="primary"
          label="Submit"
          :disable="!valuesChangedFromEditStart || history"
          @click="submit()"
        >
          <q-tooltip v-if="!valuesChangedFromEditStart"> No changes detected — nothing to save </q-tooltip>
        </q-btn>
      </div>
    </div>
  </div>

  <ReturnToFormDialog
    v-model="showReturnDialog"
    @cancel="clearForm"
  />
  <DeleteDialog
    v-model="showDeleteDialog"
    type="Queue"
    :name="copyAtEditStart?.name"
    @submit="deleteQueue()"
  />
</template>

<script setup>
import PageTitle from "@/components/PageTitle.vue";
import { ref, computed, onMounted, inject, watch } from "vue";
import { useLoginStore } from "@/stores/LoginStore.ts";
import { useRoute, useRouter, onBeforeRouteLeave } from "vue-router";
import * as api from "@/services/dataApi";
import * as notify from "../notify";
import ReturnToFormDialog from "@/dialogs/ReturnToFormDialog.vue";
import DeleteDialog from "@/dialogs/DeleteDialog.vue";

const store = useLoginStore();
const route = useRoute();
const router = useRouter();
const isMobile = inject("isMobile");
const isMedium = inject("isMedium");
const darkMode = inject("darkMode");

const queue = ref({
  name: "",
  group: store.loggedInGroup.id,
  description: "",
});

const copyAtEditStart = ref();

const valuesChangedFromEditStart = computed(() => {
  for (const key in copyAtEditStart.value) {
    if (JSON.stringify(copyAtEditStart.value[key]) !== JSON.stringify(queue.value[key])) {
      return true;
    }
  }
  return false;
});

onMounted(async () => {
  if (route.query.snapshotId && !store.showRightDrawer) {
    store.showRightDrawer = true;
  } else if (store.savedForms?.queue && route.params.id === "new") {
    copyAtEditStart.value = JSON.parse(JSON.stringify(queue.value));
    showReturnDialog.value = true;
    queue.value = store.savedForms.queue;
  } else if (route.params.id === "new") {
    copyAtEditStart.value = JSON.parse(JSON.stringify(queue.value));
  } else if (route.params.id !== "new") {
    await getQueue();
    copyAtEditStart.value = JSON.parse(JSON.stringify(queue.value));
  }
});

async function getQueue() {
  try {
    const res = await api.getItem("queues", route.params.id);
    queue.value = res.data;
  } catch (err) {
    notify.error(err.response.data.message);
  }
}

function requiredRule(val) {
  return !!val || "This field is required";
}

const form = ref(null);

function submit() {
  form.value.validate().then((success) => {
    if (!success) return;
    confirmLeave.value = true;
    if (route.params.id === "new") {
      createQueue();
    } else if (route.params.id !== "new") {
      updateQueue();
    }
  });
}

function submitDraft() {
  form.value.validate().then((success) => {
    if (!success) return;
    confirmLeave.value = true;
    if (route.params.id === "new") {
      createDraft();
    }
  });
}

async function createQueue() {
  try {
    const res = await api.addItem("queues", queue.value);
    notify.success(`Successfully created '${res.data.name}'`);
    store.savedForms.queue = null;
    router.push("/queues");
  } catch (err) {
    notify.error(err.response.data.message);
  }
}

async function createDraft() {
  try {
    const params = {
      name: queue.value.name,
      description: queue.value.description,
      group: queue.value.group,
    };
    const res = await api.addDraft("queues", params);
    notify.success(`Successfully created '${res.data.payload.name}'`);
    store.savedForms.queue = null;
    router.push("/queues");
  } catch (err) {
    notify.error(err.response.data.message);
  }
}

async function updateQueue() {
  try {
    const res = await api.updateItem("queues", route.params.id, {
      name: queue.value.name,
      description: queue.value.description,
    });
    notify.success(`Successfully updated '${res.data.name}'`);
    router.push("/queues");
  } catch (err) {
    notify.error(err.response.data.message);
  }
}

const showReturnDialog = ref(false);
const confirmLeave = ref(false);
const toPath = ref();

onBeforeRouteLeave((to) => {
  toPath.value = to.path;
  if (confirmLeave.value) {
    return true;
  } else if (valuesChangedFromEditStart.value && route.params.id === "new") {
    store.savedForms.queue = queue.value;
    return true;
  } else {
    store.savedForms.queue = null;
    return true;
  }
});

function clearForm() {
  queue.value = {
    name: "",
    group: store.loggedInGroup.id,
    description: "",
  };
  form.value.reset();
  store.savedForms.queue = null;
}

const history = computed(() => {
  return store.showRightDrawer;
});

watch(
  () => store.selectedSnapshot,
  (q) => {
    if (q) {
      queue.value = q;
      copyAtEditStart.value = queue.value;
    } else {
      getQueue();
    }
  },
);

const showDeleteDialog = ref(false);

async function deleteQueue() {
  try {
    await api.deleteItem("queues", route.params.id);
    notify.success(`Successfully deleted '${copyAtEditStart.value.name}'`);
    store.savedForms.queue = null;
    showDeleteDialog.value = false;
    router.push("/queues");
  } catch (err) {
    notify.error(err.response.data.message);
  }
}
</script>
