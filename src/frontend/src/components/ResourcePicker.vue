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
        :text-color="chipOutline ? 'black' : 'white'"
      >
        <q-icon
          :name="styles.icon"
          size="xs"
          :style="{ color: chipOutline ? computedColor : 'white' }"
          class="q-mr-sm"
        />

        <span class="q-mr-sm" style="letter-spacing: 0.8px">{{
          scope.opt[optionLabel]
        }}</span>
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

// Dynamic Styles for the Chip container
const getChipStyles = computed(() => {
  if (props.chipOutline) {
    return {
      border: `2px solid ${computedColor.value}`,
      backgroundColor: "transparent",
    };
  } else {
    return {
      backgroundColor: computedColor.value,
      border: "none",
    };
  }
});

function truncate(str) {
  if (!str) return "";
  return str.length > 50 ? str.slice(0, 50) + "..." : str;
}
</script>
