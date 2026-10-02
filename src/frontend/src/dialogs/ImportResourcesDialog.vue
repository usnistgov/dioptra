<template>
  <q-dialog
    v-model="showDialog"
    aria-labelledby="modalTitle"
  >
    <q-card
      flat
      :style="{ 'min-width': isExtraSmall ? '95%' : isMobile ? '60%' : isMedium ? '40%' : '30%' }"
    >
      <q-card-section class="bg-primary text-white q-mb-md">
        <div class="text-h6 row justify-between">Import Resources</div>
      </q-card-section>

      <q-form @submit="submit()">
        <q-card-section>
          <q-btn-toggle
            v-model="sourceType"
            toggle-color="primary"
            :options="sourceTypeOptions"
          >
            <template #git
              ><q-icon
                left
                name="fa-brands fa-github"
                size="sm"
              />Git Repo</template
            >
            <template #upload_archive
              ><q-icon
                left
                name="folder_zip"
                size="sm"
              />Upload Archive</template
            >
            <template #upload_files
              ><q-icon
                left
                name="folder"
                size="sm"
              />Upload Directory</template
            >
          </q-btn-toggle>
        </q-card-section>

        <q-card-section>
          <q-input
            v-if="sourceType === 'git'"
            v-model="gitUrl"
            outlined
            label="git repository URL"
          />
          <q-file
            v-if="sourceType === 'upload_archive'"
            v-model="archiveFile"
            outlined
            accept=".tar,.gz"
            label="Archive File Upload (.tar/.tar.gz)"
          />
          <q-file
            v-if="sourceType === 'upload_files'"
            v-model="files"
            outlined
            multiple
            append
            directory
            webkitdirectory
            mozdirectory
            label="Directory Upload"
          />
          <br />
          <q-select
            v-model="group"
            outlined
            emit-value
            map-options
            :options="store.groups"
            option-label="name"
            option-value="id"
            label="Group"
          />
          <q-input
            v-model="configPath"
            outlined
            class="q-py-md"
            label="Path to config file (dioptra.toml)"
          />
          <q-select
            v-model="conflictStrat"
            outlined
            emit-value
            map-options
            :options="conflictStratOptions"
            label="Resource name conflict resolution strategy"
          />
        </q-card-section>

        <q-separator />

        <q-card-actions
          align="right"
          class="text-primary"
        >
          <q-btn
            v-close-popup
            outline
            color="primary cancel-btn"
            label="Cancel"
            class="q-mr-xs"
          />
          <q-btn
            color="primary"
            type="submit"
          >
            Import
          </q-btn>
        </q-card-actions>
      </q-form>
    </q-card>
  </q-dialog>
</template>

<script setup>
import { inject, ref, watch } from "vue";
import * as api from "@/services/dataApi";
import { useLoginStore } from "@/stores/LoginStore.ts";
import * as notify from "../notify";

const store = useLoginStore();

const showDialog = defineModel();

const isMedium = inject("isMedium");
const isMobile = inject("isMobile");
const isExtraSmall = inject("isExtraSmall");

const gitUrlDefault = "https://github.com/usnistgov/dioptra.git#main";
const configPathDefault = "extra/dioptra.toml";
const conflictStratDefault = "fail";

const sourceTypeOptions = [
  { slot: "git", value: "git" },
  { slot: "upload_archive", value: "upload_archive" },
  { slot: "upload_files", value: "upload_files" },
];
const sourceType = ref(sourceTypeOptions[0].value);
const gitUrl = ref(gitUrlDefault);
const archiveFile = ref(null);
const files = ref(null);
const group = ref(store.loggedInGroup.id);
const conflictStratOptions = [
  { value: "fail", label: "Fail: if any imported resources have the same name, the import will fail" },
  { value: "update", label: "Update: naively match resources by name and update them as defined in import config" },
  {
    value: "overwrite",
    label: "Overwrite: delete any conflicing resources and create new resouces as defined in import config",
  },
];
const configPath = ref(conflictStratOptions[0]);
const conflictStrat = ref(conflictStratDefault);

watch(showDialog, () => {
  if (!group.value) {
    group.value = store.loggedInGroup.id;
  }
  gitUrl.value = gitUrlDefault;
  configPath.value = configPathDefault;
  conflictStrat.value = conflictStratDefault;
  archiveFile.value = null;
  files.value = null;
});

async function submit() {
  const params = {
    group: group.value,
    sourceType: sourceType.value,
    gitUrl: sourceType.value === "git" ? gitUrl.value : null,
    archiveFile: sourceType.value === "upload_archive" ? archiveFile.value : null,
    files: sourceType.value == "upload_files" ? files.value : null,
    configPath: configPath.value,
    resolveNameConflictsStrategy: conflictStrat.value,
  };
  const importWaitNotification = notify.wait("Importing resources...");
  try {
    await api.importResources(params);
    if (sourceType.value == "git") {
      notify.success(`Import from git repository '${gitUrl.value}' successful.`);
    } else if (sourceType.value == "upload_archive") {
      notify.success(`Import from archive file '${archiveFile.value.name}' successful.`);
    } else if (sourceType.value == "upload_files") {
      notify.success(`Import from directory successful.`);
    }
    showDialog.value = false;
  } catch (err) {
    notify.error(err.response.data.message);
  }
  importWaitNotification(); //dismiss the wait notification
}
</script>
