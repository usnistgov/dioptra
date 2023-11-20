<template>
  <q-card bordered class="q-pa-lg" style="min-width: 600px;">
    <q-card-section class="text-center">
        <div class="text-h5 text-weight-bold">Register</div>
        <div>Register a new user account</div>
    </q-card-section>
    <q-form @submit="submit()">
      <q-input
        class="q-py-sm"
        outlined
        label="Username"
        :rules="[requiredRule]"
        v-model="username"
      />
      <q-input
        class="q-py-md"
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
      <q-input
        class="q-py-sm"
        outlined
        label="Confirm Password"
        :type="showPassword ? 'text' : 'password'"
        :rules="[requiredRule, matchRule]"
        v-model="confirmPassword"
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
        Register
      </q-btn>
      <q-card-section class="text-center q-pt-md">
        <div>Go back to
          <a 
            role="button" 
            class="text-weight-bold text-primary" 
            style="text-decoration: none; cursor: pointer" 
            @click="formState = 'login'"
          >
            Login Menu.
          </a>
        </div>
      </q-card-section>
    </q-form>
  </q-card>
</template>

<script setup lang="ts">
  import { ref } from 'vue';
  import * as notify from '../notify';
  import * as api from '../api';
  import { useLoginStore } from '@/stores/LoginStore.js';
  import { storeToRefs } from 'pinia';

  const store = useLoginStore();
  const { formState } = storeToRefs(store);

  const requiredRule = (val: string) => (val && val.length > 0) || "This field is required";
  const matchRule = (val: string) => (val && val === password.value) || 'Password mismatch';

  const username = ref('');
  const password = ref('');
  const confirmPassword = ref('');
  const showPassword = ref(false);

  async function submit() {
    try {
      const res = await api.registerUser(username.value, password.value, confirmPassword.value);
      formState.value = 'login';
      notify.success(res.data.message);
    } catch (err: any) {
      notify.error(err.response.data.message);
    }
  }

</script>