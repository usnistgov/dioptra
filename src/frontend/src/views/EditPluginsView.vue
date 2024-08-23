<template>
  <PageTitle :title="title" />
  <div :class="`${isMobile ? '' : 'q-mx-xl'} q-mt-lg`">
    <div :class="`${isMobile ? '' : 'q-gutter-x-xl row'}`">
      <fieldset :class="`${isMobile ? 'col-12' : 'col'} `">
        <legend>Basic Info</legend>
        <q-form ref="basicInfoForm" greedy class="q-px-sm">
          <q-input 
            outlined 
            dense 
            v-model="plugin.name"
            :rules="[requiredRule, pythonModuleNameRule]"
            class="q-mb-sm q-mt-md"
            aria-required="true"
          >
            <template v-slot:before>
              <label :class="`field-label`">Name:</label>
            </template>
          </q-input>
          <q-input 
            outlined 
            dense 
            v-model.trim="plugin.description"
            class="q-mb-sm q-mt-sm"
            type="textarea"
          >
            <template v-slot:before>
              <label :class="`field-label`">Description:</label>
            </template>
          </q-input>
        </q-form>
      </fieldset>
      <fieldset :class="`${isMobile ? 'col-12 q-mt-lg' : 'col'}`">
        <legend>Tags</legend>
      </fieldset>
    </div>
  </div>

  <div :class="`${isMobile ? '' : 'q-mx-xl'} float-right q-mt-xl`">
    <q-btn  
      to="/plugins"
      color="negative" 
      label="Cancel"
      class="q-mr-lg"
    />
    <q-btn  
      @click="submit()" 
      color="primary" 
      label="Save Plugin"
      type="submit"
    />
  </div>
</template>

<script setup>
  import { ref, inject } from 'vue'
  import * as api from '@/services/dataApi'
  import { useRoute, useRouter } from 'vue-router'
  import * as notify from '../notify'
  import PageTitle from '@/components/PageTitle.vue'

  const route = useRoute()
  const router = useRouter()

  const isMobile = inject('isMobile')

  function requiredRule(val) {
    return (!!val) || "This field is required"
  }

  const plugin = ref({
    name: '',
    description: '',
  })

  const title = ref('')
  getPlugin()
  async function getPlugin() {
    try {
      const res = await api.getItem('plugins' ,route.params.id)
      plugin.value = res.data
      title.value = `Edit ${res.data.name}`
    } catch(err) {
      notify.error(err.response.data.message)
    } 
  }

  const basicInfoForm = ref()

  function submit() {
    basicInfoForm.value.validate().then(success => {
      if (success) {
        updatePlugin()
      }
      else {
        // error
      }
    })
  }

  async function updatePlugin() {
    try {
      const res = await api.updateItem('plugins', route.params.id, { 
        name: plugin.value.name,
        description: plugin.value.description
      })
      notify.success(`Successfully updated ${res.data.name}`)
      router.push('/plugins')
    } catch(err) {
      notify.error(err.response.data.message)
    } 
  }

  function pythonModuleNameRule(val) {
    if (/\s/.test(val)) {
      return "A Python module name cannot contain spaces."
    }
    if (!/^[A-Za-z_]/.test(val)) {
      return "A Python module name must start with a letter or underscore."
    }
    if (!/^[A-Za-z_][A-Za-z0-9_]*$/.test(val)) {
      return "A Python module name can only contain letters, numbers, and underscores."
    }
    if (val === "_") {
      return "A Python module name cannot be '_' with no other characters."
    }
    return true
  }

</script>