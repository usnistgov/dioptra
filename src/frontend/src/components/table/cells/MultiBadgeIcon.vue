<template>
  <div class="row items-center q-gutter-xs wrap" style="max-width: 300px">
    <BadgeIcon
      v-for="(item, i) in visibleItems"
      :key="i"
      :type="conceptType"
      :label="item.name"
      :rowId="item.id"
      :snapshotId="item.snapshotId"
      :clickable="clickable"
    />

    <q-chip
      v-if="hiddenCount > 0"
      color="grey-3"
      text-color="grey-9"
      clickable
      @click.stop
      class="q-my-none text-weight-bold"
      style="font-size: 13px"
    >
      +{{ hiddenCount }} more

      <q-menu
        anchor="bottom middle"
        self="top middle"
        class="bg-white shadow-5 border-grey-3 q-pa-md"
      >
        <div class="text-caption text-grey-7 q-mb-xs text-weight-bold" style="text-transform: capitalize;">
          Additional {{ conceptType }}s:
        </div>
        <div class="column q-pa-sm q-gutter-y-xs">
          <BadgeIcon
            v-for="(item, i) in hiddenItems"
            :key="i"
            :type="conceptType"
            :label="item.name"
            :rowId="item.id"
            :snapshotId="item.snapshotId"
            :clickable="clickable"
          />
        </div>
      </q-menu>
    </q-chip>
  </div>
</template>

<script setup>
import { computed } from "vue";
import BadgeIcon from "./BadgeIcon.vue";

const props = defineProps({
  items: {
    type: Array,
    default: () => [],
  },
  clickable: {                  
    type: Boolean,
    default: undefined,
  },
  conceptType: {
    type: String,
    required: true,
  },
  limit: {
    type: Number,
    default: 3,
  },
});

const visibleItems = computed(() => props.items?.slice(0, props.limit) || []);
const hiddenItems = computed(() => props.items?.slice(props.limit) || []);
const hiddenCount = computed(() => hiddenItems.value.length);
</script>