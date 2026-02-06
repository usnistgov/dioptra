<template>
  <div class="column q-gutter-y-xs">
    <template v-for="(param, i) in items.slice(0, 3)" :key="i">
      <div class="row no-wrap q-gutter-x-sm">
        <div
          class="rounded-borders shrink-0"
          :style="{
            marginTop: '6px',
            width: '6px',
            height: '6px',
            backgroundColor: styles.textColor,
          }"
        ></div>

        <div class="row items-baseline no-wrap q-gutter-x-sm">
          <div
            class="text-weight-bold"
            :style="{
              color: styles.textColor,
              borderBottom: `1.5px solid ${styles.textColor}`,
              lineHeight: '1.3',
            }"
          >
            {{ param.name }} :
          </div>

          <div class="row">
            <div
              class="font-mono text-weight-medium text-grey-7 cursor-help q-pr-xs"
              style="font-size: 0.75rem"
            >
              {{ param.parameterType?.name || "Unknown" }}

              <q-tooltip class="bg-grey-9" style="font-size: 11px">
                {{ getTooltip(param) }}
              </q-tooltip>
            </div>

            <div
              v-if="!param.required & (concept == 'input')"
              class="text-weight-medium text-grey-5"
              style="font-size: 0.7rem"
            >
              (optional)
            </div>
          </div>
        </div>
      </div>
    </template>

    <div v-if="items.length > 3" class="row no-wrap q-gutter-x-md">
      <div
        class="rounded-borders shrink-0"
        :style="{ marginTop: '6px', width: '6px', height: '6px', opacity: 1 }"
      ></div>
      <q-chip
        dense
        clickable
        color="grey-2"
        text-color="grey-8"
        class="text-weight-bold"
        style="font-size: 10px; height: 20px"
        @click.stop
      >
        +{{ items.length - 3 }} more

        <q-menu
          anchor="bottom middle"
          self="top left"
          class="bg-white shadow-5 border-grey-3"
        >
          <div class="column q-pa-sm q-gutter-y-xs">
            <div class="text-caption text-grey-7 q-mb-xs">
              Additional {{ type === "input" ? "Inputs" : "Outputs" }}
            </div>

            <template v-for="(param, i) in items.slice(3)" :key="i">
              <div class="row items-center no-wrap q-gutter-x-sm q-py-xs">
                <div
                  class="rounded-borders shrink-0"
                  :style="{
                    width: '6px',
                    height: '6px',
                    backgroundColor: styles.hexColor,
                  }"
                ></div>

                <div class="row items-baseline no-wrap q-gutter-x-sm">
                  <div
                    class="text-weight-bold"
                    :style="{
                      color: styles.textColor,
                      borderBottom: `1.5px solid ${styles.hexColor}`,
                      lineHeight: '1.3',
                    }"
                  >
                    {{ param.name }} :
                  </div>
                  <div
                    class="font-mono text-weight-medium text-grey-7"
                    style="font-size: 0.75rem"
                  >
                    {{ param.parameterType?.name }}
                  </div>
                </div>
              </div>
            </template>
          </div>
        </q-menu>
      </q-chip>
    </div>

    <div v-if="items.length === 0" class="text-caption text-grey-4">-</div>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { getConceptStyle } from "@/constants/tableStyles";
import { colors } from "quasar";

const { getPaletteColor } = colors;

const props = defineProps({
  items: { type: Array, default: () => [] },
  type: { type: String, default: "output" }, 
});

// Compute Colors based on Concept Type
const styles = computed(() => {
  const concept = props.type === "input" ? "input" : "output";
  const styleObj = getConceptStyle(concept);

  const fallbackColor = props.type === "input" ? "indigo-6" : "purple-6";
  const fallbackText = props.type === "input" ? "blue-grey-6" : "deep-purple-5";

  const baseColor = styleObj?.color || fallbackColor;

  return {
    hexColor: getPaletteColor(baseColor),
    textColor: getPaletteColor(fallbackText), 
  };
});

function getTooltip(param) {
  return param.description || `Type: ${param.parameterType?.name}`;
}
</script>
