<template>
  <q-chip
    v-if="styles"
    :color="styles.color"
    text-color="white"
    :size="mini ? 'sm' : size"
    :outline="chipType === 'outline'"
    square
    :clickable="isClickable"
    @click.stop="navigate" 
    :class="['text-weight-bold', mini ? 'q-py-xs q-px-xs' : 'q-py-md q-px-sm']"
  >
    <q-icon
      v-if="showIcon && styles.icon"
      :name="styles.icon"
      size="xs"
      :style="mini ? 'font-size:1.5em !important' : ''"
    />

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
import { useRouter } from "vue-router";
import { getConceptStyle } from "@/constants/tableStyles";

const router = useRouter();

const props = defineProps({
  type: String,
  label: [String, Number],
  rowId: [String, Number],
  snapshotId: [String, Number], 
  to: [String, Object],         // Escape hatch for custom URLs
  clickable: {                  // Explicit control if needed
    type: Boolean,
    default: undefined,
  },
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
  mini: {
    type: Boolean,
    default: false,
  },
});

const styles = computed(() => {
  return getConceptStyle(props.type) || { color: "grey-7", icon: "help" };
});

// Determine the target route
const targetRoute = computed(() => {
  // 1. If an explicit 'to' override is provided, use it
  if (props.to) return props.to;

  // 2. If we don't have the minimum data to construct a route, return null
  if (!props.rowId || !props.type) return null;

  // 3. Construct standard route using styles.value!
  const baseRoute = styles.value.basePath;
  
  // Safety check: if there is no basePath defined for this type, don't create a route
  if (!baseRoute) return null;

  const path = `/${baseRoute.toLowerCase()}/${props.rowId}`;

  // 4. Return the route object, conditionally adding the snapshotId query
  return props.snapshotId
    ? { path, query: { snapshotId: props.snapshotId } }
    : { path };
});

// The chip is clickable if either the prop says so, or it has a valid target route
const isClickable = computed(() => {
  if (props.clickable !== undefined) return props.clickable;
  return !!targetRoute.value;
});

function navigate() {
  if (isClickable.value && targetRoute.value) {
    router.push(targetRoute.value);
  }
}

const displayValue = computed(() => {
  const labelVal = props.label !== undefined && props.label !== null && props.label !== "" ? props.label : "NA";
  const typeVal = props.type || "";
  if (!props.formatLabel) return labelVal !== "NA" ? labelVal : typeVal;
  return props.formatLabel.replace(/{label}/g, labelVal).replace(/{type}/g, typeVal);
});


const tooltipText = computed(() => {
  if (!props.type) return "";

  const prefix = isClickable.value ? `Go to ` : ``;
  const base = `${props.type}: ${props.label || "N/A"}`;
  const idSuffix = props.rowId ? ` (ID: ${props.rowId})` : "";
  const snapSuffix = props.snapshotId ? ` | Snapshot: ${props.snapshotId}` : "";

  return prefix + base + idSuffix + snapSuffix;
});
</script>