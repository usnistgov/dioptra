<template>
  <div :class="`row q-mt-lg ${isMobile ? '' : 'q-mx-xl'} q-mb-lg`">
    <div :class="`${isMobile ? 'col-12' : 'col-5'} q-mr-xl`">
      <fieldset>
        <legend>Basic Info</legend>
        <div style="padding: 0 5%">
          <q-form ref="basicInfoForm" greedy>
            <q-input 
              outlined 
              dense 
              v-model.trim="plugin.name"
              :rules="[requiredRule]"
              class="q-mb-sm q-mt-md"
              aria-required="true"
            >
              <template v-slot:before>
                <label :class="`field-label`">Name:</label>
              </template>
            </q-input>
            <q-select
              outlined 
              v-model="plugin.group" 
              :options="loginStore.groups.map((group) => group.name)" 
              dense
              :rules="[requiredRule]"
              aria-required="true"
            >
              <template v-slot:before>
                <div class="field-label">Group:</div>
              </template>  
            </q-select>
          </q-form>
        </div>
      </fieldset>
      <fieldset class="q-mt-lg">
        <legend>Tags</legend>
        <div style="padding: 0 2%" class="row">
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
        </div>
      </fieldset>
    </div>
    <fieldset :class="`${isMobile ? 'col-12 q-mt-lg' : 'col'}`">
      <legend>Plugin Files</legend>
      <div style="padding: 0 5%">
        <BasicTable
          :columns="columns"
          :rows="[]"
          :hideSearch="true"
          :hideEditTable="true"
          @edit="(param, i) => {selectedParam = param; selectedParamIndex = i; showEditParamDialog = true}"
          @delete="(param) => {selectedParam = param; showDeleteDialog = true}"
        />

        <!-- <q-card
          flat
          bordered
          class="q-px-lg q-my-lg"
        >
          <q-card-section class="q-px-none">
            <label class="text-body1">Add Parameter</label>
          </q-card-section>
          <q-form ref="paramForm" greedy @submit.prevent="addParam">
            <q-input 
              outlined 
              dense 
              v-model.trim="parameter.name"
              :rules="[requiredRule]"
              class="q-mb-sm "
              label="Enter Name"
            />
            <q-select
              outlined 
              v-model="parameter.parameter_type" 
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
              v-model.trim="parameter.default_value"
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
        </q-card> -->
      </div>
    </fieldset>
  </div>

  <div :class="`${isMobile ? '' : 'q-mx-xl'} float-right q-mb-lg`">
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
  import { useRoute, useRouter } from 'vue-router'
  import { ref, inject, reactive, computed } from 'vue'
  import { useDataStore } from '@/stores/DataStore.ts'
  import { useLoginStore } from '@/stores/LoginStore.ts'
  import BasicTable from '@/components/BasicTable.vue'

  const store = useDataStore()
  const loginStore = useLoginStore()

  const isMobile = inject('isMobile')

  const route = useRoute()
  const router = useRouter()

  const storePlugin = computed(() => {
    return store.plugins.find((obj) => {
      return obj.id === route.params.id
    })
  })

  const plugin = reactive({
    ...storePlugin.value
  })

  function requiredRule(val) {
    return (val && val.length > 0) || "This field is required"
  }

  let selectedTags = reactive([...plugin.tags])

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

  const basicInfoForm = ref()

  function submit() {
    const index = store.plugins.findIndex((obj) => {
      return obj.id === route.params.id
    })
    plugin.tags = selectedTags
    store.plugins[index] = plugin
    router.push('/plugins')
  }

  const columns = [
    { name: 'name', label: 'Name', align: 'left', field: 'name', sortable: true, },
    { name: 'tasks', label: 'Tasks', align: 'left', field: 'tasks', sortable: true, },
  ]


</script>