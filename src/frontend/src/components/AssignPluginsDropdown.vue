<template>
  <q-select
    outlined
    dense
    v-model="selectedPlugins"
    use-input
    use-chips
    multiple
    option-label="name"
    option-value="id"
    input-debounce="100"
    :options="pluginOptions"
    @filter="getPlugins"
    @add="(added) => addPlugin(added.value)"
    @remove="(removed) => removePlugin(removed.value)"
  >
    <!-- <template v-slot:before>
      <div class="field-label">Attached Plugins:</div>
    </template> -->

    <template v-slot:selected>
      <div class="q-pa-xs full-width">
        <div
          v-for="(plugin, i) in selectedPlugins"
          :key="plugin.id"
          class="q-mt-sm"
        >
          <div
            class="row items-center no-wrap bg-white q-pa-none shadow-1"
            style="
              border-radius: 4px;
              border: 1px solid #eeeeee;
              width: fit-content;
              max-width: 100%;
            "
          >
            <q-chip
              removable
              :color="pluginStyle.color"
              :icon="pluginStyle.icon"
              text-color="white"
              size="sm"
              outline
              square
              class="text-weight-bold q-py-sm q-ma-none no-border"
              @remove="
                selectedPlugins.splice(i, 1);
                removePlugin(plugin);
              "
            >
              <span
                class="font-mono ellipsis q-pr-md"
                style="font-size: 12px; font-weight: 500"
              >
                {{ plugin.name }}
              </span>

              <q-tooltip>ID: {{ plugin.id }}</q-tooltip>
            </q-chip>

            <div
              v-if="!plugin.latestSnapshot"
              class="row items-center no-wrap q-pr-sm"
            >
              <div
                style="
                  height: 14px;
                  width: 1px;
                  background-color: #eee;
                  margin: 0 4px;
                "
              ></div>

              <q-icon name="warning" color="orange" size="xs">
                <q-tooltip>Plugin is out of date</q-tooltip>
              </q-icon>

              <q-btn
                flat
                round
                size="xs"
                color="red"
                icon="sync"
                class="q-ml-xs"
                @click.stop="syncPlugin(plugin.id, i)"
              >
                <q-tooltip>Sync to latest version</q-tooltip>
              </q-btn>
            </div>
          </div>
        </div>
      </div>
    </template>
  </q-select>
</template>

<script setup>
import { ref, watch, computed } from "vue";
import * as api from "@/services/dataApi";
import { getConceptStyle } from "@/constants/tableStyles";

const pluginStyle = computed(() => getConceptStyle("plugin"));
const selectedPlugins = defineModel("selectedPlugins");
const pluginIDsToUpdate = defineModel("pluginIDsToUpdate");
const pluginIDsToRemove = defineModel("pluginIDsToRemove");
const originalSelectedPluginIds = ref([]);
const pluginOptions = ref([]);

watch(
  selectedPlugins,
  (newVal) => {
    if (originalSelectedPluginIds.value.length === 0 && newVal?.length > 0) {
      originalSelectedPluginIds.value = newVal.map((p) => p.id);
    }
  },
  { immediate: true },
);

async function getPlugins(val = "", update) {
  update(async () => {
    try {
      const res = await api.getData("plugins", {
        search: val,
        rowsPerPage: 0,
        index: 0,
      });
      pluginOptions.value = res.data.data;
    } catch (err) {
      console.warn(err);
    }
  });
}

async function syncPlugin(pluginId, index) {
  try {
    const res = await api.getItem("plugins", pluginId);
    selectedPlugins.value.splice(index, 1, res.data);
    pluginIDsToUpdate.value.push(pluginId);
  } catch (err) {
    console.warn(err);
  }
}

function addPlugin(plugin) {
  pluginIDsToUpdate.value.push(plugin.id);
  pluginIDsToRemove.value = pluginIDsToRemove.value.filter(
    (id) => id !== plugin.id,
  );
}

function removePlugin(plugin) {
  if (originalSelectedPluginIds.value.includes(plugin.id)) {
    pluginIDsToRemove.value.push(plugin.id);
  }
  pluginIDsToUpdate.value = pluginIDsToUpdate.value.filter(
    (id) => id !== plugin.id,
  );
}
</script>

<style scoped>
.field-label {
  font-weight: 500;
  font-size: 14px;
  color: rgba(0, 0, 0, 0.6);
  margin-right: 8px;
}
</style>
