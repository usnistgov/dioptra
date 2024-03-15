<template>
  <q-card bordered class="q-pa-lg" style="min-width: 40%;">
    <q-card-section class="text-center">
        <h4 class="text-weight-bold" style="margin-top: 0; margin-bottom: 0;">Login</h4>
        <p>Login below to access all API endpoints</p>
    </q-card-section>
    <q-form @submit="submit()">
      <q-input
        class="q-py-md"
        outlined
        label="Username"
        :rules="[requiredRule]"
        v-model="username"
      />
      <q-input
        class="q-py-sm"
        outlined
        label="Password"
        :type="showPassword ? 'text' : 'password'"
        :rules="[requiredRule]"
        v-model="password"
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
  import * as api from '@/services/loginApi';
  import { useLoginStore } from '@/stores/LoginStore.ts';
  import { storeToRefs } from 'pinia';
  import * as notify from '../notify';

  const store = useLoginStore();
  const { loggedInUser } = storeToRefs(store);

  const requiredRule = (val) => (val && val.length > 0) || "This field is required";

  const username = ref('');
  const password = ref('');
  const showPassword = ref(false);

  async function submit() {
    try {
      const res = await api.login(username.value, password.value);
      loggedInUser.value = JSON.parse(JSON.stringify(username.value));
      notify.success(`${res.data.status} for ${username.value}`);
    } catch(err) {
      notify.error(err.response.data.message);
    }
  }

</script>