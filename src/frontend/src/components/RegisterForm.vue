<template>
  <q-card bordered class="q-pa-lg" style="min-width: 600px;">
    <q-card-section class="text-center">
        <div class="text-h5 text-weight-bold">Register</div>
        <div>Register a new user account</div>
    </q-card-section>
    <q-form @submit="submit()">
      <q-input
        class="q-mt-md q-mb-sm"
        outlined
        label="Username"
        :rules="[requiredRule]"
        v-model="username"
      />
      <q-input
        class="q-mb-sm"
        outlined
        label="Email Address"
        :rules="[requiredRule, emailRule]"
        v-model="emailAddress"
      />
      <q-input
        class="q-mb-sm"
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
        class="q-mb-md"
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

<script setup>
  import { ref } from 'vue';
  import * as notify from '../notify';
  import * as api from '@/services/loginApi';
  import { useLoginStore } from '@/stores/LoginStore.ts';
  import { storeToRefs } from 'pinia';

  const store = useLoginStore();
  const { formState } = storeToRefs(store);

  const requiredRule = (val) => (val && val.length > 0) || "This field is required";
  const matchRule = (val) => (val && val === password.value) || 'Password mismatch';
  const emailRule = val => {
    const emailRegex = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$/;
    return (val && emailRegex.test(val)) || "Invalid email address";
  };


  const username = ref('');
  const password = ref('');
  const emailAddress = ref('');
  const confirmPassword = ref('');
  const showPassword = ref(false);

  async function submit() {
    try {
      const res = await api.registerUser(username.value, emailAddress.value, password.value, confirmPassword.value);
      console.log('register res = ', res)
      formState.value = 'login';
      notify.success(`Successfully created user '${res.data.username}'`);
    } catch (err) {
      console.log('err = ', err)
      notify.error(err.response.data.message);
    }
  }

</script>