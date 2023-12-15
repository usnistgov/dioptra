<template>
  <q-tabs inline-label>
    <span 
      class="absolute-left q-pa-sm"
    >
      {{ loggedInUser ? `Logged in as ${loggedInUser}` : 'Logged Off' }}
      <q-btn 
        round 
        :color="loggedInUser ? 'primary' : 'grey'"
        :icon="loggedInUser ? 'person' : 'person_off'"
        size="sm"
      >
      <q-menu>
          <q-list style="min-width: 100px">
            <q-item clickable v-close-popup @click="callLogout()" v-if="loggedInUser">
              <q-item-section>Logout</q-item-section>
            </q-item>
            <!-- <q-item clickable v-close-popup v-if="loggedInUser">
              <q-item-section>Change Password</q-item-section>
            </q-item>
            <q-item clickable v-close-popup v-if="loggedInUser">
              <q-item-section>Delete Account</q-item-section>
            </q-item> -->
          </q-list>
        </q-menu>
      </q-btn>
    </span>

    <q-route-tab label="Login" icon="login" to="/" />
    <q-route-tab label="API" icon="language" to="/api" />
    <q-route-tab label="CodeMirror" :no-caps="true" icon="edit_document" to="/codemirror" />
    <q-route-tab label="Ace" icon="edit_document" to="/ace" />

    <q-toggle
      v-model="darkMode"
      class="absolute-right q-mr-sm" 
      :label="`${darkMode ? 'Dark' : 'Light'} Mode `"
      @click="$q.dark.toggle()"
    >
      <q-icon :name="darkMode ? 'bedtime' : 'light_mode'" size="sm"/>
    </q-toggle>
  </q-tabs>
</template>

<script setup lang="ts">
  import { ref } from 'vue';
  import { useQuasar } from 'quasar';
  import { useLoginStore } from '@/stores/LoginStore';
  import { storeToRefs } from 'pinia';
  import { START_LOCATION } from 'vue-router';
  import { useRouter } from 'vue-router';
  import * as api from '../api';
  import * as notify from '../notify';

  const $q = useQuasar();
  const darkMode = ref($q.dark.isActive);

  const router = useRouter();

  const store = useLoginStore();
  const { loggedInUser, formState } = storeToRefs(store);

  // check login status if page reloads
  router.beforeEach((to, from) => {
    if (from === START_LOCATION) {
      // only check if reloading on page other than home
      // since home login page has its own check
      if (to.name !== 'home') {
        callGetLoginStatus();
      }
    }
  });

  async function callGetLoginStatus() {
    try {
      const res = await api.getLoginStatus();
      loggedInUser.value = res.data.name;
    } catch(err) {
      loggedInUser.value = '';
    }
  }

  async function callLogout() {
    const previousUser = JSON.parse(JSON.stringify(loggedInUser.value));
    try {
      await api.logout();
      loggedInUser.value = '';
      formState.value = 'login';
      router.push('/');
      notify.success(`Successfully logged out from ${previousUser}`);
    } catch (err) {
      notify.error(`Error logging out from user: ${previousUser}`);
    }
  }

</script>