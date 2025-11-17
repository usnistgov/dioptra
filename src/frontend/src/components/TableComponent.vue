<template>
  <q-table
    ref="tableRef"
    :rows="props.rows"
    :columns="finalColumns"
    :title="title"
    :filter="filter"
    :selection="selection"
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
    :hideBottom="props.hideBottom && rows.length > 0"
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
        :class="`${getSelectedColor(props.selected)} cursor-pointer ${highlightRow(props)} ${disableRow(props)}` " 
        :props="props"
        @click="openResource(props); selectResource(props)"
        @auxclick="onAuxClick($event, props)"
      >
        <q-td v-for="col in props.cols" :key="col.name" :props="props" :style="props.expand ? {'border-bottom': 'none'} : {}">
          <q-menu
            v-if="selection !== 'multiple'"

            context-menu
            @show="props.selected = true"
          >
            <q-list dense>
              <q-item clickable v-close-popup @click="openResource(props)">
                <q-item-section>Open</q-item-section>
              </q-item>
              <q-item clickable v-close-popup @click="openResource(props, true)">
                <q-item-section>Open In New Tab</q-item-section>
              </q-item>
            </q-list>
          </q-menu>
          <slot v-bind="props" :name="`body-cell-${col.name}`">
            <div v-if="typeof(col.value) === 'boolean'" class="text-body1">
              {{ col.value ? '✅' : 	'❌'}}
            </div>
            <div v-else-if="col.name === 'name'">
              {{ truncateString(props.row.name, 20) }}
              <q-tooltip v-if="props.row.name.length > 20" max-width="30vw" style="overflow-wrap: break-word">
                {{ props.row.name }}
              </q-tooltip>
            </div>
            <div v-else-if="col.name === 'description'">
              {{ truncateString(props.row.description, 40) }}
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
              @click.stop="props.expand = !props.expand" 
              :icon="props.expand ? 'expand_less' : 'expand_more'" 
            />
          </slot>
        </q-td>
      </q-tr>
      <q-tr v-show="props.expand" :props="props" :class="`${highlightRow(props)}`">
        <q-td colspan="100%">
          <!-- <div class="text-left ">Additional info for {{ props.row.name }}.</div> -->
          <slot name="expandedSlot" :row="props.row" :rowProps="props" />
        </q-td>
      </q-tr>
    </template>

    <template #top-right>
      <slot name="jobLogSlot" />
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
  import { ref, watch, computed, onMounted, onBeforeUnmount } from 'vue'
  import { useQuasar } from 'quasar'
  import * as notify from '../notify'

  const props = defineProps({
  columns: Array,
  rows: Array,
  title: String,
  showExpand: Boolean,
  hideCreateBtn: Boolean,
  showToggleDraft: Boolean,
  hideSearch: Boolean,
  disableSelect: Boolean,
  hideOpenBtn: Boolean,
  hideDeleteBtn: Boolean,
  hideBottom: Boolean,
  rightCaption: String,
  showAll: Boolean,
  highlightRow: Boolean,
  selection: String,
  disabledRowKeys: {
    type: Array,
    default: []
  },
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

  const selection =  computed(() => {
    if(props.disableSelect) return 'none'
    if(props.selection === 'multiple') return 'multiple'
    return 'single'
  })

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
    else tableProps.selected = !tableProps.selected
  }

  function openResource(tableProps, openTab = false) {
    console.log('openTab = ', openTab)
    if(props.disableSelect || props.selection === 'multiple') return
    tableProps.selected = true
    emit('edit', openTab)
  }

  function deleteResource(tableProps) {
    tableProps.selected = true
    if(props.disableSelect) return
    emit('delete')
  }

  watch(showDrafts, (newVal, oldVal) => {
    if(newVal !== oldVal) selected.value = []
  })

  function getSelectedColor(selected) {
    if(darkMode.value && selected) return 'bg-deep-purple-10'
    else if(selected) return 'bg-blue-grey-1'
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

  let invalidSearchNotification = notify.wait()

  // watch(() => props.rows, (newVal) => {
  //   loading.value = false
  // })

  function onRequest(props) {
    const searchError = checkSearch(props.filter)

    invalidSearchNotification()
    if(searchError.length) {
      invalidSearchNotification = notify.wait(searchError)
      return
    }
    pagination.value = { ...props.pagination }
    const paginationOptions = props.pagination
    const { page, rowsPerPage } = props.pagination
    const index = (page - 1) * rowsPerPage
    paginationOptions.index = index
    paginationOptions.search = props.filter
    emit('request', paginationOptions, showDrafts.value)
  }

  function checkSearch(string) {
    const trimmed = string.trimEnd()

    // if search ends with unescaped colon
    if (
      trimmed.length > 1 &&
      trimmed.endsWith(':') &&
      trimmed[trimmed.length - 2] !== '\\' &&
      trimmed[trimmed.length - 2] !== ':'
    ) {
      return `Enter a value after the trailing colon.`
    }

    // if search ends with unescaped comma
    if (
      trimmed.length > 1 &&
      trimmed.endsWith(',') &&
      trimmed[trimmed.length - 2] !== '\\' &&
      trimmed[trimmed.length - 2] !== ','
    ) {
      return `Trailing comma.  Please remove or add new search criteria.`
    }

    // Count unescaped single and double quotes
    let singleQuotes = 0
    let doubleQuotes = 0

    for (let i = 0; i < trimmed.length; i++) {
      const char = trimmed[i]
      const prevChar = trimmed[i - 1]

      if (char === "'" && prevChar !== '\\') {
        singleQuotes++
      } else if (char === '"' && prevChar !== '\\') {
        doubleQuotes++
      }
    }

    if (singleQuotes % 2 !== 0 || doubleQuotes % 2 !== 0) {
      return `Unclosed quotation mark. Please close all quotes.`
    }

    return ''
  }

  onBeforeUnmount(() => {
    invalidSearchNotification()
  })

  function updateTotalRows(totalRows) {
    pagination.value.rowsNumber = totalRows
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

function highlightRow(rowProps) {
  if(props.disabledRowKeys.includes(rowProps.row[props.rowKey])) return
  if(!props.highlightRow) return
  if(!rowProps.expand) return
  if(darkMode.value) {
    return 'bg-yellow-8 text-black'
  } else {
    return 'bg-yellow-8'
  }
}

function disableRow(rowProps) {
  if(props.disabledRowKeys.includes(rowProps.row[props.rowKey])) {
    return 'disabled-row'
  }
}

function truncateString(str, limit) { 
  if(!str) return ''
  if(str?.length < limit) return str 
  return str?.slice(0, limit > 3 ? limit - 3 : limit) + '...'; 
}

function onAuxClick(event, tableProps) {
  if (event.button === 1) {   // middle mouse button only
    openResource(tableProps, true)
  }
}

</script>

<style scoped>

  .disabled-row {
    pointer-events: none;
    opacity: 0.5;
  }

</style>
