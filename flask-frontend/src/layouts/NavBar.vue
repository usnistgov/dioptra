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
            <q-item clickable v-close-popup @click="logout()" v-if="loggedInUser">
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

    <q-toggle
      v-model="darkMode"
      class="absolute-right q-mr-sm" 
      :label="`${$q.dark.isActive ? 'Dark' : 'Light'} Mode `"
      @click="$q.dark.toggle()"
    >
      <q-icon :name="darkMode ? 'bedtime' : 'light_mode'" size="sm"/>
    </q-toggle>
  </q-tabs>
</template>

<script setup lang="ts">
  import { useQuasar } from 'quasar'
  import { useLoginStore } from '@/stores/LoginStore.js'
  import { storeToRefs } from 'pinia'
  import { START_LOCATION } from 'vue-router';
  import { useRouter } from 'vue-router';

  const router = useRouter();

  const store = useLoginStore();
  const { loggedInUser } = storeToRefs(store);

  // check login status if page reloads
  router.beforeEach((to, from) => {
    if (from === START_LOCATION) {
      // only check if reloading on page other than home
      // since home login page has its own check
      if (to.name !== 'home') {
        getLoginState();
      }
    }
  })

  function getLoginState() {
    fetch('api/world/', {method: 'GET'})
    .then(res => {
      console.log('res = ', res);
      if (res.status !== 200) {
        loggedInUser.value = '';
      }
      return res.json();
    })
    .then(data => {
      console.log('data = ', data);
      loggedInUser.value = data.name;
    })
    .catch(err => {
      console.warn(err)
    })
  }

  function logout() {
    fetch('api/auth/logout', {method: 'POST'})
    .then(res => {
      console.log('res = ', res);
      return res.json();
    })
    .then(data => {
      console.log('data = ', data);
      router.push('/');
      $q.notify({
              color: 'green-7',
              textColor: 'white',
              icon: 'done',
              message: `Successfully logged out from ${loggedInUser.value}`
            })
      loggedInUser.value = '';
    })
    .catch(err => {
      console.warn(err)
    })
  }

  const $q = useQuasar()
  const darkMode = JSON.parse(JSON.stringify($q.dark.isActive))

</script>