<template>
  <PageTitle />
  <q-stepper
    v-model="step"
    header-nav
    ref="stepper"
    color="primary"
    animated
    bordered
    style="margin: 50px 100px;"
  >
    <q-step
      :name="1"
      title="Step 1: Basic Info"
      icon="settings"
      :done="step > 1"
      :header-nav="step > 1"
    >
      <q-form ref="step1Form" greedy>
        <q-input 
          outlined 
          dense 
          v-model.trim="name"
          :rules="[requiredRule]"
          class="q-mb-sm"
        >
          <template v-slot:before>
            <div :class="`text-body2 label`">Experiment Name:</div>
          </template>
        </q-input>
        <q-select
          outlined 
          v-model="group" 
          :options="groupOptions" 
          dense
          :rules="[requiredRule]"
        >
          <template v-slot:before>
            <div class="text-body2 label">Group Name:</div>
          </template>  
        </q-select>
      </q-form>

    </q-step>

    <q-step
      :name="2"
      title="Step 2: Entry Points"
      icon="create_new_folder"
      :done="step > 2"
      :header-nav="step > 2"
    >
      <div v-for="(item, i) in store.entryPoints" :key="i">
        <q-checkbox
          :label="item"
          v-model="selectedEntryPoints"
          :val="item"
        />
      </div>
      <q-btn 
        color="primary"
        icon-right="add"
        label="Create new Entry Point"
        class="q-mt-lg"
        @click="showLeaveDialog = true" 
      />
    </q-step>

    <q-step
      :name="3"
      title="Step 3: Tags"
      icon="sell"
      :header-nav="step > 3"
    >
      <div style="margin: 0 200px">
        <q-btn 
          v-for="(tag, i) in store.tags"
          :key="i" 
          :label="tag"
          no-caps
          class="q-ma-sm"
          @click="toggleTag(tag)"
          :color="selectedTags.includes(tag) ? 'primary' : 'grey-6'"
        />

        <q-input 
          v-model="newTag" 
          outlined 
          dense 
          label="Add new Tag" 
          class="q-mt-lg" 
          style="width: 250px"
          @keydown.enter.prevent="addNewTag"
        >
          <template v-slot:prepend>
            <q-icon name="sell" />
          </template>
          <template v-slot:append>
            <q-btn round dense size="sm" icon="add" color="primary" @click="addNewTag()" />
          </template>
        </q-input>
      </div>

      <p style="margin: 40px 200px">
        Selected Tags: <br>
        <q-chip 
        v-for="(tag, i) in selectedTags"
        :key="i"
        :label="tag"
        color="primary"
        class="text-white"
      />
      </p>


    </q-step>

    <template v-slot:navigation>
      <q-separator class="q-mb-lg" />
      <q-stepper-navigation>
        <q-btn v-if="step !== 3" @click="continueStep" color="primary" label="Continue" style="width: 120px" />
        <q-btn v-if="step === 3" @click="submit" color="primary" label="Submit" style="width: 120px" />
        <q-btn v-if="step > 1" color="secondary" @click="$refs.stepper.previous()" label="Back" class="q-ml-md" />
        <q-btn label="Reset" @click="reset()" class="float-right" color="orange" />
      </q-stepper-navigation>
    </template>
  </q-stepper>
  <LeaveExperimentsDialog 
    v-model="showLeaveDialog"
    @submit="leaveForm()"
  />
  <ReturnExperimentsDialog 
    v-model="showReturnDialog"
    @submit="loadForm()"
  />
</template>

<script setup>
  import PageTitle from '@/components/PageTitle.vue'
  import { ref, reactive, watch } from 'vue'
  import router from '@/router'
  import { useDataStore } from '@/stores/DataStore.ts'
  import LeaveExperimentsDialog from '@/dialogs/LeaveExperimentsDialog.vue'
  import ReturnExperimentsDialog from '@/dialogs/ReturnExperimentsDialog.vue'

  const store = useDataStore()

  const showLeaveDialog = ref(false)
  const showReturnDialog = ref(false)

  const step =  ref(1)

  const stepper = ref(null)

  const step1Form = ref(null)

  // form inputs
  const name = ref('')
  const group = ref('')
  let selectedEntryPoints = ref([])
  let selectedTags = reactive([])

  function leaveForm() {
    let savedForm = {
      name: name.value,
      group: group.value
    }
    if(selectedEntryPoints.value.length > 0) {
      savedForm.selectedEntryPoints = selectedEntryPoints.value
    }
    if(selectedTags.length > 0) {
      savedForm.selectedTags = selectedTags
    }
    store.savedExperimentForm = savedForm
    router.push('/entryPoints')
  }

  if(Object.keys(store.savedExperimentForm).length !== 0) {
    showReturnDialog.value = true
  }

  function loadForm() {
    name.value = store.savedExperimentForm.name
    group.value = store.savedExperimentForm.group
    if(store.savedExperimentForm.selectedEntryPoints?.length) {
      selectedEntryPoints.value = store.savedExperimentForm.selectedEntryPoints
    }
    if(store.savedExperimentForm.selectedTags?.length) {
      selectedTags = store.savedExperimentForm.selectedTags
    }
    showReturnDialog.value = false
  }

  watch(showReturnDialog, (newVal) => {
    // regardless if user submits, cancels, or clicks outside dialog, clear saved form
    if(newVal === false) {
      store.savedExperimentForm = {}
    }
  })

  const groupOptions = ref([
    'Group 1',
    'Group 2',
    'Group 3',
  ])

  const requiredRule = (val) => (val && val.length > 0) || "This field is required"

  function continueStep() {
    if(step.value === 1) {
      step1Form.value.validate().then(success => {
        if (success) {
          stepper.value.next()
        }
      })
    } else {
      stepper.value.next()
    }
  }

  function submit() {
    const experiment = {
      name: name.value,
      group: group.value,
      entryPoints: selectedEntryPoints.value,
      tags: selectedTags
    }
    store.experiments.push(experiment)
    router.push('/experiments')
  }

  function reset() {
    if(step.value === 1) step1Form.value.reset()
    step.value = 1
    name.value = ''
    group.value = ''
    selectedEntryPoints.value = []
    selectedTags = []
  }

  function toggleTag(tag) {
    if(!selectedTags.includes(tag)) {
      selectedTags.push(tag)
    } else {
      selectedTags.forEach((selectedTag, i) => {
        if(tag ===  selectedTag) {
          selectedTags.splice(i, 1)
        }
      })
    }
  }

  const newTag = ref('')

  function addNewTag() {
    store.tags.push(newTag.value)
    newTag.value = ''
  }

</script>

<style>
  .q-stepper__content{
    height: 450px;
  }

  .label{
    width: 150px
  }
</style>@/stores/DataStore