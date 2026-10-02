<template>
  <DialogComponent
    v-model="showDialog"
    :hideDraftBtn="true"
    @emitSubmit="emitAddOrEdit"
  >
    <template #title>
      <label id="modalTitle">
        {{ editArtifact ? "Edit Artifact" : "Register Artifact" }}
      </label>
    </template>
    <q-input
      v-if="!editArtifact"
      id="uri"
      v-model="uri"
      class="q-mb-xs"
      outlined
      dense
      autofocus
      :rules="[requiredRule]"
    >
      <template #before>
        <label
          for="uri"
          class="field-label"
          >URI:</label
        >
      </template>
    </q-input>
    <q-input
      id="description"
      v-model.trim="description"
      outlined
      type="textarea"
      dense
    >
      <template #before>
        <label
          for="description"
          class="field-label"
          >Description:</label
        >
      </template>
    </q-input>
  </DialogComponent>
</template>

<script setup>
import { ref, watch } from "vue";
import DialogComponent from "./DialogComponent.vue";
import * as api from "@/services/dataApi";
import * as notify from "../notify";

const props = defineProps(["editArtifact", "expId", "jobId"]);
const emit = defineEmits(["addArtifact", "updateArtifact"]);

function requiredRule(val) {
  return !!val || "This field is required";
}

const showDialog = defineModel();

const uri = ref("");
const description = ref("");

watch(showDialog, (newVal) => {
  if (newVal) {
    uri.value = props.editArtifact.uri;
    description.value = props.editArtifact.description;
    // group.value = props.editArtifact.group
  } else {
    uri.value = "";
    description.value = "";
  }
});

function emitAddOrEdit() {
  if (props.editArtifact) {
    emit("updateArtifact", props.editArtifact.id, description.value);
  } else {
    addArtifact();
  }
}

async function addArtifact() {
  try {
    await api.addArtifact(props.expId, props.jobId, {
      uri: uri.value,
      description: description.value,
    });
    showDialog.value = false;
    notify.success(`Successfully created artifact for Job ID: ${props.jobId}`);
  } catch (err) {
    notify.error(err.response.data.message);
  }
}
</script>
