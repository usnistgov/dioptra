<template>
  <q-table
    ref="tableRef"
    v-bind="$attrs" 
    :rows="props.rows"
    :columns="finalColumns"
    v-model:selected="selected"
    v-model:pagination="pagination"
    @request="onRequest"
    :filter="filter" 
    :rows-per-page-options="props.showAll ? [0] : [5,10,15,20,25,50,0]"
    flat bordered dense
    class="q-mt-lg"
    
    :tabindex="props.disableSelect ? '' : '0'"
    @keydown="keydown"
  >
    <template v-slot:header="props">
      <q-tr :props="props">
        <q-th 
          v-for="col in props.cols" 
          :key="col.name" 
          :class="col.__thClass"
          @click="col.sortable ? props.sort(col) : null"
        >
          <CellHeader 
            :col="col" 
            :sorted="pagination.sortBy === col.name"
            :descending="pagination.descending"
          />
        </q-th>
      </q-tr>
    </template>
      

    <template v-slot:body="props">
      <q-tr 
        :class="[getSelectedColor(props.selected), highlightRow(props), disableRow(props), 'cursor-pointer']" 
        :props="props"
        @click="openResource(props); selectResource(props)"
      >
        <q-td v-for="col in props.cols" :key="col.name" :props="props">
          <slot :name="`body-cell-${col.name}`" v-bind="props">
                        
            <ResourceName
              v-if="col.styleType === 'resource-name'"
              :text="col.value"
              :concept-type="col.conceptType"
              :max-length="col.maxLength"
              :max-width="col.maxWidth"
              :use-quotes="col.useQuotes"
              :text-type="col.textType"
              :includeIcon="col.includeIcon"
            />

            <IconID 
              v-else-if="col.styleType === 'icon-id'"
              :type="col.conceptType" 
              :label="col.value?.id || col.value"
              :row-id="col.value?.id"
              :include-icon="col.includeIcon"
            />

            <BadgeIcon 
              v-else-if="col.styleType === 'icon-badge'"
              :type="col.conceptType" 
              :label="getLabel(col.value)"
              :row-id="col.value?.id"
              :size="col.size"
              :chipType="col.chipType"
              :uppercase="col.uppercase"
              :formatLabel="col.formatLabel"
            />

            <MultiBadgeIcon
              v-else-if="col.styleType === 'multi-badge'"
              :items="col.value"
              :concept-type="col.conceptType"
            />

            <CellLongText
              v-else-if="col.styleType === 'long-text'"
              :text="col.value"
              :max-length="col.maxLength"
              :max-width="col.maxWidth"
              :use-quotes="col.useQuotes"
              :text-type="col.textType"
              :text-color="col.textColor"  
              />

            <ParameterList
              v-else-if="col.styleType === 'parameter-list'"
              :items="col.value"
              :type="col.parameterType || 'output'"
            />

            <TagList
              v-else-if="col.styleType === 'tag-list'"
              :tags="col.value"
              :row="props.row"
              @add="(row) => emit('editTags', row)"
            />

            <div 
              v-else-if="col.styleType === 'date'" 
              :class="col.textColor || 'text-grey-8'" 
              style="font-size: 13px"
            >
              {{ formatDate(col.value) }}
            </div>

            <div v-else-if="typeof col.value === 'boolean'" class="text-body1">
              {{ col.value ? '✅' : '❌' }}
            </div>

            <template v-else>
              {{ col.value }}
            </template>

            <q-btn v-if="col.name === 'delete'" icon="sym_o_delete" color="negative" flat round size="sm" @click.stop="deleteResource(props)" />
            <q-btn v-if="col.name === 'expand'" :icon="props.expand ? 'expand_less' : 'expand_more'" flat round size="sm" @click.stop="props.expand = !props.expand" />
          </slot>
        </q-td>
      </q-tr>

      <q-tr v-show="props.expand" :props="props" :class="highlightRow(props)">
        <q-td colspan="100%">
          <slot name="expandedSlot" :row="props.row" :rowProps="props" />
        </q-td>
      </q-tr>
    </template>

    <template v-slot:top-right>
      
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
        bg-color="white"
      >
        <template #append>
          <q-icon name="search" />
        </template>
      </q-input>

      <caption v-if="props.rightCaption" class="text-caption q-ml-sm">
        {{ props.rightCaption }}
      </caption>
    </template>

    <template v-slot:top-left v-if="showToggleDraft">
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
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useQuasar } from 'quasar'
import BadgeIcon from './cells/BadgeIcon.vue'
import IconID from './cells/IconID.vue'
import CellHeader from './cells/CellHeader.vue'
import CellLongText from './cells/CellLongText.vue'
import TagList from './cells/TagList.vue'
import MultiBadgeIcon from './cells/MultiBadgeIcon.vue' 
import ParameterList from './cells/ParameterList.vue'
import ResourceName from './cells/ResourceName.vue'
import * as notify from '../../notify'

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
  disabledRowKeys: { type: Array, default: [] },
  rowKey: { type: String, default: 'id' },
})

