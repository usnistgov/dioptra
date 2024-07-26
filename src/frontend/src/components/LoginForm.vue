<template>
  <q-card bordered class="q-pa-lg" style="min-width: 40%;">
    <q-card-section class="text-center">
        <h1 class="form-title" style="margin-top: 0; margin-bottom: 0;">Login</h1>
        <p>Login below to access all API endpoints</p>
    </q-card-section>
    <q-form @submit="submit()">
      <q-input
        class="q-py-md"
        outlined
        label="Username"
        :rules="[requiredRule]"
        v-model="username"
        aria-required="true"
      />
      <q-input
        class="q-py-sm"
        outlined
        label="Password"
        :type="showPassword ? 'text' : 'password'"
        :rules="[requiredRule]"
        v-model="password"
        aria-required="true"
      >
        <template v-slot:append>
          <q-icon
            :name="showPassword ? 'visibility' : 'visibility_off'"
            class="cursor-pointer"
            @click="showPassword = !showPassword"
          />
        </template>
      </q-input>
      <q-btn
        color="primary"
        class="full-width q-mt-md"
        type="submit"
      >
        Login
      </q-btn>
      <q-card-section class="text-center q-pt-md">
        <p>Don't have an account yet?
          <router-link 
            role="button" 
            class="text-weight-bold text-primary" 
            style="text-decoration: none; cursor: pointer" 
            to="/register"
          >
            Signup.
          </router-link >
        </p>
      </q-card-section>
    </q-form>
  </q-card>
</template>

<script setup>
  import { ref } from 'vue';
  import * as api from '@/services/dataApi';
  import { useLoginStore } from '@/stores/LoginStore.ts';
  import * as notify from '../notify';

  const store = useLoginStore()

  const requiredRule = (val) => (val && val.length > 0) || "This field is required";

  const username = ref('');
  const password = ref('');
  const showPassword = ref(false);

  async function submit() {
    try {
      const res = await api.login(username.value, password.value);
      callGetLoginStatus()
      notify.success(`${res.data.status} for ${username.value}`);
    } catch(err) {
      notify.error(err.response.data.message);
    }
  }

  async function callGetLoginStatus() {
    try {
      const res = await api.getLoginStatus()
      store.loggedInUser = res.data
      store.groups = res.data.groups
    } catch(err) {
      store.loggedInUser = ''
    }
  }

</script>