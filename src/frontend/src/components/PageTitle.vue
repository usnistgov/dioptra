<template>
  <div class="row q-mb-lg">
    <div class="page-title-card q-pa-md" :style="cardStyles">
      <div v-if="subtitle" class="column q-mb-xs">
        <div
          class="row items-center q-gutter-x-xs text-uppercase text-weight-bold resource-link cursor-pointer"
          :style="{
            color: hexColor,
            fontSize: '0.85rem',
            letterSpacing: '1.5px',
          }"
          @click="navigateBack"
        >
          <q-icon :name="styles.icon" size="16px" />
          <span>{{ conceptType || path[0] || "Resource" }}</span>
          <q-icon name="arrow_outward" size="12px" style="opacity: 0.7" />
        </div>

        <div class="row items-baseline q-mt-sm">
          <h1
            class="text-h4 q-my-none text-weight-medium subtitle-header"
            :style="subtitleDecoration"
            :class="darkMode ? 'text-grey-5' : 'text-grey-8'"
          >
            {{ subtitle }}
          </h1>

          <q-badge
            v-if="props.draftLabel"
            :label="draftLabel"
            outline
            :style="{ color: hexColor, borderColor: hexColor }"
            class="q-ml-md self-center"
          />
        </div>
      </div>

      <div v-else class="column">
        <div class="row items-center q-gutter-x-md q-mb-sm">
          <q-avatar
            :style="{
              backgroundColor: hexColor,
              boxShadow: `0 4px 12px ${hexColor}66`,
            }"
            text-color="white"
            size="52px"
            font-size="28px"
          >
            <q-icon :name="styles.icon" size="lg"  :color="$q.dark.isActive ? 'grey-3' : 'grey-2'" />
          </q-avatar>

          <div class="row items-center">
            <h1
              class="text-h3 q-my-none text-weight-bolder"
              style="line-height: 1"
              :class="darkMode ? 'text-white' : 'text-dark'"
            >
              {{ title }}
            </h1>

            <q-badge
              v-if="props.draftLabel"
              :label="draftLabel"
              outline
              color="primary"
              class="q-ml-md"
              :class="darkMode ? 'text-white' : ''"
            />
          </div>
        </div>
        <div v-if="caption" class="q-mt-xs" :class="darkMode ? 'text-grey-5' : 'text-grey-8'">
          {{ caption }}
        </div>
      </div>

      <nav aria-label="Breadcrumb" class="q-mt-md">
        <q-breadcrumbs :class="darkMode ? 'text-grey-4' : 'text-grey-9'" style="font-size: 0.95em">
          <template v-slot:separator>
            <q-icon name="chevron_right" size="1.4em" color="grey-4" />
          </template>

          <q-breadcrumbs-el label="Home" icon="home" to="/" />

          <q-breadcrumbs-el
            :label="path[0] === 'pluginParams' ? 'Plugin Parameters' : path[0]"
            :to="path[1] ? `/${path[0]}` : ''"
            :aria-current="`${path.length === 1 ? 'true' : 'false'}`"
            class="text-capitalize"
          />

          <q-breadcrumbs-el
            v-if="route.name === 'pluginFile'"
            :label="`${objName}`"
            :to="`/plugins/${route.params.id}`"
          />

          <q-breadcrumbs-el
            v-if="route.name === 'createExperimentJob'"
            :label="`${objName}`"
            :to="`/experiments/${route.params.id}`"
          />

          <q-breadcrumbs-el
            v-if="path[1]"
            :label="subtitle || title"
            aria-disabled="true"
            aria-current="page"
            class="text-weight-medium text-primary"
          />
        </q-breadcrumbs>
      </nav>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, inject } from "vue";
import { useRoute, useRouter } from "vue-router";
import * as api from "@/services/dataApi";
import { getConceptStyle, getConceptColorHex } from "@/constants/tableStyles";
import { useQuasar } from "quasar";

const $q = useQuasar();
const props = defineProps({
  title: String,
  draftLabel: String,
  subtitle: String,
  caption: String,
  conceptType: String,
});

const darkMode = inject("darkMode");
const route = useRoute();
const router = useRouter();

const styles = computed(() => {
  return (
    getConceptStyle(props.conceptType) || { color: "grey-8", icon: "layers" }
  );
});

const hexColor = computed(() => {
  return getConceptColorHex(props.conceptType, darkMode.value);
});


const cardStyles = computed(() => ({
  borderRadius: "10px",
  minWidth: "400px",
  width: "fit-content",
  backgroundColor: darkMode.value ? "#1d1d1d" : "white",
  boxShadow: `0 4px 175px -20px ${hexColor.value}80`,
  backgroundColor: `${hexColor.value}10`,
}));

const subtitleDecoration = computed(() => ({
  textDecoration: "underline",
  textDecorationColor: hexColor.value,
  textDecorationThickness: "3px",
  textUnderlineOffset: "16px",
  textDecorationSkipInk: "none",
}));

// --- Navigation ---
function navigateBack() {
  if (path.value[0]) {
    router.push(`/${path.value[0]}`);
  } else {
    router.back();
  }
}

// --- Path Logic ---
const path = computed(() => {
  return route.path.split("/").slice(1);
});

// --- API Fetch Logic ---
const objName = ref("");

if (route.name === "pluginFile") {
  getName("plugins");
}
if (route.name === "createExperimentJob") {
  getName("experiments");
}

async function getName(type) {
  try {
    const res = await api.getItem(type, route.params.id);
    objName.value = res.data.name;
  } catch (err) {
    console.log(err);
  }
}
</script>

<style scoped>
.page-title-card {
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease;
}

.resource-link {
  opacity: 0.85;
  transition: all 0.2s ease-in-out;
}

.resource-link:hover {
  opacity: 1;
  transform: translateX(2px);
}
</style>
