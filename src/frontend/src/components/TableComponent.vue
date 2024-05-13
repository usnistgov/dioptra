<template>
  <q-table
    :rows="props.rows"
    :columns="finalColumns"
    :title="title"
    :filter="filter"
    selection="single"
    v-model:selected="selected"
    row-key="name"
    :class="`q-mt-lg ${isMobile ? '' : 'q-mx-xl' }`"
    flat
    bordered
    dense
    :pagination="pagination"
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
          <div class="text-left ">Additional info for {{ props.row.name }}.</div>
          <slot name="expandedSlot" :row="props.row" />
        </q-td>
      </q-tr>
    </template>

    <template #top-right v-if="!hideButtons">
      <q-btn color="secondary" icon="edit" label="Edit" class="q-mr-lg" @click="$emit('edit')"  :disabled="!selected.length" />
      <q-btn color="negative" icon="sym_o_delete" label="Delete" class="q-mr-lg"  @click="$emit('delete')" :disabled="!selected.length" />
      <q-input v-model="filter" dense placeholder="Search" outlined>
          <template #append>
            <q-icon name="search" />
          </template>
        </q-input>
    </template>
  </q-table>
</template>

<script setup>
  import { ref, watch, computed, inject } from 'vue'
  import { useQuasar } from 'quasar'
  
  const isMobile = inject('isMobile')

  const props = defineProps(['columns', 'rows', 'title', 'pagination', 'showExpand', 'hideButtons'])
  defineEmits(['edit', 'delete'])

  const finalColumns = computed(() => {
    let defaultColumns = [
      { name: 'radio', align: 'center', sortable: false, label: 'Select' },
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
  const selected = defineModel()
  const radioSelected = ref('')

  function handleRadioClick(props) {
    console.log('props = ', props)
    props.selected = !props.selected
    event.stopPropagation()
  }

  watch(selected, (newVal) => {
    if(newVal.length === 0) radioSelected.value = ''
  })

  function getSelectedColor(selected) {
    if(darkMode.value && selected) return 'bg-deep-purple-10'
    else if(selected) return 'bg-blue-grey-1'
  }

</script>