const emit = defineEmits(['edit', 'delete', 'request', 'create', 'editTags'])
const $q = useQuasar()
const filter = ref('')
const selected = defineModel('selected')
const showDrafts = defineModel('showDrafts')

const darkMode = computed(() => {
  if($q.dark.mode === 'auto') return window.matchMedia('(prefers-color-scheme: dark)').matches
  return $q.dark.mode
})

// Columns Logic
const finalColumns = computed(() => {
  let defaultColumns = [ ...props.columns ]
  if(!props.hideDeleteBtn) {
    defaultColumns.push({ name: 'delete', align: 'center', sortable: false, label: 'Delete', headerStyle: 'width: 50px' })
  }
  if(props.showExpand) {
    defaultColumns.push({ name: 'expand', align: 'center', sortable: false, label: 'Expand', headerStyle: 'width: 50px' })
  }
  if(showDrafts.value) {
    defaultColumns = defaultColumns.map(column => ({ ...column, sortable: false }))
  }
  return defaultColumns
})

const pagination = ref({
  page: 1,
  rowsPerPage: props.showAll ? 0 : 15,
  sortBy: '',
  descending: false,
})
function keydown(event) {
  // Exit if no rows or selection disabled
  if(!props.rows || props.rows.length === 0) return
  if(props.disableSelect) return

  // Get the current index of the selected row
  const currentIndex = props.rows.findIndex(row => row[props.rowKey] === selected.value[0]?.[props.rowKey])
  
  if(event.key === 'ArrowUp') {
    event.preventDefault() // Prevent scrolling the page
    // Navigate to the previous row
    if(currentIndex > 0) {
      const prevRow = props.rows[currentIndex - 1]
      selected.value = [prevRow]
    }
  } else if(event.key === 'ArrowDown') {
    event.preventDefault() // Prevent scrolling the page
    // Navigate to the next row
    if (currentIndex < props.rows.length - 1) {
      const nextRow = props.rows[currentIndex + 1]
      selected.value = [nextRow]
    }
  } else if(event.key === 'Enter') {
    // If a row is selected, trigger the edit/open event
    if(selected.value.length > 0) {
      emit('edit', selected.value[0])
    }
  }
}
const tableRef = ref()
onMounted(() => {
  tableRef.value.requestServerInteraction()
})

defineExpose({ refreshTable, updateTotalRows })
function refreshTable() {
  tableRef.value.requestServerInteraction()
}

// --- SEARCH & REQUEST LOGIC ---
let invalidSearchNotification = notify.wait()

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
  const trimmed = (string || '').trimEnd();
  if (trimmed.length > 1 && trimmed.endsWith(':') && trimmed[trimmed.length - 2] !== '\\' && trimmed[trimmed.length - 2] !== ':') return `Enter a value after the trailing colon.`
  if (trimmed.length > 1 && trimmed.endsWith(',') && trimmed[trimmed.length - 2] !== '\\' && trimmed[trimmed.length - 2] !== ',') return `Trailing comma.`
  let singleQuotes = 0; let doubleQuotes = 0
  for (let i = 0; i < trimmed.length; i++) {
    const char = trimmed[i]; const prevChar = trimmed[i - 1]
    if (char === "'" && prevChar !== '\\') singleQuotes++
    else if (char === '"' && prevChar !== '\\') doubleQuotes++
  }
  if (singleQuotes % 2 !== 0 || doubleQuotes % 2 !== 0) return `Unclosed quotation mark.`
  return ''
}

onBeforeUnmount(() => { invalidSearchNotification() })

function updateTotalRows(totalRows) {
  pagination.value.rowsNumber = totalRows
}

// --- HELPERS ---
function getLabel(val) {
  if (val === null || val === undefined) return '-'
  return typeof val === 'object' ? val.name : val
}

function formatDate(dateString) {
  if(!dateString) return '-'
  const options = { year: '2-digit', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: true }
  return new Date(dateString).toLocaleString('en-US', options)
}

function selectResource(tableProps) {
  if(props.disableSelect || props.selection !== 'multiple') return
  tableProps.selected = !tableProps.selected
}

function openResource(tableProps) {
  if (props.disableSelect || props.selection === 'multiple') return;
  tableProps.selected = true;
  emit('edit', tableProps.row); 
}

function deleteResource(tableProps) {
  if(!props.disableSelect) {
     tableProps.selected = true
  }
  emit('delete', tableProps.row)
}

watch(showDrafts, (newVal, oldVal) => {
  if(newVal !== oldVal) selected.value = []
})

function getSelectedColor(selected) {
  if(darkMode.value && selected) return 'bg-deep-purple-10'
  else if(selected) return 'bg-blue-grey-1'
}

function highlightRow(rowProps) {
  if(props.disabledRowKeys.includes(rowProps.row[props.rowKey])) return
  if(!props.highlightRow) return
  if(!rowProps.expand) return
  return darkMode.value ? 'bg-yellow-8 text-black' : 'bg-yellow-8'
}

function disableRow(rowProps) {
  if(props.disabledRowKeys.includes(rowProps.row[props.rowKey])) return 'disabled-row'
}
</script>

<style scoped>
  .disabled-row {
    pointer-events: none;
    opacity: 0.5;
  }
</style>