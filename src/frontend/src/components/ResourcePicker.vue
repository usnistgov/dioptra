<template>
  <q-select
    outlined
    dense
    v-bind="$attrs"
    :model-value="modelValue"
    @update:model-value="(val) => $emit('update:model-value', val)"
    use-input
    use-chips
    multiple
    map-options
    emit-value
    :label="label"
  >
    <template v-slot:selected-item="scope">
      <q-chip
        removable
        @remove="scope.removeAtIndex(scope.index)"
        :tabindex="scope.tabindex"
        :square="chipSquare"
        :style="getChipStyles"
        :class="getChipClasses"
      >
        <q-icon
          :name="styles.icon"
          size="xs"
          :style="{ color: chipOutline ? computedColor : 'white' }"
          class="q-mr-sm"
        />

        <span class="q-mr-xs ellipsis" style="letter-spacing: 0.5px">
          {{ scope.opt[optionLabel] }}
        </span>
      </q-chip>
    </template>

    <template v-slot:option="scope">
      <q-item v-bind="scope.itemProps">
        <q-item-section avatar>
          <q-icon :name="styles.icon" :style="{ color: computedColor }" />
        </q-item-section>
        <q-item-section>
          <q-item-label>{{ scope.opt[optionLabel] }}</q-item-label>
          <q-item-label caption v-if="scope.opt.description">
            {{ truncate(scope.opt.description) }} 
          </q-item-label>
        </q-item-section>
      </q-item>
    </template>

    <template v-for="(_, slot) in $slots" v-slot:[slot]="scope">
      <slot :name="slot" v-bind="scope || {}" />
    </template>
  </q-select>
</template>

<script setup>
import { computed } from "vue";
import { getConceptStyle, getConceptColorHex } from "@/constants/tableStyles";
import { useQuasar } from "quasar";

const props = defineProps({
  modelValue: [Array, Object, String, Number],
  type: { type: String, required: true },
  label: String,
  optionLabel: { type: String, default: "name" },
  chipOutline: { type: Boolean, default: false },
  chipSquare: { type: Boolean, default: false },
  color: { type: String, default: null },
});

defineEmits(["update:model-value"]);

const $q = useQuasar();
const styles = computed(() => getConceptStyle(props.type));

const computedColor = computed(() => {
  if (props.color) return props.color;
  const isDark = $q.dark.isActive;
  return getConceptColorHex(props.type, isDark);
});

const computedColorOpposite = computed(() => {
  if (props.color) return props.color;
  const isLight =  $q.dark.isActive;
  return getConceptColorHex(props.type, isLight);
});

// Manage purely dynamic styles (borders, custom background colors)
const getChipStyles = computed(() => {
  if (props.chipOutline) {
    return {
      border: `1px solid ${computedColor.value}`
    };
  } else { 
    if ($q.dark.isActive){
      return {
        backgroundColor: computedColor.value,
        color: 'black', 
        border: "none"
      };
    }
    else {
      return {
        backgroundColor: computedColorOpposite.value,
        color: 'white', 
        border: "none"
      };
    }
  }
});

// Manage Quasar utility classes (theme-aware backgrounds and text)
const getChipClasses = computed(() => {
  if (props.chipOutline) {
    // Provides a subtle background and guarantees high-contrast text + remove icon
    return $q.dark.isActive 
      ? 'bg-grey-10 text-grey-3' 
      : 'bg-grey-2 text-grey-9';
  }
  return ''; // Solid mode classes aren't needed; it relies on getChipStyles
});

function truncate(str) {
  if (!str) return "";
  return str.length > 50 ? str.slice(0, 50) + "..." : str;
}
</script>