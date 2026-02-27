<template>
  <div
    class="row items-start no-wrap q-py-xs"
    style="max-width: 230px"
    @click.stop
  >
    <div class="col row items-center q-gutter-xs wrap">
      <q-chip
        v-for="(tag, i) in visibleTags"
        :key="i"
        :color="$q.dark.isActive ? 'grey-8' : 'blue-grey-7'"
        :text-color="$q.dark.isActive ? 'grey-3' : 'blue-grey-10'"
        dense
        outline
        square
        size="11px"
        @click.stop
        class="q-my-none text-weight-medium"
        :style="{ borderColor: $q.dark.isActive ? '#555' : '#cfd8dc', height: '20px' }"
      >
        #
        <span
          style="
            max-width: 85px;
            font-weight: 550;
            letter-spacing: 0.6px;
            padding-left: 2px;
          "
          class="ellipsis"
        >
          {{ tag.name }}
        </span>
        <q-tooltip v-if="tag.name.length > 8">{{ tag.name }}</q-tooltip>
      </q-chip>

      <q-chip
        v-if="hiddenCount > 0"
        :color="$q.dark.isActive ? 'grey-9' : 'blue-grey-1'"
        :text-color="$q.dark.isActive ? 'grey-3' : 'blue-grey-10'"
        dense
        clickable
        square
        class="q-my-none text-weight-bold"
        style="font-size: 10px; height: 20px"
      >
        +{{ hiddenCount }} more...

        <q-menu
          anchor="bottom left"
          self="top left"
          :class="[$q.dark.isActive ? 'bg-grey-9 border-grey-8' : 'bg-white border-grey-3', 'shadow-5']"
        >
          <div class="column q-pa-sm" style="min-width: 200px">
            <div
              class="text-caption text-weight-bold text-blue-grey-8 q-mb-xs q-px-xs"
            >
              ADDITIONAL TAGS
            </div>
            <q-separator class="q-mb-sm" />
            <div class="row q-gutter-xs wrap">
              <q-chip
                v-for="(tag, i) in hiddenTags"
                :key="i"
                color="blue-grey-7"
                text-color="blue-grey-10"
                dense
                outline
                square
                size="10px"
                :ripple="false"
                style="cursor: default !important;"
              >
                #
                <span
                  style="
                    font-weight: 550;
                    letter-spacing: 0.6px;
                    padding-left: 2px;
                  "
                  class="ellipsis"
                >
                  {{ tag.name }}</span
                >
              </q-chip>
            </div>
          </div>
        </q-menu>
      </q-chip>
    </div>

    <div class="q-pl-sm">
      <q-btn
        round
        size="xs"
        icon="add"
        color="grey-4"
        text-color="blue-grey-9"
        unelevated
        @click.stop="$emit('add', row)"
      >
        <q-tooltip>Edit Tags</q-tooltip>
      </q-btn>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useQuasar } from "quasar";

const $q = useQuasar();

const props = defineProps({
  tags: {
    type: Array,
    default: () => [],
  },
  row: {
    type: Object,
    required: true,
  },
  limit: {
    type: Number,
    default: 4,
  },
});

const emit = defineEmits(["add"]);

const visibleTags = computed(() => props.tags?.slice(0, props.limit) || []);
const hiddenTags = computed(() => props.tags?.slice(props.limit) || []);
const hiddenCount = computed(() => hiddenTags.value.length);
</script>

<style scoped>
.wrap {
  row-gap: 4px;
}
</style>
