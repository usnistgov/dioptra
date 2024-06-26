<template>
  <q-table
    ref="tableRef"
    :rows="props.rows"
    :columns="finalColumns"
    :title="title"
    :filter="filter"
    selection="single"
    v-model:selected="selected"
    row-key="id"
    :class="`q-mt-lg ${isMobile ? '' : 'q-mx-xl' }`"
    flat
    bordered
    dense
    v-model:pagination="pagination"
    @request="onRequest"
  >
    <template v-slot:header="props">
      <q-tr :props="props">
        <q-th v-for="col in props.cols" :key="col.name" :props="props">
          {{ col.label }}
        </q-th>
      </q-tr>
    </template> 
    <template v-slot:body="props">
      <!-- props.row[field] - field needs to be unique ID, pass this in as a prop, or just use id -->
      <q-tr 
        :class="`${getSelectedColor(props.selected)} cursor-pointer` " 
        :props="props"
        @click="props.selected = !props.selected; radioSelected = props.row.id" 
      >
        <q-td v-for="col in props.cols" :key="col.name" :props="props">
          <q-radio 
            v-model="radioSelected" 
            :val="props.row.id"
            v-if="col.name === 'radio'" 
            @click="handleRadioClick(props)"
          />
          <slot v-bind="props" :name="`body-cell-${col.name}`">
            <div v-if="typeof(col.value) === 'boolean'" class="text-body1">
              {{ col.value ? '✅' : 	'❌'}}
            </div>
            <div v-else>
              {{ col.value }}
            </div>
          </slot>
          <q-btn v-if="col.name === 'expand'" size="lg" flat dense round  @click="props.expand = !props.expand" :icon="props.expand ? 'expand_less' : 'expand_more'" @click.stop />
        </q-td>
      </q-tr>
      <q-tr v-show="props.expand" :props="props">
        <q-td colspan="100%">
          <!-- <div class="text-left ">Additional info for {{ props.row.name }}.</div> -->
          <slot name="expandedSlot" :row="props.row" />
        </q-td>
      </q-tr>
    </template>

    <template #top-right v-if="!hideButtons">
      <q-btn color="secondary" icon="edit" label="Edit" class="q-mr-lg" @click="$emit('edit')"  :disabled="!selected.length" />
      <q-btn color="negative" icon="sym_o_delete" label="Delete" class="q-mr-lg"  @click="$emit('delete')" :disabled="!selected.length" />
      <q-input v-model="filter" debounce="300" dense placeholder="Search" outlined>
          <template #append>
            <q-icon name="search" />
          </template>
        </q-input>
    </template>
    <template #top-left v-if="!hideButtons">
      <q-btn-toggle
        v-model="showDrafts"
        toggle-color="primary"
        push
        :options="[
          {label: title, value: false},
          {label: 'Drafts', value: true},
        ]"
        @click="refreshTable"
      />
    </template>
  </q-table>
</template>

<script setup>
  import { ref, watch, computed, inject, onMounted } from 'vue'
  import { useQuasar } from 'quasar'
  
  const isMobile = inject('isMobile')

  const props = defineProps(['columns', 'rows', 'title', 'showExpand', 'hideButtons'])
  const emit = defineEmits(['edit', 'delete', 'request'])

  const finalColumns = computed(() => {
    let defaultColumns = [
      { name: 'radio', align: 'center', sortable: false, label: 'Select', headerStyle: 'width: 100px' },
       ...props.columns,
      ]
    if(props.showExpand) {
      defaultColumns.push({ name: 'expand', align: 'center', sortable: false, label: 'Expand' })
    }
    return defaultColumns
  })

  const $q = useQuasar()

  const darkMode = computed(() => {
    if($q.dark.mode === 'auto') {
      return window.matchMedia('(prefers-color-scheme: dark)').matches
    }
    return $q.dark.mode
  })

  const filter = ref('')
  const selected = defineModel('selected')
  const radioSelected = ref('')
  //const showDrafts = ref(false)
  const showDrafts = defineModel('showDrafts')

  function handleRadioClick(props) {
    console.log('props = ', props)
    props.selected = !props.selected
    event.stopPropagation()
  }

  watch(selected, (newVal) => {
    if(newVal.length === 0) radioSelected.value = ''
  })

  watch(showDrafts, (newVal, oldVal) => {
    if(newVal !== oldVal) selected.value = []
  })

  function getSelectedColor(selected) {
    if(darkMode.value && selected) return 'bg-deep-purple-10'
    else if(selected) return 'bg-blue-grey-1'
  }

  const pagination = ref({
    page: 1,
    rowsPerPage: 5,
    rowsNumber: 10,
    sortBy: '',
    descending: false,
  })

  const tableRef = ref()
  onMounted(() => {
    // get initial data from server (1st page)
    tableRef.value.requestServerInteraction()
  })

  defineExpose({ refreshTable, updateTotalRows })
  function refreshTable() {
    tableRef.value.requestServerInteraction()
  }

  function onRequest(props) {
    pagination.value = { ...props.pagination }
    const paginationOptions = props.pagination
    const { page, rowsPerPage } = props.pagination
    const index = (page - 1) * rowsPerPage
    paginationOptions.index = index
    paginationOptions.search = props.filter
    emit('request', paginationOptions, showDrafts.value)
  }

  function updateTotalRows(totalRows) {
    pagination.value.rowsNumber = totalRows
  }

</script>
