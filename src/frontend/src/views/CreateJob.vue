<template>
  <PageTitle 
    title="Create Job"
  />
  <div :class="`row q-my-lg`">
    <div :class="`${isMobile ? 'col-12' : 'col-5'} q-mr-xl`">
      <fieldset>
        <legend>Basic Info</legend>
        <div class="q-ma-lg">
          <q-form ref="basicInfoForm" greedy>
            <q-select
              outlined
              dense
              v-model="job.experiment"
              clearable
              option-label="name"
              input-debounce="100"
              :options="experiments"
              @filter="getExperiments"
              :rules="[requiredRule]"
              :disable="Object.hasOwn(route.params, 'id') || (!Object.hasOwn(route.params, 'id') && experiments.length === 0)"
              class="q-mb-lg"
              :class="{'error': experimentError}"
              @update:model-value="job.entrypoint = ''; job.queue = ''; basicInfoForm.reset()"
            >
              <template v-slot:before>
                <div class="field-label">Experiment:</div>
              </template>
              <template v-slot:hint>
                <span 
                  v-if="!Object.hasOwn(route.params, 'id') && experiments.length === 0"
                  :style="{ 'color': experimentError ? '#C10015' : 'grey' }"
                >
                  No existing Experiments.  Create one
                  <router-link to="/experiments/new">
                    here
                  </router-link>
                </span>
              </template>
            </q-select>
            <q-select
              outlined
              dense
              v-model="job.entrypoint"
              clearable
              option-label="name"
              option-value="id"
              input-debounce="100"
              :options="entrypoints"
              @filter="getEntrypoints"
              :rules="[requiredRule]"
              :class="{ 'error': entrypointError }"
              :style="{ 'margin-bottom': entrypointField?.hasError ? '' : '25px' }"
              :disable="!job.experiment || allowableEntrypointIds.length === 0"
              @update:model-value="job.queue = ''; basicInfoForm.reset()"
              ref="entrypointField"
            >
              <template v-slot:before>
                <div class="field-label">Entrypoint:</div>
              </template>  
              <template v-slot:hint>
                <span v-if="!job.experiment">Select experiment first</span>
                <span 
                  v-else-if="allEntrypoints.length === 0"
                  :style="{ 'color': entrypointError ? '#C10015' : 'grey' }"
                >
                  No existing Entrypoints.  Create one
                  <router-link to="/entrypoints/new">
                    here
                  </router-link>
                </span>
                <span 
                  v-else-if="allowableEntrypointIds.length === 0"
                  :style="{ 'color': entrypointError ? '#C10015' : 'grey' }"
                >
                  {{ job.experiment.name }} has no Entrypoints, add 
                  <a href="#" @click="showAppendEntrypointDialog = true">
                    here
                  </a>
                </span>
                <span v-else>
                  If you don't see your desired Entrypoint, 
                  <a href="#" @click="showAppendEntrypointDialog = true">
                    register it with the "{{ job.experiment.name }}" Experiment first
                  </a>
                </span>
              </template>
            </q-select>
            <div
              v-if="entrypointField?.hasError"
              style="margin: 3px 0 10px 118px; font-size: 11px; color: #818181;"
            >
              If you don't see your desired Entrypoint, 
              <a href="#" @click="showAppendEntrypointDialog = true">
                register it with the "{{ job?.experiment?.name }}" Experiment first
              </a>
            </div>
            <q-select
              outlined
              dense
              v-model="job.queue"
              clearable
              option-label="name"
              input-debounce="100"
              :options="queues"
              @filter="getQueues"
              :rules="[requiredRule]"
              :class="{ 'error': queueError }"
              :style="{ 'margin-bottom': queueField?.hasError ? '' : '25px' }"
              :disable="!job.entrypoint || allowableQueueIds.length === 0"
              ref="queueField"
            >
              <template v-slot:before>
                <div class="field-label">Queue:</div>
              </template>
              <template v-slot:hint>
                <span v-if="!job.experiment && !job.entrypoint">Select Experiment and Entrypoint first</span>
                <span v-else-if="!job.entrypoint">Select Entrypoint first</span>
                <span v-else-if="allQueues.length === 0" :style="{ 'color': queueError ? '#C10015' : 'grey' }">
                  No current Queues.  Create one
                  <router-link to="/queues">
                    here
                  </router-link>
                </span>
                <span 
                  v-else-if="allowableQueueIds.length === 0"
                  :style="{ 'color': queueError ? '#C10015' : 'grey' }"
                  >
                  {{ job.entrypoint.name }} has no Queues, add 
                  <a href="#" @click="showAppendQueueDialog = true">
                    here
                  </a>
                </span>
                <span v-else>
                  If you don't see your desired Queue, 
                  <a href="#" @click="showAppendQueueDialog = true">
                    register it with the "{{ job.entrypoint.name }}" Entrypoint first
                  </a>
                </span>
              </template>
            </q-select>
            <div
              v-if="queueField?.hasError"
              style="margin: 3px 0 10px 118px; font-size: 11px; color: #818181;"
            >
              If you don't see your desired Queue,
              <a href="#" @click="showAppendQueueDialog = true">
                register it with the "{{ job?.entrypoint?.name }}" Entrypoint first
              </a>
            </div>
            <q-input
              outlined 
              v-model="job.timeout" 
              dense
              aria-required="true"
              class="q-mb-lg"
              :rules="[timeUnitRule]"
            >
              <template v-slot:before>
                <div class="field-label">Timeout:</div>
              </template>  
            </q-input>
            <q-input 
              outlined 
              dense 
              v-model.trim="job.description"
              class="q-mb-lg"
              type="textarea"
              autogrow
            >
              <template v-slot:before>
                <label :class="`field-label`">Description:</label>
              </template>
            </q-input>
          </q-form>
        </div>
      </fieldset>
    </div>
    <fieldset :class="`${isMobile ? 'col-12 q-mt-lg' : 'col'}`" :disabled="job.entrypoint === ''">
      <legend>Values</legend>
      <div class="q-px-xl">
        <BasicTable
          :columns="columns"
          :rows="parameters"
          :hideSearch="true"
          :hideEditTable="true"
          :hideDelete="true"
          @edit="(param, i) => {selectedParam = param; selectedParamIndex = i; showEditParamDialog = true}"
          @delete="(param) => {selectedParam = param; showDeleteDialog = true}"
          :inlineEditFields="['value']"
        />
        <q-btn
          v-if="!updateEntrypoint && job.entrypoint?.id === oldEntrypoint?.id && 
          oldEntrypoint?.snapshot !== latestEntrypoint?.snapshot"
          square 
          color="red"
          label="Update Values" 
          icon="sync"
          size="sm"
          @click.stop="syncJobParams()"
          class="q-mr-md"
        >
          <q-tooltip>
            Sync to latest version of entrypoint parameters and values.
          </q-tooltip>
        </q-btn>
        <q-btn
          v-if="updateEntrypoint && job.entrypoint?.id === oldEntrypoint?.id && 
          job.entrypoint.snapshot === latestEntrypoint?.snapshot"
          square 
          color="red"
          label="Revert Values" 
          icon="sync"
          size="sm"
          @click.stop="revertJobParams()"
          class="q-mr-md"
        >
          <q-tooltip>
            Revert to original job's entrypoint parameters and values.
          </q-tooltip>
        </q-btn>
      </div>
    </fieldset>
  </div>

  <div :class="`float-right q-mb-lg`">
      <q-btn
        outline
        color="primary" 
        label="Cancel"
        class="q-mr-lg cancel-btn"
        @click="confirmLeave = true; router.back()"
      />
      <q-btn  
        @click="submit()" 
        color="primary" 
        label="Submit Job"

      />
    </div>

  <DeleteDialog 
    v-model="showDeleteDialog"
    @submit="deleteParam()"
    type="Parameter"
    :name="selectedParam.name"
  />
  <EditJobParamDialog 
    v-model="showEditParamDialog"
    :editParam="selectedParam"
    @updateParam="updateParam"
  />
  <ReturnToFormDialog
    v-model="showReturnDialog"
    @cancel="clearForm"
  />
  <AppendResource
    v-model="showAppendEntrypointDialog"
    parentResourceType="experiments"
    childResourceType="entrypoints"
    :parentResourceObj="job.experiment"
    @submit="getExperiment(job.experiment.id); basicInfoForm.reset();"
  />
  <AppendResource
    v-model="showAppendQueueDialog"
    parentResourceType="entrypoints"
    childResourceType="queues"
    :parentResourceObj="job.entrypoint"
    @submit="getEntrypoint(job.entrypoint.id); basicInfoForm.reset();"
  />
