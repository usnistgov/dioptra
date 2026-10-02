<template>
  <q-toolbar class="bg-primary text-white">
    <q-btn
      v-if="store.loggedInUser"
      class="lt-lg"
      icon="menu"
      flat
      :ripple="false"
    >
      <span class="sr-only">Navigation Menu</span>
      <q-menu class="text-h6">
        <q-list style="min-width: 150px">
          <q-item
            v-close-popup
            clickable
            to="/"
          >
            <q-item-section>Home</q-item-section>
          </q-item>
          <q-item
            v-close-popup
            clickable
            to="/experiments"
          >
            <q-item-section>Experiments</q-item-section>
          </q-item>
          <q-item
            v-close-popup
            clickable
            to="/jobs"
          >
            <q-item-section>Jobs</q-item-section>
          </q-item>
          <q-item
            v-close-popup
            clickable
            to="/artifacts"
          >
            <q-item-section>Artifacts</q-item-section>
          </q-item>
          <q-item
            v-close-popup
            clickable
            to="/entrypoints"
          >
            <q-item-section>Entrypoints</q-item-section>
          </q-item>
          <q-item
            v-close-popup
            clickable
            to="/plugins"
          >
            <q-item-section>Plugins</q-item-section>
          </q-item>
          <q-item
            v-close-popup
            clickable
            to="/pluginParams"
          >
            <q-item-section>Plugin Parameters</q-item-section>
          </q-item>
          <q-item
            v-close-popup
            clickable
            to="/queues"
          >
            <q-item-section>Queues</q-item-section>
          </q-item>
          <q-item
            v-close-popup
            clickable
            to="/tags"
          >
            <q-item-section>Tags</q-item-section>
          </q-item>
          <q-item
            v-close-popup
            clickable
            to="/groups"
          >
            <q-item-section>Groups</q-item-section>
          </q-item>
        </q-list>
      </q-menu>
    </q-btn>
    <nav
      v-if="store.loggedInUser"
      class="gt-md"
    >
      <q-tabs
        :key="$route.fullPath"
        no-caps
      >
        <q-route-tab
          label="Home"
          to="/"
        />
        <q-route-tab
          label="Experiments"
          to="/experiments"
        />
        <q-route-tab
          label="Jobs"
          to="/jobs"
        />
        <q-route-tab
          label="Artifacts"
          to="/artifacts"
        />
        <q-route-tab
          label="Entrypoints"
          to="/entrypoints"
        />
        <q-route-tab
          label="Plugins"
          to="/plugins"
        />
        <q-route-tab
          label="Plugin Parameters"
          to="/pluginParams"
        />
        <q-route-tab
          label="Queues"
          to="/queues"
        />
      </q-tabs>
    </nav>

    <q-space />

    <q-btn
      v-if="store.loggedInUser"
      round
      icon="sym_o_build"
      flat
    >
      <q-menu>
        <q-list class="noselect no-link-style">
          <q-item
            v-ripple
            v-close-popup
            tag="label"
            clickable
            @click="showImportDialog = true"
          >
            <q-item-section>
              <q-item-label>Import Resources</q-item-label>
            </q-item-section>
            <q-item-section side>
              <q-icon
                name="upload"
                size="sm"
                style="cursor: pointer"
                tabindex="0"
                role="button"
                aria-hidden="false"
                @keyup.enter="showImportDialog = true"
              />
            </q-item-section>
          </q-item>
          <q-item
            v-close-popup
            to="/tags"
            exact
            clickable
          >
            <q-item-section>
              <q-item-label>Manage Tags</q-item-label>
            </q-item-section>
            <q-item-section side>
              <q-icon
                name="sym_o_sell"
                size="sm"
              />
            </q-item-section>
          </q-item>
        </q-list>
      </q-menu>
    </q-btn>

    <q-btn
      round
      icon="settings"
      flat
    >
      <q-menu>
        <q-list class="noselect">
          <q-item
            v-ripple
            tag="label"
            clickable
          >
            <q-item-section>
              <q-item-label>Light/Dark</q-item-label>
            </q-item-section>
            <q-item-section side>
              <div>
                <q-toggle
                  v-model="darkToggle"
                  color="blue"
                />
                <q-icon
                  :name="darkToggle ? 'sym_o_dark_mode' : 'sym_o_sunny'"
                  size="sm"
                  style="cursor: pointer"
                  tabindex="0"
                  role="button"
                  aria-hidden="false"
                  aria-label="Toggle light/dark mode"
                  @keyup.enter="darkToggle = !darkToggle"
                />
              </div>
            </q-item-section>
          </q-item>
          <q-separator />
          <q-item
            v-ripple
            tag="label"
            clickable
          >
            <q-item-section>
              <q-item-label>Fullscreen</q-item-label>
            </q-item-section>
            <q-item-section side>
              <div>
                <q-toggle
                  v-model="fullscreenToggle"
                  color="blue"
                  @click="$q.fullscreen.toggle()"
                />
                <q-icon
                  :name="fullscreenToggle ? 'fullscreen' : 'fullscreen_exit'"
                  size="sm"
                  style="cursor: pointer"
                  tabindex="0"
                  role="button"
                  aria-hidden="false"
                  aria-label="Toggle fullscreen mode"
                  @keyup.enter="fullscreenToggle = !fullscreenToggle"
                />
              </div>
            </q-item-section>
          </q-item>
        </q-list>
      </q-menu>
    </q-btn>

    <q-btn
      round
      icon="sym_o_info"
      flat
      class="q-mr-xs"
    >
      <q-menu>
        <q-list class="noselect no-link-style">
          <q-item
            v-ripple
            v-close-popup
            href="https://pages.nist.gov/dioptra/"
            target="_blank"
            clickable
          >
            <q-item-section>
              <q-item-label>Dioptra Documentation</q-item-label>
            </q-item-section>
            <q-item-section side>
              <q-icon
                name="sym_o_help"
                size="sm"
              />
            </q-item-section>
          </q-item>
          <q-item
            v-ripple
            v-close-popup
            href="https://github.com/usnistgov/dioptra"
            target="_blank"
            clickable
          >
            <q-item-section>
              <q-item-label>GitHub Repository</q-item-label>
            </q-item-section>
            <q-item-section side>
              <q-icon
                name="fa-brands fa-github"
                size="sm"
              />
            </q-item-section>
          </q-item>
          <q-separator />
          <q-item>
            <q-item-section>
              <q-item-label class="text-no-wrap">Dioptra Version {{ version }}</q-item-label>
            </q-item-section>
            <q-item-section side>
              <q-icon
                name="tag"
                size="sm"
              />
            </q-item-section>
          </q-item>
        </q-list>
      </q-menu>
    </q-btn>

    <q-separator
      vertical
      inset
      color="white"
    />
    <q-tabs
      shrink
      no-caps
    >
      <q-route-tab
        v-if="!store.loggedInUser"
        :label="getLabel()"
        to="/login"
      />
      <div
        v-else
        class="row"
      >
        <q-tabs
          no-caps
          inline-label
        >
          <q-route-tab
            class="gt-md"
            label="Groups"
            to="/groups"
          />
          <q-route-tab
            :label="isMobile ? '' : store.loggedInUser.username"
            to="/login"
            icon="person"
          />
          <q-btn-dropdown
            style="background-color: #cf5c36"
            icon="groups"
            :label="isMobile ? '' : store.loggedInGroup.name"
            dense
            class="q-pl-md q-my-xs"
          >
            <q-list>
              <q-item
                v-for="(group, i) in store.groups"
                :key="i"
                v-close-popup
                clickable
                :active="group.id === store.loggedInGroup.id"
                active-class="bg-blue-3 text-bold"
              >
                <q-item-section>
                  <q-item-label>{{ group.name }}</q-item-label>
                </q-item-section>
              </q-item>
            </q-list>
          </q-btn-dropdown>
        </q-tabs>
      </div>
    </q-tabs>
  </q-toolbar>
  <ImportResourcesDialog v-model="showImportDialog" />
