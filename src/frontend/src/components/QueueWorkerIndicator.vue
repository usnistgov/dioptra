<template>
  <span
    class="queue-worker-indicator q-ml-xs"
    :class="count === 0 ? 'text-negative' : 'text-grey-7'"
    tabindex="0"
    role="img"
    :aria-label="message"
  >
    <q-icon
      class="worker-icon"
      :name="count === 0 ? 'sym_o_warning' : 'sym_o_dns'"
      size="18px"
    />
    <span class="q-ml-xs">{{ count ?? '?' }}</span>
    <q-tooltip>{{ message }}</q-tooltip>
  </span>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  queueName?: string;
  count?: number;
  loading: boolean;
}>();

const message = computed(() => {
  if (props.count === undefined) {
    return props.loading ? "Checking known workers listening to this queue…" : "Known worker count unavailable";
  }
  return `${props.count} known ${props.count === 1 ? "worker" : "workers"} listening to queue "${props.queueName}"`;
});
</script>

<style scoped>
.queue-worker-indicator {
  white-space: nowrap;
}

.worker-icon {
  vertical-align: text-bottom;
}
</style>
