<template>
  <div class="row items-center">
    <PageTitle :title="`Artifact ${route.params.id}`" />
    <q-chip
      v-if="route.params.id !== 'new'"
      class="q-ml-lg"
      :color="`${darkMode ? 'grey-9' : 'grey-3'}`"
      label="View History"
      icon="history"
      @click="store.showRightDrawer = !store.showRightDrawer"
      clickable
    >
      <q-toggle
        v-model="store.showRightDrawer"
        left-label
        color="orange"
      />
    </q-chip>
  </div>
  <h2 class="q-mt-lg">Details</h2>
  <KeyValueTable :rows="rows" :disabled="store.showRightDrawer">
    <template #description="{ }">
      {{ artifact.description }}
      <q-btn icon="edit" round size="sm" color="primary" flat />
      <q-popup-edit v-model="artifact.description" auto-save v-slot="scope">
        <q-input v-model="scope.value" dense autofocus counter @keyup.enter="scope.set" />
      </q-popup-edit>
    </template>
    <template #fileUrl="{ fileUrl }">
      <!-- <a :download="`artifact-${artifact?.id}`" :href="fileUrl">{{fileUrl}}</a> -->
      <q-btn
        :href="fileUrl"
        :download="`artifact-${artifact?.id}`"
        label="Download Artifact"
        color="primary"
        icon="download"
      />
    </template>
    <template #fileSize>
      {{ prettyBytes(artifact.fileSize) }}
    </template>
    <template #job>
      <RouterLink :to="`/jobs/${artifact?.job}`">
        {{ artifact?.job }}
      </RouterLink>
    </template>
    <template #task>
      <q-select
        v-if="!store.showRightDrawer"
        dense
        v-model="selectedArtifactTask"
        :options="artifactTaskOptions"
        option-label="name"
        filled
        label="Artifact Task"
      />
      <div v-else>
        {{ artifact.task.name }}
      </div>
      <div v-if="artifactTaskOptions.length === 0" class="text-caption text-negative">
        The selected plugin has no artifact tasks with matching output param types.  Please select another plugin.
      </div>
    </template>
    <template #outputParams="{ outputParams = [] }">
      <q-chip
        v-for="param in outputParams"
        color="purple"
        text-color="white"
      >
        {{ param.name }}: {{ param.parameterType.name }}
      </q-chip>
    </template>
    <template #plugin="{ plugin = {} }">
      <div :disabled="selectedPlugin">
        <div v-if="Object.keys(plugin).length === 0" class="text-red">
          <q-icon
            name="sym_o_warning"
            size="2.5em"
          />
            The attached plugin has been deleted.
        </div>
        <q-chip
          :label="plugin.name"
          color="secondary"
          text-color="white"
          v-if="Object.keys(plugin).length > 0"
        >
          <q-badge
            v-if="!plugin.latestSnapshot" 
            color="red" 
            label="outdated" 
            rounded
            class="q-ml-xs"
          />
        </q-chip>
        <q-btn
          v-if="!plugin.latestSnapshot && Object.keys(plugin).length > 0"
          round 
          color="red" 
          icon="sync"
          size="sm"
          @click="syncPlugin(plugin.id)"
          :disable="!!selectedPlugin"
        >
          <q-tooltip>
            Sync to latest version of plugin
          </q-tooltip>
        </q-btn>
      </div>
      <q-select
        label="Select Different Plugin"
        v-model="selectedPlugin"
        @filter="getPlugins"
        :options="plugins"
        option-label="name"
        input-debounce="100"
        dense
        filled
        use-input
        clearable
        class="q-mt-sm"
      >
        <template v-slot:option="scope">
          <q-item v-bind="scope.itemProps">
            <q-item-section>
              <q-item-label>{{ scope.opt.name }}</q-item-label>
              <q-item-label caption>Number of Files: {{ scope.opt.files.length }}</q-item-label>
              <q-item-label caption>Number of artifact tasks: {{ countTasks(scope.opt) }}</q-item-label>
            </q-item-section>
          </q-item>
        </template>
      </q-select>
    </template>
  </KeyValueTable>

  <div :class="`float-right q-mb-lg`">
    <q-btn
      outline
      color="primary" 
      label="Cancel"
      class="q-mr-lg cancel-btn"
      @click="router.back()"
    />
    <q-btn  
      @click="submit()" 
      color="primary" 
      label="Save Artifact"
      type="submit"
    />
  </div>
