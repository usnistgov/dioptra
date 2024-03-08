<template>
  <q-table
    :rows="props.rows"
    :columns="[{ name: 'radio', align: 'center', sortable: false }, ...props.columns]"
    :title="title"
    :filter="filter"
    selection="single"
    v-model:selected="selected"
    row-key="name"
    class="q-mt-lg"
    flat
    bordered
  >
    <template v-slot:header="props">
      <q-tr :props="props">
        <q-th v-for="col in props.cols" :key="col.name" :props="props">
          {{ col.label }}
        </q-th>
      </q-tr>
    </template> 
    <template v-slot:body="props">
      <!-- props.row[field] - field needs to be unique ID, pass this in as a prop, using name for now -->
      <q-tr 
        :class="`${getSelectedColor(props.selected)} cursor-pointer` " 
        :props="props"
        @click="props.selected = !props.selected; radioSelected = props.row.name" 
      >
        <q-td v-for="col in props.cols" :key="col.name" :props="props">
          <q-radio v-model="radioSelected" :val="props.row.name" v-if="col.name === 'radio'" @click="handleRadioClick(props)"/>
          <slot v-bind="props" :name="`body-cell-${col.name}`"></slot>
          <div>
            {{ col.value }}
          </div>
        </q-td>
      </q-tr>
    </template>

    <template #top-right>
      <q-btn color="secondary" icon="edit" label="Edit" class="q-mr-lg" @click="$emit('edit')"  :disabled="!selected.length" />
      <q-btn color="red" icon="sym_o_delete" label="Delete" class="q-mr-lg"  @click="$emit('delete')" :disabled="!selected.length" />
      <q-input v-model="filter" dense placeholder="Search" outlined>
          <template #append>
            <q-icon name="search" />
          </template>
        </q-input>
    </template>
  </q-table>
</template>

<script setup>
  import { ref, watch, computed } from 'vue'
  import { useQuasar } from 'quasar'

  const props = defineProps(['columns', 'rows', 'title'])
  defineEmits(['edit', 'delete'])

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
