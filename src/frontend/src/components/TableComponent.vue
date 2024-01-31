<template>
  <q-table
    :rows="props.rows"
    :columns="props.columns"
    :title="title"
    :filter="filter"
    selection="single"
    v-model:selected="selected"
    row-key="name"
    class="q-mt-lg"
    flat
    bordered
  >
    <template #top-right>
      <q-btn color="secondary" icon="edit" label="Edit" class="q-mr-lg"  :disabled="!selected.length" />
      <q-btn color="red" icon="sym_o_delete" label="Delete" class="q-mr-lg"  @click="$emit('delete', selected[0])" :disabled="!selected.length" />
      <q-input v-model="filter" dense placeholder="Search" outlined>
          <template #append>
            <q-icon name="search" />
          </template>
        </q-input>
    </template>
  </q-table>
  <div>
    {{ selected }}
  </div>
</template>

<script setup>
  import { ref, watch } from 'vue'
  const props = defineProps(['columns', 'rows', 'title', 'deleteCount'])
  defineEmits(['edit', 'delete'])

  const filter = ref('')
  const selected = ref([])

  watch(() => props.deleteCount, () => {
    selected.value = []
  })

</script>