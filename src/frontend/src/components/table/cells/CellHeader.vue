<template>
  <div
    class="header-container row items-center no-wrap"
    :class="[alignClass, { 'is-sortable': col.sortable }]"
  >
    <span class="header-label"
    :class="$q.dark.isActive ? 'header-label--dark' : 'header-label--light'">
      {{ col.label }}
    </span>

    <q-icon
      v-if="col.sortable"
      :name="iconName"
      class="sort-icon"
      :class="iconStatusClass"
    />
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useQuasar } from "quasar";

const $q = useQuasar();
const props = defineProps({
  col: Object,
  sorted: Boolean,
  descending: Boolean,
});

const alignClass = computed(() => {
  const align = props.col.align || "left";
  if (align === "center") return "justify-center";
  if (align === "right") return "justify-end";
  return "justify-start";
});

const iconName = computed(() => {
  if (!props.sorted) return "unfold_more";
  return props.descending ? "arrow_downward" : "arrow_upward";
});

const iconStatusClass = computed(() => {
  return props.sorted ? "sort-icon--active" : "sort-icon--neutral";
});
</script>

<style scoped>
.header-container {
  cursor: default;
  user-select: none;
}

.is-sortable {
  cursor: pointer;
}

.header-label {
  font-weight: 600;
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding-right: 4px;
}

.header-label--light {
    color: #546e7a;
}

.header-label--dark {
    color: #cbe8f5;
}


.sort-icon {
  font-size: 16px;
  transition: opacity 0.2s ease;
}

.sort-icon--neutral {
  opacity: 0.2;
  color: #546e7a;
}

.sort-icon--active {
  opacity: 1;
  color: var(--q-primary);
  font-weight: bold;
}
</style>
