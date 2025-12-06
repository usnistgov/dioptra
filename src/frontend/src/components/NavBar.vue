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
          <q-item clickable v-close-popup to="/">
            <q-item-section>Home</q-item-section>
          </q-item>
          <q-item clickable v-close-popup to="/experiments">
            <q-item-section>Experiments</q-item-section>
          </q-item>
          <q-item clickable v-close-popup to="/jobs">
            <q-item-section>Jobs</q-item-section>
          </q-item>
          <q-item clickable v-close-popup to="/artifacts">
            <q-item-section>Artifacts</q-item-section>
          </q-item>
          <q-item clickable v-close-popup to="/entrypoints">
            <q-item-section>Entrypoints</q-item-section>
          </q-item>
          <q-item clickable v-close-popup to="/plugins">
            <q-item-section>Plugins</q-item-section>
          </q-item>
          <q-item clickable v-close-popup to="/pluginParams">
            <q-item-section>Plugin Parameters</q-item-section>
          </q-item>
          <q-item clickable v-close-popup to="/queues">
            <q-item-section>Queues</q-item-section>
          </q-item>
          <q-item clickable v-close-popup to="/tags">
            <q-item-section>Tags</q-item-section>
          </q-item>
          <q-item clickable v-close-popup to="/groups">
            <q-item-section>Groups</q-item-section>
          </q-item>
        </q-list>
      </q-menu>
    </q-btn>
    <nav v-if="store.loggedInUser" class="gt-md">
      <q-tabs no-caps :key="$route.fullPath">
        <q-route-tab label="Home" to="/" />
        <q-route-tab label="Experiments" to="/experiments" />
        <q-route-tab label="Jobs" to="/jobs" />
        <q-route-tab label="Artifacts" to="/artifacts" />
        <q-route-tab label="Entrypoints" to="/entrypoints" />
        <q-route-tab label="Plugins" to="/plugins" />
        <q-route-tab label="Plugin Parameters" to="/pluginParams" />
        <q-route-tab label="Queues" to="/queues" />
      </q-tabs>
    </nav>

    <q-space />

    <q-btn round icon="sym_o_build" flat v-if="store.loggedInUser">
      <q-menu>
        <q-list class="noselect no-link-style">
          <q-item 
            tag="label" 
            v-ripple 
            @click="showImportDialog = true"
            clickable 
            v-close-popup
          >
            <q-item-section>
              <q-item-label>Import Resources</q-item-label>
            </q-item-section>
            <q-item-section side>
              <q-icon
                name="upload"
                size="sm"
                @keyup.enter="showImportDialog = true"
                style="cursor: pointer"
                tabindex="0"
                role="button"
                aria-hidden="false"
              />
            </q-item-section>
          </q-item>
          <q-item to="/tags" exact clickable v-close-popup>
            <q-item-section>
              <q-item-label>Manage Tags</q-item-label>
            </q-item-section>
            <q-item-section side>
              <q-icon name="sym_o_sell" size="sm" />
            </q-item-section>
          </q-item>
        </q-list>
      </q-menu>
    </q-btn>

    <q-btn round icon="settings" flat>
      <q-menu>
        <q-list class="noselect">
          <q-item tag="label" v-ripple clickable>
            <q-item-section>
              <q-item-label>Light/Dark</q-item-label>
            </q-item-section>
            <q-item-section side>
              <div>
                <q-toggle color="blue" v-model="darkToggle" />
                  <q-icon 
                    :name="darkToggle ? 'sym_o_dark_mode' : 'sym_o_sunny'" 
                    size="sm" 
                    @keyup.enter="darkToggle = !darkToggle"
                    style="cursor: pointer"
                    tabindex="0" 
                    role="button"
                    aria-hidden="false"
                    aria-label="Toggle light/dark mode"
                  />
              </div>
            </q-item-section>
          </q-item>
          <q-separator />
          <q-item tag="label" v-ripple clickable>
            <q-item-section>
              <q-item-label>Fullscreen</q-item-label>
            </q-item-section>
            <q-item-section side>
              <div>
                <q-toggle color="blue" v-model="fullscreenToggle" @click="$q.fullscreen.toggle()" />
                  <q-icon 
                    :name="fullscreenToggle ? 'fullscreen' : 'fullscreen_exit'" 
                    size="sm" 
                    @keyup.enter="fullscreenToggle = !fullscreenToggle"
                    style="cursor: pointer"
                    tabindex="0" 
                    role="button"
                    aria-hidden="false"
                    aria-label="Toggle fullscreen mode"
                  />
              </div>
            </q-item-section>
          </q-item>
        </q-list>
      </q-menu>
    </q-btn>

    <q-btn round icon="sym_o_info" flat class="q-mr-xs">
      <q-menu>
        <q-list class="noselect no-link-style">
          <q-item v-ripple href="https://pages.nist.gov/dioptra/" target="_blank" clickable v-close-popup>
            <q-item-section>
              <q-item-label>Dioptra Documentation</q-item-label>
            </q-item-section>
            <q-item-section side>
              <q-icon name="sym_o_help" size="sm" />
            </q-item-section>
          </q-item>
          <q-item v-ripple href="https://github.com/usnistgov/dioptra" target="_blank" clickable v-close-popup>
            <q-item-section>
              <q-item-label>GitHub Repository</q-item-label>
            </q-item-section>
            <q-item-section side>
              <q-icon name="fa-brands fa-github" size="sm" />
            </q-item-section>
          </q-item>
          <q-separator />
          <q-item>
            <q-item-section>
              <q-item-label class="text-no-wrap">Dioptra Version {{ version }}</q-item-label>
            </q-item-section>
            <q-item-section side>
              <q-icon name="tag" size="sm" />
            </q-item-section>
          </q-item>
        </q-list>
      </q-menu>
    </q-btn>

    <q-separator vertical inset color="white" />
    <q-tabs shrink no-caps>
      <q-route-tab 
        v-if="!store.loggedInUser"
        :label="getLabel()" to="/login"
      />
      <div v-else class="row">
        <q-tabs no-caps inline-label>
          <q-route-tab class="gt-md" label="Groups" to="/groups" />
          <q-route-tab :label="isMobile ? '' : store.loggedInUser.username" to="/login" icon="person" />
          <q-btn-dropdown style="background-color: #CF5C36;" icon="groups" :label="isMobile ? '' : store.loggedInGroup.name" dense class="q-pl-md q-my-xs">
            <q-list>
              <q-item 
                v-for="(group, i) in store.groups" 
                :key="i" 
                clickable 
                v-close-popup 
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
  import { useQuasar } from 'quasar'
  import { watch, inject, ref, onMounted } from 'vue'
  import { useLoginStore } from '@/stores/LoginStore'
  import * as api from '@/services/dataApi'

  import ImportResourcesDialog from '../dialogs/ImportResourcesDialog.vue';
  const showImportDialog = defineModel()

  const store = useLoginStore()

  const $q = useQuasar()

  const isMobile = inject('isMobile')

  const darkToggle = ref($q.dark.isActive)

  watch(darkToggle, (val) => {
    $q.dark.set(val)
    localStorage.setItem('darkMode', val)
  })

  watch(() => $q.dark.isActive, (val) => {
    // light/dark can be changed externally so double check
    if(darkToggle.value !== val) {
      darkToggle.value = val
    }
  })

  const fullscreenToggle = ref($q.fullscreen.isActive)

  watch(() => $q.fullscreen.isActive, (val) => {
    // fullscreen can be exited with esc
    if(!val) {
      fullscreenToggle.value = false
    }
  })

  function getLabel() {
    if(!store.loggedInUser) return 'Sign In'
    else return `${store.loggedInUser}`
  }

  const version = ref('')

  onMounted(() => {
    getDioptraVersion()
  })

  async function getDioptraVersion() {
    try {
      version.value = await api.getDioptraVersion()
    } catch(err) {
      console.warn(err)
    }
  }

</script>
