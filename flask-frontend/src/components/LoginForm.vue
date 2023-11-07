<template>
  <q-card bordered class="q-pa-lg" style="min-width: 600px;">
    <q-card-section class="text-center">
        <div class="text-h5 text-weight-bold">Login</div>
        <div>Login below to access all API endpoints</div>
    </q-card-section>
    <q-form @submit="$emit('submit', 'api/auth/login', 'POST')">
      <q-input
        class="q-py-md"
        outlined
        label="Username"
        :rules="[requiredRule]"
        :model-value="username"
        @update:model-value="newValue => $emit('update:username', newValue)"
      >
      </q-input>
      <q-input
        class="q-py-sm"
        outlined
        label="Password"
        :rules="[requiredRule]"
        :model-value="password"
        @update:model-value="newValue => $emit('update:password', newValue)"
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
            @click="$emit('update:state', 'register')"
          >
            Signup.
          </a>
        </div>
      </q-card-section>
    </q-form>
  </q-card>
</template>

<script setup lang="ts">
  defineProps(['username', 'password', 'state'])
  defineEmits(['update:username', 'update:password', 'update:state', 'submit'])

  const requiredRule = (val: string) => (val && val.length > 0) || "This field is required";

</script>