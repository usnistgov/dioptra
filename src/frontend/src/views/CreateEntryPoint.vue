<template>
  <div :class="`row q-mt-xl ${isMobile ? '' : 'q-mx-xl'}`">
    <div :class="`${isMobile ? 'col-12' : 'col-5'} q-mr-xl`">
      <fieldset>
        <legend>Basic Info</legend>
        <div style="padding: 0 5%">
          <q-form ref="basicInfoForm" greedy>
            <q-input 
              outlined 
              dense 
              v-model.trim="entryPoint.name"
              :rules="[requiredRule]"
              class="q-mb-sm q-mt-md"
              aria-required="true"
            >
              <template v-slot:before>
                <label :class="`field-label`">Entry Point Name:</label>
              </template>
            </q-input>
            <q-select
              outlined 
              v-model="entryPoint.group" 
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
        </div>
      </fieldset>
      <fieldset class="q-mt-lg">
        <legend>Task Graph</legend>
        <div style="padding: 0 5%">
          <div>TBD</div>
        </div>
      </fieldset>
    </div>
    <fieldset :class="`${isMobile ? 'col-12 q-mt-lg' : 'col'}`">
      <legend>Parameters</legend>
      <div style="padding: 0 5%">
        <q-table
          :columns="columns"
          :rows="entryPoint.parameters"
          dense
          flat
          bordered
          class="q-mt-lg"
          separator="cell"
          :hide-bottom="params.length > 0"
        >
          <template v-slot:no-data>
            <span>No parameters entered..........</span>
          </template>
        </q-table>

        <q-card
          flat
          bordered
          class="q-px-lg q-my-xl"
        >
          <q-card-section class="q-px-none">
            <label class="text-body1">Add Parameter</label>
          </q-card-section>
          <q-form ref="paramForm" greedy @submit.prevent="addParam">
            <q-input 
              outlined 
              dense 
              v-model.trim="paramName"
              :rules="[requiredRule]"
              class="q-mb-sm "
              label="Enter Name"
            />
            <q-select
              outlined 
              v-model="paramType" 
              :options="typeOptions" 
              dense
              :rules="[requiredRule]"
              aria-required="true"
              class="q-mb-sm"
              label="Select Type"
            />
            <q-input 
              outlined 
              dense 
              v-model.trim="paramDefaultValue"
              class="q-mb-sm"
              label="Enter Default Value"
            />
            <q-card-actions align="right">
              <q-btn
                round
                color="secondary"
                icon="add"
                type="submit"
              >
                <span class="sr-only">Add Parameter</span>
                <q-tooltip>
                  Add Parameter
                </q-tooltip>
              </q-btn>
            </q-card-actions>
          </q-form>
        </q-card>
      </div>
    </fieldset>
  </div>
  <q-btn  
    @click="submit()" 
    color="primary" 
    label="Submit Entry Point"
    :class="`${isMobile ? '' : 'q-mx-xl'}`" 
  />
</template>

<script setup>
  import { ref, inject, reactive } from 'vue'
  import { useDataStore } from '@/stores/DataStore.ts'
  import { useRouter } from 'vue-router'
  
  const router = useRouter()

  const store = useDataStore()

  const isMobile = inject('isMobile')

  const requiredRule = (val) => (val && val.length > 0) || "This field is required"

  let entryPoint = reactive({
    name: '',
    group: '',
    parameters: []
  })

  const groupOptions = ref([
    'Group 1',
    'Group 2',
    'Group 3',
  ])

  const paramName = ref('')
  const paramType = ref('')
  const paramDefaultValue = ref('')

  const typeOptions = ref([
    'Path',
    'String',
    'Number',
  ])

  const basicInfoForm = ref(null)
  const paramForm = ref(null)


  const columns = [
    { name: 'name', label: 'Name', align: 'left', field: 'name', sortable: true, style: 'flex: 1' },
    { name: 'type', label: 'Type', align: 'left', field: 'parameter_type', sortable: true, style: 'flex: 1' },
    { name: 'defaultValue', label: 'Default Value (optional)', align: 'left', field: 'default_value', sortable: true, style: 'flex: 1' },
  ]

  const params = ref([])

  function addParam() {
    entryPoint.parameters.push({
      name: paramName.value,
      parameter_type: paramType.value,
      default_value: paramDefaultValue.value,
    })
    paramName.value = ''
    paramType.value = null
    paramDefaultValue.value = ''
    paramForm.value.reset()
  }

  function submit() {
    basicInfoForm.value.validate().then(success => {
      if (success) {
        store.entryPoints.push(entryPoint)
        router.push('/entrypoints')
      }
      else {
        // error
      }
    })
  }

</script>
