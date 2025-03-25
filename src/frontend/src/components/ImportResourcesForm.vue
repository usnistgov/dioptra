<template>
  <q-card bordered class="q-pa-lg" style="min-width: 40%;">
    <q-card-section class="text-center">
        <h3 class="q-mt-none q-mb-sm">Import Resources</h3>
        <p>Import resources to this Dioptra deployment from a git repository.</p>
    </q-card-section>
    <q-form @submit="submit()">
      <q-select
        v-model="sourceType"
        :options="sourceTypeOptions"
        label="Source of the resources to import"
      />
      <q-input
        class="q-py-md"
        outlined
        v-if="sourceType.value === 'git'"
        v-model="gitUrl"
        label="git repository URL"
        aria-required="true"
      />
      <q-file
        v-model="archiveFile"
        outlined
        v-if="sourceType.value === 'upload_archive'"
		accept='.tar,.gz,.zip'
        label="File Upload"
      />
      <q-file
        v-model="files"
        outlined
		multiple
		append
		directory
		webkitdirectory
		mozdirectory
        v-if="sourceType.value === 'upload_files'"
        label="File Upload"
      />
      <q-input
        class="q-py-md"
        outlined
        v-model="configPath"
        label="Path to config file (dioptra.toml)"
        aria-required="true"
      />
	  <q-select
        v-model="resolveNameConflictsStrategy"
        :options="resolveNameConflictsStrategyOptions"
        label="Strategy to resolve resource name conflicts"
      />
      <q-btn
        color="primary"
        class="full-width q-mt-md"
        type="submit"
      >
      Import
      </q-btn>
    </q-form>
  </q-card>
</template>

<script setup>
  import { ref } from 'vue';
  import * as api from '@/services/dataApi';
  import { useLoginStore } from '@/stores/LoginStore.ts';
  import * as notify from '../notify';

  const store = useLoginStore()

  const sourceTypeOptions = [
	{label: 'git repository', value: 'git'},
	{label: 'archive file upload (.zip/.tar/.tar.gz)', value: 'upload_archive'},
	{label: 'multi-file upload', value: 'upload_files'},
  ];
  const sourceType = ref(sourceTypeOptions[0]);
  const gitUrl = ref('https://github.com/usnistgov/dioptra.git#dev');
  const archiveFile = ref(null);
  const files = ref(null);
  const configPath = ref('extra/dioptra.toml');
  const resolveNameConflictsStrategyOptions = [
    {label: 'Fail to import', value:'fail'},
    {label: 'Overwrite existing resources', value:'overwrite'},
  ]
  const resolveNameConflictsStrategy = ref(resolveNameConflictsStrategyOptions[0]);

  async function submit() {
    let params = {
      group: 1,
      sourceType: sourceType.value.value,
      gitUrl: sourceType.value.value === "git" ? gitUrl.value : null,
      archiveFile: sourceType.value.value === "upload_archive" ? archiveFile.value : null,
      files: sourceType.value.value == "upload_files" ? files.value : null,
      configPath: configPath.value,
      resolveNameConflictsStrategy: resolveNameConflictsStrategy.value.value,
    };
	console.log(params)
	const importWaitNotification = notify.wait('Importing resources...');
    try {
      const res = await api.importResources(params);
      notify.success(`Import from ${gitUrl.value} successful.`);
    } catch(err) {
      notify.error(err.response.data.message);
    }
	importWaitNotification() //dismiss the wait notification
  }

</script>
