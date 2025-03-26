<template>
  <q-card bordered class="q-pa-lg" style="min-width: 40%;">
    <q-card-section class="text-center">
        <h3 class="q-mt-none q-mb-sm">Import Resources</h3>
        <p>Import resources to this Dioptra deployment from a git repository.</p>
    </q-card-section>
    <q-form @submit="submit()">
      <q-input
        class="q-py-md"
        outlined
        label="git repository URL"
        :rules="[requiredRule]"
        v-model="gitUrl"
        aria-required="true"
      />
	  <q-select
        v-model="resolveNameConflictsStrategy"
        :options="resolveNameConflictsStrategyOptions"
        label="Resource conflict resolution strategy"
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

  const requiredRule = (val) => (val && val.length > 0) || "This field is required";

  const gitUrl = ref('https://github.com/usnistgov/dioptra.git#dev');
  const resolveNameConflictsStrategy = ref('fail');
  const resolveNameConflictsStrategyOptions = ['fail', 'overwrite'];

  async function submit() {
    let params = {
      group: 1,
      sourceType: "git",
      gitUrl: gitUrl.value,
      files: [],
      archiveFile: "",
      configPath: "extra/dioptra.toml",
      resolveNameConflictsStrategy: resolveNameConflictsStrategy.value,
    };
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
