<template>
  <span class="resource-badge-list">
    <ResourceBadge
      v-for="(resource, index) in visibleResources"
      :key="index"
      :resource="resource"
      :resourceType="resourceType"
      :removable="removable"
      :clickable="clickable"
      @sync="$emit('sync', resource)"
      @remove="$emit('remove', resource)"
    />

    <q-chip
      v-if="hiddenResources.length"
      outline
      clickable
      :color="moreChipColor"
      @click.stop
    >
      +{{ hiddenResources.length }} more

      <q-menu>
        <div class="resource-badge-list__menu q-pa-sm">
          <ResourceBadge
            v-for="(resource, index) in hiddenResources"
            :key="index"
            :resource="resource"
            :resourceType="resourceType"
            :removable="removable"
            :clickable="clickable"
            stacked
            @sync="$emit('sync', resource)"
            @remove="$emit('remove', resource)"
          />
        </div>
      </q-menu>
    </q-chip>
  </span>
</template>

<script setup>
import { computed, inject } from "vue"
import ResourceBadge from "@/components/ResourceBadge.vue"

defineEmits(["sync", "remove"])

const props = defineProps({
  resources: {
    type: Array,
    default: () => [],
  },
  resourceType: {
    type: String,
    required: true,
  },
  limit: {
    type: Number,
    default: 3,
    validator: (value) => Number.isFinite(value) && value > 0,
  },
  removable: {
    type: Boolean,
    default: false,
  },
  clickable: {
    type: Boolean,
    default: true,
  },
})

const visibleResources = computed(() => props.resources.slice(0, props.limit))

const hiddenResources = computed(() => props.resources.slice(props.limit))

const darkMode = inject("darkMode")

const moreChipColor = computed(() => (darkMode.value ? "grey-4" : "grey-7"))
</script>

<style scoped>
.resource-badge-list {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
}

.resource-badge-list__menu {
  display: flex;
  flex-direction: column;
}
</style>
