<template>
  <q-btn
    flat
    dense
    no-caps
    size="md"
    class="bg-grey-2 text-blue-grey-8 q-pr-sm q-mr-sm row items-left no-wrap justify-start"
    style="max-width: 100%; min-width: 70px"
  >
    <q-icon
      v-if="includeIcon"
      :name="styles.icon"
      :color="styles.color"
      class="items-left justify-left q-mr-xs"
      size="xs"
    />
    <span style="font-size: 12px; font-weight: 500"
      >#<strong>{{ label || type }}</strong>
    </span>
    <q-tooltip>Go to {{ type }} {{ label }}</q-tooltip>
  </q-btn>
</template>

<script setup>
import { computed } from "vue";
import { useRouter } from "vue-router";
import { getConceptStyle } from "@/constants/tableStyles";

const props = defineProps({
  type: String,
  label: [String, Number],
  rowId: [String, Number],
  includeIcon: { type: Boolean, default: true },
});

const router = useRouter();
const styles = computed(() => getConceptStyle(props.type));

// function navigate() {
//   if (props.rowId && !props.isDeleted) {
//     router.push(`/${styles.value.basePath}/${props.rowId}`)
//   }
// }
</script>
