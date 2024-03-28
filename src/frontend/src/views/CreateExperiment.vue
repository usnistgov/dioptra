<template>
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
          aria-required="true"
        >
          <template v-slot:before>
            <label :class="`field-label myowndark`">Experiment Name:</label>
          </template>
        </q-input>
        <q-select
          outlined 
          v-model="group" 
          :options="groupOptions" 
          dense
          :rules="[requiredRule]"
          aria-required="true"
        >
          <template v-slot:before>
            <div class="field-label">Group Name:</div>
          </template>  
        </q-select>
      </q-form>

      <q-banner v-if="nameWarning" dense class="text-white bg-negative absolute-bottom">
        <template v-slot:avatar>
          <q-icon name="warning" color="white" />
        </template>
        You must fill out at least the name field to save a draft.
      </q-banner>
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
          :label="item.name"
          v-model="selectedEntryPoints"
          :val="item.name"
        />
      </div>
      <q-btn 
        color="primary"
        icon="add"
        label="Create new Entry Point"
        class="q-mt-lg"
        @click="router.push('/entryPoints/create')" 
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
      <q-stepper-navigation class="overflow-auto">
        <q-btn 
          :disabled="step === 1" 
          color="secondary" 
          @click="$refs.stepper.previous()" 
          label="Back" 
          style="width: 142px"
          icon="arrow_back"
        />
        <q-btn 
          v-if="step !== 3" 
          @click="continueStep" 
          color="primary" 
          label="Continue" 
          style="width: 142px"
          class="q-ml-md"
          icon-right="arrow_forward"
        />
        <q-btn 
          v-if="step === 3" 
          @click="submit()" 
          color="primary" 
          label="Submit" 
          style="width: 120px" 
          class="q-ml-md" 
        />

        <div class="float-right">
          <q-btn label="Reset" @click="reset()" icon="restart_alt" class="q-mr-md" color="negative" />
          <q-btn label="Save Draft" @click="submit(true)" icon="save" color="primary" />
        </div>

      </q-stepper-navigation>
    </template>
  </q-stepper>
  <LeaveExperimentsDialog 
    v-model="showLeaveDialog"
    @leaveForm="isSubmitting = true; router.push(toPath)"
  />
  <ReturnExperimentsDialog 
    v-model="showReturnDialog"
    @submit="loadForm()"
  />
</template>

<script setup>
  import { ref, reactive, watch, inject } from 'vue'
  import { useRouter, onBeforeRouteLeave } from 'vue-router'
  import { useDataStore } from '@/stores/DataStore.ts'
  import LeaveExperimentsDialog from '@/dialogs/LeaveExperimentsDialog.vue'
  import ReturnExperimentsDialog from '@/dialogs/ReturnExperimentsDialog.vue'

  const router = useRouter()

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

  // function leaveForm() {
  //   let savedForm = {
  //     name: name.value,
  //     group: group.value,
  //     step2Done: step2Done,
  //     step3Done: step3Done,
  //   }
  //   if(selectedEntryPoints.value.length > 0) {
  //     savedForm.selectedEntryPoints = selectedEntryPoints.value
  //   }
  //   if(selectedTags.length > 0) {
  //     savedForm.selectedTags = selectedTags
  //   }
  //   store.savedExperimentForm = savedForm
  //   router.push('/entryPoints')
  // }

  // let editMode = ref(false)

  if(Object.keys(store.savedExperimentForm).length !== 0) {
    // showReturnDialog.value = true
    // editMode.value = true
    loadForm()
  }

  function loadForm() {
    console.log('savedExperimentForm = ', store.savedExperimentForm)
    name.value = store.savedExperimentForm.name
    group.value = store.savedExperimentForm.group
    if(store.savedExperimentForm.entryPoints?.length) {
      selectedEntryPoints.value = store.savedExperimentForm.entryPoints
      step2Done.value = true
    }
    if(store.savedExperimentForm.tags?.length) {
      selectedTags = store.savedExperimentForm.tags
      step3Done.value = true
    }
    // step2Done.value = store.savedExperimentForm.step2Done
    // step3Done.value = store.savedExperimentForm.step3Done
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

  const isSubmitting = ref(false)

  let nameWarning = ref(false)

  watch(name, newVal => {
    if(newVal.length > 0) {
      nameWarning.value = false
    }
  })

  function submit(draft = false) {
    if(name.value.length === 0) {
      nameWarning.value = true
      return
    }
    const experiment = {
      name: name.value,
      group: group.value,
      entryPoints: selectedEntryPoints.value,
      tags: selectedTags,
      draft: draft
    }
    if(!store.editMode) {
      const id = new Date().getTime().toString()
      experiment.id = id
      store.experiments.push(experiment)
    } else {
      experiment.id = store.savedExperimentForm.id
      const editIndex = store.experiments.findIndex((storedExperiment) => storedExperiment.id === experiment.id)
      store.experiments[editIndex] = experiment
    }
    isSubmitting.value = true
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



  let toPath = reactive({})

  onBeforeRouteLeave((to, from, next) => {
    showLeaveDialog.value = true
    toPath = to.path
    if(isSubmitting.value) {
      store.savedExperimentForm = {}
      next(true)
    } else {
      next(false)
    }
  })

</script>

<style>
  .q-stepper__content{
    min-height: 40vh; 
  }

</style>