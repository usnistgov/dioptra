<template>
  <div :class="` flex-center q-mt-xl ${isMobile ? '' : 'flex q-pt-xl'}`">
    <q-card bordered class="q-pa-lg" style="min-width: 40%;">
      <q-card-section class="text-center">
          <h1 class="form-title" style="margin-top: 0; margin-bottom: 0;">Register</h1>
          <p>Register a new user account</p>
      </q-card-section>
      <q-form @submit="submit()">
        <q-input
          class="q-mt-md q-mb-sm"
          outlined
          label="Username"
          :rules="[requiredRule]"
          v-model="username"
          aria-required="true"
        />
        <q-input
          class="q-mb-sm"
          outlined
          label="Email Address"
          :rules="[requiredRule, emailRule]"
          v-model="email"
          aria-required="true"
        />
        <q-input
          class="q-mb-sm"
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
        <q-input
          class="q-mb-md"
          outlined
          label="Confirm Password"
          :type="showPassword ? 'text' : 'password'"
          :rules="[requiredRule, matchRule]"
          v-model="confirmPassword"
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
          Register
        </q-btn>
        <q-card-section class="text-center q-pt-md">
          <p>Go back to
            <router-link 
              role="button" 
              class="text-weight-bold text-primary" 
              style="text-decoration: none; cursor: pointer" 
              to="/login"
            >
              Login Menu.
            </router-link >
          </p>
        </q-card-section>
      </q-form>
    </q-card>
  </div>
</template>

<script setup>
  import { ref, inject } from 'vue';
  import * as notify from '../notify';
  import * as api from '@/services/dataApi';
  import { useRouter } from 'vue-router'
  
  const router = useRouter()

  const isMobile = inject('isMobile')

  const requiredRule = (val) => (val && val.length > 0) || "This field is required";
  const matchRule = (val) => (val && val === password.value) || 'Password mismatch';
  const emailRule = val => {
    const emailRegex = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$/;
    return (val && emailRegex.test(val)) || "Invalid email address";
  };

  const username = ref('');
  const password = ref('');
  const email = ref('');
  const confirmPassword = ref('');
  const showPassword = ref(false);

  async function submit() {
    try {
      const res = await api.registerUser(username.value, email.value, password.value, confirmPassword.value);
      router.push('/login')
      notify.success(`Successfully created user '${res.data.username}'`);
    } catch (err) {
      notify.error(err.response.data.message);
    }
  }

</script>