<template>
  <q-dialog v-model="showDialog">
    <q-card style="min-width: 35%">
      <q-card-section class="bg-primary text-white text-h6">
        <div class="text-h6">
          Assign {{ pluginType === "plugins" ? "Plugins" : "Artifact Plugins" }} for '{{ editObj.name }}'
        </div>
      </q-card-section>
      <q-card-section>
        <AssignPluginsDropdown
          v-model:selectedPlugins="selectedPlugins"
          v-model:pluginIDsToUpdate="pluginIDsToUpdate"
          v-model:pluginIDsToRemove="pluginIDsToRemove"
        />
      </q-card-section>
      <q-separator />
      <q-card-actions align="right">
        <q-btn
          v-close-popup
          outline
          color="primary cancel-btn"
          label="Cancel"
          class="q-mr-xs"
        />
        <q-btn
          label="Confirm"
          color="primary"
          type="submit"
          @click="submitPlugins()"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup>
import { ref, onUpdated } from "vue";
import * as api from "@/services/dataApi";
import * as notify from "../notify";
import AssignPluginsDropdown from "@/components/AssignPluginsDropdown.vue";

const props = defineProps(["editObj", "pluginType"]);
const emit = defineEmits(["refreshTable"]);

const showDialog = defineModel();

onUpdated(() => {
  pluginIDsToUpdate.value = [];
  pluginIDsToRemove.value = [];
  if (props.pluginType === "plugins") {
    selectedPlugins.value = JSON.parse(JSON.stringify(props.editObj.plugins));
  } else {
    selectedPlugins.value = JSON.parse(JSON.stringify(props.editObj.artifactPlugins));
  }
});

const selectedPlugins = ref([]);
const pluginIDsToUpdate = ref([]);
const pluginIDsToRemove = ref([]);

async function submitPlugins() {
  try {
    if (pluginIDsToUpdate.value.length > 0) {
      await api.addPluginsToEntrypoint(props.editObj.id, pluginIDsToUpdate.value, props.pluginType);
    }
    for (const pluginId of pluginIDsToRemove.value) {
      await api.removePluginFromEntrypoint(props.editObj.id, pluginId, props.pluginType);
    }
    notify.success(`Successfully updated plugins for '${props.editObj.name}'`);
    emit("refreshTable", props.editObj.id);
    showDialog.value = false;
  } catch (err) {
    notify.error(err.response.data.message);
  }
}
</script>
