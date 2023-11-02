<template>
  <div class="q-mt-xl">
    <div class="flex flex-center">
      <q-card class="q-pa-lg" style="min-width: 600px;" v-if="state === 'login'">
        <q-card-section class="text-center">
            <div class="text-h5 text-weight-bold">Login</div>
            <div>Login below to access all API endpoints</div>
        </q-card-section>
        <q-form @submit="submit(endpoint, method)">
          <q-input
            class="q-py-md"
            outlined
            label="Username"
            v-model="username"
            :rules="[requiredRule]"
          >
          </q-input>
          <q-input
            class="q-py-sm"
            outlined
            label="Password"
            v-model="password"
            :rules="[requiredRule]"
          >
          </q-input>
          <q-btn
            color="primary"
            class="full-width q-mt-md"
            type="submit"
            @click="endpoint = 'api/auth/login'; method = 'POST'"
          >
            Login
          </q-btn>
          <q-card-section class="text-center q-pt-md">
            <div>Don't have an account yet?
              <a 
                role="button" 
                class="text-weight-bold text-primary" 
                style="text-decoration: none; cursor: pointer" 
                @click="state = 'register'"
              >
                Signup.
              </a>
            </div>
          </q-card-section>
        </q-form>
      </q-card>

      <q-card class="q-pa-lg" style="min-width: 600px;" v-if="state === 'register'">
        <q-card-section class="text-center">
            <div class="text-h5 text-weight-bold">Register</div>
            <div>Register a new user account</div>
        </q-card-section>
        <q-form @submit="submit(endpoint, method)">
          <q-input
            class="q-py-sm"
            outlined
            label="Username"
            v-model="username"
            :rules="[requiredRule]"
          >
          </q-input>
          <q-input
            class="q-py-md"
            outlined
            label="Password"
            v-model="password"
            :rules="[requiredRule]"
          >
          </q-input>
          <q-input
            class="q-py-sm"
            outlined
            label="Confirm Password"
            v-model="confirmPassword"
            :rules="[requiredRule, matchRule]"
          >
          </q-input>
          <q-btn
            color="primary"
            class="full-width q-mt-md"
            type="submit"
            @click="endpoint='api/user/', method = 'POST'"
          >
            Register
          </q-btn>
          <q-card-section class="text-center q-pt-md">
            <div>Go back to
              <a 
                role="button" 
                class="text-weight-bold text-primary" 
                style="text-decoration: none; cursor: pointer" 
                @click="state = 'login'"
              >
                Login Menu.
              </a>
            </div>
          </q-card-section>
        </q-form>
      </q-card>

      <q-card class="q-pa-lg" style="min-width: 600px;" v-if="state === 'loggedIn'">
        <q-card-section class="text-center">
            <div class="text-h5 text-weight-bold">Logged In</div>
            <div>You are currently logged in as <span class="text-weight-bold text-primary">{{ loggedInUser }}</span></div>
        </q-card-section>
        <q-form @submit="submit(endpoint, method)" class="row flex-center">
          <q-checkbox
            label="Log out from all devices"
            v-model="allDevices"
            class="q-mt-md"
          />
          <q-btn
            color="orange"
            class="full-width "
            type="submit"
            @click="endpoint = `api/auth/logout?everywhere=${allDevices}`; method = 'POST'"
          >
            Log Out
          </q-btn>
        </q-form>
        <p class="text-body1 text-bold q-mt-xl">
          Additional User Account Actions
        </p>

        <q-expansion-item
          header-class="text-bold shadow-2"
          label="Change Password"
          group="somegroup"
        >
          <q-form @submit="submit(endpoint, method)">
            <q-card-section class="text-center shadow-2 q-mt-sm q-mb-sm">
              <div>
                To change your password, enter your current and new password.
              </div>
              <q-input
                class="q-py-sm"
                outlined
                label="Current Password"
                v-model="password"
                :rules="[requiredRule]"
              >
              </q-input>
              <q-input
                class="q-py-lg"
                outlined
                label="New Password"
                v-model="newPassword"
                :rules="[requiredRule]"
              >
              </q-input>
              <q-btn
                color="primary"
                class="full-width "
                type="submit"
                @click="endpoint = 'api/user/password'; method = 'POST'"
              >
                Change Password
              </q-btn>
            </q-card-section>
          </q-form>
        </q-expansion-item>
        <q-expansion-item
          header-class="text-bold shadow-2"
          label="Delete Account"
          group="somegroup"
        >
          <q-form @submit="submit(endpoint, method)">
            <q-card-section class="text-center shadow-2 q-mt-sm q-mb-sm">
              <div>
                To delete your account, enter your password and press the delete button.
              </div>
              <q-input
                class="q-py-lg"
                outlined
                label="Password"
                v-model="deleteRequestPassword"
                :rules="[requiredRule]"
              >
              </q-input>
              <q-btn
                color="red"
                class="full-width "
                type="submit"
                @click="endpoint = 'api/user/'; method = 'DELETE'"
              >
                Delete User
              </q-btn>
            </q-card-section>
          </q-form>
        </q-expansion-item>
      </q-card>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { ref, watch } from 'vue';
  import { useQuasar } from 'quasar'
  import { useLoginStore } from '@/stores/LoginStore.js'
  import { storeToRefs } from 'pinia'

  const $q = useQuasar();

  $q.loading.show();

  const requiredRule = (val: string) => (val && val.length > 0) || "This field is required";
  const matchRule = (val: string) => (val && val === password.value) || 'Password mismatch';

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
  const endpoint = ref('');
  const method = ref('');

  const username = ref('');
  const password = ref('');
  const newPassword = ref('');
  const confirmPassword = ref('');
  const deleteRequestPassword = ref('');
  const allDevices = ref(false);

  function submit(endpoint: string, method: string) {
    console.log('endpoint = ', endpoint);
    console.log('method = ', method);

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
    allDevices.value = false;
  }
</script>

