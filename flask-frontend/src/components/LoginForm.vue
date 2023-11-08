<template>
  <q-card bordered class="q-pa-lg" style="min-width: 600px;">
    <q-card-section class="text-center">
        <div class="text-h5 text-weight-bold">Login</div>
        <div>Login below to access all API endpoints</div>
    </q-card-section>
    <q-form @submit="submit()">
      <q-input
        class="q-py-md"
        outlined
        label="Username"
        :rules="[requiredRule]"
        v-model="username"
      >
      </q-input>
      <q-input
        class="q-py-sm"
        outlined
        label="Password"
        :rules="[requiredRule]"
        v-model="password"
      >
      </q-input>
      <q-btn
        color="primary"
        class="full-width q-mt-md"
        type="submit"
      >
        Login
      </q-btn>
      <q-card-section class="text-center q-pt-md">
        <div>Don't have an account yet?
          <a 
            role="button" 
            class="text-weight-bold text-primary" 
            style="text-decoration: none; cursor: pointer" 
            @click="formState = 'register'"
          >
            Signup.
          </a>
        </div>
      </q-card-section>
    </q-form>
  </q-card>
</template>

<script setup lang="ts">
  import { ref } from 'vue';
  import * as api from '../api'
  import { Notify } from 'quasar'
  import { useLoginStore } from '@/stores/LoginStore.js'
  import { storeToRefs } from 'pinia'

  const store = useLoginStore();
  const { loggedInUser, formState } = storeToRefs(store);

  const requiredRule = (val: string) => (val && val.length > 0) || "This field is required";

  const username = ref('');
  const password = ref('');

  async function submit() {
    try {
      const res = await api.login(username.value, password.value);
      loggedInUser.value = JSON.parse(JSON.stringify(username.value));
      Notify.create({
        color: 'green-7',
        textColor: 'white',
        icon: 'done',
        message: `${res.data.message} for ${username.value}`
      });
    } catch(err: any) {
      Notify.create({
        color: 'red-5',
          textColor: 'white',
          icon: 'warning',
          message: err.response.data.message
      });
    }
  }

</script>