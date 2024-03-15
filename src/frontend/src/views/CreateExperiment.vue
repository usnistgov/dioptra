<template>
  <PageTitle />
  <q-stepper
    v-model="step"
    header-nav
    ref="stepper"
    color="primary"
    animated
    bordered
    :active-icon="isStep1FormValid ? 'edit' : 'warning'"
    :class="`${isMobile ? 'q-mt-md' : 'q-ma-xl'}`"
  >
    <q-step
      :name="1"
      :title="`${isMobile ? '' : 'Step 1: Basic Info'}`"
      icon="settings"
      :done="step > 1"
      :header-nav="step > 1"
      :error="!isStep1FormValid"

    >
      <q-form ref="step1Form" greedy>
        <q-input 
          outlined 
          dense 
          v-model.trim="name"
          :rules="[requiredRule]"
          class="q-mb-sm"
          role="textbox"
        >
          <template v-slot:before>
            <label :class="`text-body2 label`">Experiment Name:</label>
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
      :title="`${isMobile ? '' : 'Step 2: Entry Points'}`"
      icon="create_new_folder"
      :done="step2Done"
      :header-nav="step2Done"
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
      :title="`${isMobile ? '' : 'Step 3: Tags'}`"
      icon="sell"
      :done="step3Done"
      :header-nav="step3Done"
    >
      <div :class="`${isMobile ? '' : 'q-mx-xl'}`">
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

      <p :class="`${isMobile ? '' : 'q-mx-xl'} q-mt-lg`">
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
  import { ref, reactive, watch, inject } from 'vue'
  import router from '@/router'
  import { useDataStore } from '@/stores/DataStore.ts'
  import LeaveExperimentsDialog from '@/dialogs/LeaveExperimentsDialog.vue'
  import ReturnExperimentsDialog from '@/dialogs/ReturnExperimentsDialog.vue'

  const store = useDataStore()

  const isMobile = inject('isMobile')

  const showLeaveDialog = ref(false)
  const showReturnDialog = ref(false)

  const step =  ref(1)
  const step2Done = ref(false)
  const step3Done = ref(false)

  watch(step, newVal => {
    if(newVal === 2) step2Done.value = true
    if(newVal === 3) step3Done.value = true
  })

  const stepper = ref(null)

  const step1Form = ref(null)
  let isStep1FormValid = ref(true)

  // form inputs
  const name = ref('')
  const group = ref('')
  let selectedEntryPoints = ref([])
  let selectedTags = reactive([])

  function leaveForm() {
    let savedForm = {
      name: name.value,
      group: group.value,
      step2Done: step2Done,
      step3Done: step3Done,
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
    step2Done.value = store.savedExperimentForm.step2Done
    step3Done.value = store.savedExperimentForm.step3Done
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
          isStep1FormValid.value = true
          stepper.value.next()
        } else {
          isStep1FormValid.value = false
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
    step2Done.value = false
    step3Done.value = false
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
    if(newTag.value.trim().length) {
      store.tags.push(newTag.value)
    }
    newTag.value = ''
  }

</script>

<style>
  .q-stepper__content{
    min-height: 40vh; 
  }

  .label{
    width: 150px
  }
</style>@/stores/DataStore