</template>

<script setup>
import PageTitle from '@/components/PageTitle.vue'
import { useRoute, useRouter } from 'vue-router'
import { onMounted, computed, ref, inject, watch } from 'vue'
import * as api from '@/services/dataApi'
import KeyValueTable from '@/components/KeyValueTable.vue'
import * as notify from '../notify'
import { useLoginStore } from '@/stores/LoginStore.ts'

const store = useLoginStore()

const route = useRoute()
const router = useRouter()

const darkMode = inject('darkMode')

onMounted(async() => {
  await getArtifact()
  await getPluginSnapshot()
  await getFileSnapshot()
  if(route.query.snapshotId && !store.showRightDrawer) {
    store.showRightDrawer = true
  }
})

const artifact = ref({
  description: '',
  task: {
    outputParams: []
  }
})

async function getArtifact() {
  try {
    const res = await api.getItem('artifacts', route.params.id)
    artifact.value = res.data
  } catch(err) {
    console.warn(err)
  }
}

async function getPluginSnapshot() {
  try {
    console.log('artifact.value.task = ', artifact.value.task)
    const res = await api.getSnapshot('plugins', artifact.value.task.pluginResourceId, artifact.value.task.pluginResourceSnapshotId)
    console.log('plugin snap = ', res.data)
    artifact.value.plugin = res.data
  } catch(err) {
    console.warn(err)
  }
}

const artifactTaskOptions = ref([])
const selectedArtifactTask = ref()

const artifactOutputTypeIds = computed(() => {
  return artifact.value.task.outputParams.map(param => param.parameterType.id)
})

const plugins = ref([])
const selectedPlugin = ref()

async function getPlugins(val = '', update) {
  update(async () => {
    try {
      const res = await api.getData('plugins', {
        search: val,
        rowsPerPage: 0, // get all
        index: 0
      })
      plugins.value = res.data.data
      plugins.value = plugins.value.filter((plugin) => plugin.id !== artifact.value.plugin.id)
    } catch(err) {
      notify.error(err.response.data.message)
    } 
  })
}

watch(() => selectedPlugin.value, (newVal) => {
  if(newVal) {
    selectedArtifactTask.value = ''
    artifactTaskOptions.value = []
    selectedPlugin.value.files.forEach((file) => {
      file.tasks.artifacts.forEach((task) => {
        const fileTaskOutputTypes = task.outputParams.map((param) => param.parameterType.id)
        if(arraysEqual(fileTaskOutputTypes, artifactOutputTypeIds.value)) {
          artifactTaskOptions.value.push(task)
        }
      })
    })
  } else {
    getFileSnapshot()
  }
})

function countTasks(plugin) {
  let numberOfTasks = 0
  plugin.files.forEach((file) => {
    numberOfTasks += file.tasks.artifacts.length
  })
  return numberOfTasks
}

async function getFileSnapshot() {
  try {
    const res = await api.getFileSnapshot(
      artifact.value.task.pluginResourceId,
      artifact.value.task.pluginFileResourceId,
      artifact.value.task.pluginFileResourceSnapshotId
    )
    console.log('file snap = ', res.data)
    artifactTaskOptions.value = []
    res.data.tasks.artifacts.forEach((task) => {
      const fileTaskOutputTypes = task.outputParams.map((param) => param.parameterType.id)
      if(arraysEqual(fileTaskOutputTypes, artifactOutputTypeIds.value)) {
        artifactTaskOptions.value.push(task)
      }
    })
    selectedArtifactTask.value = artifactTaskOptions.value.find((task) => task.id === artifact.value.task.id)
  } catch(err) {
    console.warn(err)
  }
}

function arraysEqual(a = [], b = []) {
  if (a.length !== b.length) return false
  for (let i = 0; i < a.length; i++) {
    if (a[i] !== b[i]) return false
  }
  return true
}

