<template>
  <ResourcePicker
    v-model="selectedPlugins"
    :options="pluginOptions"
    resourceType="plugin"
    label="Plugins:"
    :stacked-badges="true"
    @filter="getPlugins"
    @add="(added) => addPlugin(added.value)"
    @remove="(removed) => removePlugin(removed.value)"
    @sync="(plugin) => syncPlugin(plugin.id)"
  />
</template>

<script setup>
import { ref, watch } from "vue";
import * as api from "@/services/dataApi";
import ResourcePicker from "@/components/ResourcePicker.vue";
import * as notify from "../notify";

const selectedPlugins = defineModel("selectedPlugins");
const originalSelectedPluginIds = ref([]);

watch(
  selectedPlugins,
  (newVal) => {
    originalSelectedPluginIds.value = newVal.map((p) => p.id);
  },
  { once: true },
);

const pluginIDsToUpdate = defineModel("pluginIDsToUpdate", { default: () => [] });
const pluginIDsToRemove = defineModel("pluginIDsToRemove", { default: () => [] });

const pluginOptions = ref([]);

async function getPlugins(val = "", update) {
  update(async () => {
    try {
      const res = await api.getData("plugins", {
        search: val,
        rowsPerPage: 0, // get all
        index: 0,
      });
      pluginOptions.value = res.data.data;
    } catch (err) {
      notify.error(err.response.data.message);
    }
  });
}

async function syncPlugin(pluginId) {
  try {
    const res = await api.getItem("plugins", pluginId);
    const currentIndex = selectedPlugins.value.findIndex((plugin) => plugin.id === pluginId);
    if (currentIndex === -1) return;
    const selectionChanged =
      (selectedPlugins.value[currentIndex].snapshotId ?? selectedPlugins.value[currentIndex].snapshot) !==
      res.data.snapshot;
    selectedPlugins.value.splice(currentIndex, 1, res.data);
    if (selectionChanged) pluginIDsToUpdate.value.push(pluginId);
    notify.success(
      selectionChanged
        ? `Selected latest version of '${res.data.name}'. Submit Entrypoint to save.`
        : `Already selected latest version of '${res.data.name}'.`,
    );
  } catch (err) {
    console.warn(err);
    notify.error(err?.response?.data?.message || "Failed to sync plugin");
  }
}

function addPlugin(plugin) {
  pluginIDsToUpdate.value.push(plugin.id);
  pluginIDsToRemove.value = pluginIDsToRemove.value.filter((id) => id !== plugin.id);
}

function removePlugin(plugin) {
  if (originalSelectedPluginIds.value.includes(plugin.id)) {
    pluginIDsToRemove.value.push(plugin.id);
  }
  pluginIDsToUpdate.value = pluginIDsToUpdate.value.filter((id) => id !== plugin.id);
}

function resetOriginalSelectedPlugins() {
  originalSelectedPluginIds.value = selectedPlugins.value.map((plugin) => plugin.id);
}

defineExpose({ resetOriginalSelectedPlugins });
</script>
