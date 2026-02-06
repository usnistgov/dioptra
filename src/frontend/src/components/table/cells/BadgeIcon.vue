<template>
  <q-chip
    v-if="styles"
    :color="styles.color"
    text-color="white"
    :size="size"
    :outline="chipType === 'outline'"
    square
    class="text-weight-bold q-py-md q-px-sm"
  >
    <q-icon v-if="showIcon && styles.icon" :name="styles.icon" size="xs" />

    <span
      class="font-mono ellipsis"
      :class="[{ 'text-uppercase': uppercase }, showIcon ? 'q-ml-xs' : '']"
      style="font-size: 12px; font-weight: 500; max-width: 200px"
    >
      {{ displayValue }}
    </span>

    <q-tooltip>{{ tooltipText }}</q-tooltip>
  </q-chip>
</template>

<script setup>
import { computed } from "vue";
import { getConceptStyle } from "@/constants/tableStyles";

const props = defineProps({
  type: String,
  label: [String, Number],
  rowId: [String, Number],
  uppercase: {
    type: Boolean,
    default: true,
  },
  size: {
    type: String,
    default: "sm",
  },
  chipType: {
    type: String,
    default: "outline",
    validator: (value) => ["outline", "normal"].includes(value),
  },
  formatLabel: {
    type: String,
    default: "",
  },
  showIcon: {
    type: Boolean,
    default: true,
  },
});

const styles = computed(() => {
  return getConceptStyle(props.type) || { color: "grey-7", icon: "help" };
});

const displayValue = computed(() => {
  const labelVal =
    props.label !== undefined && props.label !== null && props.label !== ""
      ? props.label
      : "NA";

  const typeVal = props.type || "";

  if (!props.formatLabel) {
    return labelVal !== "NA" ? labelVal : typeVal;
  }

  return props.formatLabel
    .replace(/{label}/g, labelVal)
    .replace(/{type}/g, typeVal);
});

const tooltipText = computed(() => {
  if (!props.type) return "";
  const base = `${props.type}: ${props.label || "N/A"}`;
  const idSuffix = props.rowId ? ` (ID: ${props.rowId})` : "";
  return base + idSuffix;
});
</script>