</template>

<script setup>
import { useQuasar } from "quasar";
import { watch, inject, ref, onMounted } from "vue";
import { useLoginStore } from "@/stores/LoginStore";
import * as api from "@/services/dataApi";

import ImportResourcesDialog from "../dialogs/ImportResourcesDialog.vue";
const showImportDialog = defineModel();

const store = useLoginStore();

const $q = useQuasar();

const isMobile = inject("isMobile");

const darkToggle = ref($q.dark.isActive);

watch(darkToggle, (val) => {
  $q.dark.set(val);
  localStorage.setItem("darkMode", val);
});

watch(
  () => $q.dark.isActive,
  (val) => {
    // light/dark can be changed externally so double check
    if (darkToggle.value !== val) {
      darkToggle.value = val;
    }
  },
);

const fullscreenToggle = ref($q.fullscreen.isActive);

watch(
  () => $q.fullscreen.isActive,
  (val) => {
    // fullscreen can be exited with esc
    if (!val) {
      fullscreenToggle.value = false;
    }
  },
);

function getLabel() {
  if (!store.loggedInUser) return "Sign In";
  else return `${store.loggedInUser}`;
}

const version = ref("");

onMounted(() => {
  getDioptraVersion();
});

async function getDioptraVersion() {
  try {
    version.value = await api.getDioptraVersion();
  } catch (err) {
    console.warn(err);
  }
}
</script>
