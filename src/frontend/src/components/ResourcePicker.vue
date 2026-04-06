<template>
  <q-select
    v-bind="$attrs"
    :options="options"
    :model-value="modelValue"
    @update:model-value="(val) => $emit('update:model-value', val)"
    outlined
    use-input
    use-chips
    multiple
    map-options
    option-label="name"
    option-value="id"
    input-debounce="300"
  >
    <template v-slot:before>
      <div v-if="label" class="field-label">{{ label }}</div>
    </template>
    <template v-slot:selected-item="scope">
      <ResourceBadge
        :resource="scope.opt"
        :resourceType="resourceType"
        :removable="!$attrs.disable"
        :clickable="false"
        @remove="scope.removeAtIndex(scope.index)"
      />
    </template>  
    <template v-slot:option="scope">
      <q-item 
        v-bind="scope.itemProps"
        :active="scope.selected"
        :active-class="darkMode ? 'bg-blue-grey-9 text-white' : 'bg-blue-grey-1'"
        >
        <q-item-section avatar>
          <q-icon :name="styles.icon" :color="styles.color" />
        </q-item-section>
        <q-item-section>
          <q-item-label>{{ scope.opt.name }}</q-item-label>
          <q-item-label caption v-if="scope.opt.description">
            {{ scope.opt.description }} 
          </q-item-label>
        </q-item-section>
      </q-item>
    </template>
  </q-select>
</template>

<script setup>
import ResourceBadge from '@/components/ResourceBadge.vue'
import { computed, inject } from "vue"
import { getResourceStyle } from "@/services/resourceStyles"

const darkMode = inject("darkMode")

const styles = computed(() => {
  return getResourceStyle(props.resourceType, darkMode.value)
})

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => [],
  },
  options: {
    type: Array,
    default: () => [],
  },
  resourceType: {
    type: String
  },
  label: {
    type: String
  }
})

defineEmits(["update:model-value"]);

</script>