async function syncPlugin(pluginID) {
  try {
    const res = await api.getItem('plugins', pluginID)
    const latestPlugin = res.data
    console.log('latest plugin = ', latestPlugin)
    // check if latest plugin still has artifact pluginFileResourceId
    const pluginHasFile = latestPlugin?.files?.find((file) =>
      file.id === artifact.value.task.pluginFileResourceId
    )
    if (!pluginHasFile) {
      notify.error(`Latest plugin does not contain a file with id: ${artifact.value.task.pluginFileResourceId}.  Plugin cannot be synced.`)
      return
    }
    artifact.value.plugin = latestPlugin
    notify.success(`Updated to latest snapshot of plugin: ${artifact.value.plugin.name}`)

    // reload task dropdown with tasks from latest file
    const resFile = await api.getFile(pluginID, artifact.value.task.pluginFileResourceId)
    artifactTaskOptions.value = []
    selectedArtifactTask.value = ''
    let originalTaskFound = false
    resFile.data.tasks.artifacts.forEach((task) => {
      const fileTaskOutputTypeIds = task.outputParams.map((param) => param.parameterType.id)
      if(arraysEqual(fileTaskOutputTypeIds, artifactOutputTypeIds.value)) {
        artifactTaskOptions.value.push(task)
        if(task.id === artifact.value.task.id || task.name === artifact.value.task.name) {
          selectedArtifactTask.value = task
          originalTaskFound = true
        }
      }
    })
    if(!originalTaskFound) {
      notify.info(`Task "${artifact.value.task.name}" not found in latest file, please select a new artifact task.`)
    }
  } catch(err) {
    console.warn(err)
  }
}

const rows = computed(() => [
  { label: 'ID', value: artifact.value?.id },
  { label: 'Description', slot: 'description', props: { description: artifact.value?.description }  },
  { label: 'Created On', value: formatDate(artifact.value?.createdOn) },
  { label: 'Last Modified On', value: formatDate(artifact.value?.lastModifiedOn) },
  { label: 'artifactUri', value: artifact.value?.artifactUri },
  { label: 'Download', slot: 'fileUrl', props: { fileUrl: artifact.value?.fileUrl } },
  { label: 'fileSize', slot: 'fileSize' },
  { label: 'Job ID', slot: 'job' },
  { label: 'isDir', value: artifact.value?.isDir },
  { label: 'Artifact Task', slot: 'task' },
  { label: 'Output Params', slot: 'outputParams', props: { outputParams: artifact.value?.task?.outputParams }  },
  { label: 'Plugin', slot: 'plugin', props: { plugin: artifact.value?.plugin }  },
])

function formatDate(dateString) {
  const options = { year: '2-digit', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: true }
  return new Date(dateString).toLocaleString('en-US', options)
}

async function submit() {
  try {
    const res = await api.updateItem('artifacts', route.params.id, {
      description: artifact.value.description,
      pluginSnapshotId: selectedPlugin.value ? selectedPlugin.value.snapshot : artifact.value.plugin.snapshot,
      taskId: selectedArtifactTask.value.id
    })
    notify.success(`Successfully updated artifact '${route.params.id}'`)
    router.push(`/artifacts`)
  } catch(err) {
    notify.error(err.response.data.message)
  }
}

watch(() => store.selectedSnapshot, async (newVal) => {
  if(newVal) {
    console.log('newVal = ', newVal)
    artifact.value = newVal
    await getPluginSnapshot()
  } else {
    await getArtifact()
    await getPluginSnapshot()
  }
})

function prettyBytes(num) {
  if (typeof num !== 'number' || isNaN(num)) {
    return 'N/A'
  }
  const neg = num < 0;
  num = Math.abs(num);
  const units = ['Bytes', 'kB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
  if (num < 1) return (neg ? '-' : '') + num + ' B'

  const exponent = Math.min(
    Math.floor(Math.log10(num) / 3),
    units.length - 1
  )

  const value = (num / Math.pow(1000, exponent)).toFixed(2)
  return (neg ? '-' : '') + value + ' ' + units[exponent]
}

</script>