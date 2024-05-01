<template>
  <div :class="`row q-mt-lg ${isMobile ? '' : 'q-mx-xl'} q-mb-lg`">
    <fieldset :class="`${isMobile ? 'col-12' : 'col-6'} q-mr-xl`">
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
    <fieldset :class="`${isMobile ? 'col-12 q-mt-lg' : 'col'}`"> 
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
            class="q-my-lg" 
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

  <div :class="`row q-mt-lg ${isMobile ? '' : 'q-mx-xl'} q-mb-lg`">
    <fieldset :class="`${isMobile ? 'col-12 q-mt-lg' : 'col-6'}  q-mr-xl`">
      <legend>Plugin Files List</legend>
      <TableComponent 
        :rows="plugin.files"
        :columns="fileColumns"
        title="Plugin Files"
        v-model="selected"
        @edit="store.editMode = true; router.push(`/plugins/${selected[0].id}`)"
        :hideButtons="true"
      />
    </fieldset>
    <fieldset :class="`${isMobile ? 'col-12 q-mt-lg' : 'col'}`">
      <legend>Add/Edit File</legend>
      <div style="padding: 0 5%">
        <q-form ref="basicInfoForm" >
          <q-input 
            outlined 
            dense 
            v-model.trim="pluginFile.name"
            :rules="[requiredRule]"
            class="q-mb-sm q-mt-md"
            aria-required="true"
            :lazy-rules="true"
          >
            <template v-slot:before>
              <label :class="`field-label`">Filename:</label>
            </template>
          </q-input>
        </q-form>

        <!-- <div class="row q-mb-lg">
          <CodeEditor 
            v-model="pluginFile.contents"
            placeholder="#Enter Plugin File contents here..."
            style="width: 0; 
            flex-grow: 1;"
          />
        </div> -->

        <div class="row q-mb-lg">
          <q-btn
            label="Edit Code"
            color="primary"
            @click="showCodeDialog = true;"
            class="col q-mr-lg"
          />

          <q-file
            v-model="uploadedFile"
            label="Upload Python File"
            outlined
            use-chips
            dense
            accept=".py, text/x-python"
            @update:model-value="processFile"
            class="col"
          >
            <template v-slot:prepend>
              <q-icon name="attach_file" />
            </template>
          </q-file>
        </div>

        <label for="taskTable">Plugin Tasks</label>
        <BasicTable
          :columns="taskColumns"
          :rows="[]"
          :hideSearch="true"
          :hideEditTable="true"
          id="taskTable"
          @edit="(param, i) => {selectedParam = param; selectedParamIndex = i; showEditParamDialog = true}"
          @delete="(param) => {selectedParam = param; showDeleteDialog = true}"
        />
        <q-form ref="paramForm" greedy @submit.prevent="addTask" class="q-mt-lg">
            <q-input 
              outlined 
              dense 
              v-model.trim="task.name"
              :rules="[requiredRule]"
              class="q-mb-sm "
              label="Task Name"
            />
            <q-select
              outlined 
              v-model="task.input_params" 
              :options="[]" 
              dense
              :rules="[requiredRule]"
              aria-required="true"
              class="q-mb-sm"
              label="Task Input Params"
            />
            <q-input 
              outlined 
              dense 
              v-model.trim="task.output_params"
              class="q-mb-sm"
              label="Task Output Params"
            />
            <q-card-actions align="right">
              <q-btn
                round
                color="secondary"
                icon="add"
                type="submit"
              >
                <span class="sr-only">Add Task</span>
                <q-tooltip>
                  Add Task
                </q-tooltip>
              </q-btn>
            </q-card-actions>
          </q-form>
        <div :class="`float-right q-my-lg`">
          <q-btn  
            to="/plugins"
            color="negative" 
            label="Cancel"
            class="q-mr-lg"
          />
          <q-btn  
            @click="submitFile()" 
            color="primary" 
            :label="selected.length ? 'Save File' : 'Add File'"
            type="submit"
          />
        </div>
      </div>
    </fieldset>
  </div>

  selected: {{ selected }}

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

  <CodeEditorDialog
    v-model:showDialog="showCodeDialog"
    v-model:code="pluginFile.contents"
  >
    <template #title>
      <label id="modalTitle">
        {{pluginFile.name || 'New File'}}
      </label>
    </template>
  </CodeEditorDialog>
</template>

<script setup>
  import { useRoute, useRouter } from 'vue-router'
  import { ref, inject, reactive, computed, watch } from 'vue'
  import { useDataStore } from '@/stores/DataStore.ts'
  import { useLoginStore } from '@/stores/LoginStore.ts'
  import BasicTable from '@/components/BasicTable.vue'
  import TableComponent from '@/components/TableComponent.vue'
  import CodeEditor from '@/components/CodeEditor.vue'
  import CodeEditorDialog from '@/dialogs/CodeEditorDialog.vue'

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

  function submitFile() {
    
  }

  function addTask() {

  }

  const taskColumns = [
    { name: 'name', label: 'Name', align: 'left', field: 'name', sortable: true, },
    { name: 'input_params', label: 'Input Params', align: 'left', field: 'input_params', sortable: true, },
    { name: 'output_params', label: 'Output Params', align: 'left', field: 'output_params', sortable: true, },
  ]

  const selected = ref([])

  const pluginFile = computed(() => {
    if(selected.value.length) {
      return JSON.parse(JSON.stringify(selected.value[0]))
    }
    return {
      filename: '',
      contents: '',
      tasks: []
    }
  })

  const task = ref({
    name: '',
    input_params: '',
    output_params: ''
  })

  const fileColumns = [
    { name: 'filename', label: 'Filename', align: 'left', field: 'name', sortable: true, },
    { name: 'tasks', label: 'Number of Tasks', align: 'left', field: 'tasks', sortable: true, },
  ]

  const showCodeDialog = ref(false)
  const uploadedFile = ref(null)

  console.log('uploadedFile = ', uploadedFile.value)

  watch(selected, (newVal) => {
    // uploadedFile.value = null
  })

  function processFile() {
    const file = uploadedFile.value
    if (!file) {
      pluginFile.value.contents = ''
      return
    }
    const reader = new FileReader()
    reader.onload = (e) => {
      pluginFile.value.contents = e.target.result;
    }
    reader.onerror = (e) => {
      console.log('error = ', e)
    }
    reader.readAsText(file); // Reads the file as text
  }

</script>