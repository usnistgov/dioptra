<template>
  <q-table
    ref="tableRef"
    :rows="props.rows"
    :columns="finalColumns"
    :title="title"
    :filter="filter"
    selection="single"
    v-model:selected="selected"
    :row-key="props.rowKey"
    :class="'q-mt-lg'"
    flat
    bordered
    dense
    v-model:pagination="pagination"
    @request="onRequest"
    :tabindex="props.disableSelect ? '' : '0'"
    @keydown="keydown"
    :rows-per-page-options="props.showAll ? [0] : [5,10,15,20,25,50,0]"
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
        @click="openResource(props)"
        style="padding-left: 50px;"
      >
        <q-td v-for="col in props.cols" :key="col.name" :props="props">
          <slot v-bind="props" :name="`body-cell-${col.name}`">
            <div v-if="typeof(col.value) === 'boolean'" class="text-body1">
              {{ col.value ? '✅' : 	'❌'}}
            </div>
            <div v-else-if="col.name === 'name'">
              {{ props.row.name?.length <= 18 ? props.row.name : props.row.name?.replace(/(.{17})..+/, "$1…") }}
              <q-tooltip v-if="props.row.name.length > 18" max-width="30vw" style="overflow-wrap: break-word">
                {{ props.row.name }}
              </q-tooltip>
            </div>
            <div v-else-if="col.name === 'description'">
              {{ props.row.description?.length <= 40 ? props.row.description : props.row.description?.replace(/(.{39})..+/, "$1…") }}
              <q-tooltip v-if="props.row.description?.length > 40" max-width="30vw" style="overflow-wrap: break-word">
                {{ props.row.description }}
              </q-tooltip>
            </div>
            <div v-else-if="col.name === 'tags'">
              <q-chip
                v-for="(tag, i) in props.row.tags"
                :key="i"
                color="primary" 
                text-color="white"
                clickable
                @click.stop
                class="q-my-none"
              >
                {{ tag.name.length <= 18 ? tag.name : tag.name.replace(/(.{17})..+/, "$1…") }}
                <q-tooltip v-if="tag.name.length > 18" max-width="30vw" style="overflow-wrap: break-word">
                  {{ tag.name }}
                </q-tooltip>
              </q-chip>
              <q-btn
                round
                size="xs"
                icon="add"
                @click.stop="$emit('editTags', props.row)"
                color="grey-5"
                text-color="black"
                class="q-ml-xs"
              />
            </div>
            <div v-else-if="col.name === 'createdOn' || col.name === 'lastModifiedOn'">
              {{ formatDate(col.value) }}
            </div>
            <div v-else-if="!Array.isArray(col.value)">
              <!-- if value is an array, then render it with a custom slot -->
              {{ col.value }}
            </div>
            <!-- <q-btn
              v-if="col.name === 'open'"
              round
              color="primary"
              icon="edit"
              size="sm"
              @click.stop="openResource(props)"
            /> -->
            <q-btn
              v-if="col.name === 'delete'"
              round
              color="negative"
              icon="sym_o_delete"
              size="sm"
              @click.stop="deleteResource(props)"
            />
            <q-btn 
              v-if="col.name === 'expand'" 
              size="md" flat dense round  
              @click="props.expand = !props.expand" 
              :icon="props.expand ? 'expand_less' : 'expand_more'" 
              @click.stop="emitExpand(props.expand, props.row)"
            />
          </slot>
        </q-td>
      </q-tr>
      <q-tr v-show="props.expand" :props="props">
        <q-td colspan="100%">
          <!-- <div class="text-left ">Additional info for {{ props.row.name }}.</div> -->
          <slot name="expandedSlot" :row="props.row" />
        </q-td>
      </q-tr>
    </template>

    <template #top-right>
      <q-btn
        v-if="!hideCreateBtn" 
        color="primary" 
        icon="add" 
        label="Create" 
        class="q-mr-lg" 
        @click="$emit('create')"
      />
      <q-input 
        v-if="!hideSearch" 
        v-model="filter" 
        debounce="300" 
        dense 
        placeholder="Search" 
        outlined
      >
        <template #append>
          <q-icon name="search" />
        </template>
      </q-input>
      <caption v-if="props.rightCaption" class="text-caption">
        {{ props.rightCaption }}
      </caption>
    </template>
    <template #top-left v-if="showToggleDraft">
      <q-btn-toggle
        v-model="showDrafts"
        toggle-color="primary"
        push
        style="box-shadow: 0 0 0 0.5px grey"
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

  const props = defineProps({
  columns: Array,
  rows: Array,
  title: String,
  showExpand: Boolean,
  hideCreateBtn: Boolean,
  showToggleDraft: Boolean,
  hideSearch: Boolean,
  disableSelect: Boolean,
  disableUnselect: Boolean,
  hideOpenBtn: Boolean,
  hideDeleteBtn: Boolean,
  rightCaption: String,
  showAll: Boolean,
  rowKey: {
    type: String,
    default: 'id'
  },
})
  const emit = defineEmits([
    'edit', 
    'delete', 
    'request', 
    'expand', 
    'editTags', 
    'create'
  ])

  const finalColumns = computed(() => {
    let defaultColumns = [ ...props.columns ]
    // if(!props.hideOpenBtn) {
    //   defaultColumns.push({ name: 'open', align: 'center', sortable: false, label: 'Open', headerStyle: 'width: 50px' })
    // }
    if(!props.hideDeleteBtn) {
      defaultColumns.push({ name: 'delete', align: 'center', sortable: false, label: 'Delete', headerStyle: 'width: 50px' })
    }
    if(props.showExpand) {
      defaultColumns.push({ name: 'expand', align: 'center', sortable: false, label: 'Expand', headerStyle: 'width: 50px' })
    }
    if(showDrafts.value) {
      defaultColumns = defaultColumns.map(column => ({
        ...column,
        sortable: false
      }))
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
  //const showDrafts = ref(false)
  const showDrafts = defineModel('showDrafts')

  function selectResource(tableProps) {
    if(props.disableSelect) return
    if(props.disableUnselect) tableProps.selected = true
    else tableProps.selected = !tableProps.selected
  }

  function openResource(tableProps) {
    if(props.disableSelect) return
    tableProps.selected = true
    emit('edit')
  }

  function deleteResource(tableProps) {
    tableProps.selected = true
    if(props.disableSelect) return
    emit('delete')
  }

  watch(() => props.rows, (newVal) => {
    // when viewing history, auto select first (latest) row
    if (newVal.length > 0 && props.rowKey === 'snapshot') {
      if (tableRef.value && newVal[0]) {
        selected.value = [newVal[0]]
      }
    }
  }, { deep: true })

  watch(showDrafts, (newVal, oldVal) => {
    if(newVal !== oldVal) selected.value = []
  })

  function getSelectedColor(selected) {
    if(darkMode.value && selected) return 'bg-deep-purple-10'
    // else if(selected) return 'bg-blue-grey-1'
  }

  const pagination = ref({
    page: 1,
    rowsPerPage: props.showAll ? 0 : 15,
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

  function emitExpand(expanded, row) {
    if(expanded) {
      emit('expand', row)
    }
  }

  function formatDate(dateString) {
    const options = { year: '2-digit', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: true }
    return new Date(dateString).toLocaleString('en-US', options)
  }

  function keydown(event) {
  // exit if no rows or selection disabled
  if(!props.rows || props.rows.length === 0) return
  if(props.disableSelect) return

  // Get the current index of the selected row
  const currentIndex = props.rows.findIndex(row => row[props.rowKey] === selected.value[0]?.[props.rowKey])
  if(event.key === 'ArrowUp') {
    // Navigate to the previous row (if not at the first row)
    if(currentIndex > 0) {
      const prevRow = props.rows[currentIndex - 1]
      selected.value = [prevRow]
    }
  } else if(event.key === 'ArrowDown') {
    // Navigate to the next row (if not at the last row)
    if (currentIndex < props.rows.length - 1) {
      const nextRow = props.rows[currentIndex + 1]
      selected.value = [nextRow]
    }
  } else if(event.key === 'Enter') {
    emit('edit')
  }
}

</script>
