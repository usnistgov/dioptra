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
      <q-input 
        outlined 
        dense 
        v-model.trim="orgName" 
        autofocus 
        :rules="[requiredRule]"
        lazy-rules="ondemand"
        ref="orgNameRef"
        class="q-mb-sm"
        @update:model-value="orgNameRef.validate()"
      >
        <template v-slot:before>
          <div :class="`text-body2 label`">Organization Name:</div>
        </template>
      </q-input>
      <q-input 
        outlined 
        dense 
        v-model.trim="name" 
        autofocus 
        :rules="[requiredRule]"
        lazy-rules="ondemand"
        ref="nameRef"
        class="q-mb-sm"
        @update:model-value="nameRef.validate()"
      >
        <template v-slot:before>
          <div :class="`text-body2 label`">Experiment Name:</div>
        </template>
      </q-input>
      <q-select
        outlined 
        v-model="team" 
        :options="groupOptions" 
        dense
        ref="teamRef"
        :rules="[requiredRule]"
        lazy-rules="ondemand"
        @update:model-value="teamRef.resetValidation()"
      >
        <template v-slot:before>
          <div class="text-body2 label">Team Name:</div>
        </template>  
      </q-select>

    </q-step>

    <q-step
      :name="2"
      title="Step 2: Entry Points"
      icon="create_new_folder"
      :done="step > 2"
      :header-nav="step > 2"
    >
      An ad group contains one or more ads which target a shared set of keywords.

    </q-step>

    <q-step
      :name="3"
      title="Step 3: Tags"
      icon="sell"
      :header-nav="step > 3"
    >
      Try out different ad text to see what brings in the most customers, and learn how to
      enhance your ads using features like ad extensions. If you run into any problems with
      your ads, find out how to tell if they're running and how to resolve approval issues.
    </q-step>

    <template v-slot:navigation>
      <q-separator class="q-mb-lg" />
      <q-stepper-navigation>
        <q-btn @click="continueStep" color="primary" :label="step === 3 ? 'Submit' : 'Continue'" style="width: 120px" />
        <q-btn v-if="step > 1" color="secondary" @click="$refs.stepper.previous()" label="Back" class="q-ml-md" />
        <q-btn label="Reset" @click="reset()" class="float-right" color="orange" />
      </q-stepper-navigation>
    </template>
  </q-stepper>
</template>

<script setup>
  import PageTitle from '@/components/PageTitle.vue'
  import { ref } from 'vue'

  const step =  ref(1)

  const stepper = ref(null)

  const orgName = ref('')
  const orgNameRef = ref(null)

  const name = ref('')
  const nameRef = ref(null)

  const team = ref('')
  const teamRef = ref(null)
  const groupOptions = ref([
    'Team 1',
    'Team 2',
    'Team 3',
  ])

  const requiredRule = (val) => (val && val.length > 0) || "This field is required"

  function continueStep() {
    if(step.value === 1) {
      orgNameRef.value.validate()
      nameRef.value.validate()
      teamRef.value.validate()
      if(!orgNameRef.value.hasError && !nameRef.value.hasError && !teamRef.value.hasError) {
        stepper.value.next()
      }
    } else {
      stepper.value.next()
    }
  }

  function reset() {
    step.value = 1
    orgName.value = ''
    name.value = ''
    team.value = ''
  }


</script>

<style>
  .q-stepper__content{
    height: 50%;
  }

  .label{
    width: 150px
  }
</style>