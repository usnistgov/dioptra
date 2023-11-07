<template>
  <div class="flex flex-center q-mt-xl q-pt-xl">
    <LoginForm 
      v-if="state === 'login'"
      v-model:username="username"
      v-model:password="password"
      @submit="submit"
      @update:state="(val) => state = val"
    />

    <RegisterForm 
      v-if="state === 'register'"
      v-model:username="username"
      v-model:password="password"
      v-model:confirmPassword="confirmPassword"
      @submit="submit"
      @update:state="(val) => state = val"
    />

    <LoggedInForm 
      v-if="state === 'loggedIn'"
      v-model:username="username"
      v-model:password="password"
      v-model:newPassword="newPassword"
      v-model:deleteRequestPassword="deleteRequestPassword"
      @submit="submit"
    />
  </div>
</template>

<script setup lang="ts">
  import { ref, watch } from 'vue';
  import { useQuasar } from 'quasar'
  import { useLoginStore } from '@/stores/LoginStore.js'
  import { storeToRefs } from 'pinia'
  import LoginForm from '../components/LoginForm.vue'
  import RegisterForm from '../components/RegisterForm.vue'
  import LoggedInForm from '../components/LoggedInForm.vue'

  const $q = useQuasar();

  $q.loading.show();

  const store = useLoginStore();
  const { loggedInUser } = storeToRefs(store);

  // if logging out from dropdown
  watch(loggedInUser, async(newVal) => {
    if(!newVal) {
      state.value = 'login';
    }
  })

  // get login state
  fetch('api/world/', {method: 'GET'})
    .then(res => {
      console.log('res = ', res);
      if (res.status === 401) {
        state.value = 'login';
        loggedInUser.value = '';
      }
      if (res.status === 200) {
        state.value = 'loggedIn';
      }
      $q.loading.hide();
      return res.json();
    })
    .then(data => {
      console.log('data = ', data);
      loggedInUser.value = data.name;
    })
    .catch(err => {
      console.warn(err)
    })

  const state = ref('');

  const username = ref('');
  const password = ref('');
  const newPassword = ref('');
  const confirmPassword = ref('');
  const deleteRequestPassword = ref('');

  function submit(endpoint: string, method: string) {
    let body = {};

    if (endpoint === 'api/user/' && method === 'POST') {
      body = {
        name: username.value,
        password: password.value,
        confirmPassword: confirmPassword.value
      }
    }
    if (endpoint === 'api/user/password' && method === 'POST') {
      body = {
        currentPassword: password.value,
        newPassword: newPassword.value
      }
    }
    if (endpoint === 'api/user/' && method === 'DELETE') {
      body = {
        password: deleteRequestPassword.value,
      }
    }
    if (endpoint === 'api/auth/login') {
      body = {
        username: username.value,
        password: password.value,
      }
    }

    fetch(endpoint, {
      method: method,
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(body)
    })
      .then(res => {
        if (res.status === 200) {
          return res.json();
        } else {
          throw new Error('Failed to make the POST request');
        }
      })
      .then(data => {
        console.log('data = ', data);
        let message = ''
        if (endpoint === 'api/auth/login') {
          message = `Successfully logged in as ${username.value}`;
          loggedInUser.value = JSON.parse(JSON.stringify(username.value));
          username.value = '';
          password.value = '';
          state.value = 'loggedIn';
        }
        if (endpoint === 'api/user/' && method === 'POST') {
          message = `Successfully created user: ${username.value}`;
          reset();
          state.value = 'login';
        }
        if (endpoint === 'api/user/' && method === 'DELETE') {
          message = `Successfully deleted user: ${loggedInUser.value}`;
          reset();
          state.value = 'login';
        }
        if (endpoint.includes('api/auth/logout')) {
          message = `Successfully logged out from ${loggedInUser.value}`;
          reset();
          state.value = 'login';
        }
        if (endpoint === 'api/user/password') {
          message = `Successfully changed password for user: ${loggedInUser.value}`;
          reset();
          state.value = 'login';
        }
        $q.notify({
              color: 'green-7',
              textColor: 'white',
              icon: 'done',
              message: message
            })
      })
      .catch(error => {
        console.error('error = ', error);
        $q.notify({
              color: 'red-5',
              textColor: 'white',
              icon: 'warning',
              message: `${error}`
            })
      });
  }

  function reset() {
    username.value = '';
    password.value = '';
    newPassword.value = '';
    confirmPassword.value = '';
    loggedInUser.value = '';
    deleteRequestPassword.value = '';
  }
</script>

