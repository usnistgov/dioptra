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
      <q-option-group
        :options="entryPoints"
        type="checkbox"
        v-model="selectedEntryPoints"
      >

      </q-option-group>
    </q-step>

    <q-step
      :name="3"
      title="Step 3: Tags"
      icon="sell"
      :header-nav="step > 3"
    >
      <div style="margin: 0 200px">
        <q-btn 
          v-for="(tag, i) in tags"
          :key="i" 
          :label="tag.label"
          no-caps
          class="q-ma-sm"
          @click="tag.active = !tag.active"
          :color="tag.active ? 'primary' : 'grey-6'"
        />
      </div>

      <p style="margin: 50px 200px">
        Selected Tags: <br>
        <q-chip 
        v-for="(tag, i) in selectedTags"
        :key="i"
        :label="tag.label"
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
</template>

<script setup>
  import PageTitle from '@/components/PageTitle.vue'
  import { ref, computed } from 'vue'
  import router from '@/router'
  import { useDataStore } from '@/stores/DataStore.ts'
  const store = useDataStore()

  const step =  ref(1)

  const stepper = ref(null)

  const step1Form = ref(null)

  const name = ref('')

  const group = ref('')

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
      tags: selectedTagLabels.value
    }
    store.experiments.push(experiment)
    router.push('/experiments')
  }

  function reset() {
    if(step.value === 1) step1Form.value.reset()
    step.value = 1
    name.value = ''
    group.value = ''
  }

  const selectedEntryPoints = ref([])

  const entryPoints = [
    {label: 'Entry Point 1', value: 'Entry Point 1'},
    {label: 'Entry Point 2', value: 'Entry Point 2'},
    {label: 'Entry Point 3', value: 'Entry Point 3'},
    {label: 'Entry Point 4', value: 'Entry Point 4'},
    {label: 'Entry Point 5', value: 'Entry Point 5'},
    {label: 'Entry Point 6', value: 'Entry Point 6'},
  ]

  const tags = ref([
    { label: 'Machine Learning', active: false },
    { label: 'Adversarial Machine Learning', active: false },
    { label: 'Tensorflow', active: false },
    { label: 'vgg16', active: false },
    { label: 'Image Classification', active: false },
    { label: 'Patch Attack', active: false },
    { label: 'Categorical Data', active: false },
    { label: 'AI', active: false }
  ])

  const selectedTags = computed(() => {
    return tags.value.filter((tag) => tag.active === true)
  })

  const selectedTagLabels = computed(() => {
    return selectedTags.value.map((tag) => tag.label)
  })

</script>

<style>
  .q-stepper__content{
    height: 350px;
  }

  .label{
    width: 150px
  }
</style>@/stores/DataStore