</template>

<script setup>
  import { ref, inject, watch, computed, onMounted } from 'vue'
  import { useRouter, onBeforeRouteLeave } from 'vue-router'
  import DeleteDialog from '@/dialogs/DeleteDialog.vue'
  import EditJobParamDialog from '@/dialogs/EditJobParamDialog.vue'
  import BasicTable from '@/components/BasicTable.vue'
  import { useRoute } from 'vue-router'
  import * as api from '@/services/dataApi'
  import * as notify from '../notify'
  import PageTitle from '@/components/PageTitle.vue'
  import ReturnToFormDialog from '@/dialogs/ReturnToFormDialog.vue'
  import { useLoginStore } from '@/stores/LoginStore'
  import AppendResource from '@/dialogs/AppendResource.vue'

  const store = useLoginStore()

  const route = useRoute()
  
  const router = useRouter()

  const isMobile = inject('isMobile')

  function requiredRule(val) {
    return (!!val) || "This field is required"
  }

  function timeUnitRule(val) {
    return (/^\d+[hms]$/.test(val)) || "Value must be an integer followed by 'h', 'm', or 's'";
  }

  const oldJob = ref()
  const oldEntrypoint = ref()
  const updateEntrypoint = ref(false)
  const latestEntrypoint = ref()

  const job = ref({
    description: '',
    timeout: '24h',
    queue: '',
    entrypoint: '',
    experiment: ''
  })

  const valuesChanged = computed(() => {
    return job.value.description !== '' ||
           job.value.timeout !== '24h' ||
           (job.value.queue !== '' && job.value.queue !== null) ||
           job.value.entrypoint !== ''
  })

  const parameters = ref([])

  const computedValue = computed(() => {
    let output = {}
    if (parameters.value.length === 0) return output
    parameters.value.forEach((param) => {
      output[param.name] = param.value
    })
    return output
  })

  watch(() => job.value.entrypoint, (newVal) => {
    parameters.value = []
    if(Array.isArray(newVal?.parameters)) {
      newVal.parameters.forEach((param) => {
        // if re-running a job
        if(history.state.oldJobId) {
          // if entrypoint parameters are being synced or 
          // a different entrypoint is chosen
          if(updateEntrypoint.value || oldJob.value.entrypoint.id !== newVal.id){
            parameters.value.push({
              name: param.name,
              value: param.defaultValue,
              type: param.parameterType
            })
          }
          else {
            // only add parameters that exist in the original job
            if (oldJob.value.values[param.name]) {
              parameters.value.push({
                name: param.name,
                value: (history.state.oldJobId) ? oldJob.value.values[param.name] : param.defaultValue,
                type: param.parameterType
              })
            }
          }
        }
        // if creating a new job
        else {
          parameters.value.push({
              name: param.name,
              value: param.defaultValue,
              type: param.parameterType
          })
        }
      })
    }
  })

  watch(() => job.value.experiment, async (newVal) => {
    if(newVal) {
      await getEntrypoints()
    } else {
      entrypointError.value = false
    }
  })

  watch(() => job.value.entrypoint, async (newVal) => {
    if(newVal) {
      await getQueues()
    } else {
      queueError.value = false
    }
  })

  const basicInfoForm = ref(null)

  const columns = [
    { name: 'name', label: 'Name', align: 'left', field: 'name', sortable: true, },
    { name: 'value', label: 'Value', align: 'left', field: 'value', sortable: true, },
    { name: 'parameterType', label: 'Type', align: 'left', field: 'type', sortable: true, },
    // { name: 'actions', label: 'Actions', align: 'center',  },
  ]

  const experimentError = ref(false)
  const entrypointError = ref(false)
  const queueError = ref(false)

  function submit() {
    basicInfoForm.value.validate().then(success => {
      // quasar doesn't validate disabled fields, need to manually do it below
      if(!job.experiment && experiments.value.length === 0 && !Object.hasOwn(route.params, 'id')) {
        experimentError.value = true
      }
      if(job.value.experiment && !job.value.entrypoint && (allEntrypoints.value.length === 0 || allowableEntrypointIds.value.length === 0)) {
        entrypointError.value = true
      }
      if(job.value.entrypoint && !job.value.queue && (allQueues.value.length === 0 || allowableQueueIds.value.length === 0)) {
        queueError.value = true
      }
      if(success && job.value.experiment && job.value.entrypoint && job.value.queue) {
        confirmLeave.value = true
        createJob()
      }
      else {
        // error
      }
    })
  }

  const expJobOrAllJobs = computed(() => {
    // determine if experiment job form or all jobs form, when saving form
    if(Object.hasOwn(route.params, 'id')) {
      return route.params.id
    } else {
      return 'allJobs'
    }
  })

  async function createJob() {
    const payload = {
      description: job.value.description,
      queue: job.value.queue.id,
      entrypoint: job.value.entrypoint.id,
      values: computedValue.value,
      timeout: job.value.timeout,
      entrypointSnapshot: (history.state.oldJobId && !updateEntrypoint.value) ? oldEntrypoint.value.snapshot : job.value.entrypoint.snapshot
    }  
    try {
      await api.addJob(job.value.experiment.id, payload)
      notify.success(`Successfully created job`)
      store.savedForms.jobs[expJobOrAllJobs.value] = null
      router.push(expJobOrAllJobs.value === 'allJobs' ? `/jobs` : `/experiments/${route.params.id}/jobs`)
    } catch(err) {
      // error shows when redis isn't installed, but job is still created
      store.savedForms.jobs[expJobOrAllJobs.value] = null
      notify.error(err.response.data.message)
    }
  }

  const showDeleteDialog = ref(false)
  const selectedParam = ref({})
  const selectedParamIndex = ref('')

  function deleteParam() {
    parameters.value = parameters.value.filter((param) => param.name !== selectedParam.value.name)
    showDeleteDialog.value = false
  }

  const showEditParamDialog = ref(false)

  function updateParam(parameter) {
    parameters.value[selectedParamIndex.value] = { ...parameter }
    showEditParamDialog.value = false
  }

  // const experiment = ref()
  const experiments = ref([])
  const queues = ref([])
  const allQueues = ref([])
  const entrypoints = ref([])
  const allEntrypoints = ref([])

  async function getExperiments(val = '', update) {
    const fetchData = async () => {
      try {
        const res = await api.getData('experiments', {
          search: val,
          rowsPerPage: 0, // get all
          index: 0
        });
        experiments.value = res.data.data
      } catch (err) {
        notify.error(err.response.data.message)
      }
    }

    if (update) {
      // when used by the dropdown
      await update(fetchData)
    } else {
      // when used by watcher
      await fetchData()
    }
  }

  const allowableQueueIds = computed(() => {
    if(!job.value.entrypoint) return []
    return job.value.entrypoint.queues.map((q) => q.id)
  })

  async function getQueues(val = '', update) {
    const fetchData = async () => {
      try {
        const res = await api.getData('queues', {
          search: val,
          rowsPerPage: 0, // get all
          index: 0
        })
        allQueues.value = res.data.data
        queues.value = res.data.data.filter((q) =>
          allowableQueueIds.value.includes(q.id)
        )
      } catch(err) {
        notify.error(err.response.data.message)
      } 
    }

    if (update) {
      // when used by the dropdown
      await update(fetchData)
    } else {
      // when used by mounted
      await fetchData()
    }
  }

  const allowableEntrypointIds = computed(() => {
    if(!job.value.experiment) return []
    return job.value.experiment.entrypoints.map((ep) => ep.id)
  }) 

  watch(() => allowableEntrypointIds.value, (newVal) => {
    if(newVal.length === 0) job.value.entrypoint = ''
    else entrypointError.value = false
  })

  watch(() => allowableQueueIds.value, (newVal) => {
    if(newVal.length === 0) job.value.queue = ''
    else queueError.value = false
  })

  async function getEntrypoints(val = '', update) {
    const fetchData = async () => {
      try {
        const res = await api.getData('entrypoints', {
          search: val,
          rowsPerPage: 0, // get all
          index: 0
        })
        allEntrypoints.value = res.data.data
        entrypoints.value = res.data.data.filter((ep) => 
          allowableEntrypointIds.value.includes(ep.id)
        )
      } catch(err) {
        notify.error(err.response.data.message)
      } 
    }

    if (update) {
      // when used by the dropdown
      await update(fetchData)
    } else {
      // when used by mounted
      await fetchData()
    }
  }

  async function getExperiment(id) {
    if(!id) return
    try {
      const res = await api.getItem('experiments', id)
      job.value.experiment = res.data
    } catch(err) {
      console.warn(err)
    }
  }

  async function getEntrypoint(id) {
    if(!id) return
    try {
      const res = await api.getItem('entrypoints', id)
      job.value.entrypoint = res.data

      // display the old job's values when re-running a job
      if(history.state.oldJobId && !updateEntrypoint.value) {
        job.value.entrypoint.parameters = oldEntrypoint.value.parameters
        job.value.values = oldJob.value.values
      }
    } catch(err) {
      console.warn(err)
    }
  }

  async function getResource(type, id) {
    try {
      const res = await api.getItem(type, id)
      return res.data
    } catch(err) {
      console.warn(err)
    }
  }

  onMounted(async () => {
    // if re-running a job
    if(history.state.oldJobId) {
      oldJob.value = (await(api.getSnapshot('jobs', history.state.oldJobId, history.state.jobSnapshotId))).data
      oldEntrypoint.value = (await api.getSnapshot("entrypoints", oldJob.value.entrypoint.id, oldJob.value.entrypoint.snapshotId)).data
      latestEntrypoint.value = await getResource("entrypoints", oldJob.value.entrypoint.id)
      await getExperiment(oldJob.value.experiment.id)
      
      if(allowableEntrypointIds.value.includes(oldJob.value.entrypoint.id)) {
        await getEntrypoint(oldJob.value.entrypoint.id)
      } else {
        notify.error(`Entrypoint ${oldJob.value.entrypoint.name} is no longer linked to experiment ${oldJob.value.experiment.name}`)
      }
      if(allowableQueueIds.value.includes(oldJob.value.queue.id)) {
        job.value.queue = await getResource('queues', oldJob.value.queue.id)
      } else {
        notify.error(`Queue ${oldJob.value.queue.name} is no longer linked to entrypoint ${oldJob.value.entrypoint.name}`)
      }
      job.value.description = oldJob.value.description
    }
    if(Object.hasOwn(route.params, 'id')) {
      await getExperiment(route.params.id)
    } else {
      await getExperiments()
    }

    if(store.savedForms.jobs[expJobOrAllJobs.value] && !history.state.oldJobId) {
      job.value = store.savedForms.jobs[expJobOrAllJobs.value]
      // check if saved values are still valid
      // load latest version of each resource
      // if a child is no longer linked to parent resource, discard
      if(job.value.experiment && job.value.experiment.id) {
        try {
          const res = await api.getItem('experiments', job.value.experiment.id)
          job.value.experiment = res.data
        } catch(err) {
          clearForm()
          console.warn(err)
        }
      }
      if(job.value.entrypoint && job.value.entrypoint.id) {
        try {
          const res = await api.getItem('entrypoints', job.value.entrypoint.id)
          if(allowableEntrypointIds.value.includes(res.data.id)) {
            job.value.entrypoint = res.data
          } else {
            job.value.entrypoint = ''
          }
        } catch(err) {
          job.value.entrypoint = ''
          console.warn(err)
        }
      }
      if(job.value.queue && job.value.queue.id) {
        try {
          const res = await api.getItem('queues', job.value.queue.id)
          if(allowableQueueIds.value.includes(res.data.id)) {
            job.value.queue = res.data
          } else {
            job.value.queue = ''
          }
        } catch(err) {
          job.value.queue = ''
          console.warn(err)
        }
      }
      basicInfoForm.value.reset()
      if(job.value.experiment && job.value.experiment.id) {
        showReturnDialog.value = true
      }
    }
  })

  onBeforeRouteLeave((to, from, next) => {
    toPath.value = to.path
    if(!valuesChanged.value) {
      store.savedForms.jobs[expJobOrAllJobs.value] = null
      next(true)
    } else if(confirmLeave.value) {
      next(true)
    } else {
      store.savedForms.jobs[expJobOrAllJobs.value] = job.value
      next(true)
    }
  })

  const showReturnDialog = ref(false)
  const confirmLeave = ref(false)
  const toPath = ref()

  async function clearForm() {
    job.value = {
      description: '',
      queue: '',
      entrypoint: '',
      timeout: '24h'
    }
    if(!Object.hasOwn(route.params, 'id')) {
      job.value.experiment = ''
    }
    basicInfoForm.value.reset()
    store.savedForms.jobs[expJobOrAllJobs.value] = null
    await getExperiment(route.params.id)
  }

  const queueHint = computed(() => {
    if(!job.value.experiment) return 'Select experiment and entrypoint first'
    if(!job.value.entrypoint) return 'Select entrypoint first'
    return ''
  })

  const showAppendEntrypointDialog = ref(false)
  const showAppendQueueDialog = ref(false)

  const entrypointField = ref()
  const queueField = ref()

  async function syncJobParams() {
    try {
      updateEntrypoint.value = true
      await getEntrypoint(oldJob.value.entrypoint.id)
      notify.success(`Successfully updated to use the latest entrypoint parameters and values`)
    } catch(err) {
      console.warn(err)
    }
  }
  
  async function revertJobParams() {
    try {
      updateEntrypoint.value = false
      await getEntrypoint(oldJob.value.entrypoint.id)
      notify.success(`Successfully updated to use the original job parameters and values`)
    } catch(err) {
      console.warn(err)
    }
  }

</script>


<style scoped>
  .error :deep(.q-field__control) {
    border: 2px solid #C10015 !important;
  }
</style>
